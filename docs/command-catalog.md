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
- regular track mutation and selection
- return-track inspection, return mixer mutation, and send control in a set with existing return tracks
- Session View clip and note round trips
- Arrangement View clip creation, edit, delete, import, and duplication
- browser discovery and validated built-in loading
- built-in MIDI-effect and audio-effect loading
- top-level device inspection, selection, parameter read/write, activator-helper enable/disable, same-track reordering, deletion, and device-view collapse/expand on native devices
- positive `fold_track` / `unfold_track` round-trip on a real foldable group track
- system-owned Instrument Rack and Audio Effect Rack creation, chain insertion, nested device insertion, and recursive structure readback
- exposed rack macro value read/write on a validated system-owned rack plus stable rejection of native macro-authoring directives
- direct live-vs-Memory Bank comparison on an imported non-system-owned rack target (`808 Selector Rack.adg`) before and after `refresh_rack_memory_entry`
- nested rack-device parameter read/write via track-relative LOM-style paths
- project-root Memory Bank persistence for system-owned and imported racks in saved Live Sets
- rack, chain, and drum-rack inspection/mutation

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
| `get_session_path` | Return session/project path | confirmed |
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
- `get_session_path` is now directly validated against a saved `.als` and is the persistence anchor for the project Memory Bank workflow.
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
| `set_track_name` | Rename track | confirmed |
| `set_track_color` | Set track color | confirmed |
| `set_track_volume` | Set volume | confirmed |
| `set_track_pan` | Set pan | confirmed |
| `set_track_mute` | Set mute | confirmed |
| `set_track_solo` | Set solo | confirmed |
| `set_track_arm` | Set arm | confirmed |
| `set_track_monitoring` | Set monitoring mode | plausible |
| `freeze_track` | Freeze track | needs audit |
| `flatten_track` | Flatten track | needs audit |
| `fold_track` | Fold group/foldable track | confirmed |
| `unfold_track` | Unfold group/foldable track | confirmed |
| `unarm_all` | Unarm all armable tracks | plausible |
| `unsolo_all` | Unsolo all tracks | plausible |
| `unmute_all` | Unmute all tracks | plausible |
| `set_track_delay` | Set track delay | needs audit |
| `set_send_level` | Set send level | confirmed |
| `get_return_tracks` | List return tracks | confirmed |
| `get_return_track_info` | Inspect one return track | confirmed |
| `set_return_volume` | Set return volume | confirmed |
| `set_return_pan` | Set return pan | confirmed |
| `set_track_input_routing` | Set input routing type | needs audit |
| `set_track_output_routing` | Set output routing type | needs audit |
| `get_track_input_routing` | Read available/current input routing | plausible |
| `get_track_output_routing` | Read available/current output routing | plausible |
| `select_track` | Select normal, return, or master track in Live view | confirmed |
| `get_selected_track` | Return the selected normal, return, or master track | confirmed |

### Notes

- `set_track_color` is validated against the applied/read-back color because the LOM maps requested RGB values to the nearest track color chooser value.
- `set_track_solo` is confirmed as a target-state write only; the LOM does not guarantee exclusive-solo side effects.
- `set_track_arm` now raises a stable error when the target cannot be armed.
- `select_track` requires exactly one of `track_index`, `return_index`, or `master=True`.
- `get_selected_track` now returns `selection_type`, `name`, `index`, `track_index`, and `return_index` so callers can distinguish regular-track, return-track, and master-track selections.
- `fold_track` and `unfold_track` are confirmed on the current Live 12.3.7 set using foldable group track `5-Group`, with the original `fold_state` restored during cleanup.
- during that run, the selection stayed on the pre-existing return-track target and the current Python Remote Script surface did not expose child-track `is_visible` readback, so confirmation rests on `fold_state` round-trip plus grouped-child discovery rather than direct visibility assertions.

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
| `get_track_devices` | List devices on track | confirmed |
| `get_device_parameters` | List parameters for a device | confirmed |
| `set_device_parameter` | Set parameter by index | confirmed |
| `set_device_parameter_by_name` | Set parameter by name | confirmed |
| `get_device_parameter_by_name` | Read parameter by name | confirmed |
| `get_device_parameters_at_path` | List parameters for a nested device in a rack tree | confirmed |
| `set_device_parameter_at_path` | Set nested device parameter by index using a rack path | confirmed |
| `set_device_parameter_by_name_at_path` | Set nested device parameter by name using a rack path | confirmed |
| `toggle_device` | Activator-parameter toggle helper | confirmed |
| `set_device_enabled` | Activator-parameter enable helper | confirmed |
| `delete_device` | Delete device from track | confirmed |
| `move_device` | Reorder device on track | confirmed |
| `show_plugin_window` | Expand device in the device chain | confirmed |
| `hide_plugin_window` | Collapse device in the device chain | confirmed |
| `load_instrument_or_effect` | Load browser item onto track | confirmed |
| `get_device_class_name` | Return device class | confirmed |
| `select_device` | Select device | confirmed |
| `get_selected_device` | Return selected device | confirmed |

