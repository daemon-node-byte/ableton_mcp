# Ableton Live 12 Feasibility Spike, Steps 1 and 2

Date: 2026-04-09
Project: AbletonMCP_v2
Focus: Step 1 and Step 2 of the focused feasibility spike against Ableton Live 12

## Status update after the current implementation pass

The feasibility question is now slightly narrower because the repo no longer just declares the arrangement surface; it also encodes the corrected API contracts in code.

Important updates:
- `create_arrangement_audio_clip` now requires `file_path` plus `start_time`, matching the official `Track.create_audio_clip(file_path, position)` contract
- `get_arrangement_length` now uses `Song.song_length` with clip-end fallback
- `duplicate_to_arrangement` now uses `Track.duplicate_clip_to_arrangement(...)`
- take-lane handling now assumes `Track.create_take_lane()` and `TakeLane.create_midi_clip(start_time, length)` where available

What still requires Live-backed validation has not changed:
- actual undo behavior
- overlap and failure semantics
- audio import edge cases
- view/selection side effects

## Scope

This document covers the first two items from the recommended feasibility spike:

1. arrangement MIDI clip insertion
2. arrangement audio clip insertion

The goal here is not to claim final implementation success yet. The goal is to review the current codebase, compare it against the research assumptions, and define what is already present versus what must be validated directly inside Ableton Live 12.

## What I reviewed

Current repo contents:

- `AbletonMCP_Remote_Script/__init__.py`
- `mcp_server/__init__.py`
- `pyproject.toml`
- `ableton_live_mcp_discoveries.md`

The key finding is that this repo is already much farther along than a blank feasibility spike.
The Remote Script command dispatcher already declares a broad surface for arrangement, device, rack, browser, take lane, and plugin-related operations.

## Immediate finding: Step 1 and 2 are already represented in the Remote Script API surface

From the current `AbletonMCP_Remote_Script/__init__.py` command dispatcher, the repo already exposes these arrangement-related commands:

- `get_arrangement_clips`
- `get_all_arrangement_clips`
- `create_arrangement_midi_clip`
- `create_arrangement_audio_clip`
- `delete_arrangement_clip`
- `resize_arrangement_clip`
- `move_arrangement_clip`
- `add_notes_to_arrangement_clip`
- `get_arrangement_clip_notes`
- `duplicate_to_arrangement`

That changes the nature of the feasibility spike.

Instead of asking "can this repo be extended to support arrangement insertion?", the more precise question is now:

- do the existing arrangement commands work reliably in Ableton Live 12
- what exact Live API calls do they rely on
- what are the edge cases and failure modes
- what data model should the MCP layer expose for these operations

## Step 1. Arrangement MIDI clip insertion

### Current status from code review

This repo already has an exposed command named:

- `create_arrangement_midi_clip`

It also appears to have supporting commands that suggest a broader arrangement workflow exists or is intended:

- `get_arrangement_clips`
- `add_notes_to_arrangement_clip`
- `get_arrangement_clip_notes`
- `resize_arrangement_clip`
- `move_arrangement_clip`
- `duplicate_to_arrangement`

### What this means

This is strong evidence that arrangement MIDI clip creation is already considered a first-class feature in this codebase.
So for Step 1, the feasibility question is no longer architectural. It is now a validation question.

### What must be validated directly in Live 12

#### Functional validation
- Can a blank MIDI clip be created on a MIDI track in Arrangement View?
- Can the clip be created at an arbitrary start time in beats?
- Can the clip be created with a specified length?
- Does the command reject invalid targets cleanly, for example:
  - audio track instead of MIDI track
  - negative start time
  - overlapping or invalid ranges if Live rejects them

#### Post-create edit validation
- Can notes be inserted into the newly created arrangement clip with `add_notes_to_arrangement_clip`?
- Can notes be read back from that clip?
- Can the clip then be moved or resized without breaking note retrieval?

#### View and selection behavior
- Does clip creation require Arrangement View to be focused first?
- Does it affect the current selection or UI state in unwanted ways?
- Does it trigger Back to Arrangement or other playback-state changes unexpectedly?

#### Undo behavior
- Does the action appear as a single clean undo step inside Live?
- If note insertion follows clip creation, does Live treat that as one or multiple undo steps?

### Expected success criteria for Step 1

Step 1 is successful if all of the following are true in Live 12:

1. `create_arrangement_midi_clip` creates a MIDI clip on the requested track and timeline position.
2. The clip can accept note insertion and note retrieval.
3. The operation is stable across repeated runs.
4. The action behaves sanely with undo.
5. Invalid operations fail with clear structured errors.

### Risks specific to Step 1

- The command may exist in the dispatcher but still be partially implemented or incorrect internally.
- Live API behavior may differ based on whether the target track already has arrangement material.
- Some operations may succeed only when the target view or selection state is a certain way.
- Timing fields may use beats, bars, or internal clip offsets inconsistently if not normalized carefully.

### Recommendation after code review

Step 1 should now be treated as a runtime verification task, not a design exploration task.
The code surface already exists. The next move is to test it against a controlled Ableton Live 12 session.

