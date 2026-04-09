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
- `get_browser_tree`
- `get_browser_items_at_path`
- `search_browser`
- `load_instrument_or_effect`
- `load_drum_kit`

Arrangement Batch 2 notes:
- `create_arrangement_audio_clip` was validated with the absolute path `/System/Library/Sounds/Funk.aiff`
- negative cases were validated for missing `file_path`, relative paths, nonexistent files, ambiguous selectors, non-positive resize lengths, and audio-clip move rejection
- the disposable validation run restored the set to the original 4-track state after cleanup
- undo behavior was intentionally not documented as verified

Browser and loading batch notes:
- browser discovery was validated against the running Live browser with `get_browser_tree`, `get_browser_items_at_path`, and `search_browser`
- built-in loading was validated with `load_instrument_or_effect(device_name="Drift")`, `load_instrument_or_effect(uri="query:Synths#Drift")`, and `load_drum_kit(rack_uri="query:Drums#FileId_5422")`
- negative cases were validated for blank browser queries, unknown categories, missing browser path components, invalid URIs, invalid `target_index`, missing sources, duplicate sources, and generic `Drum Rack` URIs
- the disposable validation run restored the set to the original 4-track state after cleanup

## Priority order

1. Extended browser and device loading beyond the validated built-in slice
2. Take lanes
3. Plugin-window behavior
4. Arrangement undo behavior and any future audio-clip move strategy

## 1. Extended browser and device loading beyond the validated built-in slice

Validate:
- `load_instrument_or_effect` with built-in audio-effect and MIDI-effect targets
- `load_instrument_or_effect` with third-party plugin URIs if the browser exposes loadable entries
- additional browser URI classes beyond the validated built-in instrument and drum-kit flows
- any insert-position semantics that matter for non-instrument content classes

Record:
- exact content classes and URIs tested
- whether effect insertion behaves differently from instrument insertion
- whether third-party plugin URIs are loadable or need separate handling
- any platform-specific issues

## 2. Take lanes

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

## 3. Plugin-window behavior

Validate:
- `show_plugin_window`
- `hide_plugin_window`

Record:
- whether these commands affect only device-chain collapse
- whether any actual plugin editor visibility changes occur
- whether command names should be narrowed or aliased in a future pass

## 4. Remaining arrangement residuals

Validate:
- undo behavior after `create_arrangement_audio_clip`
- undo behavior after `resize_arrangement_clip`, `move_arrangement_clip`, and `duplicate_to_arrangement`
- whether a future audio-clip move path is worth supporting at all

Record:
- whether Live exposes clean undo steps for each arrangement mutation
- whether any safe audio-clip move strategy exists without direct file-path recovery
- any unexpected selection or playback side effects
