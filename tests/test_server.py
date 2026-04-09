from __future__ import absolute_import, print_function, unicode_literals

import asyncio
import unittest
from unittest import mock

from mcp_server.command_specs import FIRST_CLASS_MCP_COMMANDS

try:
    from mcp_server import server as ableton_server
except ModuleNotFoundError as exc:
    if exc.name == "mcp":
        ableton_server = None
    else:
        raise


@unittest.skipIf(ableton_server is None, "mcp SDK is not installed in this Python environment")
class ServerRegistrationTests(unittest.TestCase):
    def test_entrypoint_exists(self):
        self.assertTrue(callable(ableton_server.main))

    def test_expected_tools_are_registered(self):
        tool_names = set(tool.name for tool in asyncio.run(ableton_server.mcp.list_tools()))
        expected = set(FIRST_CLASS_MCP_COMMANDS)
        expected.add("ableton_raw_command")
        self.assertEqual(expected, tool_names)

    def test_raw_command_returns_stability_metadata(self):
        with mock.patch.object(ableton_server, "_invoke", return_value={"ok": True}) as invoke_mock:
            result = ableton_server.ableton_raw_command("health_check", {})
        invoke_mock.assert_called_once_with("health_check", {})
        self.assertEqual("health_check", result["command"])
        self.assertIn("stability", result)
        self.assertEqual({"ok": True}, result["result"])
