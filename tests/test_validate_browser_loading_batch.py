from __future__ import absolute_import, print_function, unicode_literals

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

from mcp_server.client import AbletonTransportError


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_browser_loading_batch.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_browser_loading_batch", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BrowserLoadingBatchValidatorTests(unittest.TestCase):
    def test_audit_third_party_searches_records_no_result_and_all_timeout_limitation(self):
        module = load_module()
        validator = module.BrowserLoadingBatchValidator()
        plugin_targets = [
            {
                "track_index": 4,
                "track_name": "5-Serum 2",
                "device_index": 0,
                "device_name": "Serum 2",
                "queries": ["Serum 2", "Serum"],
            }
        ]

        with mock.patch.object(validator, "call", return_value={"count": 0, "results": []}):
            with mock.patch.object(
                validator,
                "call_with_timeout",
                side_effect=AbletonTransportError("Timed out waiting for Ableton response"),
            ):
                audit, discovered_uri = validator.audit_third_party_searches(plugin_targets)

        self.assertIsNone(discovered_uri)
        self.assertEqual(plugin_targets, audit["plugin_targets"])
        self.assertTrue(any(search["category"] == "instruments" for search in audit["searches"]))
        self.assertTrue(any(search.get("timed_out") for search in audit["searches"]))
        self.assertTrue(
            any("No discoverable third-party plugin URI was surfaced" in item for item in audit["limitations"])
        )
        self.assertTrue(
            any("category='all'" in item for item in audit["limitations"])
        )


if __name__ == "__main__":
    unittest.main()
