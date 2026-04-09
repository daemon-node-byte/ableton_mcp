# AbletonMCP_v2 Command Catalog

This is the canonical inventory of commands exposed by the current Remote Script dispatcher.

Use this doc for:

- command names grouped by domain
- quick-read purpose notes
- broad readiness shorthand

Use [mcp_server/command_specs.py](/Users/joshmclain/code/AbletonMCP_v2/mcp_server/command_specs.py) for exact parameter metadata, MCP exposure, and canonical stability labels.

## How to Read This

- `confirmed` means directly validated against a real Ableton Live 12 session
- everything else is still a repo-level estimate and should be treated with appropriate caution
- commands not promoted to first-class MCP tools are still reachable through `ableton_raw_command(...)`

## Validation Snapshot

Direct Live validation currently covers:

- connectivity and session inspection
- Session View clip and note round trips
- Arrangement View clip creation, edit, delete, import, and duplication
- browser discovery and validated built-in loading

For setup and validator commands, use [docs/install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md).

## 1. Health

| Command | Purpose | Status |
|---|---|---|
| `health_check` | Basic connectivity / session sanity check | confirmed |

## 2. Session / transport / song

| Command | Purpose | Status |
|---|---|---|
| `get_session_info` | Return core set/session info | confirmed |
| `get_current_song_time` | Read current arrangement time | confirmed |
| `set_current_song_time` | Set current arrangement time | plausible |
| `set_tempo` | Set project tempo | plausible |
| `set_time_signature` | Set time signature | plausible |
| `start_playback` | Start playback | plausible |
| `stop_playback` | Stop playback | plausible |
| `continue_playback` | Continue playback | plausible |
| `start_recording` | Enable arrangement record mode | plausible |
| `stop_recording` | Disable arrangement record mode | plausible |
| `toggle_session_record` | Toggle session record | plausible |
| `toggle_arrangement_record` | Toggle arrangement record | plausible |
| `set_metronome` | Enable/disable metronome | plausible |
| `tap_tempo` | Trigger tap tempo | plausible |
| `undo` | Undo last action | plausible |
| `redo` | Redo last undone action | plausible |
| `capture_midi` | Trigger Capture MIDI | plausible |
| `re_enable_automation` | Re-enable automation | plausible |
| `set_arrangement_loop` | Set arrangement loop start/length/on-off | plausible |
| `get_cpu_load` | Return CPU-ish metric | needs audit |
| `get_session_path` | Return session/project path | high risk |
| `get_locators` | List locators / cue points | plausible |
| `create_locator` | Create locator / cue | needs audit |
| `delete_locator` | Delete locator / cue | needs audit |
| `jump_to_time` | Jump playback cursor to time | plausible |
| `jump_to_next_cue` | Jump to next cue | plausible |
| `jump_to_prev_cue` | Jump to previous cue | plausible |
| `set_punch_in` | Toggle punch-in | plausible |
| `set_punch_out` | Toggle punch-out | plausible |
| `trigger_back_to_arrangement` | Trigger Back to Arrangement behavior | needs audit |
| `get_back_to_arrangement` | Read Back to Arrangement state | plausible |
| `set_session_automation_record` | Toggle session automation record | plausible |
| `get_session_automation_record` | Read session automation record state | plausible |
| `set_overdub` | Toggle overdub | plausible |
| `stop_all_clips` | Stop all clips | plausible |
| `get_arrangement_length` | Return arrangement length | needs audit |

### Notes

- `get_cpu_load` and `get_session_path` were corrected to use official Live API properties.
- locator creation/deletion may still need closer runtime verification.

## 3. Tracks

