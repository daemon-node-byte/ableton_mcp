from __future__ import absolute_import, print_function, unicode_literals

import asyncio
import unittest
from unittest import mock

from mcp_server.command_specs import FIRST_CLASS_MCP_COMMANDS

try:
    from mcp_server import server as ableton_server
except ModuleNotFoundError as exc:
    if exc.name in ("fastmcp", "mcp"):
        ableton_server = None
    else:
        raise


@unittest.skipIf(ableton_server is None, "fastmcp is not installed in this Python environment")
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

    def test_get_session_path_wrapper_forwards_expected_params(self):
        with mock.patch.object(ableton_server, "_invoke", return_value={"path": "/tmp/Test.als"}) as invoke_mock:
            result = ableton_server.get_session_path()
        invoke_mock.assert_called_once_with("get_session_path", {})
        self.assertEqual({"path": "/tmp/Test.als"}, result)

    def test_main_uses_stdio_transport_by_default(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with mock.patch.object(ableton_server.mcp, "run") as run_mock:
                ableton_server.main()
        run_mock.assert_called_once_with(transport="stdio")

    def test_main_uses_http_transport_with_cloud_run_defaults(self):
        env = {
            "ABLETON_MCP_TRANSPORT": "http",
            "PORT": "9090",
        }
        with mock.patch.dict("os.environ", env, clear=True):
            with mock.patch.object(ableton_server.mcp, "run") as run_mock:
                ableton_server.main()
        run_mock.assert_called_once_with(
            transport="http",
            host="0.0.0.0",
            port=9090,
            path="/mcp/",
        )

    def test_main_maps_streamable_http_to_http(self):
        env = {
            "ABLETON_MCP_TRANSPORT": "streamable-http",
            "PORT": "7000",
            "ABLETON_MCP_BIND_HOST": "127.0.0.1",
            "ABLETON_MCP_HTTP_PATH": "custom",
        }
        with mock.patch.dict("os.environ", env, clear=True):
            with mock.patch.object(ableton_server.mcp, "run") as run_mock:
                ableton_server.main()
        run_mock.assert_called_once_with(
            transport="http",
            host="127.0.0.1",
            port=7000,
            path="/custom/",
        )

    def test_main_uses_sse_transport_with_http_binding(self):
        env = {
            "ABLETON_MCP_TRANSPORT": "sse",
            "PORT": "8088",
            "ABLETON_MCP_HTTP_PATH": "/events",
        }
        with mock.patch.dict("os.environ", env, clear=True):
            with mock.patch.object(ableton_server.mcp, "run") as run_mock:
                ableton_server.main()
        run_mock.assert_called_once_with(
            transport="sse",
            host="0.0.0.0",
            port=8088,
            path="/events/",
        )

    def test_main_rejects_invalid_transport(self):
        env = {"ABLETON_MCP_TRANSPORT": "websocket"}
        with mock.patch.dict("os.environ", env, clear=True):
            with self.assertRaisesRegex(ValueError, "Unsupported ABLETON_MCP_TRANSPORT"):
                ableton_server.main()

    def test_track_wrappers_forward_expected_params(self):
        cases = (
            (
                "set_track_name",
                lambda: ableton_server.set_track_name(2, "Bass"),
                "set_track_name",
                {"track_index": 2, "name": "Bass"},
            ),
            (
                "set_track_color",
                lambda: ableton_server.set_track_color(2, 16711935),
                "set_track_color",
                {"track_index": 2, "color": 16711935},
            ),
            (
                "set_track_volume",
                lambda: ableton_server.set_track_volume(2, 0.65),
                "set_track_volume",
                {"track_index": 2, "volume": 0.65},
            ),
            (
                "set_track_pan",
                lambda: ableton_server.set_track_pan(2, -0.3),
                "set_track_pan",
                {"track_index": 2, "pan": -0.3},
            ),
            (
                "set_track_mute",
                lambda: ableton_server.set_track_mute(2, True),
                "set_track_mute",
                {"track_index": 2, "mute": True},
            ),
            (
                "set_track_solo",
                lambda: ableton_server.set_track_solo(2, True),
                "set_track_solo",
                {"track_index": 2, "solo": True},
            ),
            (
                "set_track_arm",
                lambda: ableton_server.set_track_arm(2, True),
                "set_track_arm",
                {"track_index": 2, "arm": True},
            ),
            (
                "fold_track",
                lambda: ableton_server.fold_track(2),
                "fold_track",
                {"track_index": 2},
            ),
            (
                "unfold_track",
                lambda: ableton_server.unfold_track(2),
                "unfold_track",
                {"track_index": 2},
            ),
            (
                "set_send_level",
                lambda: ableton_server.set_send_level(2, 1, 0.4),
                "set_send_level",
                {"track_index": 2, "send_index": 1, "level": 0.4},
            ),
            (
                "get_return_tracks",
                lambda: ableton_server.get_return_tracks(),
                "get_return_tracks",
                {},
            ),
            (
                "get_return_track_info",
                lambda: ableton_server.get_return_track_info(1),
                "get_return_track_info",
                {"return_index": 1},
            ),
            (
                "set_return_volume",
                lambda: ableton_server.set_return_volume(1, 0.7),
                "set_return_volume",
                {"return_index": 1, "volume": 0.7},
            ),
            (
                "set_return_pan",
                lambda: ableton_server.set_return_pan(1, -0.2),
                "set_return_pan",
                {"return_index": 1, "pan": -0.2},
            ),
            (
                "select_track:track",
                lambda: ableton_server.select_track(track_index=2),
                "select_track",
                {"track_index": 2},
            ),
            (
                "select_track:return",
                lambda: ableton_server.select_track(return_index=1),
                "select_track",
                {"return_index": 1},
            ),
            (
                "select_track:master",
                lambda: ableton_server.select_track(master=True),
                "select_track",
                {"master": True},
            ),
            (
                "get_selected_track",
                lambda: ableton_server.get_selected_track(),
                "get_selected_track",
                {},
            ),
        )

        for label, caller, command_name, expected_params in cases:
            with self.subTest(wrapper=label):
                with mock.patch.object(ableton_server, "_invoke", return_value={"ok": True}) as invoke_mock:
                    result = caller()
                invoke_mock.assert_called_once_with(command_name, expected_params)
                self.assertEqual({"ok": True}, result)

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

    def test_take_lane_wrappers_forward_expected_params(self):
        cases = (
            (
                "get_take_lanes",
                lambda: ableton_server.get_take_lanes(2),
                "get_take_lanes",
                {"track_index": 2},
            ),
            (
                "create_take_lane",
                lambda: ableton_server.create_take_lane(2),
                "create_take_lane",
                {"track_index": 2},
            ),
            (
                "set_take_lane_name",
                lambda: ableton_server.set_take_lane_name(2, 1, "Lead Takes"),
                "set_take_lane_name",
                {"track_index": 2, "lane_index": 1, "name": "Lead Takes"},
            ),
            (
                "create_midi_clip_in_lane",
                lambda: ableton_server.create_midi_clip_in_lane(2, 1, start_time=8.0, length=2.0),
                "create_midi_clip_in_lane",
                {"track_index": 2, "lane_index": 1, "start_time": 8.0, "length": 2.0},
            ),
            (
                "get_clips_in_take_lane",
                lambda: ableton_server.get_clips_in_take_lane(2, 1),
                "get_clips_in_take_lane",
                {"track_index": 2, "lane_index": 1},
            ),
        )
        for _label, invoke_call, expected_command, expected_params in cases:
            with mock.patch.object(ableton_server, "_invoke", return_value={"ok": True}) as invoke_mock:
                result = invoke_call()
            invoke_mock.assert_called_once_with(expected_command, expected_params)
            self.assertEqual({"ok": True}, result)

    def test_rack_and_drum_wrappers_forward_expected_params(self):
        cases = (
            (
                "create_rack",
                lambda: ableton_server.create_rack(2, "audio_effect", "Mix Rack", target_path="devices 0 chains 1"),
                "create_rack",
                {
                    "track_index": 2,
                    "rack_type": "audio_effect",
                    "name": "Mix Rack",
                    "target_path": "devices 0 chains 1",
                },
            ),
            (
                "insert_rack_chain",
                lambda: ableton_server.insert_rack_chain(2, "devices 0", "Tone Chain", index=1),
                "insert_rack_chain",
                {"track_index": 2, "rack_path": "devices 0", "name": "Tone Chain", "index": 1},
            ),
            (
                "insert_device_in_chain",
                lambda: ableton_server.insert_device_in_chain(2, "devices 0 chains 1", "Eq8", target_index=0),
                "insert_device_in_chain",
                {
                    "track_index": 2,
                    "chain_path": "devices 0 chains 1",
                    "native_device_name": "Eq8",
                    "target_index": 0,
                },
            ),
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
                "get_rack_structure",
                lambda: ableton_server.get_rack_structure(2, "devices 0"),
                "get_rack_structure",
                {"track_index": 2, "rack_path": "devices 0"},
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
                "get_device_parameters_at_path",
                lambda: ableton_server.get_device_parameters_at_path(2, "devices 0 chains 0 devices 1"),
                "get_device_parameters_at_path",
                {"track_index": 2, "device_path": "devices 0 chains 0 devices 1"},
            ),
            (
                "set_device_parameter_at_path",
                lambda: ableton_server.set_device_parameter_at_path(2, "devices 0 chains 0 devices 1", 3, 0.42),
                "set_device_parameter_at_path",
                {
                    "track_index": 2,
                    "device_path": "devices 0 chains 0 devices 1",
                    "parameter_index": 3,
                    "value": 0.42,
                },
            ),
            (
                "set_device_parameter_by_name_at_path",
                lambda: ableton_server.set_device_parameter_by_name_at_path(
                    2,
                    "devices 0 chains 0 devices 1",
                    "Gain A",
                    6.0,
                ),
                "set_device_parameter_by_name_at_path",
                {
                    "track_index": 2,
                    "device_path": "devices 0 chains 0 devices 1",
                    "name": "Gain A",
                    "value": 6.0,
                },
            ),
            (
                "get_drum_rack_pads",
                lambda: ableton_server.get_drum_rack_pads(2, 5),
                "get_drum_rack_pads",
                {"track_index": 2, "device_index": 5},
            ),
            (
                "read_memory_bank",
                lambda: ableton_server.read_memory_bank("racks.md"),
                "read_memory_bank",
                {"file_name": "racks.md"},
            ),
            (
                "write_memory_bank",
                lambda: ableton_server.write_memory_bank("racks.md", "# Rack Catalog"),
                "write_memory_bank",
                {"file_name": "racks.md", "content": "# Rack Catalog"},
            ),
            (
                "append_rack_entry",
                lambda: ableton_server.append_rack_entry("## Rack: rack_1"),
                "append_rack_entry",
                {"rack_data": "## Rack: rack_1"},
            ),
            (
                "get_system_owned_racks",
                lambda: ableton_server.get_system_owned_racks(),
                "get_system_owned_racks",
                {},
            ),
            (
                "refresh_rack_memory_entry",
                lambda: ableton_server.refresh_rack_memory_entry(2, "devices 0"),
                "refresh_rack_memory_entry",
                {"track_index": 2, "rack_path": "devices 0"},
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

    def test_apply_rack_blueprint_wrapper_forwards_expected_params(self):
        blueprint = {
            "track_index": 2,
            "rack_type": "audio_effect",
            "rack_name": "Mix Rack",
            "chains": [{"name": "EQ"}],
        }
        with mock.patch.object(ableton_server, "_invoke", return_value={"ok": True}) as invoke_mock:
            result = ableton_server.apply_rack_blueprint(blueprint)
        invoke_mock.assert_called_once_with("apply_rack_blueprint", {"blueprint": blueprint})
        self.assertEqual({"ok": True}, result)
