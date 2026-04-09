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
- `create_arrangement_audio_clip`
- `delete_arrangement_clip`
- `resize_arrangement_clip`
- `move_arrangement_clip`
- `add_notes_to_arrangement_clip`
- `get_arrangement_clip_notes`
- `duplicate_to_arrangement`

Arrangement Batch 2 notes:
- `create_arrangement_audio_clip` was validated with the absolute path `/System/Library/Sounds/Funk.aiff`
- negative cases were validated for missing `file_path`, relative paths, nonexistent files, ambiguous selectors, non-positive resize lengths, and audio-clip move rejection
- the disposable validation run restored the set to the original 4-track state after cleanup
- undo behavior was intentionally not documented as verified

## Priority order

1. Native device insertion via `Track.insert_device(...)`
2. Browser URI loading
3. Take lanes
4. Plugin-window behavior
5. Arrangement undo behavior and any future audio-clip move strategy

## 1. Native device insertion

Validate:
- `load_instrument_or_effect` with `device_name`

Record:
- exact device names that succeed
- index-placement behavior
- failure behavior for invalid insert positions
- Live 12.3+ requirement confirmation

## 2. Browser URI loading

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

## 3. Take lanes

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

## 4. Plugin-window behavior

Validate:
- `show_plugin_window`
- `hide_plugin_window`

Record:
- whether these commands affect only device-chain collapse
- whether any actual plugin editor visibility changes occur
- whether command names should be narrowed or aliased in a future pass

## 5. Remaining arrangement residuals

Validate:
- undo behavior after `create_arrangement_audio_clip`
- undo behavior after `resize_arrangement_clip`, `move_arrangement_clip`, and `duplicate_to_arrangement`
- whether a future audio-clip move path is worth supporting at all

Record:
- whether Live exposes clean undo steps for each arrangement mutation
- whether any safe audio-clip move strategy exists without direct file-path recovery
- any unexpected selection or playback side effects
