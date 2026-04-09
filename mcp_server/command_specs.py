"""Canonical command registry for the AbletonMCP Remote Script.

This module is the Python-side source of truth for:
- command names exposed by the Remote Script dispatcher
- basic parameter contracts
- result-shape summaries
- stability labels for repo-only development
- which commands are promoted to first-class MCP tools in this pass
"""

from __future__ import absolute_import, print_function, unicode_literals

from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple


STABILITY_VALUES = ("likely-complete", "partial", "stub", "unverified")


@dataclass(frozen=True)
class CommandSpec(object):
    name: str
    domain: str
    required_params: Tuple[str, ...] = ()
    optional_params: Tuple[str, ...] = ()
    result_schema: str = "dict"
    write: bool = False
    stability: str = "unverified"
    mcp_exposed: bool = False
    notes: str = ""

    @property
    def tool_description(self):
        description = "{} command. Stability: {}.".format(self.domain.replace("_", " ").title(), self.stability)
        if self.notes:
            description = "{} {}".format(description, self.notes)
        return description


def _spec(
    name,
    domain,
    required=(),
    optional=(),
    result="dict",
    write=False,
    stability="unverified",
    exposed=False,
    notes="",
):
    if stability not in STABILITY_VALUES:
        raise ValueError("Invalid stability '{}'".format(stability))
    return CommandSpec(
        name=name,
        domain=domain,
        required_params=tuple(required),
        optional_params=tuple(optional),
        result_schema=result,
        write=write,
        stability=stability,
        mcp_exposed=exposed,
        notes=notes,
    )


FIRST_CLASS_MCP_COMMANDS = (
    "health_check",
    "get_session_info",
    "get_current_song_time",
    "set_current_song_time",
    "set_tempo",
    "start_playback",
    "stop_playback",
    "get_all_track_names",
    "get_track_info",
    "create_midi_track",
    "create_audio_track",
    "create_clip",
    "get_clip_notes",
    "add_notes_to_clip",
    "get_arrangement_clips",
    "create_arrangement_midi_clip",
    "add_notes_to_arrangement_clip",
    "get_arrangement_clip_notes",
    "get_track_devices",
    "get_device_parameters",
    "set_device_parameter_by_name",
    "get_device_parameter_by_name",
)


