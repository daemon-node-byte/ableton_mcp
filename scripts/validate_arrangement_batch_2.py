from __future__ import absolute_import, print_function, unicode_literals

import argparse
import json
import os
import struct
import sys
import tempfile
import time
import wave

from mcp_server.client import AbletonCommandError, AbletonRemoteClient


DEFAULT_AUDIO_CREATE_START = 64.0
DEFAULT_AUDIO_MOVE_START = 72.0
DEFAULT_RESIZE_START = 80.0
DEFAULT_MOVE_START = 96.0
DEFAULT_MOVED_MIDI_START = 104.0
DEFAULT_DUPLICATED_START = 120.0
DEFAULT_SESSION_SLOT_INDEX = 0


def _approx_equal(left, right, tolerance=0.001):
    return abs(float(left) - float(right)) <= tolerance


class ArrangementBatchValidator(object):
    def __init__(self, audio_file, host, port, connect_timeout, response_timeout):
        self.audio_file = audio_file
        self._provided_audio_file = audio_file
        self._generated_audio_file = None
        self.client = AbletonRemoteClient(
            host=host,
            port=port,
            connect_timeout=connect_timeout,
            response_timeout=response_timeout,
        )
        self.created_track_indices = []
        self.summary = {
            "baseline": {},
            "audio_input": {},
            "validated_commands": [],
            "negative_cases": [],
            "mutation_audits": {},
            "audio_move_policy_audit": {},
            "undo_behavior": "arrangement mutation residual pass in progress",
            "cleanup": {
                "deleted_tracks": [],
                "temp_audio_file": None,
                "temp_audio_file_removed": False,
            },
        }

    def call(self, command_name, params=None):
        return self.client.send_command(command_name, params or {})

    def expect_error(self, command_name, params, expected_substring):
        try:
            self.call(command_name, params)
        except AbletonCommandError as exc:
            message = str(exc)
            if expected_substring not in message:
                raise AssertionError(
                    "Expected '{}' in error for '{}', got '{}'".format(
                        expected_substring, command_name, message
                    )
                )
            self.summary["negative_cases"].append(
                {"command": command_name, "status": "ok", "matched": expected_substring}
            )
            return
        raise AssertionError("Expected '{}' to fail".format(command_name))

    def require(self, condition, message):
        if not condition:
            raise AssertionError(message)

    def _record_validated_command(self, command_name):
        if command_name not in self.summary["validated_commands"]:
            self.summary["validated_commands"].append(command_name)

    def _create_temp_audio_file(self):
        fd, temp_path = tempfile.mkstemp(prefix="ableton-mcp-arrangement-", suffix=".wav")
        os.close(fd)
        try:
            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(44100)
                wav_file.writeframes(struct.pack("<h", 0) * 22050)
        except Exception:
            if os.path.isfile(temp_path):
                os.unlink(temp_path)
            raise
        self._generated_audio_file = temp_path
        self.summary["cleanup"]["temp_audio_file"] = temp_path
        return temp_path

    def _resolve_audio_file(self):
        if self._provided_audio_file:
            provided_file = str(self._provided_audio_file)
            if not os.path.isabs(provided_file):
                raise ValueError("--audio-file must be an absolute path")
            if not os.path.isfile(provided_file):
                raise ValueError("--audio-file does not exist: {}".format(provided_file))
            self.audio_file = provided_file
            self.summary["audio_input"] = {
                "mode": "provided_file",
                "file_path": provided_file,
            }
            return provided_file

        generated_file = self._create_temp_audio_file()
        self.audio_file = generated_file
        self.summary["audio_input"] = {
            "mode": "generated_temp_wav",
            "file_path": generated_file,
        }
        return generated_file

    def _undo_redo_state(self):
        session_info = self.call("get_session_info", {})
        can_undo = session_info.get("can_undo")
        can_redo = session_info.get("can_redo")
        return {
            "can_undo": bool(can_undo) if can_undo is not None else None,
            "can_redo": bool(can_redo) if can_redo is not None else None,
            "available": can_undo is not None and can_redo is not None,
        }

    def _capture_observable_state(self):
        session_info = self.call("get_session_info", {})
        state = {
            "is_playing": bool(session_info.get("is_playing")),
            "current_song_time": float(session_info.get("current_song_time", 0.0)),
            "selected_track": None,
        }
        try:
            selected = self.call("get_selected_track", {})
            state["selected_track"] = {
                "selection_type": selected.get("selection_type"),
                "track_index": selected.get("track_index"),
                "return_index": selected.get("return_index"),
                "name": selected.get("name"),
            }
        except Exception as exc:
            state["selected_track"] = {"available": False, "error": str(exc)}
        return state

    def _summarize_side_effects(self, before_state, after_state):
        return {
            "before": before_state,
            "after": after_state,
            "changed": {
                "is_playing": before_state.get("is_playing") != after_state.get("is_playing"),
                "current_song_time": not _approx_equal(
                    before_state.get("current_song_time", 0.0),
                    after_state.get("current_song_time", 0.0),
                ),
                "selected_track": before_state.get("selected_track") != after_state.get("selected_track"),
            },
        }

    def _ensure_audio_clip_presence(self, track_index, start_time, expected_present):
        clips = self.track_clips(track_index)
        matching = [
            clip
            for clip in clips
            if _approx_equal(clip["start_time"], start_time) and bool(clip.get("is_audio_clip"))
        ]
        if expected_present:
            self.require(bool(matching), "Expected audio clip at start_time {}".format(start_time))
        else:
            self.require(not matching, "Audio clip should not be present at start_time {}".format(start_time))
        return matching[0] if matching else None

    def _get_midi_clip_at(self, track_index, start_time):
        for clip in self.track_clips(track_index):
            if _approx_equal(clip["start_time"], start_time) and bool(clip.get("is_midi_clip")):
                return clip
        return None

    def _ensure_midi_clip_length(self, track_index, start_time, expected_length):
        clip = self._get_midi_clip_at(track_index, start_time)
        self.require(clip is not None, "Expected MIDI clip at start_time {}".format(start_time))
        self.require(
            _approx_equal(clip["length"], expected_length),
            "Expected MIDI clip length {} at start_time {}, got {}".format(
                expected_length,
                start_time,
                clip["length"],
            ),
        )
        return clip

    def _run_round_trip_audit(self, audit_name, mutate_callback, verify_mutated, verify_undone, verify_redone):
        def wait_for_verification(verify_callback, mutate_result, phase_label, timeout=2.0, interval=0.1):
            deadline = time.time() + timeout
            last_error = None
            while time.time() < deadline:
                try:
                    if bool(verify_callback(mutate_result)):
                        return True, None
                except Exception as exc:
                    last_error = str(exc)
                time.sleep(interval)
            if last_error:
                return False, "{} {} verification failed: {}".format(audit_name, phase_label, last_error)
            return False, "{} {} verification failed".format(audit_name, phase_label)

        state_before = self._capture_observable_state()
        result = {
            "status": "failed",
            "mutate_applied": False,
            "undo_reverted": False,
            "redo_restored": False,
            "undo_redo": {"before": self._undo_redo_state()},
            "side_effects": None,
            "failure_phase": None,
            "failure_error": None,
        }

        mutate_result = None
        try:
            mutate_result = mutate_callback()
            result["undo_redo"]["after_mutate"] = self._undo_redo_state()
            mutated_ok, mutate_error = wait_for_verification(verify_mutated, mutate_result, "mutate")
            result["mutate_applied"] = mutated_ok
            if not mutated_ok:
                result["failure_phase"] = "mutate"
                result["failure_error"] = mutate_error
                return result

            self.call("undo", {})
            result["undo_redo"]["after_undo"] = self._undo_redo_state()
            undone_ok, undo_error = wait_for_verification(verify_undone, mutate_result, "undo")
            result["undo_reverted"] = undone_ok
            if not undone_ok:
                result["failure_phase"] = "undo"
                result["failure_error"] = undo_error
                return result

            self.call("redo", {})
            result["undo_redo"]["after_redo"] = self._undo_redo_state()
            redone_ok, redo_error = wait_for_verification(verify_redone, mutate_result, "redo")
            result["redo_restored"] = redone_ok
            if not redone_ok:
                result["failure_phase"] = "redo"
                result["failure_error"] = redo_error
                return result

            result["status"] = "ok"
            return result
        except Exception as exc:
            result["failure_phase"] = result["failure_phase"] or "exception"
            result["failure_error"] = str(exc)
            return result
        finally:
            state_after = self._capture_observable_state()
            result["side_effects"] = self._summarize_side_effects(state_before, state_after)

    def find_clip(self, clips, start_time):
        for clip in clips:
            if _approx_equal(clip["start_time"], start_time):
                return clip
        raise AssertionError("Expected clip at start_time {}".format(start_time))

    def track_clips(self, track_index):
        return self.call("get_arrangement_clips", {"track_index": track_index})["clips"]

    def _create_disposable_audio_track(self, name):
        created = self.call("create_audio_track", {})
        track_index = int(created["index"])
        self.created_track_indices.append(track_index)
        self.call("set_track_name", {"track_index": track_index, "name": name})
        return track_index

    def _create_disposable_midi_track(self, name):
        created = self.call("create_midi_track", {})
        track_index = int(created["index"])
        self.created_track_indices.append(track_index)
        self.call("set_track_name", {"track_index": track_index, "name": name})
        return track_index

    def safe_cleanup(self):
        for track_index in sorted(self.created_track_indices, reverse=True):
            try:
                self.call("delete_track", {"track_index": track_index})
                self.summary["cleanup"]["deleted_tracks"].append(track_index)
            except Exception:
                pass
        if self._generated_audio_file and os.path.isfile(self._generated_audio_file):
            try:
                os.unlink(self._generated_audio_file)
                self.summary["cleanup"]["temp_audio_file_removed"] = True
            except Exception:
                self.summary["cleanup"]["temp_audio_file_removed"] = False

    def _audit_create_audio_clip_round_trip(self):
        audio_track_index = self._create_disposable_audio_track("Arrangement Audit Create Audio")

        def mutate_callback():
            return self.call(
                "create_arrangement_audio_clip",
                {
                    "track_index": audio_track_index,
                    "file_path": self.audio_file,
                    "start_time": DEFAULT_AUDIO_CREATE_START,
                },
            )

        def verify_mutated(_result):
            clip = self._ensure_audio_clip_presence(audio_track_index, DEFAULT_AUDIO_CREATE_START, True)
            return clip is not None

        def verify_undone(_result):
            self._ensure_audio_clip_presence(audio_track_index, DEFAULT_AUDIO_CREATE_START, False)
            return True

        def verify_redone(_result):
            clip = self._ensure_audio_clip_presence(audio_track_index, DEFAULT_AUDIO_CREATE_START, True)
            return clip is not None

        return self._run_round_trip_audit(
            "create_arrangement_audio_clip",
            mutate_callback,
            verify_mutated,
            verify_undone,
            verify_redone,
        )

    def _audit_resize_round_trip(self):
        midi_track_index = self._create_disposable_midi_track("Arrangement Audit Resize MIDI")

        self.call(
            "create_arrangement_midi_clip",
            {"track_index": midi_track_index, "start_time": DEFAULT_RESIZE_START, "length": 4.0},
        )
        self._ensure_midi_clip_length(midi_track_index, DEFAULT_RESIZE_START, 4.0)

        def mutate_callback():
            return self.call(
                "resize_arrangement_clip",
                {"track_index": midi_track_index, "start_time": DEFAULT_RESIZE_START, "length": 6.0},
            )

        def verify_mutated(_result):
            self._ensure_midi_clip_length(midi_track_index, DEFAULT_RESIZE_START, 6.0)
            return True

        def verify_undone(_result):
            self._ensure_midi_clip_length(midi_track_index, DEFAULT_RESIZE_START, 4.0)
            return True

        def verify_redone(_result):
            self._ensure_midi_clip_length(midi_track_index, DEFAULT_RESIZE_START, 6.0)
            return True

        return self._run_round_trip_audit(
            "resize_arrangement_clip",
            mutate_callback,
            verify_mutated,
            verify_undone,
            verify_redone,
        )

    def _audit_move_midi_round_trip(self):
        midi_track_index = self._create_disposable_midi_track("Arrangement Audit Move MIDI")

        self.call(
            "create_arrangement_midi_clip",
            {"track_index": midi_track_index, "start_time": DEFAULT_MOVE_START, "length": 4.0},
        )
        self.require(
            self._get_midi_clip_at(midi_track_index, DEFAULT_MOVE_START) is not None,
            "Expected setup MIDI clip for move audit",
        )

        def mutate_callback():
            return self.call(
                "move_arrangement_clip",
                {
                    "track_index": midi_track_index,
                    "start_time": DEFAULT_MOVE_START,
                    "new_start_time": DEFAULT_MOVED_MIDI_START,
                },
            )

        def verify_mutated(_result):
            return (
                self._get_midi_clip_at(midi_track_index, DEFAULT_MOVE_START) is None
                and self._get_midi_clip_at(midi_track_index, DEFAULT_MOVED_MIDI_START) is not None
            )

        def verify_undone(_result):
            return (
                self._get_midi_clip_at(midi_track_index, DEFAULT_MOVE_START) is not None
                and self._get_midi_clip_at(midi_track_index, DEFAULT_MOVED_MIDI_START) is None
            )

        def verify_redone(_result):
            return (
                self._get_midi_clip_at(midi_track_index, DEFAULT_MOVE_START) is None
                and self._get_midi_clip_at(midi_track_index, DEFAULT_MOVED_MIDI_START) is not None
            )

        return self._run_round_trip_audit(
            "move_arrangement_clip_midi",
            mutate_callback,
            verify_mutated,
            verify_undone,
            verify_redone,
        )

    def _audit_duplicate_to_arrangement_round_trip(self):
        midi_track_index = self._create_disposable_midi_track("Arrangement Audit Duplicate MIDI")

        self.call("create_clip", {"track_index": midi_track_index, "slot_index": DEFAULT_SESSION_SLOT_INDEX, "length": 4.0})
        midi_notes = [
            {"pitch": 60, "time": 0.0, "duration": 0.5, "velocity": 100, "mute": False},
            {"pitch": 64, "time": 1.0, "duration": 0.5, "velocity": 100, "mute": False},
            {"pitch": 67, "time": 2.0, "duration": 0.5, "velocity": 100, "mute": False},
        ]
        self.call(
            "add_notes_to_clip",
            {
                "track_index": midi_track_index,
                "slot_index": DEFAULT_SESSION_SLOT_INDEX,
                "notes": midi_notes,
            },
        )

        def mutate_callback():
            return self.call(
                "duplicate_to_arrangement",
                {
                    "track_index": midi_track_index,
                    "slot_index": DEFAULT_SESSION_SLOT_INDEX,
                    "start_time": DEFAULT_DUPLICATED_START,
                },
            )

        def verify_mutated(_result):
            clip = self._get_midi_clip_at(midi_track_index, DEFAULT_DUPLICATED_START)
            if clip is None:
                return False
            note_result = self.call(
                "get_arrangement_clip_notes",
                {"track_index": midi_track_index, "start_time": DEFAULT_DUPLICATED_START},
            )
            return int(note_result.get("count", 0)) == 3

        def verify_undone(_result):
            return self._get_midi_clip_at(midi_track_index, DEFAULT_DUPLICATED_START) is None

        def verify_redone(_result):
            clip = self._get_midi_clip_at(midi_track_index, DEFAULT_DUPLICATED_START)
            if clip is None:
                return False
            note_result = self.call(
                "get_arrangement_clip_notes",
                {"track_index": midi_track_index, "start_time": DEFAULT_DUPLICATED_START},
            )
            return int(note_result.get("count", 0)) == 3

        return self._run_round_trip_audit(
            "duplicate_to_arrangement",
            mutate_callback,
            verify_mutated,
            verify_undone,
            verify_redone,
        )

    def _audit_audio_move_policy(self):
        audio_track_index = self._create_disposable_audio_track("Arrangement Audit Audio Move Policy")

        self.call(
            "create_arrangement_audio_clip",
            {
                "track_index": audio_track_index,
                "file_path": self.audio_file,
                "start_time": DEFAULT_AUDIO_MOVE_START,
            },
        )
        try:
            self.call(
                "move_arrangement_clip",
                {
                    "track_index": audio_track_index,
                    "start_time": DEFAULT_AUDIO_MOVE_START,
                    "new_start_time": DEFAULT_AUDIO_MOVE_START + 8.0,
                },
            )
        except AbletonCommandError as exc:
            message = str(exc)
            self.require("MIDI clips only" in message, "Unexpected audio move error: {}".format(message))
            self.summary["negative_cases"].append(
                {
                    "command": "move_arrangement_clip",
                    "status": "ok",
                    "matched": "MIDI clips only",
                }
            )
            return {
                "status": "intentionally_unsupported_confirmed",
                "error": message,
            }
        raise AssertionError("Audio move unexpectedly succeeded; contract drifted from intentionally unsupported state")

    def run(self):
        try:
            self._resolve_audio_file()
            baseline = self.call("health_check", {})
            session_info = self.call("get_session_info", {})
            self.summary["baseline"] = {
                "health_check": baseline,
                "track_count": session_info["track_count"],
            }

            failures = []

            mutation_audits = (
                ("create_arrangement_audio_clip", "create_arrangement_audio_clip", self._audit_create_audio_clip_round_trip),
                ("resize_arrangement_clip", "resize_arrangement_clip", self._audit_resize_round_trip),
                ("move_arrangement_clip_midi", "move_arrangement_clip", self._audit_move_midi_round_trip),
                ("duplicate_to_arrangement", "duplicate_to_arrangement", self._audit_duplicate_to_arrangement_round_trip),
            )
            for audit_key, command_name, callback in mutation_audits:
                try:
                    audit_result = callback()
                    self.summary["mutation_audits"][audit_key] = audit_result
                    if audit_result.get("status") == "ok":
                        self._record_validated_command(command_name)
                        self._record_validated_command("undo")
                        self._record_validated_command("redo")
                    else:
                        failures.append(audit_key)
                except Exception as exc:
                    self.summary["mutation_audits"][audit_key] = {
                        "status": "failed",
                        "error": str(exc),
                    }
                    failures.append(audit_key)

            try:
                self.summary["audio_move_policy_audit"] = self._audit_audio_move_policy()
            except Exception as exc:
                self.summary["audio_move_policy_audit"] = {
                    "status": "failed",
                    "error": str(exc),
                }
                failures.append("audio_move_policy_audit")

            negative_midi_track_index = self._create_disposable_midi_track("Arrangement Audit Negative MIDI")
            self.expect_error(
                "create_arrangement_audio_clip",
                {
                    "track_index": negative_midi_track_index,
                    "file_path": self.audio_file,
                    "start_time": DEFAULT_AUDIO_CREATE_START,
                },
                "is a MIDI track",
            )

            if failures:
                self.summary["undo_behavior"] = (
                    "not fully confirmed; see mutation_audits for failing arrangement residual cases"
                )
                raise AssertionError("Arrangement residual audits failed: {}".format(", ".join(failures)))

            self.summary["undo_behavior"] = (
                "manually confirmed for create_arrangement_audio_clip, resize_arrangement_clip, "
                "move_arrangement_clip (MIDI), and duplicate_to_arrangement via mutate/undo/redo readback"
            )

            return self.summary
        finally:
            self.safe_cleanup()


def main():
    parser = argparse.ArgumentParser(description="Validate Arrangement Batch 2 against a running Ableton bridge.")
    parser.add_argument(
        "--audio-file",
        help=(
            "Optional absolute path to an audio file for import testing. "
            "If omitted, the validator generates a temporary WAV file."
        ),
    )
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=9877)
    parser.add_argument("--connect-timeout", type=float, default=5.0)
    parser.add_argument("--response-timeout", type=float, default=30.0)
    args = parser.parse_args()

    if args.audio_file and not args.audio_file.startswith("/"):
        parser.error("--audio-file must be an absolute path")

    validator = ArrangementBatchValidator(
        audio_file=args.audio_file,
        host=args.host,
        port=args.port,
        connect_timeout=args.connect_timeout,
        response_timeout=args.response_timeout,
    )
    try:
        summary = validator.run()
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc), "summary": validator.summary}, indent=2, sort_keys=True))
        raise
    print(json.dumps({"status": "ok", "summary": summary}, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Arrangement Batch 2 validation failed: {}".format(exc), file=sys.stderr)
        raise
