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

    def test_create_arrangement_audio_clip_wrapper_forwards_expected_params(self):
        with mock.patch.object(ableton_server, "_invoke", return_value={"ok": True}) as invoke_mock:
            result = ableton_server.create_arrangement_audio_clip(2, "/tmp/test.wav", 64.0)
        invoke_mock.assert_called_once_with(
            "create_arrangement_audio_clip",
            {"track_index": 2, "file_path": "/tmp/test.wav", "start_time": 64.0},
        )
        self.assertEqual({"ok": True}, result)

    def test_move_arrangement_clip_wrapper_uses_optional_selector(self):
        with mock.patch.object(ableton_server, "_invoke", return_value={"ok": True}) as invoke_mock:
            result = ableton_server.move_arrangement_clip(3, 88.0, start_time=80.0)
        invoke_mock.assert_called_once_with(
            "move_arrangement_clip",
            {"track_index": 3, "new_start_time": 88.0, "start_time": 80.0},
        )
        self.assertEqual({"ok": True}, result)

    def test_duplicate_to_arrangement_wrapper_forwards_expected_params(self):
        with mock.patch.object(ableton_server, "_invoke", return_value={"ok": True}) as invoke_mock:
            result = ableton_server.duplicate_to_arrangement(1, 0, start_time=96.0)
        invoke_mock.assert_called_once_with(
            "duplicate_to_arrangement",
            {"track_index": 1, "slot_index": 0, "start_time": 96.0},
        )
        self.assertEqual({"ok": True}, result)

    def test_get_browser_tree_wrapper_forwards_expected_params(self):
        with mock.patch.object(ableton_server, "_invoke", return_value={"ok": True}) as invoke_mock:
            result = ableton_server.get_browser_tree("instruments")
        invoke_mock.assert_called_once_with("get_browser_tree", {"category_type": "instruments"})
        self.assertEqual({"ok": True}, result)

    def test_search_browser_wrapper_forwards_expected_params(self):
        with mock.patch.object(ableton_server, "_invoke", return_value={"ok": True}) as invoke_mock:
            result = ableton_server.search_browser("drift", "instruments")
        invoke_mock.assert_called_once_with(
            "search_browser",
            {"query": "drift", "category": "instruments"},
        )
        self.assertEqual({"ok": True}, result)

    def test_load_instrument_or_effect_wrapper_forwards_expected_params(self):
        with mock.patch.object(ableton_server, "_invoke", return_value={"ok": True}) as invoke_mock:
            result = ableton_server.load_instrument_or_effect(2, device_name="Drift", target_index=0)
        invoke_mock.assert_called_once_with(
            "load_instrument_or_effect",
            {"track_index": 2, "device_name": "Drift", "target_index": 0},
        )
        self.assertEqual({"ok": True}, result)

    def test_load_drum_kit_wrapper_forwards_expected_params(self):
        with mock.patch.object(ableton_server, "_invoke", return_value={"ok": True}) as invoke_mock:
            result = ableton_server.load_drum_kit(2, "query:Drums#FileId_5422")
        invoke_mock.assert_called_once_with(
            "load_drum_kit",
            {"track_index": 2, "rack_uri": "query:Drums#FileId_5422"},
        )
        self.assertEqual({"ok": True}, result)

    def test_rack_and_drum_wrappers_forward_expected_params(self):
        cases = (
            (
                "get_rack_chains",
                lambda: ableton_server.get_rack_chains(2, 5),
                "get_rack_chains",
                {"track_index": 2, "device_index": 5},
            ),
            (
                "get_rack_macros",
                lambda: ableton_server.get_rack_macros(2, 5),
                "get_rack_macros",
                {"track_index": 2, "device_index": 5},
            ),
            (
                "set_rack_macro",
                lambda: ableton_server.set_rack_macro(2, 5, 1, 0.75),
                "set_rack_macro",
                {"track_index": 2, "device_index": 5, "macro_index": 1, "value": 0.75},
            ),
            (
                "get_chain_devices",
                lambda: ableton_server.get_chain_devices(2, 5, 0),
                "get_chain_devices",
                {"track_index": 2, "device_index": 5, "chain_index": 0},
            ),
            (
                "set_chain_mute",
                lambda: ableton_server.set_chain_mute(2, 5, 0, True),
                "set_chain_mute",
                {"track_index": 2, "device_index": 5, "chain_index": 0, "mute": True},
            ),
            (
                "set_chain_solo",
                lambda: ableton_server.set_chain_solo(2, 5, 0, True),
                "set_chain_solo",
                {"track_index": 2, "device_index": 5, "chain_index": 0, "solo": True},
            ),
            (
                "set_chain_volume",
                lambda: ableton_server.set_chain_volume(2, 5, 0, 0.42),
                "set_chain_volume",
                {"track_index": 2, "device_index": 5, "chain_index": 0, "volume": 0.42},
            ),
            (
                "get_drum_rack_pads",
                lambda: ableton_server.get_drum_rack_pads(2, 5),
                "get_drum_rack_pads",
                {"track_index": 2, "device_index": 5},
            ),
            (
                "set_drum_rack_pad_note",
                lambda: ableton_server.set_drum_rack_pad_note(2, 5, 36, 48),
                "set_drum_rack_pad_note",
                {"track_index": 2, "device_index": 5, "note": 36, "new_note": 48},
            ),
            (
                "set_drum_rack_pad_mute",
                lambda: ableton_server.set_drum_rack_pad_mute(2, 5, 36, True),
                "set_drum_rack_pad_mute",
                {"track_index": 2, "device_index": 5, "note": 36, "mute": True},
            ),
            (
                "set_drum_rack_pad_solo",
                lambda: ableton_server.set_drum_rack_pad_solo(2, 5, 36, True),
                "set_drum_rack_pad_solo",
                {"track_index": 2, "device_index": 5, "note": 36, "solo": True},
            ),
        )

        for label, caller, command_name, expected_params in cases:
            with self.subTest(wrapper=label):
                with mock.patch.object(ableton_server, "_invoke", return_value={"ok": True}) as invoke_mock:
                    result = caller()
                invoke_mock.assert_called_once_with(command_name, expected_params)
                self.assertEqual({"ok": True}, result)
