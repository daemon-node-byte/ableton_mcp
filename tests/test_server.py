from __future__ import absolute_import, print_function, unicode_literals

import asyncio
import unittest
from unittest import mock

from mcp_server.command_specs import FIRST_CLASS_MCP_COMMANDS, get_command_spec

try:
    from mcp_server import server as ableton_server
    from mcp_server import _registry as ableton_registry
    from mcp_server.tools import (
        arrangement as arrangement_tools,
        browser as browser_tools,
        device as device_tools,
        memory_bank as memory_bank_tools,
        rack as rack_tools,
        song as song_tools,
        take_lane as take_lane_tools,
        track as track_tools,
    )
except ModuleNotFoundError as exc:
    if exc.name in ("fastmcp", "mcp"):
        ableton_server = None
    else:
        raise


def _list_tools():
    return asyncio.run(ableton_server.mcp.list_tools())


def _tool_by_name(name):
    for tool in _list_tools():
        if tool.name == name:
            return tool
    raise AssertionError("Tool '{}' not registered".format(name))


@unittest.skipIf(ableton_server is None, "fastmcp is not installed in this Python environment")
class ServerEntrypointTests(unittest.TestCase):
    def test_entrypoint_exists(self):
        self.assertTrue(callable(ableton_server.main))

    def test_inferred_object_aliases_exist(self):
        self.assertIs(ableton_server.mcp, ableton_server.server)
        self.assertIs(ableton_server.mcp, ableton_server.app)

    def test_module_exports_include_inferred_aliases(self):
        self.assertIn("mcp", ableton_server.__all__)
        self.assertIn("server", ableton_server.__all__)
        self.assertIn("app", ableton_server.__all__)


@unittest.skipIf(ableton_server is None, "fastmcp is not installed in this Python environment")
class RegisteredToolsTests(unittest.TestCase):
    def test_every_first_class_command_is_registered(self):
        tool_names = {tool.name for tool in _list_tools()}
        expected = set(FIRST_CLASS_MCP_COMMANDS)
        expected.add("ableton_raw_command")
        self.assertEqual(expected, tool_names)

    def test_read_only_tool_has_read_only_annotation(self):
        tool = _tool_by_name("health_check")
        annotations = tool.annotations
        self.assertTrue(bool(annotations and annotations.readOnlyHint))
        self.assertFalse(bool(annotations and annotations.destructiveHint))

    def test_write_tool_has_destructive_annotation(self):
        tool = _tool_by_name("set_tempo")
        annotations = tool.annotations
        self.assertFalse(bool(annotations and annotations.readOnlyHint))
        self.assertTrue(bool(annotations and annotations.destructiveHint))

    def test_every_tool_annotation_matches_spec_write_flag(self):
        for tool in _list_tools():
            if tool.name == "ableton_raw_command":
                continue
            spec = get_command_spec(tool.name)
            annotations = tool.annotations
            self.assertIsNotNone(annotations, msg=tool.name)
            self.assertEqual(
                not spec.write,
                bool(annotations.readOnlyHint),
                msg="readOnlyHint mismatch for {}".format(tool.name),
            )
            self.assertEqual(
                spec.write,
                bool(annotations.destructiveHint),
                msg="destructiveHint mismatch for {}".format(tool.name),
            )


