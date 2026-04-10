# AbletonMCP

[![Version v0.3-beta.0](https://img.shields.io/badge/version-v0.3--beta.0-blue)](README.md)
[![Ableton Live 12](https://img.shields.io/badge/Ableton%20Live-12-000000)](docs/install-and-use-mcp.md)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](docs/install-and-use-mcp.md)
[![MCP stdio](https://img.shields.io/badge/MCP-stdio-2E8B57)](docs/install-and-use-mcp.md)
[![Docker Ready](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](docs/install-and-use-mcp.md)

AbletonMCP is a Python-first MCP server for Ableton Live 12 built around a custom Remote Script and a Python `stdio` MCP server.

## What It Includes

- [AbletonMCP_Remote_Script](/Users/joshmclain/code/AbletonMCP_v2/AbletonMCP_Remote_Script)
  - runs inside Ableton Live and exposes a TCP bridge on `localhost:9877`
- [mcp_server](/Users/joshmclain/code/AbletonMCP_v2/mcp_server)
  - talks to the bridge and exposes MCP tools over `stdio`
- [mcp_server/command_specs.py](/Users/joshmclain/code/AbletonMCP_v2/mcp_server/command_specs.py)
  - source of truth for command metadata, stability, and MCP exposure

## Why This Exists

- many existing Ableton MCP stacks are strongest in Session View and weaker in arrangement editing, browser loading, and deeper device workflows
- this repo keeps the ambitious surface in Python instead of stopping at stock `AbletonOSC` coverage
- the historical research that led here is preserved in [docs/ableton_live_mcp_discoveries.md](/Users/joshmclain/code/AbletonMCP_v2/docs/ableton_live_mcp_discoveries.md)

## Current Status

Validated locally in Ableton Live 12 on `2026-04-09`:

- core connectivity and session introspection
- Session View clip and MIDI note round trips
- Arrangement View MIDI/audio clip creation, edit, delete, and duplication flows
- browser discovery plus built-in instrument, drum-kit, MIDI-effect, and audio-effect loading
- first-class MCP tools for rack, chain, and drum-rack inspection/mutation
- LOM-backed drum-pad remap via `DrumChain.in_note` for Live 12.3+

Still in the validation backlog:

- take lane workflows
- plugin-window behavior
- third-party or broader browser/effect loading beyond the validated built-in slice
- arrangement undo behavior and audio-move policy

## Quick Start

1. Copy [AbletonMCP_Remote_Script](/Users/joshmclain/code/AbletonMCP_v2/AbletonMCP_Remote_Script) into Ableton's MIDI Remote Scripts directory and select `AbletonMCP_Remote_Script` as the control surface.
2. Smoke test the Live bridge:

```bash
printf '{"type":"health_check","params":{}}\n' | nc localhost 9877
```

3. Run the MCP server locally:

```bash
cd /Users/joshmclain/code/AbletonMCP_v2
uv run --python 3.11 ableton-mcp
```

For Docker, MCP client config, validator commands, and troubleshooting, use the canonical setup guide in [docs/install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md).

## Command Surface

First-class MCP tools currently cover:

- health, transport, and session inspection
- basic track inspection and creation
- Session View clip and note workflows
- Arrangement View clip creation and editing
- device inspection and named parameter access
- browser discovery and validated built-in loading
- rack, chain, and drum-rack inspection/mutation

Anything not promoted yet is still reachable through `ableton_raw_command(...)`.

Use these as the current sources of truth:

- [docs/command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md)
  - domain-by-domain command inventory
- [mcp_server/command_specs.py](/Users/joshmclain/code/AbletonMCP_v2/mcp_server/command_specs.py)
  - exact parameter metadata, stability labels, and MCP exposure

## Docs

- [docs/install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md)
  - canonical setup, runtime usage, validators, and troubleshooting
- [docs/command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md)
  - canonical command reference
- [docs/manual-validation-backlog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/manual-validation-backlog.md)
  - next Live validation targets
- [docs/README.md](/Users/joshmclain/code/AbletonMCP_v2/docs/README.md)
  - docs index and reading order

Archived research and planning:

- [docs/ableton_live_mcp_discoveries.md](/Users/joshmclain/code/AbletonMCP_v2/docs/ableton_live_mcp_discoveries.md)
- [docs/api-comparison-and-codegen-prep.md](/Users/joshmclain/code/AbletonMCP_v2/docs/api-comparison-and-codegen-prep.md)
- [docs/feasibility-spike-step-1-2.md](/Users/joshmclain/code/AbletonMCP_v2/docs/feasibility-spike-step-1-2.md)
- [docs/remote-script-module-split-plan.md](/Users/joshmclain/code/AbletonMCP_v2/docs/remote-script-module-split-plan.md)
