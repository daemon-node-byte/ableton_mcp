# Ableton Live 12 API Comparison and Codegen Prep

Status: concise archive
Date: 2026-04-09

## Why This Still Matters

This doc explains why the current dispatcher was treated as a believable capability map instead of being replaced outright.

For current runtime facts, use:

- [README.md](/Users/joshmclain/code/AbletonMCP_v2/README.md)
- [install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md)
- [command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md)

## Current Takeaway

- the inherited Remote Script was broad, partially generated, and implementation-uncertain
- the dispatcher still mapped well to real Live 12 concepts
- that made it a better preservation baseline than a clean-slate rewrite
- the repo now has a command registry in `mcp_server/command_specs.py` and a split mixin-based Remote Script layout

## Areas That Still Look Well-Aligned With Live 12

- song and transport control
- tracks, mixer, and routing concepts
- Session View clip and MIDI note workflows
- arrangement clip operations
- device, rack, chain, and parameter inspection
- browser and take-lane feature targets

## Areas That Still Need Extra Caution

- browser loading beyond the validated built-in instrument and drum-kit slice
- take-lane workflows
- plugin-window behavior
- automation and envelope editing
- nested rack traversal edge cases
- undo and rollback expectations for destructive actions

## Guidance That Still Stands

- preserve the public command surface before refactoring behavior
- keep `AbletonMCP_Remote_Script/__init__.py` thin and continue the module split
- use `mcp_server/command_specs.py` as the canonical contract layer
- validate high-risk claims in a real Live session before promoting them
- keep plugin support pragmatic: parameter access first, profile/alias layers second

## What Changed Since The Original Draft

- arrangement create/edit/import is no longer speculative
- browser discovery and built-in browser loading are no longer speculative
- the remaining uncertainty is narrower and more operational than architectural

## Related Docs

- [command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md)
- [remote-script-module-split-plan.md](/Users/joshmclain/code/AbletonMCP_v2/docs/remote-script-module-split-plan.md)
- [ableton_live_mcp_discoveries.md](/Users/joshmclain/code/AbletonMCP_v2/docs/ableton_live_mcp_discoveries.md)
