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
    description: str = ""

    @property
    def tool_description(self):
        if self.description:
            stability_tag = " (Stability: {}.)".format(self.stability)
            return self.description.rstrip() + stability_tag
        fallback = "{} command. Stability: {}.".format(
            self.domain.replace("_", " ").title(), self.stability
        )
        if self.notes:
            fallback = "{} {}".format(fallback, self.notes)
        return fallback


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
    description="",
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
        description=description,
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
    "get_take_lanes",
    "create_take_lane",
    "set_take_lane_name",
    "create_midi_clip_in_lane",
    "get_clips_in_take_lane",
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
RACK_MACRO_NOTE = (
    "Validated in Ableton Live 12.3.7 locally on 2026-04-11 for exposed macro value read/write on a "
    "top-level system-owned rack. The validation helper created a disposable system-owned rack when the "
    "saved Memory Bank inventory no longer matched live top-level rack devices. This confirms macro value "
    "inspection and mutation for already-exposed macros only. The LOM audit found no documented native "
    "macro-to-parameter or macro-to-macro authoring API."
)
USER_RACK_SEMANTICS_NOTE = (
    "Direct rack inspection was revalidated in Ableton Live 12.3.7 locally on 2026-04-12 against imported "
    "rack preset '808 Selector Rack.adg' before Memory Bank import. Live structure and already-exposed "
    "macros are directly inspectable, but trustworthy repo-level semantic metadata for imported/user-authored "
    "racks still requires explicit Memory Bank import via refresh_rack_memory_entry."
)