| Command | Purpose | Status |
|---|---|---|
| `get_track_info` | Return detailed info for one track | confirmed |
| `get_all_track_names` | List track names | confirmed |
| `create_midi_track` | Create MIDI track | confirmed |
| `create_audio_track` | Create audio track | plausible |
| `create_return_track` | Create return track | plausible |
| `delete_track` | Delete track | confirmed |
| `duplicate_track` | Duplicate track | plausible |
| `set_track_name` | Rename track | plausible |
| `set_track_color` | Set track color | plausible |
| `set_track_volume` | Set volume | plausible |
| `set_track_pan` | Set pan | plausible |
| `set_track_mute` | Set mute | plausible |
| `set_track_solo` | Set solo | plausible |
| `set_track_arm` | Set arm | plausible |
| `set_track_monitoring` | Set monitoring mode | plausible |
| `freeze_track` | Freeze track | needs audit |
| `flatten_track` | Flatten track | needs audit |
| `fold_track` | Fold group/foldable track | plausible |
| `unfold_track` | Unfold group/foldable track | plausible |
| `unarm_all` | Unarm all armable tracks | plausible |
| `unsolo_all` | Unsolo all tracks | plausible |
| `unmute_all` | Unmute all tracks | plausible |
| `set_track_delay` | Set track delay | needs audit |
| `set_send_level` | Set send level | plausible |
| `get_return_tracks` | List return tracks | plausible |
| `get_return_track_info` | Inspect one return track | plausible |
| `set_return_volume` | Set return volume | plausible |
| `set_return_pan` | Set return pan | plausible |
| `set_track_input_routing` | Set input routing type | needs audit |
| `set_track_output_routing` | Set output routing type | needs audit |
| `get_track_input_routing` | Read available/current input routing | plausible |
| `get_track_output_routing` | Read available/current output routing | plausible |
| `select_track` | Select track in Live view | plausible |
| `get_selected_track` | Return selected track | plausible |

## 4. Master / cue / meters

| Command | Purpose | Status |
|---|---|---|
| `get_master_info` | Read master mixer state | plausible |
| `set_master_volume` | Set master volume | plausible |
| `set_master_pan` | Set master pan | plausible |
| `get_master_output_meter` | Read output meter | plausible |
| `get_cue_volume` | Read cue volume | plausible |
| `set_cue_volume` | Set cue volume | plausible |

## 5. Session View clips

| Command | Purpose | Status |
|---|---|---|
| `get_clip_info` | Inspect a session clip | plausible |
| `create_clip` | Create clip in session slot | confirmed |
| `delete_clip` | Delete session clip | confirmed |
| `duplicate_clip` | Duplicate session clip slot | needs audit |
| `set_clip_name` | Rename clip | plausible |
| `set_clip_color` | Set clip color | plausible |
| `fire_clip` | Launch clip | plausible |
| `stop_clip` | Stop clip/slot | plausible |
| `get_clip_notes` | Read MIDI notes | confirmed |
| `add_notes_to_clip` | Add MIDI notes | confirmed |
| `set_clip_notes` | Replace MIDI notes | plausible |
| `remove_notes_from_clip` | Remove MIDI notes in range | plausible |
| `set_clip_loop` | Set looping and loop range | plausible |
| `set_clip_markers` | Set clip markers | plausible |
| `set_clip_gain` | Set audio clip gain | plausible |
| `set_clip_pitch` | Set audio clip coarse/fine pitch | plausible |
| `set_clip_warp_mode` | Set audio clip warp mode | needs audit |
| `quantize_clip` | Quantize MIDI clip | plausible |
| `duplicate_clip_loop` | Duplicate clip loop | plausible |
| `get_clip_automation` | Read clip automation/envelope data | needs audit |
| `set_clip_automation` | Write clip automation/envelope data | high risk |
| `clear_clip_automation` | Clear clip automation/envelope data | needs audit |

## 6. Arrangement View clips

| Command | Purpose | Status |
|---|---|---|
| `get_arrangement_clips` | List arrangement clips for one track | confirmed |
| `get_all_arrangement_clips` | List arrangement clips across tracks | plausible |
| `create_arrangement_midi_clip` | Create MIDI clip in arrangement | confirmed |
| `create_arrangement_audio_clip` | Create audio clip in arrangement | confirmed |
| `delete_arrangement_clip` | Delete arrangement clip | confirmed |
| `resize_arrangement_clip` | Resize arrangement clip | confirmed |
| `move_arrangement_clip` | Move arrangement clip | confirmed |
| `add_notes_to_arrangement_clip` | Add MIDI notes to arrangement clip | confirmed |
| `get_arrangement_clip_notes` | Read notes from arrangement clip | confirmed |
| `duplicate_to_arrangement` | Copy session clip to arrangement | confirmed |

### Notes

- `create_arrangement_audio_clip` is validated with an absolute existing `file_path` on an audio track.
- `delete_arrangement_clip`, `resize_arrangement_clip`, and `move_arrangement_clip` require exactly one selector: `clip_index` or `start_time`.
- `move_arrangement_clip` remains MIDI-only in this pass.
- arrangement undo behavior is still not documented as supported.

## 7. Scenes

