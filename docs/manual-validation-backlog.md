# Manual Validation Backlog

This doc is the operational shortlist for the next Live 12 validation runs.

## Recently Validated

Confirmed locally on `2026-04-09`:

- connectivity and session inspection
- Session View clip and MIDI note round trips
- Arrangement View MIDI/audio clip creation, edit, delete, and duplication flows
- browser discovery plus built-in instrument and drum-kit loading

For the exact validated commands, use [docs/install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md) and [docs/command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md).

## Next Priorities

### 1. Extended browser and device loading

Validate:

- `load_instrument_or_effect` with built-in audio-effect and MIDI-effect targets
- `load_instrument_or_effect` with third-party plugin URIs if the browser exposes them
- browser URI classes beyond the validated built-in instrument and drum-kit flows
- insert-position behavior for non-instrument content

Record:

- the exact URIs and content classes tested
- whether effect insertion behaves differently from instrument insertion
- whether third-party plugin URIs are loadable or need separate handling
- any platform-specific issues

### 2. Take lanes

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

### 3. Plugin-window behavior

Validate:

- `show_plugin_window`
- `hide_plugin_window`

Record:

- whether these commands only affect device-chain collapse
- whether any actual plugin editor visibility changes occur
- whether the command names should be narrowed later

### 4. Arrangement residuals

Validate:

- undo behavior after `create_arrangement_audio_clip`
- undo behavior after `resize_arrangement_clip`, `move_arrangement_clip`, and `duplicate_to_arrangement`
- whether audio clip move support should remain intentionally unsupported

Record:

- whether Live exposes clean undo steps for each mutation
- whether any safe audio-clip move strategy exists without file-path recovery
- any unexpected selection or playback side effects
