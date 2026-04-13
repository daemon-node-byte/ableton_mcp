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
- positive `fold_track` / `unfold_track` round-trip on foldable group track `5-Group`, with original `fold_state` restored during cleanup
- exposed rack macro value read/write on a validated system-owned rack, plus stable rejection of native macro-authoring directives
- LOM-backed contract decision that native macro-to-parameter authoring and macro-to-macro authoring remain explicitly unsupported

Confirmed locally on `2026-04-12`:

- direct live-vs-Memory Bank comparison on an imported non-system-owned rack target using `scripts/validate_macro_and_user_rack_batch.py`
- browser-loaded preset `808 Selector Rack.adg` was inspected via `get_rack_structure` and `get_rack_macros`, then imported with `refresh_rack_memory_entry` and re-read through `get_system_owned_racks`
- validated repo guidance that live structure and already-exposed macros are directly inspectable before import, while authoritative repo-level semantic metadata still begins at explicit Memory Bank import
- browser loading was extended to confirm loadable `sounds` preset URIs in addition to built-in instrument, drum-kit, MIDI-effect, and audio-effect URIs
- third-party browser loading is now a confirmed current limitation on the validated browser surface: category-scoped searches for installed plugin target `Serum 2` produced no discoverable loadable URI, and `search_browser(category='all')` timed out
- take-lane command slice `get_take_lanes`, `create_take_lane`, `set_take_lane_name`, `create_midi_clip_in_lane`, and `get_clips_in_take_lane` round-tripped successfully on a disposable MIDI track
- `delete_take_lane` is not documented in the LOM and was unavailable on the validated Python Remote Script surface, so it remains outside the confirmed core and now fails with a stable error when unavailable
- arrangement residual validator was upgraded to record mutation-level `can_undo` / `can_redo` snapshots plus observable side effects, and it confirmed the stable intentionally-unsupported audio-move contract (`move_arrangement_clip` on audio clips returns the MIDI-only error)

For the exact validated commands, use [docs/install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md) and [docs/command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md).

## Next Priorities

### 1. Third-party plugin behavior beyond the current native-device audit

Validate:

- `load_instrument_or_effect` with third-party plugin URIs if the browser exposes them
- whether third-party plugin parameters remain stable enough for profile-style aliases after manual Configure
- whether any safe, user-facing contract exists for actual plugin editor visibility beyond `Device.View.is_collapsed`

Record:

- the exact plugin URIs and parameter surfaces tested
- whether plugin parameters survive reopen and reselection
- whether any true editor-window behavior is exposed or whether the current collapse/expand contract should remain the final one

### 2. Arrangement residuals

Validate:

- why undo in the upgraded residual validator currently pops disposable track setup instead of proving clip-state rollback for:
  - `create_arrangement_audio_clip`
  - `resize_arrangement_clip`
  - `move_arrangement_clip` (MIDI path)
  - `duplicate_to_arrangement`

Record:

- whether those four mutations can be isolated to clean mutate -> undo revert -> redo restore clip-state readback on disposable tracks
- `can_undo` / `can_redo` snapshots before mutate and after undo/redo for each affected mutation
- unexpected side effects already observed in the failed pass (selected track jump and current song time drift)
