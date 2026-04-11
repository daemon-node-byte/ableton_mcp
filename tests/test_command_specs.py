from __future__ import absolute_import, print_function, unicode_literals

import re
import unittest
from pathlib import Path

from mcp_server.command_specs import COMMAND_SPECS, FIRST_CLASS_MCP_COMMANDS


ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_PATH = ROOT / "AbletonMCP_Remote_Script" / "__init__.py"


class CommandSpecTests(unittest.TestCase):
    def test_command_spec_registry_covers_dispatcher(self):
        dispatcher_text = DISPATCHER_PATH.read_text()
        dispatcher_commands = re.findall(r'cmd_type == "([^"]+)"', dispatcher_text)
        self.assertEqual(set(dispatcher_commands), set(COMMAND_SPECS))

    def test_first_class_commands_exist_and_are_marked_exposed(self):
        for command_name in FIRST_CLASS_MCP_COMMANDS:
            self.assertIn(command_name, COMMAND_SPECS)
            self.assertTrue(COMMAND_SPECS[command_name].mcp_exposed)

    def test_no_duplicate_private_method_names_exist_across_remote_script_modules(self):
        method_locations = {}
        duplicates = {}
        for path in sorted((ROOT / "AbletonMCP_Remote_Script").glob("*.py")):
            text = path.read_text()
            for method_name in re.findall(r"^\s*def (_[A-Za-z0-9_]+)\(", text, flags=re.MULTILINE):
                location = "{}:{}".format(path.name, method_name)
                if method_name in method_locations:
                    duplicates.setdefault(method_name, [method_locations[method_name]])
                    duplicates[method_name].append(location)
                else:
                    method_locations[method_name] = location
        self.assertEqual({}, duplicates)

    def test_device_audit_specs_match_lom_aligned_expectations(self):
        self.assertEqual("confirmed", COMMAND_SPECS["toggle_device"].stability)
        self.assertEqual("confirmed", COMMAND_SPECS["set_device_enabled"].stability)
        self.assertEqual("confirmed", COMMAND_SPECS["move_device"].stability)
        self.assertIn("Track.insert_device", COMMAND_SPECS["load_instrument_or_effect"].notes)
        self.assertIn("track.devices ordering", COMMAND_SPECS["get_track_devices"].notes)
        self.assertIn("excluded the mixer device", COMMAND_SPECS["get_track_devices"].notes)
