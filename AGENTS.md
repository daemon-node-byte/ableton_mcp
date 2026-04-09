# AGENTS.md - AbletonMCP_v2

This repo is for building a Python-first MCP server and Ableton Remote Script for Ableton Live 12.

## Current reality

This codebase is partially inherited from a prior agent run that timed out and was abandoned.
Do **not** assume the current code is complete just because methods or command names exist.

Treat the repo as:
- partially generated
- structurally promising
- implementation-uncertain
- suitable for controlled completion and refactoring

## Project goal

Build a comprehensive Ableton Live 12 MCP server with strong support for:
- session control
- arrangement control
- tracks, scenes, clips, and notes
- devices, racks, chains, and macros
- browser-driven loading
- third-party plugin parameter access
- future plugin profiles such as Serum 2

Python is the preferred implementation language.

## Guiding assumptions

1. The current command dispatcher in `AbletonMCP_Remote_Script/__init__.py` is the best available map of intended features.
2. Individual implementations may be incomplete, wrong, stubbed, or inconsistent.
3. Preserve capability coverage unless there is a clear reason to remove a command.
4. Prefer refactoring into modules over growing the monolithic `__init__.py` further.
5. Do not claim runtime correctness unless it has been directly validated.

## Near-term priorities

### Priority 1: Preserve and organize
Before changing behavior, preserve the intended feature surface.

If you refactor, first extract and document:
- command names
- params
- return shapes
- dependencies on Live objects

### Priority 2: Split the Remote Script into domains
Refactor the Remote Script into focused modules such as:
- `song_ops.py`
- `track_ops.py`
- `session_clip_ops.py`
- `arrangement_ops.py`
- `device_ops.py`
- `rack_ops.py`
- `browser_ops.py`
- `take_lane_ops.py`
- `view_ops.py`
- `utils.py`

Keep `__init__.py` as the entrypoint and dispatcher.

### Priority 3: Mark uncertain code
When touching implementations, classify methods as:
- confirmed
- likely-complete
- partial
- stub
- unverified

Use comments or docs to make uncertainty explicit.

### Priority 4: Improve command contracts
Every command should have a clear contract:
- required params
- optional params
- parameter types
- result schema
- likely error conditions

This is especially important for later MCP tool generation.

## Specific guidance for key domains

### Arrangement operations
Arrangement support is a major project goal.
Commands such as:
- `create_arrangement_midi_clip`
- `create_arrangement_audio_clip`
- `move_arrangement_clip`
- `resize_arrangement_clip`
- `add_notes_to_arrangement_clip`
should be preserved and improved, not removed casually.

### Browser loading
Browser-related commands are strategically important.
Even if implementation is incomplete, keep the command surface and improve it carefully.

### Plugin support
For VSTs and third-party plugins:
- rely on Live-exposed parameters first
- do not invent deep plugin control that Live does not expose
- prefer a profile/alias layer above raw parameters
- Serum 2 should eventually be handled as a plugin profile, not special-case magic

### Racks and chains
Nested rack traversal is a project differentiator.
Preserve rack, chain, macro, and drum-rack related commands where possible.

## Code generation rules

1. Do not rewrite the entire project from scratch unless explicitly asked.
2. Prefer small, reviewable refactors.
3. Preserve public command names unless there is a documented migration reason.
4. If a method is missing but the dispatcher references it, either:
   - implement it, or
   - mark it clearly as unverified / TODO
   - but do not silently drop it
5. Keep Python 3.10+ compatibility.
6. Keep dependencies minimal unless a new dependency clearly improves correctness or maintainability.

## Documentation to maintain

Keep these docs up to date as work progresses:
- `docs/ableton_live_mcp_discoveries.md`
- `docs/feasibility-spike-step-1-2.md`
- `docs/api-comparison-and-codegen-prep.md`
- `docs/command-catalog.md`
- `docs/remote-script-module-split-plan.md`

If the command surface changes materially, document it.

## Good next tasks for future agents

- extract a command catalog from the current dispatcher
- split the Remote Script into domain modules
- define typed schemas for MCP-facing command payloads
- audit arrangement methods for completeness
- audit device/rack/plugin methods for completeness
- prepare Serum 2 parameter profile scaffolding

## Bad next tasks for future agents

- replacing the current architecture with a totally different stack without discussion
- deleting large command areas because they look hard
- assuming plugin UI automation is available just because parameter access exists
- claiming runtime support that has not been validated

## Bottom line

This repo already points in the right direction.
The job now is to turn a probably-partial generated prototype into a structured, believable, codegen-friendly implementation without losing the ambitious feature surface.