_COMMAND_SPECS = [
    _spec(
        "health_check", "health",
        result="{status, tempo, is_playing, track_count}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09.",
        description=(
            "Cheap liveness probe for the Ableton Remote Script bridge. "
            "Returns {status: 'ok', tempo, is_playing, track_count} when Live is reachable. "
            "Use as the first call in a session to confirm the bridge is up before issuing other tools."
        ),
    ),

    _spec(
        "get_session_info", "song",
        result="session snapshot with tracks, return tracks, and scenes",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09.",
        description=(
            "Snapshot of the current Live Set: tempo, transport state, scene count, "
            "and per-track summaries (name, type, mute/solo/arm, send count). "
            "Use for orientation at the start of a task. For full clip/device detail call get_track_info per track."
        ),
    ),
    _spec(
        "get_current_song_time", "song",
        result="{current_song_time}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09.",
        description=(
            "Read the Arrangement playhead position in beats. Returns {current_song_time}."
        ),
    ),
    _spec(
        "set_current_song_time", "song",
        required=("time",), result="{current_song_time}",
        write=True, stability="likely-complete", exposed=True,
        description=(
            "Move the Arrangement playhead. Pass time in beats (>= 0). Returns the new {current_song_time}. "
            "Idempotent: re-applying the same time is a no-op."
        ),
    ),
    _spec(
        "set_tempo", "song",
        required=("tempo",), result="{tempo}",
        write=True, stability="likely-complete", exposed=True,
        description=(
            "Set the master tempo in BPM. Live's documented range is 20.0..999.0 BPM. "
            "Returns the applied {tempo}."
        ),
    ),
    _spec("set_time_signature", "song", optional=("numerator", "denominator"), result="{numerator, denominator}", write=True, stability="likely-complete"),
    _spec(
        "start_playback", "song",
        result="{is_playing}",
        write=True, stability="likely-complete", exposed=True,
        description=(
            "Start the global transport. Returns {is_playing: True}. Idempotent: calling while already playing is a no-op."
        ),
    ),
    _spec(
        "stop_playback", "song",
        result="{is_playing}",
        write=True, stability="likely-complete", exposed=True,
        description=(
            "Stop the global transport and reset the Arrangement playhead per Live's stop semantics. "
            "Returns {is_playing: False}. Idempotent: calling while already stopped is a no-op."
        ),
    ),
    _spec("continue_playback", "song", result="{is_playing}", write=True, stability="likely-complete"),
    _spec("start_recording", "song", result="{recording}", write=True, stability="likely-complete"),
    _spec("stop_recording", "song", result="{recording}", write=True, stability="likely-complete"),
    _spec("toggle_session_record", "song", result="{session_record}", write=True, stability="likely-complete"),
    _spec("toggle_arrangement_record", "song", result="{record_mode}", write=True, stability="likely-complete"),
    _spec("set_metronome", "song", required=("enabled",), result="{metronome}", write=True, stability="likely-complete"),
    _spec("tap_tempo", "song", result="{tempo}", write=True, stability="likely-complete"),
    _spec("undo", "song", result="{ok}", write=True, stability="likely-complete", notes="Global undo remains likely-complete. In the 2026-04-12 arrangement residual validator pass, can_undo/can_redo snapshots were captured for the audited arrangement mutation slice, but undo repeatedly popped disposable track setup instead of proving clean clip-state rollback for those mutations."),
    _spec("redo", "song", result="{ok}", write=True, stability="likely-complete", notes="Global redo remains likely-complete. In the 2026-04-12 arrangement residual validator pass, redo evidence was captured for the audited arrangement mutation slice, but a clean arrangement clip mutate->undo->redo round-trip was not yet proven in that run because undo targeted disposable track setup."),
    _spec("capture_midi", "song", result="{ok}", write=True, stability="likely-complete"),
    _spec("re_enable_automation", "song", result="{ok}", write=True, stability="likely-complete"),
    _spec("set_arrangement_loop", "song", optional=("start", "length", "enabled"), result="{loop_start, loop_length, loop_on}", write=True, stability="likely-complete"),
    _spec("get_cpu_load", "song", result="{cpu_load}", stability="likely-complete", notes="Backed by Application.average_process_usage."),
    _spec(
        "get_session_path", "song",
        result="{path}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 against a saved Live Set. Backed by Song.file_path and used for project-root Memory Bank persistence.",
        description=(
            "Filesystem path of the open Live Set. Returns {path: '<absolute path>'} for a saved set; "
            "{path: null} when the set has never been saved. Used by Memory Bank tools to anchor project-root storage."
        ),
    ),
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

    _spec(
        "get_track_info", "track",
        required=("track_index",),
        result="track details with devices, clip slots, sends",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09.",
        description=(
            "Detailed view of a single regular track: name, type, mixer state, devices[], clip_slots[], sends[]. "
            "Use after get_session_info to drill into a specific track. track_index addresses regular tracks only "
            "(0-based); for return tracks call get_return_track_info, and for the master use the master-specific tools."
        ),
    ),
    _spec(
        "get_all_track_names", "track",
        result="{tracks[]}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09.",
        description=(
            "Compact list of all regular tracks: returns {tracks: [{index, name, type}]}. "
            "Cheaper than get_session_info when you only need names; does not include return or master tracks."
        ),
    ),
    _spec(
        "create_midi_track", "track",
        optional=("index",), result="{index, name}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 with create/delete cleanup.",
        description=(
            "Create a new MIDI track. Optional index inserts at that position (0-based); omit to append at the end. "
            "Returns {index, name} of the new track. Not idempotent."
        ),
    ),
    _spec(
        "create_audio_track", "track",
        optional=("index",), result="{index, name}",
        write=True, stability="likely-complete", exposed=True,
        description=(
            "Create a new audio track. Optional index inserts at that position (0-based); omit to append at the end. "
            "Returns {index, name} of the new track. Not idempotent."
        ),
    ),
    _spec("create_return_track", "track", result="{index, name}", write=True, stability="likely-complete"),
    _spec("delete_track", "track", required=("track_index",), result="{deleted_index}", write=True, stability="confirmed", notes="Validated in Ableton Live 12 locally on 2026-04-09 with create/delete cleanup."),
    _spec("duplicate_track", "track", required=("track_index",), result="{original_index}", write=True, stability="likely-complete"),
    _spec(
        "set_track_name", "track",
        required=("track_index", "name"),
        result="{name}", write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with direct readback on a disposable track.",
        description="Rename a regular track. Returns the applied {name}.",
    ),
    _spec(
        "set_track_color", "track",
        required=("track_index", "color"),
        result="{color}", write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 against the applied/read-back color because Live maps requested RGB values to the nearest chooser color.",
        description=(
            "Set the track color. Pass color as Live's packed integer (0xRRGGBB). "
            "Live snaps the value to the nearest chooser entry, so the returned {color} may differ from the requested one — "
            "always validate against the read-back, not the request."
        ),
    ),
    _spec(
        "set_track_volume", "track",
        required=("track_index", "volume"),
        result="{volume}", write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with direct readback on a disposable track. Writes clamp to 0.0..1.0.",
        description=(
            "Set track volume in normalized mixer units (0.0..1.0; 0.85 ≈ 0 dB). "
            "Out-of-range values are clamped. Returns the applied {volume}."
        ),
    ),
    _spec(
        "set_track_pan", "track",
        required=("track_index", "pan"),
        result="{pan}", write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with direct readback on a disposable track. Writes clamp to -1.0..1.0.",
        description=(
            "Set track pan from -1.0 (full left) to 1.0 (full right); 0.0 = center. "
            "Out-of-range values are clamped. Returns the applied {pan}."
        ),
    ),
    _spec(
        "set_track_mute", "track",
        required=("track_index", "mute"),
        result="{mute}", write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with direct readback on a disposable track.",
        description="Mute or unmute a track. Pass mute=true/false. Returns the applied {mute}.",
    ),
    _spec(
        "set_track_solo", "track",
        required=("track_index", "solo"),
        result="{solo}", write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with target-state readback on a disposable track. Live exclusive-solo side effects are not assumed.",
        description=(
            "Solo or unsolo a track. Pass solo=true/false. Returns the applied {solo}. "
            "Live's exclusive-solo preference may unsolo other tracks as a side effect — read those tracks back if you need to know."
        ),
    ),
    _spec(
        "set_track_arm", "track",
        required=("track_index", "arm"),
        result="{arm}", write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 on an armable disposable track. Raises a stable ValueError when the target track cannot be armed.",
        description=(
            "Arm or disarm a track for recording. Pass arm=true/false. Returns the applied {arm}. "
            "Group, return, and master tracks are not armable — those raise a stable ValueError."
        ),
    ),
    _spec("set_track_monitoring", "track", required=("track_index",), optional=("monitoring",), result="{monitoring}", write=True, stability="likely-complete"),
    _spec("freeze_track", "track", required=("track_index",), result="{ok}", write=True, stability="partial"),
    _spec("flatten_track", "track", required=("track_index",), result="{ok}", write=True, stability="partial"),
    _spec(
        "fold_track", "track",
        required=("track_index",), result="{fold_state}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 on foldable group track '5-Group' with a positive fold/unfold round-trip and restored original fold_state. The current Python Remote Script surface did not expose child-track is_visible readback, so confirmation rests on fold_state round-trip plus grouped-child discovery rather than direct visibility assertions. Still raises a stable ValueError when the target track is not foldable.",
        description=(
            "Collapse a group track to hide its children. Returns {fold_state: True}. "
            "Only foldable group tracks accept this — non-foldable tracks raise a stable ValueError."
        ),
    ),
    _spec(
        "unfold_track", "track",
        required=("track_index",), result="{fold_state}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 on foldable group track '5-Group' with a positive fold/unfold round-trip and restored original fold_state. The current Python Remote Script surface did not expose child-track is_visible readback, so confirmation rests on fold_state round-trip plus grouped-child discovery rather than direct visibility assertions. Still raises a stable ValueError when the target track is not foldable.",
        description=(
            "Expand a group track to show its children. Returns {fold_state: False}. "
            "Only foldable group tracks accept this — non-foldable tracks raise a stable ValueError."
        ),
    ),
    _spec("unarm_all", "track", result="{ok}", write=True, stability="likely-complete"),
    _spec("unsolo_all", "track", result="{ok}", write=True, stability="likely-complete"),
    _spec("unmute_all", "track", result="{ok}", write=True, stability="likely-complete"),
    _spec("set_track_delay", "track", required=("track_index", "delay_ms"), result="{delay_ms}", write=True, stability="partial"),
    _spec(
        "set_send_level", "track",
        required=("track_index", "send_index", "level"),
        result="{send_index, level}", write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 on a disposable track in a set with existing return tracks. Writes clamp to 0.0..1.0 and raise a stable ValueError on bad send_index.",
        description=(
            "Set a track's send level (its contribution to a return). send_index is 0-based against the set's return tracks. "
            "level is 0.0..1.0 (clamped). Returns {send_index, level}. Raises a stable ValueError on out-of-range send_index."
        ),
    ),
    _spec(
        "get_return_tracks", "track",
        result="{return_tracks[]}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 in a set with existing return tracks.",
        description=(
            "List the set's return tracks. Returns {return_tracks: [{return_index, name, ...}]}. "
            "Use return_index in get_return_track_info / set_return_volume / set_return_pan."
        ),
    ),
    _spec(
        "get_return_track_info", "track",
        required=("return_index",), result="return track details",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 and uses stable return-track bounds checking.",
        description=(
            "Detailed view of one return track: name, mixer state, devices[]. return_index is 0-based against the set's return tracks. "
            "Out-of-range values raise a stable ValueError."
        ),
    ),
    _spec(
        "set_return_volume", "track",
        required=("return_index", "volume"), result="{volume}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with direct readback on an existing return track. Writes clamp to 0.0..1.0 and use stable return-track lookup.",
        description=(
            "Set a return track's volume in normalized mixer units (0.0..1.0; clamped). "
            "return_index is 0-based against the set's return tracks. Returns the applied {volume}."
        ),
    ),
    _spec(
        "set_return_pan", "track",
        required=("return_index", "pan"), result="{pan}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 with direct readback on an existing return track. Writes clamp to -1.0..1.0 and use stable return-track lookup.",
        description=(
            "Set a return track's pan from -1.0 (full left) to 1.0 (full right); 0.0 = center. Clamped. "
            "return_index is 0-based against the set's return tracks. Returns the applied {pan}."
        ),
    ),
    _spec("set_track_input_routing", "track", required=("track_index", "routing_type"), result="{input_routing_type}", write=True, stability="partial"),
    _spec("set_track_output_routing", "track", required=("track_index", "routing_type"), result="{output_routing_type}", write=True, stability="partial"),
    _spec("get_track_input_routing", "track", required=("track_index",), result="{current_input_routing, available_input_routing_types[]}", stability="likely-complete"),
    _spec("get_track_output_routing", "track", required=("track_index",), result="{current_output_routing, available_output_routing_types[]}", stability="likely-complete"),
    _spec(
        "select_track", "track",
        optional=("track_index", "return_index", "master"),
        result="{selection_type, index, track_index, return_index, name, selected_track_index}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for regular-track, return-track, and master-track selection. Requires exactly one of track_index, return_index, or master=True.",
        description=(
            "Select a track in Live's UI. Pass exactly one selector: track_index for a regular track, "
            "return_index for a return track, or master=True for the master. Passing zero or multiple raises a stable ValueError. "
            "Returns {selection_type, index, track_index, return_index, name, selected_track_index} reflecting the new selection."
        ),
    ),
    _spec(
        "get_selected_track", "track",
        result="{selection_type, index, track_index, return_index, name}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for regular-track, return-track, and master-track selections. Distinguishes track, return_track, master_track, and unknown.",
        description=(
            "Read the current track selection. Returns {selection_type, index, track_index, return_index, name}. "
            "selection_type is one of 'track', 'return_track', 'master_track', or 'unknown'."
        ),
    ),
    _spec("get_master_info", "track", result="{volume, pan, output_meter_left, output_meter_right}", stability="likely-complete"),
    _spec("set_master_volume", "track", required=("volume",), result="{volume}", write=True, stability="likely-complete"),
    _spec("set_master_pan", "track", required=("pan",), result="{pan}", write=True, stability="likely-complete"),
    _spec("get_master_output_meter", "track", result="{left, right}", stability="likely-complete"),
    _spec("get_cue_volume", "track", result="{cue_volume}", stability="likely-complete"),
    _spec("set_cue_volume", "track", required=("volume",), result="{cue_volume}", write=True, stability="likely-complete"),

    _spec("get_clip_info", "session_clip", required=("track_index", "slot_index"), result="session clip details", stability="likely-complete"),
    _spec(
        "create_clip", "session_clip",
        required=("track_index", "slot_index"), optional=("length",),
        result="session clip details",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 with create/delete cleanup.",
        description=(
            "Create an empty MIDI clip in a Session View slot. slot_index is the row in the track's clip_slots. "
            "length is in beats (defaults to 4.0). Returns the new clip's details. Not idempotent."
        ),
    ),
    _spec("delete_clip", "session_clip", required=("track_index", "slot_index"), result="{ok}", write=True, stability="confirmed", notes="Validated in Ableton Live 12 locally on 2026-04-09 with create/delete cleanup."),
    _spec("duplicate_clip", "session_clip", required=("track_index", "slot_index"), optional=("destination_slot_index",), result="{ok, destination_slot_index}", write=True, stability="partial"),
    _spec("set_clip_name", "session_clip", required=("track_index", "slot_index", "name"), result="{name}", write=True, stability="likely-complete"),
    _spec("set_clip_color", "session_clip", required=("track_index", "slot_index", "color"), result="{color}", write=True, stability="likely-complete"),
    _spec("fire_clip", "session_clip", required=("track_index", "slot_index"), result="{ok}", write=True, stability="likely-complete"),
    _spec("stop_clip", "session_clip", required=("track_index", "slot_index"), result="{ok}", write=True, stability="likely-complete"),
    _spec(
        "get_clip_notes", "session_clip",
        required=("track_index", "slot_index"),
        result="{notes[], count}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 with note round-trip verification.",
        description=(
            "Read all MIDI notes from a Session clip. Returns {notes: [{pitch, start_time, duration, velocity, mute}], count}. "
            "Times are clip-relative beats."
        ),
    ),
    _spec(
        "add_notes_to_clip", "session_clip",
        required=("track_index", "slot_index", "notes"),
        result="{added}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 with note round-trip verification.",
        description=(
            "Append MIDI notes to a Session clip without removing existing notes. "
            "Each note: {pitch (0..127), start_time (beats >= 0), duration (beats > 0), velocity (1..127), mute (bool)}. "
            "Returns {added: <count>}."
        ),
    ),
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

    _spec(
        "get_arrangement_clips", "arrangement",
        required=("track_index",),
        result="{track_index, clips[]}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09.",
        description=(
            "List a track's Arrangement clips in start-time order. "
            "Returns {track_index, clips: [{clip_index, start_time, end_time, length, name, is_midi_clip, ...}]}."
        ),
    ),
    _spec("get_all_arrangement_clips", "arrangement", result="{tracks[]}", stability="likely-complete"),
    _spec(
        "create_arrangement_midi_clip", "arrangement",
        required=("track_index", "start_time"), optional=("length",),
        result="{start_time, end_time, length, name}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 with note round-trip verification.",
        description=(
            "Create an empty MIDI clip on a track at start_time (beats). length defaults to 4.0 and must be > 0. "
            "Returns {start_time, end_time, length, name}. Not idempotent."
        ),
    ),
    _spec(
        "create_arrangement_audio_clip", "arrangement",
        required=("track_index", "file_path", "start_time"),
        result="{start_time, end_time, length, name, file_path}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 with an absolute file path on an audio track. The 2026-04-12 arrangement residual pass confirmed mutate application but did not yet confirm a clean clip-state undo/redo round-trip for this mutation in the disposable-track validator flow.",
        description=(
            "Place an audio clip on an audio track at start_time (beats). file_path must be an absolute path "
            "to an existing file. Returns {start_time, end_time, length, name, file_path}."
        ),
    ),
    _spec(
        "delete_arrangement_clip", "arrangement",
        required=("track_index",), optional=("clip_index", "start_time"),
        result="{ok}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09. Requires exactly one selector: clip_index or start_time.",
        description=(
            "Delete one Arrangement clip on the given track. Pass exactly one selector: clip_index "
            "(0-based index in arrangement_clips) or start_time (the existing clip's start in beats). "
            "Passing zero or both raises a stable ValueError. Returns {ok: True}."
        ),
    ),
    _spec(
        "resize_arrangement_clip", "arrangement",
        required=("track_index", "length"), optional=("clip_index", "start_time"),
        result="{start_time, end_time, length}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 for MIDI arrangement clips. Requires length > 0 and exactly one selector. The 2026-04-12 arrangement residual pass confirmed mutate application but did not yet confirm a clean clip-state undo/redo round-trip for this mutation in the disposable-track validator flow.",
        description=(
            "Set an Arrangement clip's length in beats. length must be > 0. "
            "Pass exactly one selector: clip_index or start_time. Returns {start_time, end_time, length}."
        ),
    ),
    _spec(
        "move_arrangement_clip", "arrangement",
        required=("track_index", "new_start_time"), optional=("clip_index", "start_time"),
        result="{start_time, end_time, length, notes_restored}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 for MIDI arrangement clips only. Requires exactly one selector. Audio clip move remains intentionally unsupported. The 2026-04-12 arrangement residual pass confirmed MIDI mutate application but did not yet confirm a clean clip-state undo/redo round-trip for this mutation in the disposable-track validator flow.",
        description=(
            "Move a MIDI Arrangement clip to new_start_time (beats). MIDI-only by design — audio clips raise a stable error. "
            "Pass exactly one selector: clip_index or start_time. Returns {start_time, end_time, length, notes_restored}."
        ),
    ),
    _spec(
        "add_notes_to_arrangement_clip", "arrangement",
        required=("track_index", "notes"), optional=("clip_index", "start_time"),
        result="{added}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 with note round-trip verification.",
        description=(
            "Append MIDI notes to an Arrangement MIDI clip without removing existing notes. "
            "Each note: {pitch (0..127), start_time (clip-relative beats), duration (beats > 0), velocity (1..127), mute (bool)}. "
            "Pass exactly one selector: clip_index or start_time. Returns {added: <count>}."
        ),
    ),
    _spec(
        "get_arrangement_clip_notes", "arrangement",
        required=("track_index",), optional=("clip_index", "start_time"),
        result="{notes[], count}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 with note round-trip verification.",
        description=(
            "Read all MIDI notes from an Arrangement MIDI clip. "
            "Pass exactly one selector: clip_index or start_time. "
            "Returns {notes: [{pitch, start_time, duration, velocity, mute}], count}."
        ),
    ),
    _spec(
        "duplicate_to_arrangement", "arrangement",
        required=("track_index", "slot_index"), optional=("start_time",),
        result="{ok, start_time, source_track_index, source_slot_index}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 with session-to-arrangement MIDI note round-trip verification. The 2026-04-12 arrangement residual pass confirmed mutate application but did not yet confirm a clean clip-state undo/redo round-trip for this mutation in the disposable-track validator flow.",
        description=(
            "Duplicate a Session clip to the Arrangement on the same track. "
            "start_time (beats) is optional; defaults to a Live-side anchor. "
            "Returns {ok, start_time, source_track_index, source_slot_index}."
        ),
    ),

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

    _spec(
        "get_track_devices", "device",
        required=("track_index",),
        result="{track_index, devices[]}",
        stability="confirmed", exposed=True,
        notes=DEVICE_INDEX_NOTES,
        description=(
            "List a track's top-level devices in order. "
            "Returns {track_index, devices: [{device_index, name, class_name, ...}]}. "
            "On the validated Python Remote Script surface, track.devices excludes the mixer device."
        ),
    ),
    _spec(
        "get_device_parameters", "device",
        required=("track_index", "device_index"),
        result="device parameter details",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 for top-level native-device parameter inspection on a disposable MIDI track. {}".format(DEVICE_INDEX_NOTES),
        description=(
            "Inspect a top-level device's automatable parameters. "
            "Returns {device_name, parameters: [{index, name, value, display_value, min, max}]}. "
            "For nested devices inside racks use get_device_parameters_at_path."
        ),
    ),
    _spec("set_device_parameter", "device", required=("track_index", "device_index", "parameter_index", "value"), result="{parameter_index, name, value, display_value}", write=True, stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 for writable top-level native-device parameters on a disposable MIDI track."),
    _spec(
        "set_device_parameter_by_name", "device",
        required=("track_index", "device_index", "name", "value"),
        result="{name, value, display_value}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 for writable top-level native-device parameters by name on a disposable MIDI track.",
        description=(
            "Set a top-level device parameter by its Live name. "
            "Validated EQ Eight shorthand aliases ('Gain A', 'Frequency A', 'Q A') and device aliases ('Eq8') are normalized. "
            "Returns {name, value, display_value} after Live's clamp/quantize."
        ),
    ),
    _spec(
        "get_device_parameter_by_name", "device",
        required=("track_index", "device_index", "name"),
        result="single parameter details",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 against the same native-device parameter targets used for write/readback.",
        description=(
            "Read a single top-level device parameter by Live name. "
            "Returns {index, name, value, display_value, min, max}. Same name normalization as the by-name setter."
        ),
    ),
    _spec(
        "get_device_parameters_at_path", "device",
        required=("track_index", "device_path"),
        result="nested device parameter details",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 on nested built-in devices inside system-owned rack trees. Uses track-relative LOM-style device paths.",
        description=(
            "Inspect a nested device's parameters via a track-relative LOM-style path "
            "(e.g. 'devices 0 chains 1 devices 2'). "
            "Returns {device_path, device_name, parameters: [...]}."
        ),
    ),
    _spec(
        "set_device_parameter_at_path", "device",
        required=("track_index", "device_path", "parameter_index", "value"),
        result="{device_path, parameter_index, name, value}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for nested built-in device tuning inside system-owned rack trees. Uses track-relative LOM-style device paths.",
        description=(
            "Set a nested device parameter by index. device_path is a track-relative LOM-style path. "
            "parameter_index is 0-based. Returns {device_path, parameter_index, name, value} after Live's clamp/quantize."
        ),
    ),
    _spec(
        "set_device_parameter_by_name_at_path", "device",
        required=("track_index", "device_path", "name", "value"),
        result="{device_path, parameter_index, name, value}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for nested built-in device tuning inside system-owned rack trees. Uses track-relative LOM-style device paths and resolves validated EQ Eight shorthand aliases.",
        description=(
            "Set a nested device parameter by Live name. device_path is a track-relative LOM-style path. "
            "Validated EQ Eight shorthand aliases ('Gain A', 'Frequency A', 'Q A') are resolved before lookup. "
            "Returns {device_path, parameter_index, name, value}."
        ),
    ),
    _spec("toggle_device", "device", required=("track_index", "device_index"), result="{is_active, enabled, parameter_name, mode, stability}", write=True, stability="confirmed", notes=DEVICE_ACTIVATOR_HELPER_NOTE),
    _spec("set_device_enabled", "device", required=("track_index", "device_index", "enabled"), result="{is_active, enabled, parameter_name, mode, stability}", write=True, stability="confirmed", notes=DEVICE_ACTIVATOR_HELPER_NOTE),
    _spec("delete_device", "device", required=("track_index", "device_index"), result="{ok, deleted_index}", write=True, stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 for top-level native-device deletion on a disposable MIDI track. {}".format(DEVICE_INDEX_NOTES)),
    _spec("move_device", "device", required=("track_index", "device_index", "new_index"), result="{ok, new_index, requested_index, stability}", write=True, stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 for same-track reordering of top-level native audio effects on a disposable MIDI track. Uses Song.move_device(device, target, target position) on the validated Python surface. {}".format(DEVICE_INDEX_NOTES)),
    _spec("show_plugin_window", "device", required=("track_index", "device_index"), result="{ok, device_name, mode, collapsed, stability}", write=True, stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 only for device-view expansion via Device.View.is_collapsed. This is not confirmed plugin editor window control."),
    _spec("hide_plugin_window", "device", required=("track_index", "device_index"), result="{ok, device_name, mode, collapsed, stability}", write=True, stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 only for device-view collapse via Device.View.is_collapsed. This is not confirmed plugin editor window control."),
    _spec(
        "load_instrument_or_effect", "device",
        required=("track_index",), optional=("device_name", "native_device_name", "target_index", "uri"),
        result="{ok, mode, device_count_before, device_count_after, ...}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 for built-in native instrument names and discovered built-in instrument, sounds preset, MIDI-effect, and audio-effect URIs, then revalidated on 2026-04-11 for top-level native device insertion metadata and on 2026-04-12 for the current third-party discovery limitation. Requires exactly one source. Native device_name/native_device_name insertion relies on Track.insert_device and is therefore limited to native Live devices. Third-party plugin URI loading is not currently discoverable through the validated normalized browser roots, so the confirmed URI path remains built-in content only.",
        description=(
            "Load a device or preset onto a track. Pass exactly one of device_name, native_device_name, or uri "
            "(zero or multiple raises a stable ValueError). target_index is a native-only insertion index used "
            "with native_device_name (Track.insert_device) and must be >= 0. Confirmed for built-in Live content; "
            "third-party plugin URI loading is not currently discoverable. "
            "Returns {ok, mode, device_count_before, device_count_after, ...}."
        ),
    ),
    _spec("get_device_class_name", "device", required=("track_index", "device_index"), result="{class_name, name}", stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 for top-level native devices on a disposable MIDI track."),
    _spec("select_device", "device", required=("track_index", "device_index"), result="{ok, device_name}", write=True, stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 against top-level native devices on a selected disposable MIDI track."),
    _spec("get_selected_device", "device", result="{selected, track_index, device_index, name, class_name}", stability="confirmed", notes="Validated in Ableton Live 12.3.7 locally on 2026-04-11 using Song.View.selected_track plus Track.View.selected_device on a disposable MIDI track."),

    _spec(
        "create_rack", "rack",
        required=("track_index", "rack_type", "name"), optional=("target_path",),
        result="{rack_id, rack_path, device_index, name, rack_type}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for native Instrument Rack and Audio Effect Rack creation on disposable tracks and nested chain targets. Registers system-owned racks in the project Memory Bank.",
        description=(
            "Create a system-owned native rack on a track. rack_type is 'instrument' or 'audio_effect'. "
            "target_path optionally inserts the rack into an existing chain (track-relative LOM-style path). "
            "Returns {rack_id, rack_path, device_index, name, rack_type}; the new rack is registered in the project Memory Bank."
        ),
    ),
    _spec(
        "insert_rack_chain", "rack",
        required=("track_index", "rack_path", "name"), optional=("index",),
        result="{rack_path, chain_index, chain_path, name}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for system-owned Instrument Rack and Audio Effect Rack chains. Uses RackDevice.insert_chain() with track-relative LOM-style rack paths.",
        description=(
            "Add a chain to a system-owned rack via RackDevice.insert_chain(). rack_path is a track-relative "
            "LOM-style path (e.g. 'devices 0'). index is an optional 0-based insert position. "
            "Returns {rack_path, chain_index, chain_path, name}."
        ),
    ),
    _spec(
        "insert_device_in_chain", "rack",
        required=("track_index", "chain_path", "native_device_name"), optional=("device_name", "target_index"),
        result="{chain_path, device_path, name, class_name}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for built-in Live device insertion inside system-owned rack chains. Uses Chain.insert_device() and normalizes validated native-device aliases such as Eq8 -> EQ Eight.",
        description=(
            "Insert a built-in Live device into a system-owned rack chain via Chain.insert_device(). "
            "chain_path is a track-relative LOM-style path. native_device_name is normalized for validated aliases "
            "('Eq8' -> 'EQ Eight'). target_index is an optional 0-based insert position. Native devices only. "
            "Returns {chain_path, device_path, name, class_name}."
        ),
    ),
    _spec(
        "get_rack_chains", "rack",
        required=("track_index", "device_index"),
        result="{rack_name, chains[]}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 and revalidated on 2026-04-10 against populated system-owned Instrument Rack and Audio Effect Rack chains. Chain lookup is bounds-checked.",
        description=(
            "List a rack device's chains. device_index addresses the rack on the track. "
            "Returns {rack_name, chains: [{chain_index, name, device_count, mute, solo, volume}]}."
        ),
    ),
    _spec(
        "get_rack_macros", "rack",
        required=("track_index", "device_index"),
        result="{rack_name, macros[]}",
        stability="confirmed", exposed=True,
        notes="{} Returns stable macro indices for read/write use. {}".format(RACK_MACRO_NOTE, USER_RACK_SEMANTICS_NOTE),
        description=(
            "Read a rack's macro values. Returns {rack_name, macros: [{macro_index, name, value, min, max}]}. "
            "Returns currently exposed macros only — macro-to-parameter/macro-to-macro authoring is not exposed by the LOM."
        ),
    ),
    _spec(
        "set_rack_macro", "rack",
        required=("track_index", "device_index", "macro_index", "value"),
        result="{name, value}",
        write=True, stability="confirmed", exposed=True,
        notes="{} Macro writes clamp to the parameter range.".format(RACK_MACRO_NOTE),
        description=(
            "Write a rack macro value (already-exposed macros only). value is clamped to the macro's documented range. "
            "Returns {name, value}."
        ),
    ),
    _spec(
        "get_rack_structure", "rack",
        required=("track_index", "rack_path"),
        result="{track_index, rack_path, rack}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for recursive rack-tree serialization, then rechecked on 2026-04-12 during the imported-rack comparison against browser-loaded preset '808 Selector Rack.adg'. Recursively serializes chains, return_chains, nested devices, macros, and track-relative LOM-style paths. {}".format(USER_RACK_SEMANTICS_NOTE),
        description=(
            "Recursively serialize a rack: chains, return_chains, nested devices, macros, and track-relative LOM-style paths. "
            "rack_path is a track-relative LOM-style path. "
            "For imported/user-authored racks, semantic metadata is enriched only after refresh_rack_memory_entry."
        ),
    ),
    _spec(
        "get_chain_devices", "rack",
        required=("track_index", "device_index", "chain_index"),
        result="{chain_name, devices[]}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 and revalidated on 2026-04-10 on populated system-owned rack chains. Chain lookup is bounds-checked.",
        description=(
            "List the devices inside one rack chain. chain_index is bounds-checked. "
            "Returns {chain_name, devices: [{device_index, name, class_name, ...}]}."
        ),
    ),
    _spec(
        "set_chain_mute", "rack",
        required=("track_index", "device_index", "chain_index", "mute"),
        result="{mute}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 and revalidated on 2026-04-10 on populated system-owned rack chains. Chain lookup is bounds-checked.",
        description="Mute/unmute a rack chain. chain_index is bounds-checked. Returns {mute}.",
    ),
    _spec(
        "set_chain_solo", "rack",
        required=("track_index", "device_index", "chain_index", "solo"),
        result="{solo}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 and revalidated on 2026-04-10 on populated system-owned rack chains. Chain lookup is bounds-checked.",
        description="Solo/unsolo a rack chain. chain_index is bounds-checked. Returns {solo}.",
    ),
    _spec(
        "set_chain_volume", "rack",
        required=("track_index", "device_index", "chain_index", "volume"),
        result="{volume}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 and revalidated on 2026-04-10 on populated system-owned rack chains. Chain volume writes clamp to the supported range.",
        description=(
            "Set a rack chain's volume in normalized units (0.0..1.0; clamped). "
            "chain_index is bounds-checked. Returns {volume}."
        ),
    ),
    _spec(
        "apply_rack_blueprint", "rack",
        required=("blueprint",),
        result="{rack_id, rack_path, created_racks, created_chains, created_devices, structure}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 for deterministic system-owned rack generation and nested tuning, then rechecked on 2026-04-11 for the stable unsupported macro-authoring error path. The LOM audit found no documented native macro-to-parameter or macro-to-macro authoring API, so macro-mapping directives remain intentionally unsupported.",
        description=(
            "Build a system-owned rack tree from a declarative blueprint and tune nested parameters. "
            "macro_mappings and macro_to_macro_mappings are intentionally rejected with a stable error (no documented LOM API). "
            "Returns {rack_id, rack_path, created_racks, created_chains, created_devices, structure}."
        ),
    ),
    _spec(
        "get_drum_rack_pads", "rack",
        required=("track_index", "device_index"),
        result="{drum_pads[], count}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09. Top-level Drum Racks expose drum_pads. Inner Drum Racks return zero pads.",
        description=(
            "List a top-level Drum Rack's pads. "
            "Returns {drum_pads: [{note, name, mute, solo, has_chain}], count}. "
            "Inner (nested) Drum Racks return an empty list."
        ),
    ),
    _spec(
        "set_drum_rack_pad_note", "rack",
        required=("track_index", "device_index", "note", "new_note"),
        result="{note}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09. Uses DrumChain.in_note because DrumPad.note is read-only in the LOM. Requires Live 12.3+ and remap readback is validated on the destination pad.",
        description=(
            "Remap a Drum Rack pad to a new MIDI note via DrumChain.in_note. note is the source pad's current MIDI note; "
            "new_note is the target (0..127). Requires Live 12.3+. Returns {note} (the new note)."
        ),
    ),
    _spec(
        "set_drum_rack_pad_mute", "rack",
        required=("track_index", "device_index", "note", "mute"),
        result="{note, mute}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09. Pad lookup is note-based on top-level Drum Racks and falls back to chain mute when pad-level mute does not stick.",
        description=(
            "Mute/unmute a Drum Rack pad by its current MIDI note. "
            "Falls back to chain-level mute when pad-level mute does not stick. Returns {note, mute}."
        ),
    ),
    _spec(
        "set_drum_rack_pad_solo", "rack",
        required=("track_index", "device_index", "note", "solo"),
        result="{note, solo}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09. Pad lookup is note-based on top-level Drum Racks.",
        description="Solo/unsolo a Drum Rack pad by its current MIDI note. Returns {note, solo}.",
    ),

    _spec(
        "get_browser_tree", "browser",
        optional=("category_type",), result="browser tree snapshot",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 across the normalized top-level browser categories.",
        description=(
            "Snapshot of the top-level browser tree under the chosen normalized root. "
            "Roots: 'all', 'instruments', 'audio_effects', 'midi_effects', 'drums', 'sounds', 'samples', 'packs', 'user_library'."
        ),
    ),
    _spec(
        "get_browser_items_at_path", "browser",
        optional=("path",), result="{items[], path}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 for top-level browser navigation, then extended on 2026-04-12 to confirm the normalized built-in roots include sounds presets in addition to instruments, drums, MIDI effects, and audio effects.",
        description=(
            "List browser items at a slash-separated path under one of the normalized roots "
            "(e.g. 'instruments/Operator'). Empty path returns the root listing. Returns {items: [...], path}."
        ),
    ),
    _spec(
        "search_browser", "browser",
        optional=("query", "category"), result="{query, results[], count}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09. Requires a non-empty query. Category-scoped searches are the confirmed path; broad category='all' plugin discovery can time out on the validated build.",
        description=(
            "Substring search across browser content (case-insensitive). Requires non-empty query. "
            "category scopes the search to one normalized root; category='all' may time out on large libraries — "
            "prefer category-scoped searches. Returns {query, results: [{name, uri, ...}], count}."
        ),
    ),
    _spec(
        "load_drum_kit", "browser",
        required=("track_index", "rack_uri"),
        result="{ok, loaded, device_count_before, device_count_after, ...}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12 locally on 2026-04-09 for discovered built-in drum-kit preset URIs. Generic Drum Rack device entries remain rejected.",
        description=(
            "Load a Drum Rack preset onto a track via its browser URI (discoverable via search_browser). "
            "Generic 'Drum Rack' device entries are rejected — pass a preset URI. "
            "Returns {ok, loaded, device_count_before, device_count_after, ...}."
        ),
    ),

    _spec(
        "get_take_lanes", "take_lane",
        required=("track_index",),
        result="{take_lanes[], available}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3.7 locally on 2026-04-12 on a disposable MIDI track. Returns available=true on the validated build and stable lane counts/clip counts.",
        description=(
            "List a track's take lanes. Returns {take_lanes: [{lane_index, name, clip_count}], available}. "
            "available=False indicates the running Live build does not expose take_lanes."
        ),
    ),
    _spec(
        "create_take_lane", "take_lane",
        required=("track_index",),
        result="{ok, name, stability}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3.7 locally on 2026-04-12 using documented Track.create_take_lane() on a disposable MIDI track.",
        description="Create a new take lane on the track via Track.create_take_lane(). Returns {ok, name, stability}.",
    ),
    _spec(
        "set_take_lane_name", "take_lane",
        required=("track_index", "lane_index", "name"),
        result="{name}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3.7 locally on 2026-04-12 for TakeLane.name mutation with stable lane index bounds checking.",
        description=(
            "Rename a take lane. lane_index is 0-based against the track's take_lanes. "
            "Out-of-range indices raise a stable ValueError. Returns {name}."
        ),
    ),
    _spec(
        "create_midi_clip_in_lane", "take_lane",
        required=("track_index", "lane_index"), optional=("start_time", "length"),
        result="{start_time, end_time, length, name}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3.7 locally on 2026-04-12 using documented TakeLane.create_midi_clip(start_time, length). Requires a MIDI track, start_time >= 0, and length > 0.",
        description=(
            "Create an empty MIDI clip in a take lane via TakeLane.create_midi_clip(start_time, length). "
            "MIDI tracks only. start_time defaults to 0; length must be > 0. "
            "Returns {start_time, end_time, length, name}."
        ),
    ),
    _spec(
        "get_clips_in_take_lane", "take_lane",
        required=("track_index", "lane_index"),
        result="{clips[]}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3.7 locally on 2026-04-12 for arrangement-clip readback on a disposable take lane after clip creation.",
        description=(
            "List Arrangement clips in a take lane. Returns {clips: [{start_time, end_time, length, name, ...}]}."
        ),
    ),
    _spec("delete_take_lane", "take_lane", required=("track_index", "lane_index"), result="{ok}", write=True, stability="partial", notes="Not part of the confirmed LOM-backed core in this pass. The validated Python Remote Script surface on 2026-04-12 did not expose Track.delete_take_lane, so this command now raises a stable ValueError when that helper is unavailable."),

    _spec("get_current_view", "view", result="{view}", stability="likely-complete"),
    _spec("focus_view", "view", required=("view",), result="{view|error}", write=True, stability="likely-complete"),
    _spec("show_arrangement_view", "view", result="{view|error}", write=True, stability="likely-complete"),
    _spec("show_session_view", "view", result="{view|error}", write=True, stability="likely-complete"),
    _spec("show_detail_view", "view", optional=("detail",), result="{view|error}", write=True, stability="likely-complete"),

    _spec(
        "read_memory_bank", "memory_bank",
        required=("file_name",), result="markdown string",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 against the saved-set project-root .ableton-mcp/memory directory.",
        description=(
            "Read a Memory Bank markdown file from the current Live Set's '.ableton-mcp/memory/' directory. "
            "Returns the file's contents as a string. Requires a saved Live Set (see get_session_path)."
        ),
    ),
    _spec(
        "write_memory_bank", "memory_bank",
        required=("file_name", "content"), result="confirmation string",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 against the saved-set project-root .ableton-mcp/memory directory. Requires a saved Live Set.",
        description=(
            "Overwrite a Memory Bank file with new markdown content. "
            "Resolved relative to the current Live Set's '.ableton-mcp/memory/' directory. "
            "Requires a saved Live Set. Returns a confirmation string."
        ),
    ),
    _spec(
        "append_rack_entry", "memory_bank",
        required=("rack_data",), result="confirmation string",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 by appending a rack-note record into the project Memory Bank.",
        description=(
            "Append a rack-note record (markdown blob) to the project Memory Bank's racks.md inventory. "
            "Returns a confirmation string."
        ),
    ),
    _spec(
        "get_system_owned_racks", "memory_bank",
        result="{count, racks[]}",
        stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 and re-read on 2026-04-12 after importing browser-loaded preset '808 Selector Rack.adg' with refresh_rack_memory_entry. Returns the parsed system-owned rack inventory tracked in racks.md, including explicitly imported rack entries.",
        description=(
            "Read the parsed system-owned rack inventory from the Memory Bank's racks.md "
            "(includes both racks created via create_rack and explicitly imported racks). "
            "Returns {count, racks: [{rack_id, name, track_index, rack_path, ...}]}."
        ),
    ),
    _spec(
        "refresh_rack_memory_entry", "memory_bank",
        required=("track_index", "rack_path"),
        result="{rack_id, track_index, rack_path}",
        write=True, stability="confirmed", exposed=True,
        notes="Validated in Ableton Live 12.3+ locally on 2026-04-10 by re-snapshotting live rack structure into the project Memory Bank using a track-relative LOM-style rack path, then revalidated on 2026-04-12 by importing browser-loaded preset '808 Selector Rack.adg'. This is the current repo-level path for upgrading imported/user-authored racks from direct live inspection into authoritative Memory Bank metadata.",
        description=(
            "Re-snapshot a live rack's structure into the Memory Bank. "
            "rack_path is a track-relative LOM-style path. "
            "This is the supported path for promoting imported/user-authored racks to authoritative Memory Bank metadata. "
            "Returns {rack_id, track_index, rack_path}."
        ),
    ),
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
