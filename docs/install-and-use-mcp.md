# Install and Use AbletonMCP v2

This is the canonical setup and runtime usage guide for AbletonMCP.

## Overview

AbletonMCP has two parts:

1. `AbletonMCP_Remote_Script`, which runs inside Ableton Live
2. the Python MCP server in `mcp_server`, which exposes tools over `stdio`

The Live-side bridge listens on TCP port `9877` by default.

## Prerequisites

- Ableton Live 12
- Python `3.10+`
- `uv` for the recommended local run flow
- Docker only if you want the containerized server
- an MCP client that can launch a `stdio` server process

## 1. Install the Remote Script

Copy [AbletonMCP_Remote_Script](/Users/joshmclain/code/AbletonMCP_v2/AbletonMCP_Remote_Script) into Ableton's MIDI Remote Scripts directory.

Typical locations:

- macOS: `/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts/AbletonMCP_Remote_Script`
- Windows: `C:\Users\<you>\Documents\Ableton\User Library\Remote Scripts\AbletonMCP_Remote_Script`

Then in Ableton Live:

1. Open `Settings` / `Preferences` > `Link, Tempo & MIDI`.
2. In a Control Surface slot, choose `AbletonMCP_Remote_Script`.
3. Leave Live open while using the MCP server.

## 2. Smoke Test the Live Bridge

Run this on the same machine as Ableton Live:

```bash
printf '{"type":"health_check","params":{}}\n' | nc localhost 9877
```

Expected response shape:

```json
{"status":"success","result":{"status":"ok","tempo":120.0,"is_playing":false,"track_count":4}}
```

If this fails, fix the Live-side install before involving MCP.

## 3. Run the MCP Server Locally

Recommended command:

```bash
cd /Users/joshmclain/code/AbletonMCP_v2
uv run --python 3.11 ableton-mcp
```

Useful environment variables:

- `ABLETON_MCP_HOST` default: `localhost`
- `ABLETON_MCP_PORT` default: `9877`
- `ABLETON_MCP_CONNECT_TIMEOUT` default: `5.0`
- `ABLETON_MCP_RESPONSE_TIMEOUT` default: `30.0`
- `ABLETON_MCP_TRANSPORT` default: `stdio`

## 4. Docker Alternative

Build:

```bash
docker build -t ableton-mcp-v2 .
```

Run:

```bash
docker run --rm -i \
  -e ABLETON_MCP_HOST=host.docker.internal \
  -e ABLETON_MCP_PORT=9877 \
  ableton-mcp-v2
```

On Linux, also add:

```bash
--add-host=host.docker.internal:host-gateway
```

## 5. Example MCP Client Configuration

Example Docker-backed `mcpServers` entry:

```json
{
  "mcpServers": {
    "ableton": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "ABLETON_MCP_HOST=host.docker.internal",
        "-e",
        "ABLETON_MCP_PORT=9877",
        "ableton-mcp-v2"
      ]
    }
  }
}
```

On Linux, add `--add-host=host.docker.internal:host-gateway` to the Docker args.

## 6. Current Verified Scope

Direct Live validation on `2026-04-09` currently covers:

- connectivity and session inspection
- Session View clip creation, note write, note read, and cleanup
- Arrangement View MIDI/audio clip creation, resize, move, delete, and duplication
- browser discovery and validated built-in loading for instruments and drum kits

For the full command surface and status map, use [docs/command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md) and [mcp_server/command_specs.py](/Users/joshmclain/code/AbletonMCP_v2/mcp_server/command_specs.py).

## 7. Validation Helpers

Arrangement batch:

```bash
uv run --python 3.11 python scripts/validate_arrangement_batch_2.py \
  --audio-file /absolute/path/to/audio-file.wav
```

Browser and loading batch:

```bash
uv run --python 3.11 python scripts/validate_browser_loading_batch.py
```

## 8. Important Contract Notes

- `create_arrangement_audio_clip` requires an absolute existing `file_path`
- `delete_arrangement_clip`, `resize_arrangement_clip`, and `move_arrangement_clip` require exactly one selector: `clip_index` or `start_time`
- `move_arrangement_clip` is currently MIDI-only
- `get_browser_tree`, `get_browser_items_at_path`, and `search_browser` share the normalized top-level category set:
  `all`, `instruments`, `audio_effects`, `midi_effects`, `drums`, `sounds`, `samples`, `packs`, `user_library`
- `search_browser` requires a non-empty query
- `load_instrument_or_effect` requires exactly one of `device_name`, `native_device_name`, or `uri`
- `load_instrument_or_effect` only accepts `target_index` for native insertion and requires `target_index >= 0`
- `load_drum_kit` requires a loadable drum-kit preset URI and rejects the generic `Drum Rack` device entry

## 9. Troubleshooting

### The MCP server cannot connect

Usually means:

- the Remote Script is not installed
- the wrong control surface is selected
- Ableton Live is not open
- the bridge on `localhost:9877` is not responding

### Docker cannot reach Ableton

Use `ABLETON_MCP_HOST=host.docker.internal`.
On Linux, also add `--add-host=host.docker.internal:host-gateway`.

### Local Python run fails

Use the pinned command:

```bash
uv run --python 3.11 ableton-mcp
```

## 10. Honesty Note

This repo is runnable today, but it is still in an audit-heavy phase.
Some commands are `confirmed`, some are `likely-complete`, and some remain provisional.

Use [docs/command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md) and [mcp_server/command_specs.py](/Users/joshmclain/code/AbletonMCP_v2/mcp_server/command_specs.py) for the current maturity map.
