# Remote Script Module Split Plan

Date: 2026-04-09
Target: `AbletonMCP_Remote_Script/__init__.py`
Goal: split the monolithic Remote Script into domain modules without losing the current command surface

## Status update

This split has now been started in code:
- `AbletonMCP_Remote_Script/__init__.py` is back to bootstrap, TCP server lifecycle, scheduling, and dispatch
- shared helpers moved into `core.py`
- the domain operations now live in the existing `*_ops.py` mixin modules
- the command surface is mirrored in `mcp_server/command_specs.py` for MCP tool generation and audit tracking
- core session and arrangement note flows have now been runtime-validated in Ableton Live 12

Remaining work:
- broader runtime validation inside Ableton Live 12 beyond the now-confirmed clip/note flows
- replacing the long `elif` dispatcher with a registry only after behavior audits settle
- deeper review of provisional domains like browser loading, take lanes, and plugin-window behavior

## Why split now

The current Remote Script is doing too many jobs in one file:
- entrypoint bootstrap
- TCP server lifecycle
- scheduling / thread safety
- command dispatch
- song logic
- track logic
- session clip logic
- arrangement logic
- device logic
- rack logic
- browser logic
- take lane logic
- UI/view logic

That makes the next code generation pass risky.
If an agent edits the monolith directly, it is too easy to break unrelated areas or lose commands that only exist because of a prior partial generation pass.

## Current design rule

For the next stage, we should **preserve the public command surface exactly** while changing only the internal organization.

That means:
- command names stay the same
- request shape stays the same unless explicitly documented
- dispatcher remains the single external command router for now
- helper methods move to modules in small steps

## Recommended target structure

```text
AbletonMCP_Remote_Script/
  __init__.py
  dispatcher.py
  core.py
  song_ops.py
  track_ops.py
  session_clip_ops.py
  arrangement_ops.py
  scene_ops.py
  device_ops.py
  rack_ops.py
  browser_ops.py
  take_lane_ops.py
  view_ops.py
```

## Module responsibilities

### `__init__.py`
Keep only:
- imports
- `create_instance`
- `AbletonMCP` class shell
- lifecycle hooks
- server bootstrap
- `_process_command`
- `_dispatch`

The class may still own the methods initially, but new logic should be delegated out.

### `core.py`
Shared utilities and helpers:
- `_get_track`
- `_get_clip_slot`
- `_get_clip`
- `_get_device`
- `_find_arrangement_clip`
- small serialization helpers like `_clip_to_dict`
- parameter validation helpers

### `song_ops.py`
Commands in this module:
- `health_check`
- `get_session_info`
- `get_current_song_time`
- `set_current_song_time`
- `set_tempo`
- `set_time_signature`
- `start_playback`
- `stop_playback`
- `continue_playback`
- `start_recording`
- `stop_recording`
- `toggle_session_record`
- `toggle_arrangement_record`
- `set_metronome`
- `tap_tempo`
- `undo`
- `redo`
- `capture_midi`
- `re_enable_automation`
- `set_arrangement_loop`
- `get_cpu_load`
- `get_session_path`
- `get_locators`
- `create_locator`
- `delete_locator`
- `jump_to_time`
- `jump_to_next_cue`
- `jump_to_prev_cue`
- `set_punch_in`
- `set_punch_out`
- `trigger_back_to_arrangement`
- `get_back_to_arrangement`
- `set_session_automation_record`
- `get_session_automation_record`
- `set_overdub`
- `stop_all_clips`
- `get_arrangement_length`

### `track_ops.py`
Commands in this module:
- track CRUD
- track routing
- send levels
- return tracks
- master track and cue volume
- selected track helpers

### `session_clip_ops.py`
Commands in this module:
- session clip CRUD
- note CRUD
- loop / markers
- gain / pitch / warp
- clip automation commands

### `arrangement_ops.py`
Commands in this module:
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