## Step 2. Arrangement audio clip insertion

### Current status from code review

This repo already exposes:

- `create_arrangement_audio_clip`

This is significant because arrangement audio insertion is often harder than MIDI clip creation.
It usually depends on file-path handling, source media validity, track type validation, and sometimes different Live API semantics from MIDI clip creation.

### What this means

Again, Step 2 is no longer hypothetical in this codebase. It is an implementation validation problem.

### What must be validated directly in Live 12

#### Functional validation
- Can an audio file be placed on an audio track at a specific arrangement time?
- What input shape does the command require:
  - absolute file path
  - URI
  - sample already in the browser
- Does the imported clip preserve expected metadata such as:
  - clip length
  - warp state
  - file path reference

#### Track and file validation
- Does the command correctly reject insertion onto a MIDI track?
- Does it fail cleanly if the file does not exist?
- What happens with unsupported or unusual audio formats?
- What happens with long files, stereo files, or files with unusual sample rates?

#### Timeline behavior
- Is the clip inserted exactly at the requested arrangement position?
- Does insertion overwrite anything, overlap, or create a new lane/placement behavior that needs to be modeled explicitly?
- Does it respect existing arrangement structure and track content?

#### Audio-specific state
- What are the defaults for warp mode, gain, and clip markers after import?
- Can the resulting arrangement clip be moved and resized with the existing arrangement commands?
- Can the clip's file path be read back reliably afterward?

#### Undo behavior
- Does the insertion show up as a clean undo step?
- Are file import and placement one action or multiple actions?

### Expected success criteria for Step 2

Step 2 is successful if all of the following are true in Live 12:

1. `create_arrangement_audio_clip` inserts a valid audio clip on an audio track.
2. The insertion uses a predictable and documented path/file contract.
3. The resulting clip can be enumerated with `get_arrangement_clips`.
4. The imported clip can be moved/resized without breaking state.
5. Invalid files or track targets fail cleanly.

### Risks specific to Step 2

- Audio insertion may depend on browser APIs or file import mechanics that behave differently from MIDI clip creation.
- Live may import the sample successfully but produce unexpected defaults for warping or markers.
- File path handling may differ across macOS and Windows.
- This operation may be more brittle than the command name suggests.

### Recommendation after code review

Step 2 should also be treated as a runtime verification task, but with a stronger emphasis on file-path and media-contract testing.
This is likely the higher-risk item of the two.

## New understanding of the repo

The research document proposed a feasibility spike because arrangement insertion was still partly speculative.
That is no longer the case for this codebase.

This repo already appears to be aiming at a much richer Live 12 control surface than the research draft assumed, including:

- arrangement clip operations
- rack and chain operations
- plugin window commands
- browser operations
- take lane operations
- automation operations

So the practical next step is not more abstract planning.
It is a targeted runtime validation pass that proves which of these implemented commands are real, stable, and production-worthy.

## Recommended test matrix for Step 1 and 2

### Test Set A: MIDI arrangement insertion
Use a clean Live 12 set with:
- one MIDI track
- no existing arrangement clips on that track

Run and record:
1. Create MIDI arrangement clip at bar 1 for 4 bars
2. Add a small note pattern
3. Read notes back
4. Resize clip
5. Move clip
6. Undo sequence manually in Live

Capture:
- request payload
- response payload
- visible result in Live
- any error messages
- undo behavior

### Test Set B: Audio arrangement insertion
Use a clean Live 12 set with:
- one audio track
- one known short WAV file

Run and record:
1. Insert audio clip at bar 1
2. Read arrangement clips back
3. Move clip
4. Resize clip
5. Inspect clip path, warp state, and markers if exposed
6. Undo sequence manually in Live

Capture:
- file path used
- response payload
- exact clip placement
- resulting default audio settings
- undo behavior

### Test Set C: Failure cases
- MIDI clip on audio track
- audio clip on MIDI track
- invalid negative start time
- zero or negative length
- missing audio file path
- unsupported file path or malformed path

## Suggested output format for runtime validation

For each test case, record:

- command name
- input params
- expected result
- actual result
- pass/fail
- notes

This should go into a follow-up doc, for example:
- `feasibility-spike-runtime-results.md`

## Conclusion

### Step 1 conclusion
Arrangement MIDI clip insertion is already represented in the current Remote Script surface and appears intended as a supported feature. The main unknown is runtime reliability in Ableton Live 12, not conceptual possibility.

### Step 2 conclusion
Arrangement audio clip insertion is also already represented in the current Remote Script surface. It is probably the more fragile of the two due to file import semantics, and it should be validated carefully with controlled sample files.

## Next recommended action

Run a real Live 12 validation pass for these exact commands first:

1. `create_arrangement_midi_clip`
2. `add_notes_to_arrangement_clip`
3. `get_arrangement_clip_notes`
4. `create_arrangement_audio_clip`
5. `get_arrangement_clips`
6. `move_arrangement_clip`
7. `resize_arrangement_clip`

If those tests pass, then the project can move confidently into the next spike areas:
- nested device tree traversal
- Serum 2 parameter discovery
- browser-based native/plugin loading
