# Manual Validation Backlog

Date: 2026-04-09
Project: AbletonMCP_v2
Purpose: prioritize the next Live 12 runtime validation loop now that the repo has a real MCP server, a command registry, and corrected high-risk API contracts

## Completed on 2026-04-09

Confirmed locally in Ableton Live 12:
- `health_check`
- `get_session_info`
- `get_current_song_time`
- `get_all_track_names`
- `get_track_info`
- `create_midi_track` plus `delete_track`
- `create_clip` plus `delete_clip`
- `add_notes_to_clip` plus `get_clip_notes`
- `get_arrangement_clips`
- `create_arrangement_midi_clip`
- `add_notes_to_arrangement_clip`
- `get_arrangement_clip_notes`

## Priority order

1. Arrangement audio clip flow with real file paths
2. Native device insertion via `Track.insert_device(...)`
3. Browser URI loading
4. Take lanes
5. Plugin-window behavior
6. Remaining arrangement MIDI edge cases: `resize_arrangement_clip`, `move_arrangement_clip`, `duplicate_to_arrangement`, and undo behavior

## 1. Arrangement audio clip flow

Validate:
- `create_arrangement_audio_clip` with absolute file paths
- `get_arrangement_clips`
- `resize_arrangement_clip`
- any realistic audio-clip move workflow we decide to support

Record:
- exact source file path
- resulting clip placement
- warp defaults
- marker defaults
- failure behavior for missing files and wrong track types

## 2. Native device insertion

Validate:
- `load_instrument_or_effect` with `device_name`

Record:
- exact device names that succeed
- index-placement behavior
- failure behavior for invalid insert positions
- Live 12.3+ requirement confirmation

## 3. Browser URI loading

Validate:
- `load_instrument_or_effect` with `uri`
- `load_drum_kit`
- `get_browser_tree`
- `get_browser_items_at_path`
- `search_browser`

Record:
- URIs tested
- whether `get_item_by_uri` resolves reliably
- which content classes are loadable
- any platform-specific issues

## 4. Take lanes

Validate:
- `create_take_lane`
- `set_take_lane_name`
- `create_midi_clip_in_lane`
- `get_clips_in_take_lane`
- `delete_take_lane`

Record:
- whether the API exists in the target Live build
- whether take-lane creation has side effects
- how take-lane clip enumeration behaves after comping and recording

## 5. Plugin-window behavior

Validate:
- `show_plugin_window`
- `hide_plugin_window`

Record:
- whether these commands affect only device-chain collapse
- whether any actual plugin editor visibility changes occur
- whether command names should be narrowed or aliased in a future pass

## 6. Remaining arrangement MIDI edge cases

Validate:
- `resize_arrangement_clip`
- `move_arrangement_clip`
- `duplicate_to_arrangement`

Record:
- whether note data survives each operation
- whether the recreated clip path for `move_arrangement_clip` behaves sanely
- undo behavior
- any unexpected selection or playback side effects