### Notes

- top-level device inspection and mutation were revalidated in Ableton Live 12.3.7 on 2026-04-11 on a disposable MIDI track loaded with native devices.
- on the validated Python Remote Script surface, `get_track_devices` on a fresh disposable track returned no mixer device even though the LOM docs say `Track.devices` includes it. Top-level `device_index` now reflects the observed `track.devices` ordering for this build.
- third-party plugin parameters may still require manual Configure in Live before they appear.
- `toggle_device` and `set_device_enabled` are confirmed only for the narrowed activator-parameter helper contract. The LOM exposes `Device.is_active` as read-only, so these commands should not be treated as universal device power setters.
- `move_device` is confirmed for same-track top-level native-device reordering on the validated Live 12.3.7 build and uses the documented `Song.move_device(...)` API on the Python surface.
- `get_selected_device` should be interpreted as `song.view.selected_track` plus `selected_track.view.selected_device`, not an undocumented song-level selected-device child.
- `show_plugin_window` and `hide_plugin_window` are confirmed only for device-view collapse/expand via `Device.View.is_collapsed`, not plugin editor control.
- `load_instrument_or_effect` is validated in Live for native built-in device insertion plus discovered built-in instrument, MIDI-effect, and audio-effect URIs, and native insertion metadata was revalidated on 2026-04-11 during the device audit pass.
- native `device_name` / `native_device_name` insertion is limited by `Track.insert_device`, which the LOM documents as native Live devices only. Max for Live and third-party plugin insertion remain backlog work.
- third-party plugin URIs remain backlog work.
- `target_index` only applies to native insertion, not browser URI loading.
- the path-based device commands use track-relative LOM-style paths such as `devices 0 chains 1 devices 2`.
- EQ Eight shorthand names such as `Gain A`, `Frequency A`, and `Q A` are normalized to the validated Live parameter names during nested rack tuning.

## 9. Racks and chains

| Command | Purpose | Status |
|---|---|---|
| `create_rack` | Create a native Instrument Rack or Audio Effect Rack | confirmed |
| `insert_rack_chain` | Insert a chain into a target rack | confirmed |
| `insert_device_in_chain` | Insert a built-in Live device into a rack chain | confirmed |
| `get_rack_chains` | List rack chains and chain state | confirmed |
| `get_rack_macros` | List rack macros | confirmed |
| `set_rack_macro` | Set rack macro value | confirmed |
| `get_rack_structure` | Recursively inspect a rack tree with nested paths | confirmed |
| `get_chain_devices` | List devices in a chain | confirmed |
| `set_chain_mute` | Mute chain | confirmed |
| `set_chain_solo` | Solo chain | confirmed |
| `set_chain_volume` | Set chain volume | confirmed |
| `apply_rack_blueprint` | Create and tune a deterministic system-owned rack tree | confirmed |

### Notes

