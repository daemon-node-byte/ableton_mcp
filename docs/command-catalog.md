# AbletonMCP_v2 Command Catalog

Date: 2026-04-09
Source: current dispatcher in `AbletonMCP_Remote_Script/__init__.py`
Purpose: canonical command surface for refactoring, MCP tool generation, and implementation audits

Python-side source of truth:
- `mcp_server/command_specs.py`

## Status note

This catalog reflects the **intended** command surface currently exposed by the Remote Script dispatcher.
It does **not** guarantee that every implementation is complete or correct.

Recommended interpretation:
- use this as the public capability map
- preserve it during refactors unless there is a deliberate migration decision
- treat implementation status as provisional unless marked `confirmed` from direct Live validation
- use `mcp_server/command_specs.py` for the current stability label and MCP exposure state

## Conventions

### Execution style
Commands fall into two broad groups:
- **read-style** commands, which generally return data immediately
- **write-style** commands, which are generally wrapped in `_schedule_and_wait(...)` to execute safely on Ableton's main thread

### Canonical stability labels now used in code
- **confirmed**: directly validated against a real Ableton Live 12 session
- **likely-complete**: repo review plus official API docs suggest the implementation is directionally sound
- **partial**: command exists and is useful, but known edge cases or contract issues remain
- **stub**: intentional placeholder or best-effort fallback
- **unverified**: present in the surface but not trusted yet

### Runtime validation snapshot
Validated locally in Ableton Live 12 on 2026-04-09:
- `health_check`
- `get_session_info`
- `get_current_song_time`
- `get_all_track_names`
- `get_track_info`
- `create_midi_track`
- `delete_track`
- `create_clip`
- `delete_clip`
- `get_clip_notes`
- `add_notes_to_clip`
- `get_arrangement_clips`
- `create_arrangement_midi_clip`
- `add_notes_to_arrangement_clip`
- `get_arrangement_clip_notes`

### MCP exposure in this pass
- First-class MCP tools:
  `health_check`, `get_session_info`, `get_current_song_time`, `set_current_song_time`, `set_tempo`, `start_playback`, `stop_playback`, `get_all_track_names`, `get_track_info`, `create_midi_track`, `create_audio_track`, `create_clip`, `get_clip_notes`, `add_notes_to_clip`, `get_arrangement_clips`, `create_arrangement_midi_clip`, `add_notes_to_arrangement_clip`, `get_arrangement_clip_notes`, `get_track_devices`, `get_device_parameters`, `set_device_parameter_by_name`, `get_device_parameter_by_name`
- All other commands are still callable through the development escape hatch tool `ableton_raw_command(...)`.

### Important implementation corrections now reflected in code
- `get_cpu_load` now uses `Application.average_process_usage`
- `get_session_path` now uses `Song.file_path`
- `get_arrangement_length` now uses `Song.song_length` with clip-end fallback
- `create_arrangement_audio_clip` now follows the Live API contract `Track.create_audio_clip(file_path, position)`
- `create_take_lane` now uses `Track.create_take_lane()`
- `create_midi_clip_in_lane` now follows `TakeLane.create_midi_clip(start_time, length)`
- `load_instrument_or_effect` now prefers `Track.insert_device(...)` for native Live devices and keeps URI loading as provisional

---

## 1. Health

| Command | Purpose | Status |
|---|---|---|
| `health_check` | Basic connectivity / session sanity check | confirmed |

---

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
- `get_cpu_load` and `get_session_path` were corrected in the current implementation to use official Live API properties.
- locator creation/deletion may need special care because the current code appears to rely on `set_or_delete_cue()` in a way that may not be precise enough.

---

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

---

## 4. Master / cue / meters

| Command | Purpose | Status |
|---|---|---|
| `get_master_info` | Read master mixer state | plausible |
| `set_master_volume` | Set master volume | plausible |
| `set_master_pan` | Set master pan | plausible |
| `get_master_output_meter` | Read output meter | plausible |
| `get_cue_volume` | Read cue volume | plausible |
| `set_cue_volume` | Set cue volume | plausible |

---

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

---

## 6. Arrangement View clips

