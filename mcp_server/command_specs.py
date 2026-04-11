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


STABILITY_VALUES = ("confirmed", "likely-complete", "partial", "stub", "unverified")


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
    "get_session_path",
    "get_current_song_time",
    "set_current_song_time",
    "set_tempo",
    "start_playback",
    "stop_playback",
    "get_all_track_names",
    "get_track_info",
    "create_midi_track",
    "create_audio_track",
    "set_track_name",
    "set_track_color",
    "set_track_volume",
    "set_track_pan",
    "set_track_mute",
    "set_track_solo",
    "set_track_arm",
    "fold_track",
    "unfold_track",
    "set_send_level",
    "get_return_tracks",
    "get_return_track_info",
    "set_return_volume",
    "set_return_pan",
    "select_track",
    "get_selected_track",
    "create_clip",
    "get_clip_notes",
    "add_notes_to_clip",
    "get_arrangement_clips",
    "create_arrangement_midi_clip",
    "create_arrangement_audio_clip",
    "delete_arrangement_clip",
    "resize_arrangement_clip",
    "move_arrangement_clip",
    "add_notes_to_arrangement_clip",
    "get_arrangement_clip_notes",
    "duplicate_to_arrangement",
    "get_track_devices",
    "get_device_parameters",
    "set_device_parameter_by_name",
    "get_device_parameter_by_name",
    "get_device_parameters_at_path",
    "set_device_parameter_at_path",
    "set_device_parameter_by_name_at_path",
    "get_browser_tree",
    "get_browser_items_at_path",
    "search_browser",
    "load_instrument_or_effect",
    "load_drum_kit",
    "create_rack",
    "insert_rack_chain",
    "insert_device_in_chain",
    "get_rack_chains",
    "get_rack_macros",
    "set_rack_macro",
    "get_rack_structure",
    "get_chain_devices",
    "set_chain_mute",
    "set_chain_solo",
    "set_chain_volume",
    "apply_rack_blueprint",
    "get_drum_rack_pads",
    "set_drum_rack_pad_note",
    "set_drum_rack_pad_mute",
    "set_drum_rack_pad_solo",
    "read_memory_bank",
    "write_memory_bank",
    "append_rack_entry",
    "get_system_owned_racks",
    "refresh_rack_memory_entry",
)


DEVICE_INDEX_NOTES = (
    "Validated in Ableton Live 12.3.7 locally on 2026-04-11 on a disposable MIDI track loaded with "
    "native devices. Top-level device_index follows the current Remote Script track.devices ordering; "
    "on the validated Python Remote Script surface, track.devices excluded the mixer device."
)
DEVICE_ACTIVATOR_HELPER_NOTE = (
    "Validated in Ableton Live 12.3.7 locally on 2026-04-11 as an activator-parameter helper on "
    "native devices loaded onto a disposable MIDI track. The LOM documents Device.is_active as "
    "read-only, so this command is confirmed only for the helper semantics, not as a universal "
    "device-power setter."
)