### `scene_ops.py`
Commands in this module:
- scene CRUD
- fire/select scene

### `device_ops.py`
Commands in this module:
- device listing
- parameter listing
- parameter set/get
- device enable / delete / move
- plugin window helpers
- device selection
- browser item loading onto track

### `rack_ops.py`
Commands in this module:
- rack chains
- macros
- chain devices
- chain mute / solo / volume
- drum rack pad operations

### `browser_ops.py`
Commands in this module:
- browser tree
- browser path lookup
- browser search
- drum kit load helper

### `take_lane_ops.py`
Commands in this module:
- take lane listing
- set name
- create clip in lane
- get clips in lane
- delete lane
- creation behavior notes / fallback behavior

### `view_ops.py`
Commands in this module:
- current view
- focus view
- show arrangement
- show session
- show detail

## Best migration strategy

### Phase A. Create scaffolding without changing behavior
Create empty or near-empty modules and move only helper functions first.

Safe first moves:
- move `_get_track`, `_get_clip_slot`, `_get_clip`, `_get_device`, `_find_arrangement_clip`, `_clip_to_dict` into `core.py`
- import them back into `__init__.py` or wrap them through mixins/helpers

Why:
- these helpers are used across many domains
- moving them first reduces duplication pressure
- low risk compared to moving behavioral methods immediately

### Phase B. Extract domain methods in chunks
Recommended extraction order:

1. `view_ops.py`
2. `scene_ops.py`
3. `browser_ops.py`
4. `rack_ops.py`
5. `device_ops.py`
6. `arrangement_ops.py`
7. `session_clip_ops.py`
8. `track_ops.py`
9. `song_ops.py`

Reason:
- view and scene modules are smaller and less entangled
- song/track/session clip logic is broader and should move later
- arrangement and device logic are core domains and deserve careful review while moving

### Phase C. Introduce a dispatcher registry
After modules exist, replace the long `elif` chain with a registry structure like:

```python
COMMANDS = {
    "get_session_info": self._get_session_info,
    "create_midi_track": lambda p: self._schedule_and_wait(lambda: self._create_midi_track(p)),
}
```

This should happen only after modules are stable enough that the command surface is documented and preserved.

## Important code issues already visible

These should be called out before or during the split.

### Likely broken or suspicious methods
- `_get_cpu_load`
  - currently returns `self.song().get_current_beats_song_time().numerator`
  - this does not look like CPU load

- `_get_session_path`
  - currently returns `self.song().get_current_beats_song_time().denominator`
  - this does not look like session path

- first `_get_arrangement_length`
  - earlier in the file it returns `self.song().arrangement_overdub`
  - later it returns `self.song().arrangement_length` with a fallback
  - duplicate method definition means the later one wins, but this is a sign of generation artifacts

- `_create_arrangement_audio_clip`
  - uses `track.create_audio_clip(start_time, length)`
  - may be valid or may reflect a guessed API surface; needs audit

- `_delete_arrangement_clip`
  - assumes `track.delete_clip(clip)` exists
  - this needs verification against actual Live API expectations

### Generation artifact warning
The file already shows signs of partial or conflicting generation.
During refactor, preserve behavior but annotate suspicious areas clearly.

## Recommended documentation to maintain during split

When the split starts, keep these docs updated:
- `command-catalog.md`
- `api-comparison-and-codegen-prep.md`
- this file

If a command is moved, note the destination module.
If a command is found to be obviously wrong, note that too.

## Minimal next implementation move

The safest first code change is:

1. create the module files
2. add comments/docstrings describing their intended command families
3. optionally move only shared helper methods into `core.py`
4. leave the dispatcher intact for now

That gets the repo structurally ready for code generation without risking a large behavior break in one pass.

## Bottom line

Do not do a big-bang rewrite.

Do a preservation-first split:
- keep commands stable
- move helpers first
- extract small domains next
- document suspicious methods as you go
- treat the current file as a partially valid prototype, not a reliable source of truth
