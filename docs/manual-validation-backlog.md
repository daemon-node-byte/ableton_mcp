# Manual Validation Backlog

This doc is the operational shortlist for the next Live 12 validation runs.

## Recently Validated

Confirmed locally on `2026-04-10`:

- connectivity and session inspection
- regular track mutation and selection
- return-track inspection, return mixer mutation, and send control in a set with existing return tracks
- Session View clip and MIDI note round trips
- Arrangement View MIDI/audio clip creation, edit, delete, and duplication flows
- browser discovery plus built-in instrument, drum-kit, MIDI-effect, and audio-effect loading
- system-owned Instrument Rack and Audio Effect Rack creation, chain insertion, nested device insertion, recursive structure readback, and nested parameter tuning
- project-root Memory Bank persistence for saved Live Sets
- blueprint-driven rack generation with stable rejection of unsupported native macro-mapping directives
- rack, chain, and drum-rack inspection/mutation
- Drum Rack note remap via `DrumChain.in_note` on the validated Live build

Confirmed locally on `2026-04-11`:

- top-level device enumeration, selection, parameter read/write, class lookup, deletion, and same-track reordering on native devices
- activator-helper behavior for `toggle_device` and `set_device_enabled` on native devices
- device-view collapse/expand behavior for `show_plugin_window` and `hide_plugin_window`
- observed on the validated Python Remote Script surface that `track.devices` excluded the mixer device on a fresh disposable MIDI track

For the exact validated commands, use [docs/install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md) and [docs/command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md).

## Next Priorities

### 1. Native macro authoring and user-rack semantics

Validate and scope separately:

- whether any documented LOM path exists for authoring native macro-to-parameter mappings
- whether macro-to-macro authoring is possible or should remain explicitly unsupported
- whether imported user-authored racks can be given trustworthy semantic metadata without manual Memory Bank import

Record:

- the exact LOM objects or missing APIs involved
- whether the limitation is API-level or implementation-level
- what remains safe to expose as inspection-only versus system-owned authoring

### 2. Positive fold / unfold validation on a real group track

Validate:

- `fold_track`
- `unfold_track`

Record:

- the exact foldable group track used
- original and restored `fold_state`
- whether any selection or visibility side effects occur in the current Live build

### 3. Extended third-party browser and device loading

Validate:

- `load_instrument_or_effect` with third-party plugin URIs if the browser exposes them
- browser URI classes beyond the validated built-in instrument and drum-kit flows
- insert-position behavior for non-instrument content

Record:

- the exact URIs and content classes tested
- whether effect insertion behaves differently from instrument insertion
- whether third-party plugin URIs are loadable or need separate handling
- any platform-specific issues

### 4. Take lanes

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

### 5. Third-party plugin behavior beyond the current native-device audit

Validate:

- `load_instrument_or_effect` with third-party plugin URIs if the browser exposes them
- whether third-party plugin parameters remain stable enough for profile-style aliases after manual Configure
- whether any safe, user-facing contract exists for actual plugin editor visibility beyond `Device.View.is_collapsed`

Record:

- the exact plugin URIs and parameter surfaces tested
- whether plugin parameters survive reopen and reselection
- whether any true editor-window behavior is exposed or whether the current collapse/expand contract should remain the final one

### 6. Arrangement residuals

Validate:

- undo behavior after `create_arrangement_audio_clip`
- undo behavior after `resize_arrangement_clip`, `move_arrangement_clip`, and `duplicate_to_arrangement`
- whether audio clip move support should remain intentionally unsupported

Record:

- whether Live exposes clean undo steps for each mutation
- whether any safe audio-clip move strategy exists without file-path recovery
- any unexpected selection or playback side effects