- these commands are now promoted as first-class MCP tools and have repo-level contract coverage.
- `get_rack_macros` returns stable macro indices intended for `set_rack_macro`.
- system-owned Instrument Rack and Audio Effect Rack authoring is now directly validated in Live 12.3+ using native rack insertion plus chain/device creation.
- `get_rack_structure` returns track-relative LOM-style paths for racks, chains, devices, and return chains so later tuning calls can reuse them directly.
- `apply_rack_blueprint` supports deterministic built-in device graphs and rejects native macro-mapping directives with a stable unsupported error.
- native macro value read/write is confirmed only for already-exposed rack macros.
- the LOM-backed contract for this repo now treats native macro-to-parameter authoring and macro-to-macro authoring as explicitly unsupported, not merely unimplemented.
- imported/user-authored racks are validated for direct live structure and already-exposed macro inspection before import, but repo-level semantic metadata is only considered authoritative after `refresh_rack_memory_entry`.

## 10. Drum rack

| Command | Purpose | Status |
|---|---|---|
| `get_drum_rack_pads` | List drum rack pads and chain info | confirmed |
| `set_drum_rack_pad_note` | Remap pad note | confirmed |
| `set_drum_rack_pad_mute` | Mute pad | confirmed |
| `set_drum_rack_pad_solo` | Solo pad | confirmed |

### Notes

- these commands are now promoted as first-class MCP tools and have repo-level contract coverage.
- top-level Drum Racks expose `drum_pads`; inner Drum Racks return zero pad entries.
- `DrumPad.note` is treated as read-only. `set_drum_rack_pad_note` now remaps via `DrumChain.in_note`, which targets Live 12.3+ and requires a top-level pad with at least one chain.
- `get_drum_rack_pads` includes chain-backed note metadata so Live-side validators can read back remaps on the destination pad.
- `set_drum_rack_pad_mute` now reflects effective mute state and falls back to chain mute when pad-level mute does not stick in Live.

## 11. Memory Bank

| Command | Purpose | Status |
|---|---|---|
| `read_memory_bank` | Read a project Memory Bank file | confirmed |
| `write_memory_bank` | Write a project Memory Bank file | confirmed |
| `append_rack_entry` | Append an additional rack note or record | confirmed |
| `get_system_owned_racks` | List tracked system-owned racks for the current project | confirmed |
| `refresh_rack_memory_entry` | Re-snapshot a tracked rack into the Memory Bank | confirmed |

### Notes

- the Memory Bank lives under `.ableton-mcp/memory` at the saved Ableton project root.
- Memory Bank writes require a saved Live Set because the project root is derived from `Song.file_path`.
- system-owned rack entries store rack identity, blueprint provenance, recursive structure, current macro snapshot, and explicit notes when native macro mappings are unsupported or unknown.
- `refresh_rack_memory_entry` was revalidated on `2026-04-12` against imported rack preset `808 Selector Rack.adg` and remains the current path for importing a non-system-owned rack into authoritative Memory Bank metadata.

## 12. Browser

| Command | Purpose | Status |
|---|---|---|
| `get_browser_tree` | List browser categories/tree | confirmed |
| `get_browser_items_at_path` | Navigate browser by path | confirmed |
| `search_browser` | Search browser subtree | confirmed |
| `load_drum_kit` | Load drum kit by URI/path | confirmed |

### Notes

- browser discovery is directly validated in Live 12 across the normalized top-level categories.
- `search_browser` rejects blank queries instead of crawling the whole browser.
- `load_drum_kit` is validated for discovered built-in drum-kit preset URIs and rejects the generic `Drum Rack` device entry.
- third-party plugin URIs and broader effect-loading behavior remain backlog work.

## 13. Take lanes (Live 12+)

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

## 14. View / selection / UI focus

| Command | Purpose | Status |
|---|---|---|
| `get_current_view` | Return current focused document view | plausible |
| `focus_view` | Focus named view | plausible |
| `show_arrangement_view` | Focus Arranger view | plausible |
| `show_session_view` | Focus Session view | plausible |
| `show_detail_view` | Show detail view variant | plausible |
| `get_arrangement_length` | Read arrangement length | needs audit |