_COMMAND_SPECS = [
    _spec("health_check", "health", result="{status, tempo, is_playing, track_count}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09."),

    _spec("get_session_info", "song", result="session snapshot with tracks, return tracks, and scenes", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09."),
    _spec("get_current_song_time", "song", result="{current_song_time}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09."),
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
    _spec("get_session_path", "song", result="{path}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 against a saved Live Set. Backed by Song.file_path and used for project-root Memory Bank persistence."),
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

    _spec("get_track_info", "track", required=("track_index",), result="track details with devices, clip slots, sends", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09."),
    _spec("get_all_track_names", "track", result="{tracks[]}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09."),
    _spec("create_midi_track", "track", optional=("index",), result="{index, name}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 with create/delete cleanup."),
    _spec("create_audio_track", "track", optional=("index",), result="{index, name}", write=True, stability="likely-complete", exposed=True),
    _spec("create_return_track", "track", result="{index, name}", write=True, stability="likely-complete"),
    _spec("delete_track", "track", required=("track_index",), result="{deleted_index}", write=True, stability="confirmed", notes="Validated in Ableton Live 12 locally on 2026-04-09 with create/delete cleanup."),
    _spec("duplicate_track", "track", required=("track_index",), result="{original_index}", write=True, stability="likely-complete"),
    _spec("set_track_name", "track", required=("track_index", "name"), result="{name}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with direct readback on a disposable track."),
    _spec("set_track_color", "track", required=("track_index", "color"), result="{color}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 against the applied/read-back color because Live maps requested RGB values to the nearest chooser color."),
    _spec("set_track_volume", "track", required=("track_index", "volume"), result="{volume}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with direct readback on a disposable track. Writes clamp to 0.0..1.0."),
    _spec("set_track_pan", "track", required=("track_index", "pan"), result="{pan}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with direct readback on a disposable track. Writes clamp to -1.0..1.0."),
    _spec("set_track_mute", "track", required=("track_index", "mute"), result="{mute}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with direct readback on a disposable track."),
    _spec("set_track_solo", "track", required=("track_index", "solo"), result="{solo}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with target-state readback on a disposable track. Live exclusive-solo side effects are not assumed."),
    _spec("set_track_arm", "track", required=("track_index", "arm"), result="{arm}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 on an armable disposable track. Raises a stable ValueError when the target track cannot be armed."),
    _spec("set_track_monitoring", "track", required=("track_index",), optional=("monitoring",), result="{monitoring}", write=True, stability="likely-complete"),
    _spec("freeze_track", "track", required=("track_index",), result="{ok}", write=True, stability="partial"),
    _spec("flatten_track", "track", required=("track_index",), result="{ok}", write=True, stability="partial"),
    _spec("fold_track", "track", required=("track_index",), result="{fold_state}", write=True, stability="likely-complete", exposed=True, notes="Negative-path validation ran in Ableton Live 12.3+ locally on 2026-04-10 and raises a stable ValueError when the target track is not foldable. Positive round-trip confirmation still requires an existing foldable group track."),
    _spec("unfold_track", "track", required=("track_index",), result="{fold_state}", write=True, stability="likely-complete", exposed=True, notes="Awaiting positive round-trip validation on an existing foldable group track. Negative-path validation is covered by the stable foldability check."),
    _spec("unarm_all", "track", result="{ok}", write=True, stability="likely-complete"),
    _spec("unsolo_all", "track", result="{ok}", write=True, stability="likely-complete"),
    _spec("unmute_all", "track", result="{ok}", write=True, stability="likely-complete"),
    _spec("set_track_delay", "track", required=("track_index", "delay_ms"), result="{delay_ms}", write=True, stability="partial"),
    _spec("set_send_level", "track", required=("track_index", "send_index", "level"), result="{send_index, level}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 on a disposable track in a set with existing return tracks. Writes clamp to 0.0..1.0 and raise a stable ValueError on bad send_index."),
    _spec("get_return_tracks", "track", result="{return_tracks[]}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 in a set with existing return tracks."),
    _spec("get_return_track_info", "track", required=("return_index",), result="return track details", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 and uses stable return-track bounds checking."),
    _spec("set_return_volume", "track", required=("return_index", "volume"), result="{volume}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with direct readback on an existing return track. Writes clamp to 0.0..1.0 and use stable return-track lookup."),
    _spec("set_return_pan", "track", required=("return_index", "pan"), result="{pan}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with direct readback on an existing return track. Writes clamp to -1.0..1.0 and use stable return-track lookup."),
    _spec("set_track_input_routing", "track", required=("track_index", "routing_type"), result="{input_routing_type}", write=True, stability="partial"),
    _spec("set_track_output_routing", "track", required=("track_index", "routing_type"), result="{output_routing_type}", write=True, stability="partial"),
    _spec("get_track_input_routing", "track", required=("track_index",), result="{current_input_routing, available_input_routing_types[]}", stability="likely-complete"),
    _spec("get_track_output_routing", "track", required=("track_index",), result="{current_output_routing, available_output_routing_types[]}", stability="likely-complete"),
    _spec("select_track", "track", optional=("track_index", "return_index", "master"), result="{selection_type, index, track_index, return_index, name, selected_track_index}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for regular-track, return-track, and master-track selection. Requires exactly one of track_index, return_index, or master=True."),
    _spec("get_selected_track", "track", result="{selection_type, index, track_index, return_index, name}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for regular-track, return-track, and master-track selections. Distinguishes track, return_track, master_track, and unknown."),
    _spec("get_master_info", "track", result="{volume, pan, output_meter_left, output_meter_right}", stability="likely-complete"),
    _spec("set_master_volume", "track", required=("volume",), result="{volume}", write=True, stability="likely-complete"),
    _spec("set_master_pan", "track", required=("pan",), result="{pan}", write=True, stability="likely-complete"),
    _spec("get_master_output_meter", "track", result="{left, right}", stability="likely-complete"),
    _spec("get_cue_volume", "track", result="{cue_volume}", stability="likely-complete"),
    _spec("set_cue_volume", "track", required=("volume",), result="{cue_volume}", write=True, stability="likely-complete"),

    _spec("get_clip_info", "session_clip", required=("track_index", "slot_index"), result="session clip details", stability="likely-complete"),
    _spec("create_clip", "session_clip", required=("track_index", "slot_index"), optional=("length",), result="session clip details", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 with create/delete cleanup."),
    _spec("delete_clip", "session_clip", required=("track_index", "slot_index"), result="{ok}", write=True, stability="confirmed", notes="Validated in Ableton Live 12 locally on 2026-04-09 with create/delete cleanup."),
    _spec("duplicate_clip", "session_clip", required=("track_index", "slot_index"), optional=("destination_slot_index",), result="{ok, destination_slot_index}", write=True, stability="partial"),
    _spec("set_clip_name", "session_clip", required=("track_index", "slot_index", "name"), result="{name}", write=True, stability="likely-complete"),
    _spec("set_clip_color", "session_clip", required=("track_index", "slot_index", "color"), result="{color}", write=True, stability="likely-complete"),
    _spec("fire_clip", "session_clip", required=("track_index", "slot_index"), result="{ok}", write=True, stability="likely-complete"),
    _spec("stop_clip", "session_clip", required=("track_index", "slot_index"), result="{ok}", write=True, stability="likely-complete"),
    _spec("get_clip_notes", "session_clip", required=("track_index", "slot_index"), result="{notes[], count}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 with note round-trip verification."),
    _spec("add_notes_to_clip", "session_clip", required=("track_index", "slot_index", "notes"), result="{added}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 with note round-trip verification."),
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

    _spec("get_arrangement_clips", "arrangement", required=("track_index",), result="{track_index, clips[]}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09."),
    _spec("get_all_arrangement_clips", "arrangement", result="{tracks[]}", stability="likely-complete"),
    _spec("create_arrangement_midi_clip", "arrangement", required=("track_index", "start_time"), optional=("length",), result="{start_time, end_time, length, name}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 with note round-trip verification."),
    _spec("create_arrangement_audio_clip", "arrangement", required=("track_index", "file_path", "start_time"), result="{start_time, end_time, length, name, file_path}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 with an absolute file path on an audio track."),
    _spec("delete_arrangement_clip", "arrangement", required=("track_index",), optional=("clip_index", "start_time"), result="{ok}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09. Requires exactly one selector: clip_index or start_time."),
    _spec("resize_arrangement_clip", "arrangement", required=("track_index", "length"), optional=("clip_index", "start_time"), result="{start_time, end_time, length}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 for MIDI arrangement clips. Requires length > 0 and exactly one selector."),
    _spec("move_arrangement_clip", "arrangement", required=("track_index", "new_start_time"), optional=("clip_index", "start_time"), result="{start_time, end_time, length, notes_restored}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 for MIDI arrangement clips only. Requires exactly one selector."),
    _spec("add_notes_to_arrangement_clip", "arrangement", required=("track_index", "notes"), optional=("clip_index", "start_time"), result="{added}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 with note round-trip verification."),
    _spec("get_arrangement_clip_notes", "arrangement", required=("track_index",), optional=("clip_index", "start_time"), result="{notes[], count}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 with note round-trip verification."),
    _spec("duplicate_to_arrangement", "arrangement", required=("track_index", "slot_index"), optional=("start_time",), result="{ok, start_time, source_track_index, source_slot_index}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 with session-to-arrangement MIDI note round-trip verification."),

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

    _spec("get_track_devices", "device", required=("track_index",), result="{track_index, devices[]}", stability="confirmed", exposed=True, notes=DEVICE_INDEX_NOTES),
    _spec("get_device_parameters", "device", required=("track_index", "device_index"), result="device parameter details", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 for top-level native-device parameter inspection on a disposable MIDI track. {}".format(DEVICE_INDEX_NOTES)),
    _spec("set_device_parameter", "device", required=("track_index", "device_index", "parameter_index", "value"), result="{parameter_index, name, value, display_value}", write=True, stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 for writable top-level native-device parameters on a disposable MIDI track."),
    _spec("set_device_parameter_by_name", "device", required=("track_index", "device_index", "name", "value"), result="{name, value, display_value}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 for writable top-level native-device parameters by name on a disposable MIDI track."),
    _spec("get_device_parameter_by_name", "device", required=("track_index", "device_index", "name"), result="single parameter details", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 against the same native-device parameter targets used for write/readback."),
    _spec("get_device_parameters_at_path", "device", required=("track_index", "device_path"), result="nested device parameter details", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 on nested built-in devices inside system-owned rack trees. Uses track-relative LOM-style device paths."),
    _spec("set_device_parameter_at_path", "device", required=("track_index", "device_path", "parameter_index", "value"), result="{device_path, parameter_index, name, value}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for nested built-in device tuning inside system-owned rack trees. Uses track-relative LOM-style device paths."),
    _spec("set_device_parameter_by_name_at_path", "device", required=("track_index", "device_path", "name", "value"), result="{device_path, parameter_index, name, value}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for nested built-in device tuning inside system-owned rack trees. Uses track-relative LOM-style device paths and resolves validated EQ Eight shorthand aliases."),
    _spec("toggle_device", "device", required=("track_index", "device_index"), result="{is_active, enabled, parameter_name, mode, stability}", write=True, stability="confirmed", notes=DEVICE_ACTIVATOR_HELPER_NOTE),
    _spec("set_device_enabled", "device", required=("track_index", "device_index", "enabled"), result="{is_active, enabled, parameter_name, mode, stability}", write=True, stability="confirmed", notes=DEVICE_ACTIVATOR_HELPER_NOTE),
    _spec("delete_device", "device", required=("track_index", "device_index"), result="{ok, deleted_index}", write=True, stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 for top-level native-device deletion on a disposable MIDI track. {}".format(DEVICE_INDEX_NOTES)),
    _spec("move_device", "device", required=("track_index", "device_index", "new_index"), result="{ok, new_index, requested_index, stability}", write=True, stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 for same-track reordering of top-level native audio effects on a disposable MIDI track. Uses Song.move_device(device, target, target position) on the validated Python surface. {}".format(DEVICE_INDEX_NOTES)),
    _spec("show_plugin_window", "device", required=("track_index", "device_index"), result="{ok, device_name, mode, collapsed, stability}", write=True, stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 only for device-view expansion via Device.View.is_collapsed. This is not confirmed plugin editor window control."),
    _spec("hide_plugin_window", "device", required=("track_index", "device_index"), result="{ok, device_name, mode, collapsed, stability}", write=True, stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 only for device-view collapse via Device.View.is_collapsed. This is not confirmed plugin editor window control."),
    _spec("load_instrument_or_effect", "device", required=("track_index",), optional=("device_name", "native_device_name", "target_index", "uri"), result="{ok, mode, device_count_before, device_count_after, ...}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 for built-in native instrument names and discovered built-in instrument, MIDI-effect, and audio-effect URIs, then revalidated on 2026-04-11 for top-level native device insertion metadata during the device audit pass. Requires exactly one source. Native device_name/native_device_name insertion relies on Track.insert_device and is therefore limited to native Live devices; Max for Live devices and third-party plugin insertion remain backlog work."),
    _spec("get_device_class_name", "device", required=("track_index", "device_index"), result="{class_name, name}", stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 for top-level native devices on a disposable MIDI track."),
    _spec("select_device", "device", required=("track_index", "device_index"), result="{ok, device_name}", write=True, stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 against top-level native devices on a selected disposable MIDI track."),
    _spec("get_selected_device", "device", result="{selected, track_index, device_index, name, class_name}", stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 using Song.View.selected_track plus Track.View.selected_device on a disposable MIDI track."),

    _spec("create_rack", "rack", required=("track_index", "rack_type", "name"), optional=("target_path",), result="{rack_id, rack_path, device_index, name, rack_type}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for native Instrument Rack and Audio Effect Rack creation on disposable tracks and nested chain targets. Registers system-owned racks in the project Memory Bank."),
    _spec("insert_rack_chain", "rack", required=("track_index", "rack_path", "name"), optional=("index",), result="{rack_path, chain_index, chain_path, name}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for system-owned Instrument Rack and Audio Effect Rack chains. Uses RackDevice.insert_chain() with track-relative LOM-style rack paths."),
    _spec("insert_device_in_chain", "rack", required=("track_index", "chain_path", "native_device_name"), optional=("device_name", "target_index"), result="{chain_path, device_path, name, class_name}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for built-in Live device insertion inside system-owned rack chains. Uses Chain.insert_device() and normalizes validated native-device aliases such as Eq8 -> EQ Eight."),
    _spec("get_rack_chains", "rack", required=("track_index", "device_index"), result="{rack_name, chains[]}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 and revalidated on 2026-04-10 against populated system-owned Instrument Rack and Audio Effect Rack chains. Chain lookup is bounds-checked."),
    _spec("get_rack_macros", "rack", required=("track_index", "device_index"), result="{rack_name, macros[]}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 and revalidated on 2026-04-10 against system-owned racks. Returns stable macro indices for read/write use."),
    _spec("set_rack_macro", "rack", required=("track_index", "device_index", "macro_index", "value"), result="{name, value}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 and revalidated on 2026-04-10 against system-owned racks. Macro writes clamp to the parameter range."),
    _spec("get_rack_structure", "rack", required=("track_index", "rack_path"), result="{track_index, rack_path, rack}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10. Recursively serializes chains, return_chains, nested devices, macros, and track-relative LOM-style paths for a system-owned rack tree."),
    _spec("get_chain_devices", "rack", required=("track_index", "device_index", "chain_index"), result="{chain_name, devices[]}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 and revalidated on 2026-04-10 on populated system-owned rack chains. Chain lookup is bounds-checked."),
    _spec("set_chain_mute", "rack", required=("track_index", "device_index", "chain_index", "mute"), result="{mute}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 and revalidated on 2026-04-10 on populated system-owned rack chains. Chain lookup is bounds-checked."),
    _spec("set_chain_solo", "rack", required=("track_index", "device_index", "chain_index", "solo"), result="{solo}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 and revalidated on 2026-04-10 on populated system-owned rack chains. Chain lookup is bounds-checked."),
    _spec("set_chain_volume", "rack", required=("track_index", "device_index", "chain_index", "volume"), result="{volume}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 and revalidated on 2026-04-10 on populated system-owned rack chains. Chain volume writes clamp to the supported range."),
    _spec("apply_rack_blueprint", "rack", required=("blueprint",), result="{rack_id, rack_path, created_racks, created_chains, created_devices, structure}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for deterministic system-owned rack generation and nested tuning. Rejects undocumented native macro-mapping directives with a stable ValueError."),
    _spec("get_drum_rack_pads", "rack", required=("track_index", "device_index"), result="{drum_pads[], count}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09. Top-level Drum Racks expose drum_pads. Inner Drum Racks return zero pads."),
    _spec("set_drum_rack_pad_note", "rack", required=("track_index", "device_index", "note", "new_note"), result="{note}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09. Uses DrumChain.in_note because DrumPad.note is read-only in the LOM. Requires Live 12.3+ and remap readback is validated on the destination pad."),
    _spec("set_drum_rack_pad_mute", "rack", required=("track_index", "device_index", "note", "mute"), result="{note, mute}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09. Pad lookup is note-based on top-level Drum Racks and falls back to chain mute when pad-level mute does not stick."),
    _spec("set_drum_rack_pad_solo", "rack", required=("track_index", "device_index", "note", "solo"), result="{note, solo}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09. Pad lookup is note-based on top-level Drum Racks."),

    _spec("get_browser_tree", "browser", optional=("category_type",), result="browser tree snapshot", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 across the normalized top-level browser categories."),
    _spec("get_browser_items_at_path", "browser", optional=("path",), result="{items[], path}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 for top-level browser navigation, including instruments and drums."),
    _spec("search_browser", "browser", optional=("query", "category"), result="{query, results[], count}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09. Requires a non-empty query."),
    _spec("load_drum_kit", "browser", required=("track_index", "rack_uri"), result="{ok, loaded, device_count_before, device_count_after, ...}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12 locally on 2026-04-09 for discovered built-in drum-kit preset URIs. Generic Drum Rack device entries remain rejected."),

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

    _spec("read_memory_bank", "memory_bank", required=("file_name",), result="markdown string", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 against the saved-set project-root .ableton-mcp/memory directory."),
    _spec("write_memory_bank", "memory_bank", required=("file_name", "content"), result="confirmation string", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 against the saved-set project-root .ableton-mcp/memory directory. Requires a saved Live Set."),
    _spec("append_rack_entry", "memory_bank", required=("rack_data",), result="confirmation string", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 by appending a rack-note record into the project Memory Bank."),
    _spec("get_system_owned_racks", "memory_bank", result="{count, racks[]}", stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10. Returns the parsed system-owned rack inventory tracked in racks.md."),
    _spec("refresh_rack_memory_entry", "memory_bank", required=("track_index", "rack_path"), result="{rack_id, track_index, rack_path}", write=True, stability="confirmed", exposed=True, notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 by re-snapshotting live rack structure into the project Memory Bank using a track-relative LOM-style rack path."),
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
