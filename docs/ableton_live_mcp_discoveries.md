# Ableton Live 12 MCP Server Research and Development Plan

Status: concise archive
Date: 2026-04-09

## Why This Still Matters

This doc captures the ecosystem research that justified a custom Remote Script backend and a broader Live 12 feature goal.

It is no longer the place for the current verified command list or setup flow. Use these instead:

- [README.md](/Users/joshmclain/code/AbletonMCP_v2/README.md)
- [install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md)
- [command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md)

## Main Conclusions

- Arrangement editing is feasible in an MCP-oriented Live stack; it is not just a Session View problem.
- Browser/device loading is where stock `AbletonOSC`-style stacks tend to hit their limits.
- Device parameter access is broadly feasible, but third-party plugin depth depends on what Live exposes as automatable parameters.
- A Python-first server is realistic if it owns its own Remote Script.
- The key remaining uncertainty is no longer whether the overall approach works, but how far it can go safely for third-party loading, plugin profiles, undo, and high-risk mutations.

## Ecosystem Takeaways

- `ahujasid/ableton-mcp`
  - good Python Remote Script reference and proof that a custom bridge can go beyond stock OSC
- `Simon-Kansara/ableton-live-mcp-server`
  - strong example of broad MCP mapping over `AbletonOSC`, but still limited by that surface
- `nozomi-koborinai/ableton-osc-mcp`
  - useful negative reference for browser-loading limits in pure `AbletonOSC` stacks
- `uisato/ableton-mcp-extended`
  - ambitious Python feature surface and useful browser/audio-import reference
- `xiaolaa2/ableton-copilot-mcp`
  - strongest evidence found that arrangement manipulation and browser-driven loading are practical
- `ideoforms/AbletonOSC`
  - valuable capability catalog and fallback bridge, but not enough by itself for a fully featured server

## What The Live API Suggested

High-confidence targets:

- song and transport control
- track creation and mixer control
- Session View clip and MIDI note workflows
- device enumeration and parameter access
- browser navigation

Directionally feasible but implementation-sensitive:

- arrangement clip editing
- browser loading
- take lanes
- clip automation
- nested rack traversal

Still limited by Live parameter exposure:

- third-party plugin control
- plugin-specific profile depth
- Serum-style alias layers

## What Changed In This Repo

The research question is now narrower than it was when this doc started:

- arrangement create/edit/import is now validated in Live
- built-in browser discovery is now validated in Live
- built-in instrument and drum-kit loading is now validated in Live

The remaining research questions are:

- how far browser loading goes beyond the validated built-in slice
- which plugin parameters are stable enough for curated profiles
- what undo guarantees are realistic for destructive mutations
- whether any low-latency side channel is worth adding later

## Architecture Guidance That Survived

- Prefer a custom Python Remote Script plus Python MCP server as the primary backend.
- Keep room for compatibility or fallback backends later if they help testing or interoperability.
- Separate browser discovery from device insertion/loading so the implementation can evolve without rewriting the tool layer.
- Treat plugin support as parameter/profile work, not UI automation.

## Sources Reviewed

- `ahujasid/ableton-mcp`
- `Simon-Kansara/ableton-live-mcp-server`
- `nozomi-koborinai/ableton-osc-mcp`
- `uisato/ableton-mcp-extended`
- `FabianTinkl/AbletonMCP`
- `xiaolaa2/ableton-copilot-mcp`
- `ideoforms/AbletonOSC`
- Cycling '74 Live Object Model documentation for Live 12.3.5