@unittest.skipIf(ableton_server is None, "fastmcp is not installed in this Python environment")
class TransportSelectionTests(unittest.TestCase):
    def test_main_uses_stdio_transport_by_default(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with mock.patch.object(ableton_server.mcp, "run") as run_mock:
                ableton_server.main()
        run_mock.assert_called_once_with(transport="stdio")

    def test_main_uses_http_transport_with_cloud_run_defaults(self):
        env = {"ABLETON_MCP_TRANSPORT": "http", "PORT": "9090"}
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


@unittest.skipIf(ableton_server is None, "fastmcp is not installed in this Python environment")
class RawCommandTests(unittest.TestCase):
    def test_raw_command_returns_stability_metadata(self):
        with mock.patch.object(ableton_registry, "invoke", return_value={"ok": True}) as invoke_mock:
            result = ableton_server.ableton_raw_command("health_check", {})
        invoke_mock.assert_called_once_with("health_check", {})
        self.assertEqual("health_check", result["command"])
        self.assertIn("stability", result)
        self.assertIn("domain", result)
        self.assertIn("mcp_exposed", result)
        self.assertEqual({"ok": True}, result["result"])


@unittest.skipIf(ableton_server is None, "fastmcp is not installed in this Python environment")
class WrapperForwardingTests(unittest.TestCase):
    """Representative cases that exercise parameter normalization patterns.

    The meta-test above proves every first-class command is registered; these
    cases cover the non-trivial patterns (None-stripping, exclusive selectors,
    multi-optional params, JsonDict passthrough)."""

    def _assert_invoke(self, caller, expected_command, expected_params):
        with mock.patch.object(ableton_registry, "invoke", return_value={"ok": True}) as invoke_mock:
            result = caller()
        invoke_mock.assert_called_once_with(expected_command, expected_params)
        self.assertEqual({"ok": True}, result)

    def test_zero_arg_read_wrapper(self):
        self._assert_invoke(
            lambda: song_tools.get_session_path(),
            "get_session_path",
            {},
        )

    def test_simple_write_wrapper(self):
        self._assert_invoke(
            lambda: track_tools.set_track_volume(2, 0.65),
            "set_track_volume",
            {"track_index": 2, "volume": 0.65},
        )

    def test_optional_index_is_omitted_when_none(self):
        self._assert_invoke(
            lambda: track_tools.create_midi_track(),
            "create_midi_track",
            {},
        )

    def test_optional_index_is_forwarded_when_set(self):
        self._assert_invoke(
            lambda: track_tools.create_midi_track(3),
            "create_midi_track",
            {"index": 3},
        )

    def test_select_track_exclusive_selectors(self):
        self._assert_invoke(
            lambda: track_tools.select_track(track_index=2),
            "select_track",
            {"track_index": 2},
        )
        self._assert_invoke(
            lambda: track_tools.select_track(return_index=1),
            "select_track",
            {"return_index": 1},
        )
        self._assert_invoke(
            lambda: track_tools.select_track(master=True),
            "select_track",
            {"master": True},
        )

    def test_move_arrangement_clip_forwards_both_optional_selectors(self):
        self._assert_invoke(
            lambda: arrangement_tools.move_arrangement_clip(3, 88.0, start_time=80.0),
            "move_arrangement_clip",
            {"track_index": 3, "new_start_time": 88.0, "start_time": 80.0},
        )

    def test_delete_arrangement_clip_forwards_clip_index_selector(self):
        self._assert_invoke(
            lambda: arrangement_tools.delete_arrangement_clip(3, clip_index=0),
            "delete_arrangement_clip",
            {"track_index": 3, "clip_index": 0},
        )

    def test_duplicate_to_arrangement_with_start_time(self):
        self._assert_invoke(
            lambda: arrangement_tools.duplicate_to_arrangement(1, 0, start_time=96.0),
            "duplicate_to_arrangement",
            {"track_index": 1, "slot_index": 0, "start_time": 96.0},
        )

    def test_load_instrument_or_effect_only_forwards_set_optionals(self):
        self._assert_invoke(
            lambda: device_tools.load_instrument_or_effect(2, device_name="Drift", target_index=0),
            "load_instrument_or_effect",
            {"track_index": 2, "device_name": "Drift", "target_index": 0},
        )

    def test_create_midi_clip_in_lane_forwards_both_optional_floats(self):
        self._assert_invoke(
            lambda: take_lane_tools.create_midi_clip_in_lane(2, 1, start_time=8.0, length=2.0),
            "create_midi_clip_in_lane",
            {"track_index": 2, "lane_index": 1, "start_time": 8.0, "length": 2.0},
        )

    def test_create_rack_with_optional_target_path(self):
        self._assert_invoke(
            lambda: rack_tools.create_rack(2, "audio_effect", "Mix Rack", target_path="devices 0 chains 1"),
            "create_rack",
            {
                "track_index": 2,
                "rack_type": "audio_effect",
                "name": "Mix Rack",
                "target_path": "devices 0 chains 1",
            },
        )

    def test_apply_rack_blueprint_passes_jsondict_verbatim(self):
        blueprint = {
            "track_index": 2,
            "rack_type": "audio_effect",
            "rack_name": "Mix Rack",
            "chains": [{"name": "EQ"}],
        }
        self._assert_invoke(
            lambda: rack_tools.apply_rack_blueprint(blueprint),
            "apply_rack_blueprint",
            {"blueprint": blueprint},
        )

    def test_search_browser_defaults_category_to_all(self):
        self._assert_invoke(
            lambda: browser_tools.search_browser("drift"),
            "search_browser",
            {"query": "drift", "category": "all"},
        )

    def test_memory_bank_write_forwards_content(self):
        self._assert_invoke(
            lambda: memory_bank_tools.write_memory_bank("racks.md", "# Rack Catalog"),
            "write_memory_bank",
            {"file_name": "racks.md", "content": "# Rack Catalog"},
        )


if __name__ == "__main__":
    unittest.main()
