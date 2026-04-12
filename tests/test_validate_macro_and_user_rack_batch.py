from __future__ import absolute_import, print_function, unicode_literals

import importlib.util
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_macro_and_user_rack_batch.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_macro_and_user_rack_batch", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeClient(object):
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def send_command(self, name, params):
        self.calls.append((name, params))
        response = self.responses[name]
        if isinstance(response, Exception):
            raise response
        return response


class MacroAndUserRackBatchValidatorTests(unittest.TestCase):
    def test_parse_args_requires_paired_manual_target_flags(self):
        module = load_module()
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                module.parse_args(["--user-rack-track-index", "1"])
            with self.assertRaises(SystemExit):
                module.parse_args(["--user-rack-device-index", "2"])

    def test_run_skips_memory_bank_inventory_when_session_is_unsaved(self):
        module = load_module()
        fake_client = FakeClient(
            {
                "health_check": {"status": "ok"},
                "get_session_info": {"track_count": 5},
                "get_session_path": {"path": ""},
            }
        )
        with mock.patch.object(module, "AbletonRemoteClient", return_value=fake_client):
            validator = module.MacroAndUserRackBatchValidator()

        validator.validate_system_owned_macro_round_trip = mock.Mock()
        validator.validate_unsupported_macro_authoring = mock.Mock()
        validator.validate_user_rack = mock.Mock()
        validator.safe_cleanup = mock.Mock()

        summary = validator.run()

        self.assertEqual("", summary["baseline"]["session_path"])
        self.assertEqual(0, summary["baseline"]["system_owned_rack_count"])
        self.assertIn(
            {
                "name": "get_system_owned_racks",
                "reason": "Current Live Set is not saved, so Memory Bank inventory is unavailable",
            },
            summary["skipped_checks"],
        )
        validator.validate_system_owned_macro_round_trip.assert_called_once_with({"count": 0, "racks": []})
        validator.validate_unsupported_macro_authoring.assert_called_once_with("")
        validator.validate_user_rack.assert_called_once_with("")
        self.assertEqual(
            ["health_check", "get_session_info", "get_session_path"],
            [name for name, _params in fake_client.calls],
        )

    def test_validate_user_rack_records_direct_and_imported_summary_fields(self):
        module = load_module()
        fake_client = FakeClient(
            {
                "get_track_devices": {
                    "devices": [
                        {
                            "index": 0,
                            "name": "Imported Rack",
                            "is_rack": True,
                        }
                    ]
                },
                "get_rack_structure": {
                    "rack": {
                        "name": "Imported Rack",
                        "has_macro_mappings": True,
                        "visible_macro_count": 4,
                    }
                },
                "get_rack_macros": {
                    "rack_name": "Imported Rack",
                    "macros": [
                        {"index": 0, "name": "Tone"},
                        {"index": 1, "name": "Drive"},
                    ],
                },
                "refresh_rack_memory_entry": {"rack_id": "rack-123"},
                "get_system_owned_racks": {
                    "racks": [
                        {
                            "rack_id": "rack-123",
                            "imported": True,
                            "macro_count": 2,
                            "notes": ["Imported via refresh_rack_memory_entry"],
                        }
                    ]
                },
            }
        )
        with mock.patch.object(module, "AbletonRemoteClient", return_value=fake_client):
            validator = module.MacroAndUserRackBatchValidator(
                user_rack_track_index=3,
                user_rack_device_index=0,
            )

        validator.validate_user_rack("/tmp/Imported Rack Validation.als")

        audit = validator.summary["user_rack_audit"]
        self.assertEqual("validated_with_manual_target", audit["status"])
        self.assertEqual(3, audit["track_index"])
        self.assertEqual(0, audit["device_index"])
        self.assertEqual("devices 0", audit["rack_path"])
        self.assertEqual("Imported Rack", audit["rack_name"])
        self.assertEqual(["Tone", "Drive"], audit["direct_macro_names"])
        self.assertEqual(2, audit["direct_macro_count"])
        self.assertEqual(4, audit["direct_visible_macro_count"])
        self.assertTrue(audit["direct_has_macro_mappings"])
        self.assertEqual("rack-123", audit["memory_bank_rack_id"])
        self.assertTrue(audit["memory_bank_imported"])
        self.assertEqual(2, audit["memory_bank_macro_count"])
        self.assertEqual(["Imported via refresh_rack_memory_entry"], audit["memory_bank_notes"])

    def test_main_prints_success_envelope(self):
        module = load_module()

        class FakeValidator(object):
            def __init__(self, *args, **kwargs):
                pass

            def run(self):
                return {"validated_commands": ["get_rack_structure"]}

        buffer = io.StringIO()
        with mock.patch.object(module, "MacroAndUserRackBatchValidator", FakeValidator):
            with redirect_stdout(buffer):
                module.main([])

        payload = json.loads(buffer.getvalue())
        self.assertEqual("ok", payload["status"])
        self.assertEqual(["get_rack_structure"], payload["summary"]["validated_commands"])


if __name__ == "__main__":
    unittest.main()
