from __future__ import absolute_import, print_function, unicode_literals

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mcp_server.client import AbletonCommandError


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_arrangement_batch_2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_arrangement_batch_2", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArrangementBatchValidatorTests(unittest.TestCase):
    def test_resolve_audio_file_uses_provided_absolute_file(self):
        module = load_module()
        with tempfile.NamedTemporaryFile(suffix=".wav") as audio_file:
            validator = module.ArrangementBatchValidator(
                audio_file=audio_file.name,
                host="localhost",
                port=9877,
                connect_timeout=1.0,
                response_timeout=1.0,
            )
            resolved = validator._resolve_audio_file()

        self.assertEqual(audio_file.name, resolved)
        self.assertEqual("provided_file", validator.summary["audio_input"]["mode"])
        self.assertEqual(audio_file.name, validator.summary["audio_input"]["file_path"])

    def test_resolve_audio_file_generates_temp_wav_and_cleanup_removes_it(self):
        module = load_module()
        validator = module.ArrangementBatchValidator(
            audio_file=None,
            host="localhost",
            port=9877,
            connect_timeout=1.0,
            response_timeout=1.0,
        )
        resolved = validator._resolve_audio_file()

        self.assertTrue(Path(resolved).is_file())
        self.assertEqual("generated_temp_wav", validator.summary["audio_input"]["mode"])

        with mock.patch.object(validator, "call", return_value={"ok": True}):
            validator.safe_cleanup()

        self.assertFalse(Path(resolved).exists())
        self.assertTrue(validator.summary["cleanup"]["temp_audio_file_removed"])

    def test_run_records_mutation_audit_summary_and_audio_move_policy(self):
        module = load_module()

        validator = module.ArrangementBatchValidator(
            audio_file=None,
            host="localhost",
            port=9877,
            connect_timeout=1.0,
            response_timeout=1.0,
        )

        def fake_call(command_name, params=None):
            params = params or {}
            if command_name == "health_check":
                return {"status": "ok"}
            if command_name == "get_session_info":
                return {
                    "track_count": 2,
                    "is_playing": False,
                    "current_song_time": 0.0,
                    "can_undo": True,
                    "can_redo": False,
                }
            if command_name == "create_audio_track":
                return {"index": 10}
            if command_name == "create_midi_track":
                return {"index": 11}
            if command_name == "set_track_name":
                return {"name": params.get("name", "")}
            if command_name == "create_arrangement_audio_clip" and int(params.get("track_index", -1)) == 11:
                raise AbletonCommandError(
                    "Ableton command 'create_arrangement_audio_clip' failed: Track 11 is a MIDI track, not audio"
                )
            if command_name == "delete_track":
                return {"deleted_index": params.get("track_index")}
            return {"ok": True}

        fake_audit = {
            "status": "ok",
            "mutate_applied": True,
            "undo_reverted": True,
            "redo_restored": True,
            "undo_redo": {
                "before": {"can_undo": True, "can_redo": False, "available": True},
                "after_mutate": {"can_undo": True, "can_redo": True, "available": True},
                "after_undo": {"can_undo": True, "can_redo": True, "available": True},
                "after_redo": {"can_undo": True, "can_redo": True, "available": True},
            },
            "side_effects": {
                "before": {"is_playing": False, "current_song_time": 0.0, "selected_track": None},
                "after": {"is_playing": False, "current_song_time": 0.0, "selected_track": None},
                "changed": {
                    "is_playing": False,
                    "current_song_time": False,
                    "selected_track": False,
                },
            },
        }

        with mock.patch.object(validator, "_resolve_audio_file") as resolve_mock:
            validator.audio_file = "/tmp/fake-audio.wav"
            validator.summary["audio_input"] = {
                "mode": "generated_temp_wav",
                "file_path": validator.audio_file,
            }
            resolve_mock.side_effect = lambda: validator.audio_file
            with mock.patch.object(validator, "call", side_effect=fake_call):
                with mock.patch.object(
                    validator,
                    "_audit_create_audio_clip_round_trip",
                    return_value=dict(fake_audit),
                ):
                    with mock.patch.object(
                        validator,
                        "_audit_resize_round_trip",
                        return_value=dict(fake_audit),
                    ):
                        with mock.patch.object(
                            validator,
                            "_audit_move_midi_round_trip",
                            return_value=dict(fake_audit),
                        ):
                            with mock.patch.object(
                                validator,
                                "_audit_duplicate_to_arrangement_round_trip",
                                return_value=dict(fake_audit),
                            ):
                                with mock.patch.object(
                                    validator,
                                    "_audit_audio_move_policy",
                                    return_value={
                                        "status": "intentionally_unsupported_confirmed",
                                        "error": "MIDI clips only",
                                    },
                                ):
                                    summary = validator.run()

        self.assertIn("create_arrangement_audio_clip", summary["mutation_audits"])
        self.assertIn("resize_arrangement_clip", summary["mutation_audits"])
        self.assertIn("move_arrangement_clip_midi", summary["mutation_audits"])
        self.assertIn("duplicate_to_arrangement", summary["mutation_audits"])
        self.assertEqual(
            "intentionally_unsupported_confirmed",
            summary["audio_move_policy_audit"]["status"],
        )
        self.assertIn("undo", summary["validated_commands"])
        self.assertIn("redo", summary["validated_commands"])

    def test_audio_move_policy_audit_requires_midi_only_error(self):
        module = load_module()
        validator = module.ArrangementBatchValidator(
            audio_file="/tmp/fake-audio.wav",
            host="localhost",
            port=9877,
            connect_timeout=1.0,
            response_timeout=1.0,
        )

        def fake_call(command_name, params=None):
            if command_name == "create_arrangement_audio_clip":
                return {"ok": True}
            if command_name == "move_arrangement_clip":
                raise AbletonCommandError("Ableton command 'move_arrangement_clip' failed: MIDI clips only")
            raise AssertionError("Unexpected command {}".format(command_name))

        with mock.patch.object(validator, "_create_disposable_audio_track", return_value=5):
            with mock.patch.object(validator, "call", side_effect=fake_call):
                result = validator._audit_audio_move_policy()

        self.assertEqual("intentionally_unsupported_confirmed", result["status"])
        self.assertTrue(any(case["command"] == "move_arrangement_clip" for case in validator.summary["negative_cases"]))


if __name__ == "__main__":
    unittest.main()