| Command | Purpose | Status |
|---|---|---|
| `get_all_scenes` | List scenes | plausible |
| `create_scene` | Create scene | plausible |
| `delete_scene` | Delete scene | plausible |
| `fire_scene` | Launch scene | plausible |
| `stop_scene` | Stop scene / scene-related action | needs audit |
| `set_scene_name` | Rename scene | plausible |
| `set_scene_color` | Set scene color | plausible |
| `duplicate_scene` | Duplicate scene | plausible |
| `select_scene` | Select scene | plausible |
| `get_selected_scene` | Return selected scene | plausible |

## 8. Devices and parameters

| Command | Purpose | Status |
|---|---|---|
| `get_track_devices` | List devices on track | plausible |
| `get_device_parameters` | List parameters for a device | plausible |
| `set_device_parameter` | Set parameter by index | plausible |
| `set_device_parameter_by_name` | Set parameter by name | plausible |
| `get_device_parameter_by_name` | Read parameter by name | plausible |
| `toggle_device` | Toggle device active state | needs audit |
| `set_device_enabled` | Set device enabled state | plausible |
| `delete_device` | Delete device from track | plausible |
| `move_device` | Reorder device on track | plausible |
| `show_plugin_window` | Show/select plugin window | needs audit |
| `hide_plugin_window` | Hide/collapse plugin window | needs audit |
| `load_instrument_or_effect` | Load browser item onto track | likely-complete |
| `get_device_class_name` | Return device class | plausible |
| `select_device` | Select device | plausible |
| `get_selected_device` | Return selected device | plausible |

### Notes

- third-party plugin parameters may still require manual Configure in Live before they appear.
- `show_plugin_window` and `hide_plugin_window` are still best-effort device-view helpers, not proven plugin editor control.
- `load_instrument_or_effect` has a validated native insert path plus a validated built-in browser URI path.
- `target_index` only applies to native insertion, not browser URI loading.

## 9. Racks and chains

| Command | Purpose | Status |
|---|---|---|
| `get_rack_chains` | List rack chains and chain state | plausible |
| `get_rack_macros` | List rack macros | plausible |
| `set_rack_macro` | Set rack macro value | plausible |
| `get_chain_devices` | List devices in a chain | plausible |
| `set_chain_mute` | Mute chain | plausible |
| `set_chain_solo` | Solo chain | plausible |
| `set_chain_volume` | Set chain volume | plausible |

## 10. Drum rack

| Command | Purpose | Status |
|---|---|---|
| `get_drum_rack_pads` | List drum rack pads and chain info | plausible |
| `set_drum_rack_pad_note` | Remap pad note | needs audit |
| `set_drum_rack_pad_mute` | Mute pad | plausible |
| `set_drum_rack_pad_solo` | Solo pad | plausible |

## 11. Browser

| Command | Purpose | Status |
|---|---|---|
| `get_browser_tree` | List browser categories/tree | confirmed |
| `get_browser_items_at_path` | Navigate browser by path | confirmed |
| `search_browser` | Search browser subtree | confirmed |
| `load_drum_kit` | Load drum kit by URI/path | likely-complete |

### Notes

- browser discovery is directly validated in Live 12 across the normalized top-level categories.
- `search_browser` rejects blank queries instead of crawling the whole browser.
- `load_drum_kit` is validated for discovered built-in drum-kit preset URIs and rejects the generic `Drum Rack` device entry.
- third-party plugin URIs and broader effect-loading behavior remain backlog work.

## 12. Take lanes (Live 12+)

| Command | Purpose | Status |
|---|---|---|
| `get_take_lanes` | List take lanes on track | plausible |
| `create_take_lane` | Create take lane | high risk |
| `set_take_lane_name` | Rename take lane | needs audit |
| `create_midi_clip_in_lane` | Create MIDI clip in take lane | high risk |
| `get_clips_in_take_lane` | List clips in take lane | needs audit |
| `delete_take_lane` | Delete take lane | high risk |

### Notes

- the implementation now uses `Track.create_take_lane()` when available.
- this domain should still be treated as experimental until it gets direct runtime coverage.

## 13. View / selection / UI focus

| Command | Purpose | Status |
|---|---|---|
| `get_current_view` | Return current focused document view | plausible |
| `focus_view` | Focus named view | plausible |
| `show_arrangement_view` | Focus Arranger view | plausible |
| `show_session_view` | Focus Session view | plausible |
| `show_detail_view` | Show detail view variant | plausible |
| `get_arrangement_length` | Read arrangement length | needs audit |
