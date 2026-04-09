# Remote Script Module Split Plan

Status: concise archive
Date: 2026-04-09

## Why This Still Matters

This doc captures the preservation-first refactor strategy for moving away from the original monolithic Remote Script without losing the command surface.

The split is already underway, but the core rules still matter whenever the Remote Script grows again.

## Current State

- `AbletonMCP_Remote_Script/__init__.py` now handles bootstrap, TCP bridge lifecycle, scheduling, and dispatch
- shared helpers live in `core.py`
- domain behavior is split into `*_ops.py` mixins
- `mcp_server/command_specs.py` mirrors the command surface for contracts and MCP exposure

## Target Structure

- `song_ops.py`
  - health, song, and transport behavior
- `track_ops.py`
  - tracks, returns, routing, and mixer control
- `session_clip_ops.py`
  - Session View clip and MIDI note workflows
- `arrangement_ops.py`
  - arrangement clip creation, editing, import, and duplication
- `scene_ops.py`
  - scene creation, selection, and firing
- `device_ops.py`
  - devices, parameters, insertion, and selection
- `rack_ops.py`
  - racks, chains, macros, and drum-rack helpers
- `browser_ops.py`
  - browser navigation, search, and drum-kit loading
- `take_lane_ops.py`
  - take-lane commands and fallbacks
- `view_ops.py`
  - UI focus and view helpers

## Rules That Still Stand

- preserve command names unless there is a documented migration reason
- keep request and response shapes stable unless contract changes are explicitly documented
- prefer small extractions over big-bang rewrites
- document suspicious behavior instead of silently deleting it
- keep docs and `command_specs.py` in sync with the code

## Remaining Work

- replace the long `elif` dispatcher with a registry only after behavior audits settle
- keep validating extended browser/plugin loading beyond the built-in slice
- finish take-lane validation
- audit plugin-window behavior
- continue tightening high-risk domains without shrinking the intended feature surface

## Related Docs

- [command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md)
- [api-comparison-and-codegen-prep.md](/Users/joshmclain/code/AbletonMCP_v2/docs/api-comparison-and-codegen-prep.md)
- [manual-validation-backlog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/manual-validation-backlog.md)