| Command | Purpose | Status |
|---|---|---|
| `get_arrangement_clips` | List arrangement clips for one track | confirmed |
| `get_all_arrangement_clips` | List arrangement clips across tracks | plausible |
| `create_arrangement_midi_clip` | Create MIDI clip in arrangement | confirmed |
| `create_arrangement_audio_clip` | Create audio clip in arrangement | high risk |
| `delete_arrangement_clip` | Delete arrangement clip | needs audit |
| `resize_arrangement_clip` | Resize arrangement clip | needs audit |
| `move_arrangement_clip` | Move arrangement clip | needs audit |
| `add_notes_to_arrangement_clip` | Add MIDI notes to arrangement clip | confirmed |
| `get_arrangement_clip_notes` | Read notes from arrangement clip | confirmed |
| `duplicate_to_arrangement` | Copy session clip to arrangement | needs audit |

### Notes
- This is one of the most important domains in the project.
- `create_arrangement_audio_clip` is strategically important and now uses the official `file_path + start_time` contract.
- `move_arrangement_clip` currently appears to recreate clips, which is believable but should be audited for data loss and audio behavior.

---

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

---

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
| `load_instrument_or_effect` | Load browser item onto track | high risk |
| `get_device_class_name` | Return device class | plausible |
| `select_device` | Select device | plausible |
| `get_selected_device` | Return selected device | plausible |

### Notes
- `get_device_parameters` explicitly acknowledges that third-party plugin parameters may require manual Configure in Live before they appear.
- That is a good assumption and should be preserved in docs and tool design.
- `show_plugin_window` / `hide_plugin_window` are now explicitly treated as partial because the current implementation only manipulates device-chain collapse state.
- `load_instrument_or_effect` now has a safer native-device insertion path for Live 12.3+ and keeps browser URI loading as provisional.

---

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

### Notes
- Nested rack handling is an important differentiator for this project.
- These commands are good candidates for early modularization into `rack_ops.py`.

---

## 10. Drum rack

| Command | Purpose | Status |
|---|---|---|
| `get_drum_rack_pads` | List drum rack pads and chain info | plausible |
| `set_drum_rack_pad_note` | Remap pad note | needs audit |
| `set_drum_rack_pad_mute` | Mute pad | plausible |
| `set_drum_rack_pad_solo` | Solo pad | plausible |

---

## 11. Browser

| Command | Purpose | Status |
|---|---|---|
| `get_browser_tree` | List browser categories/tree | plausible |
| `get_browser_items_at_path` | Navigate browser by path | plausible |
| `search_browser` | Search browser subtree | needs audit |
| `load_drum_kit` | Load drum kit by URI/path | high risk |

### Notes
- Browser support is strategically important.
- It is also one of the first areas likely to break if the generated code guessed incorrectly about browser APIs.

---

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
- The implementation has been corrected to use `Track.create_take_lane()` when available.
- This domain should be treated as experimental until audited.

---

## 13. View / selection / UI focus

| Command | Purpose | Status |
|---|---|---|
| `get_current_view` | Return current focused document view | plausible |
| `focus_view` | Focus named view | plausible |
| `show_arrangement_view` | Focus Arranger view | plausible |
| `show_session_view` | Focus Session view | plausible |
| `show_detail_view` | Show detail view variant | plausible |
| `get_arrangement_length` | Read arrangement length | needs audit |

---

## Command counts by domain

| Domain | Count |
|---|---:|
| Health | 1 |
| Session / transport / song | 31 |
| Tracks | 28 |
| Master / cue | 6 |
| Session clips | 19 |
| Arrangement clips | 10 |
| Scenes | 9 |
| Devices / parameters | 14 |
| Racks / chains | 7 |
| Drum rack | 4 |
| Browser | 4 |
| Take lanes | 6 |
| View / selection | 6 |
| **Total** | **145** |

## Recommended next artifacts

Based on this catalog, the most useful next docs/codegen helpers are:

1. `command-status-audit.md`
   - mark each command as confirmed, likely-complete, partial, stub, or unverified

2. `command-schemas.md`
   - define params and result shapes for each command family

3. modular refactor plan
   - map each command family to a future module

## Recommended next refactor split

- `song_ops.py` → Health + Session/transport
- `track_ops.py` → Tracks + Master
- `session_clip_ops.py` → Session clips
- `arrangement_ops.py` → Arrangement clips
- `scene_ops.py` → Scenes
- `device_ops.py` → Devices
- `rack_ops.py` → Racks + Drum Rack
- `browser_ops.py` → Browser
- `take_lane_ops.py` → Take lanes
- `view_ops.py` → View/selection

## Bottom line

This dispatcher already defines a large and credible command surface.
It is a strong enough public capability map to anchor the next code generation pass.
The main work now is not inventing commands, but auditing and organizing them without losing coverage.