_COMMAND_SPECS = [
    _spec("health_check", "health", result="{status, tempo, is_playing, track_count}", stability="likely-complete", exposed=True),

    _spec("get_session_info", "song", result="session snapshot with tracks, return tracks, and scenes", stability="likely-complete", exposed=True),
    _spec("get_current_song_time", "song", result="{current_song_time}", stability="likely-complete", exposed=True),
    _spec("set_current_song_time", "song", required=("time",), result="{current_song_time}", write=True, stability="likely-complete", exposed=True),
    _spec("set_tempo", "song", required=("tempo",), result="{tempo}", write=True, stability="likely-complete", exposed=True),
    _spec("set_time_signature", "song", optional=("numerator", "denominator"), result="{numerator, denominator}", write=True, stability="likely-complete"),
    _spec("start_playback", "song", result="{is_playing}", write=True, stability="likely-complete", exposed=True),
    _spec("stop_playback", "song", result="{is_playing}", write=True, stability="likely-complete", exposed=True),
    _spec("continue_playback", "song", result="{is_playing}", write=True, stability="likely-complete"),
    _spec("start_recording", "song", result="{recording}", write=True, stability="likely-complete"),
    _spec("stop_recording", "song", result="{recording}", write=True, stability="likely-complete"),
    _spec("toggle_session_record", "song", result="{session_record}", write=True, stability="likely-complete"),
    _spec("toggle_arrangement_record", "song", result="{record_mode}", write=True, stability="likely-complete"),
    _spec("set_metronome", "song", required=("enabled",), result="{metronome}", write=True, stability="likely-complete"),
    _spec("tap_tempo", "song", result="{tempo}", write=True, stability="likely-complete"),
    _spec("undo", "song", result="{ok}", write=True, stability="likely-complete"),
    _spec("redo", "song", result="{ok}", write=True, stability="likely-complete"),
    _spec("capture_midi", "song", result="{ok}", write=True, stability="likely-complete"),
    _spec("re_enable_automation", "song", result="{ok}", write=True, stability="likely-complete"),
    _spec("set_arrangement_loop", "song", optional=("start", "length", "enabled"), result="{loop_start, loop_length, loop_on}", write=True, stability="likely-complete"),
    _spec("get_cpu_load", "song", result="{cpu_load}", stability="likely-complete", notes="Backed by Application.average_process_usage."),
    _spec("get_session_path", "song", result="{path}", stability="likely-complete", notes="Backed by Song.file_path."),
    _spec("get_locators", "song", result="{locators[]}", stability="likely-complete"),
    _spec("create_locator", "song", optional=("time", "name"), result="{ok, time, name}", write=True, stability="partial"),
    _spec("delete_locator", "song", required=("locator_index",), result="{ok}", write=True, stability="partial"),
    _spec("jump_to_time", "song", required=("time",), result="{current_song_time}", write=True, stability="likely-complete"),
    _spec("jump_to_next_cue", "song", result="{current_song_time}", write=True, stability="likely-complete"),
    _spec("jump_to_prev_cue", "song", result="{current_song_time}", write=True, stability="likely-complete"),
    _spec("set_punch_in", "song", required=("enabled",), result="{punch_in}", write=True, stability="likely-complete"),
    _spec("set_punch_out", "song", required=("enabled",), result="{punch_out}", write=True, stability="likely-complete"),
    _spec("trigger_back_to_arrangement", "song", result="{ok}", write=True, stability="partial"),
    _spec("get_back_to_arrangement", "song", result="{back_to_arranger}", stability="likely-complete"),
    _spec("set_session_automation_record", "song", required=("enabled",), result="{session_automation_record}", write=True, stability="likely-complete"),
    _spec("get_session_automation_record", "song", result="{session_automation_record}", stability="likely-complete"),
    _spec("set_overdub", "song", required=("enabled",), result="{overdub}", write=True, stability="likely-complete"),
    _spec("stop_all_clips", "song", result="{ok}", write=True, stability="likely-complete"),
    _spec("get_arrangement_length", "song", result="{arrangement_length}", stability="likely-complete", notes="Backed by Song.song_length with clip-end fallback."),

    _spec("get_track_info", "track", required=("track_index",), result="track details with devices, clip slots, sends", stability="likely-complete", exposed=True),
    _spec("get_all_track_names", "track", result="{tracks[]}", stability="likely-complete", exposed=True),
    _spec("create_midi_track", "track", optional=("index",), result="{index, name}", write=True, stability="likely-complete", exposed=True),
    _spec("create_audio_track", "track", optional=("index",), result="{index, name}", write=True, stability="likely-complete", exposed=True),
    _spec("create_return_track", "track", result="{index, name}", write=True, stability="likely-complete"),
    _spec("delete_track", "track", required=("track_index",), result="{deleted_index}", write=True, stability="likely-complete"),
    _spec("duplicate_track", "track", required=("track_index",), result="{original_index}", write=True, stability="likely-complete"),
    _spec("set_track_name", "track", required=("track_index", "name"), result="{name}", write=True, stability="likely-complete"),
    _spec("set_track_color", "track", required=("track_index", "color"), result="{color}", write=True, stability="likely-complete"),
    _spec("set_track_volume", "track", required=("track_index", "volume"), result="{volume}", write=True, stability="likely-complete"),
    _spec("set_track_pan", "track", required=("track_index", "pan"), result="{pan}", write=True, stability="likely-complete"),
    _spec("set_track_mute", "track", required=("track_index", "mute"), result="{mute}", write=True, stability="likely-complete"),
    _spec("set_track_solo", "track", required=("track_index", "solo"), result="{solo}", write=True, stability="likely-complete"),
    _spec("set_track_arm", "track", required=("track_index", "arm"), result="{arm}", write=True, stability="likely-complete"),
    _spec("set_track_monitoring", "track", required=("track_index",), optional=("monitoring",), result="{monitoring}", write=True, stability="likely-complete"),
    _spec("freeze_track", "track", required=("track_index",), result="{ok}", write=True, stability="partial"),
    _spec("flatten_track", "track", required=("track_index",), result="{ok}", write=True, stability="partial"),
    _spec("fold_track", "track", required=("track_index",), result="{fold_state}", write=True, stability="likely-complete"),
    _spec("unfold_track", "track", required=("track_index",), result="{fold_state}", write=True, stability="likely-complete"),
    _spec("unarm_all", "track", result="{ok}", write=True, stability="likely-complete"),
    _spec("unsolo_all", "track", result="{ok}", write=True, stability="likely-complete"),
    _spec("unmute_all", "track", result="{ok}", write=True, stability="likely-complete"),
    _spec("set_track_delay", "track", required=("track_index", "delay_ms"), result="{delay_ms}", write=True, stability="partial"),
    _spec("set_send_level", "track", required=("track_index", "send_index", "level"), result="{send_index, level}", write=True, stability="likely-complete"),
    _spec("get_return_tracks", "track", result="{return_tracks[]}", stability="likely-complete"),
    _spec("get_return_track_info", "track", required=("return_index",), result="return track details", stability="likely-complete"),
    _spec("set_return_volume", "track", required=("return_index", "volume"), result="{volume}", write=True, stability="likely-complete"),
    _spec("set_return_pan", "track", required=("return_index", "pan"), result="{pan}", write=True, stability="likely-complete"),
    _spec("set_track_input_routing", "track", required=("track_index", "routing_type"), result="{input_routing_type}", write=True, stability="partial"),
    _spec("set_track_output_routing", "track", required=("track_index", "routing_type"), result="{output_routing_type}", write=True, stability="partial"),
    _spec("get_track_input_routing", "track", required=("track_index",), result="{current_input_routing, available_input_routing_types[]}", stability="likely-complete"),
    _spec("get_track_output_routing", "track", required=("track_index",), result="{current_output_routing, available_output_routing_types[]}", stability="likely-complete"),
    _spec("select_track", "track", required=("track_index",), result="{selected_track_index}", write=True, stability="likely-complete"),
    _spec("get_selected_track", "track", result="{index, name}", stability="likely-complete"),
    _spec("get_master_info", "track", result="{volume, pan, output_meter_left, output_meter_right}", stability="likely-complete"),
    _spec("set_master_volume", "track", required=("volume",), result="{volume}", write=True, stability="likely-complete"),
    _spec("set_master_pan", "track", required=("pan",), result="{pan}", write=True, stability="likely-complete"),
    _spec("get_master_output_meter", "track", result="{left, right}", stability="likely-complete"),
    _spec("get_cue_volume", "track", result="{cue_volume}", stability="likely-complete"),
    _spec("set_cue_volume", "track", required=("volume",), result="{cue_volume}", write=True, stability="likely-complete"),

    _spec("get_clip_info", "session_clip", required=("track_index", "slot_index"), result="session clip details", stability="likely-complete"),
    _spec("create_clip", "session_clip", required=("track_index", "slot_index"), optional=("length",), result="session clip details", write=True, stability="likely-complete", exposed=True),
    _spec("delete_clip", "session_clip", required=("track_index", "slot_index"), result="{ok}", write=True, stability="likely-complete"),
    _spec("duplicate_clip", "session_clip", required=("track_index", "slot_index"), optional=("destination_slot_index",), result="{ok, destination_slot_index}", write=True, stability="partial"),
    _spec("set_clip_name", "session_clip", required=("track_index", "slot_index", "name"), result="{name}", write=True, stability="likely-complete"),
    _spec("set_clip_color", "session_clip", required=("track_index", "slot_index", "color"), result="{color}", write=True, stability="likely-complete"),
    _spec("fire_clip", "session_clip", required=("track_index", "slot_index"), result="{ok}", write=True, stability="likely-complete"),
    _spec("stop_clip", "session_clip", required=("track_index", "slot_index"), result="{ok}", write=True, stability="likely-complete"),
    _spec("get_clip_notes", "session_clip", required=("track_index", "slot_index"), result="{notes[], count}", stability="likely-complete", exposed=True),
    _spec("add_notes_to_clip", "session_clip", required=("track_index", "slot_index", "notes"), result="{added}", write=True, stability="likely-complete", exposed=True),
    _spec("set_clip_notes", "session_clip", required=("track_index", "slot_index", "notes"), result="{count}", write=True, stability="likely-complete"),
    _spec("remove_notes_from_clip", "session_clip", required=("track_index", "slot_index"), optional=("from_time", "time_span", "from_pitch", "pitch_span"), result="{ok}", write=True, stability="likely-complete"),
    _spec("set_clip_loop", "session_clip", required=("track_index", "slot_index"), optional=("looping", "loop_start", "loop_end"), result="{looping, loop_start, loop_end}", write=True, stability="likely-complete"),
    _spec("set_clip_markers", "session_clip", required=("track_index", "slot_index"), optional=("start_marker", "end_marker"), result="{start_marker, end_marker}", write=True, stability="likely-complete"),
    _spec("set_clip_gain", "session_clip", required=("track_index", "slot_index", "gain"), result="{gain}", write=True, stability="likely-complete"),
    _spec("set_clip_pitch", "session_clip", required=("track_index", "slot_index"), optional=("coarse", "fine"), result="{pitch_coarse, pitch_fine}", write=True, stability="likely-complete"),
    _spec("set_clip_warp_mode", "session_clip", required=("track_index", "slot_index"), optional=("warp_mode",), result="{warp_mode}", write=True, stability="partial"),
    _spec("quantize_clip", "session_clip", required=("track_index", "slot_index"), optional=("quantize_to", "amount"), result="{ok}", write=True, stability="likely-complete"),
    _spec("duplicate_clip_loop", "session_clip", required=("track_index", "slot_index"), result="{ok, length}", write=True, stability="likely-complete"),
    _spec("get_clip_automation", "session_clip", required=("track_index", "slot_index"), optional=("device_index", "parameter_index", "parameter_name"), result="{envelope[], parameter}", stability="partial"),
    _spec("set_clip_automation", "session_clip", required=("track_index", "slot_index", "envelope"), optional=("device_index", "parameter_index"), result="{ok, points_added}", write=True, stability="partial"),
    _spec("clear_clip_automation", "session_clip", required=("track_index", "slot_index"), optional=("device_index", "parameter_index"), result="{ok}", write=True, stability="partial"),

    _spec("get_arrangement_clips", "arrangement", required=("track_index",), result="{track_index, clips[]}", stability="likely-complete", exposed=True),
    _spec("get_all_arrangement_clips", "arrangement", result="{tracks[]}", stability="likely-complete"),
    _spec("create_arrangement_midi_clip", "arrangement", required=("track_index", "start_time"), optional=("length",), result="{start_time, end_time, length, name}", write=True, stability="likely-complete", exposed=True),
    _spec("create_arrangement_audio_clip", "arrangement", required=("track_index", "file_path", "start_time"), result="{start_time, end_time, length, name, file_path}", write=True, stability="partial", notes="Corrected to Track.create_audio_clip(file_path, position)."),
    _spec("delete_arrangement_clip", "arrangement", required=("track_index",), optional=("clip_index", "start_time"), result="{ok}", write=True, stability="partial"),
    _spec("resize_arrangement_clip", "arrangement", required=("track_index", "length"), optional=("clip_index", "start_time"), result="{start_time, end_time, length}", write=True, stability="partial"),
    _spec("move_arrangement_clip", "arrangement", required=("track_index", "new_start_time"), optional=("clip_index", "start_time"), result="{start_time, end_time, length, notes_restored}", write=True, stability="partial"),
    _spec("add_notes_to_arrangement_clip", "arrangement", required=("track_index", "notes"), optional=("clip_index", "start_time"), result="{added}", write=True, stability="likely-complete", exposed=True),
    _spec("get_arrangement_clip_notes", "arrangement", required=("track_index",), optional=("clip_index", "start_time"), result="{notes[], count}", stability="likely-complete", exposed=True),
    _spec("duplicate_to_arrangement", "arrangement", required=("track_index", "slot_index"), optional=("start_time",), result="{ok, start_time, source_track_index, source_slot_index}", write=True, stability="likely-complete"),

    _spec("get_all_scenes", "scene", result="{scenes[]}", stability="likely-complete"),
    _spec("create_scene", "scene", optional=("index",), result="{index, name}", write=True, stability="likely-complete"),
    _spec("delete_scene", "scene", required=("scene_index",), result="{deleted_index}", write=True, stability="likely-complete"),
    _spec("fire_scene", "scene", required=("scene_index",), result="{ok}", write=True, stability="likely-complete"),
    _spec("stop_scene", "scene", required=("scene_index",), result="{ok}", write=True, stability="partial"),
    _spec("set_scene_name", "scene", required=("scene_index", "name"), result="{name}", write=True, stability="likely-complete"),
    _spec("set_scene_color", "scene", required=("scene_index", "color"), result="{color}", write=True, stability="likely-complete"),
    _spec("duplicate_scene", "scene", required=("scene_index",), result="{original_index}", write=True, stability="likely-complete"),
    _spec("select_scene", "scene", required=("scene_index",), result="{selected_scene_index}", write=True, stability="likely-complete"),
    _spec("get_selected_scene", "scene", result="{index, name}", stability="likely-complete"),

    _spec("get_track_devices", "device", required=("track_index",), result="{track_index, devices[]}", stability="likely-complete", exposed=True),
    _spec("get_device_parameters", "device", required=("track_index", "device_index"), result="device parameter details", stability="likely-complete", exposed=True),
    _spec("set_device_parameter", "device", required=("track_index", "device_index", "parameter_index", "value"), result="{parameter_index, name, value, display_value}", write=True, stability="likely-complete"),
    _spec("set_device_parameter_by_name", "device", required=("track_index", "device_index", "name", "value"), result="{name, value, display_value}", write=True, stability="likely-complete", exposed=True),
    _spec("get_device_parameter_by_name", "device", required=("track_index", "device_index", "name"), result="single parameter details", stability="likely-complete", exposed=True),
    _spec("toggle_device", "device", required=("track_index", "device_index"), result="{is_active}", write=True, stability="partial"),
    _spec("set_device_enabled", "device", required=("track_index", "device_index", "enabled"), result="{is_active}", write=True, stability="likely-complete"),
    _spec("delete_device", "device", required=("track_index", "device_index"), result="{ok, deleted_index}", write=True, stability="likely-complete"),
    _spec("move_device", "device", required=("track_index", "device_index", "new_index"), result="{ok, new_index}", write=True, stability="likely-complete"),
    _spec("show_plugin_window", "device", required=("track_index", "device_index"), result="{ok, device_name, mode, stability}", write=True, stability="partial", notes="Best-effort device view expansion only."),
    _spec("hide_plugin_window", "device", required=("track_index", "device_index"), result="{ok, device_name, mode, stability}", write=True, stability="partial", notes="Best-effort device view collapse only."),
    _spec("load_instrument_or_effect", "device", required=("track_index",), optional=("device_name", "native_device_name", "target_index", "uri"), result="{ok, mode, ...}", write=True, stability="partial", notes="Native device insertion is safer than browser URI loading."),
    _spec("get_device_class_name", "device", required=("track_index", "device_index"), result="{class_name, name}", stability="likely-complete"),
    _spec("select_device", "device", required=("track_index", "device_index"), result="{ok, device_name}", write=True, stability="likely-complete"),
    _spec("get_selected_device", "device", result="{selected, track_index, device_index, name, class_name}", stability="likely-complete"),

    _spec("get_rack_chains", "rack", required=("track_index", "device_index"), result="{rack_name, chains[]}", stability="likely-complete"),
    _spec("get_rack_macros", "rack", required=("track_index", "device_index"), result="{rack_name, macros[]}", stability="likely-complete"),
    _spec("set_rack_macro", "rack", required=("track_index", "device_index", "macro_index", "value"), result="{name, value}", write=True, stability="likely-complete"),
    _spec("get_chain_devices", "rack", required=("track_index", "device_index", "chain_index"), result="{chain_name, devices[]}", stability="likely-complete"),
    _spec("set_chain_mute", "rack", required=("track_index", "device_index", "chain_index", "mute"), result="{mute}", write=True, stability="likely-complete"),
    _spec("set_chain_solo", "rack", required=("track_index", "device_index", "chain_index", "solo"), result="{solo}", write=True, stability="likely-complete"),
    _spec("set_chain_volume", "rack", required=("track_index", "device_index", "chain_index", "volume"), result="{volume}", write=True, stability="likely-complete"),
    _spec("get_drum_rack_pads", "rack", required=("track_index", "device_index"), result="{drum_pads[], count}", stability="likely-complete"),
    _spec("set_drum_rack_pad_note", "rack", required=("track_index", "device_index", "note", "new_note"), result="{note}", write=True, stability="partial"),
    _spec("set_drum_rack_pad_mute", "rack", required=("track_index", "device_index", "note", "mute"), result="{note, mute}", write=True, stability="likely-complete"),
    _spec("set_drum_rack_pad_solo", "rack", required=("track_index", "device_index", "note", "solo"), result="{note, solo}", write=True, stability="likely-complete"),

    _spec("get_browser_tree", "browser", optional=("category_type",), result="browser tree snapshot", stability="likely-complete"),
    _spec("get_browser_items_at_path", "browser", optional=("path",), result="{items[], path}", stability="likely-complete"),
    _spec("search_browser", "browser", optional=("query", "category"), result="{query, results[], count}", stability="partial"),
    _spec("load_drum_kit", "browser", required=("track_index", "rack_uri"), result="{ok, loaded, stability}", write=True, stability="partial"),

    _spec("get_take_lanes", "take_lane", required=("track_index",), result="{take_lanes[], available}", stability="likely-complete"),
    _spec("create_take_lane", "take_lane", required=("track_index",), result="{ok, name, stability}", write=True, stability="likely-complete", notes="Corrected to Track.create_take_lane()."),
    _spec("set_take_lane_name", "take_lane", required=("track_index", "lane_index", "name"), result="{name}", write=True, stability="partial"),
    _spec("create_midi_clip_in_lane", "take_lane", required=("track_index", "lane_index"), optional=("start_time", "length"), result="{start_time, end_time, length, name}", write=True, stability="partial", notes="Corrected to TakeLane.create_midi_clip(start_time, length)."),
    _spec("get_clips_in_take_lane", "take_lane", required=("track_index", "lane_index"), result="{clips[]}", stability="partial"),
    _spec("delete_take_lane", "take_lane", required=("track_index", "lane_index"), result="{ok|message}", write=True, stability="partial"),

    _spec("get_current_view", "view", result="{view}", stability="likely-complete"),
    _spec("focus_view", "view", required=("view",), result="{view|error}", write=True, stability="likely-complete"),
    _spec("show_arrangement_view", "view", result="{view|error}", write=True, stability="likely-complete"),
    _spec("show_session_view", "view", result="{view|error}", write=True, stability="likely-complete"),
    _spec("show_detail_view", "view", optional=("detail",), result="{view|error}", write=True, stability="likely-complete"),
]


COMMAND_SPECS = dict((spec.name, spec) for spec in _COMMAND_SPECS)

if len(COMMAND_SPECS) != len(_COMMAND_SPECS):
    raise ValueError("Duplicate command names detected in command spec registry")

for command_name in FIRST_CLASS_MCP_COMMANDS:
    spec = COMMAND_SPECS.get(command_name)
    if spec is None:
        raise ValueError("First-class MCP command '{}' is missing from the registry".format(command_name))
    if not spec.mcp_exposed:
        raise ValueError("First-class MCP command '{}' must be marked mcp_exposed".format(command_name))


def get_command_spec(command_name):
    spec = COMMAND_SPECS.get(command_name)
    if spec is None:
        raise KeyError("Unknown command '{}'".format(command_name))
    return spec


def iter_command_specs():
    return tuple(COMMAND_SPECS.values())


def iter_first_class_specs():
    return tuple(COMMAND_SPECS[name] for name in FIRST_CLASS_MCP_COMMANDS)
