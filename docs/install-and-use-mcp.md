# Install and Use AbletonMCP v2

Date: 2026-04-09
Project: AbletonMCP_v2
Audience: local users who want to run the MCP server against Ableton Live 12, either directly or through Docker

## Overview

AbletonMCP v2 has two parts:

1. the Ableton Live Remote Script
2. the Python MCP server

The Remote Script runs inside Ableton Live and listens on TCP port `9877` by default.
The MCP server talks to that Remote Script and exposes MCP tools to your client over `stdio`.

## Prerequisites

- Ableton Live 12
- Docker Desktop or Docker Engine if you want the containerized MCP server
- an MCP client that can launch a `stdio` server process

## 1. Install the Ableton Remote Script

Copy the repo folder [AbletonMCP_Remote_Script](/Users/joshmclain/code/AbletonMCP_v2/AbletonMCP_Remote_Script) into your Ableton User Library Remote Scripts directory and rename the installed folder to `AbletonMCP`.

Typical paths:

- macOS: `/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts`
- Windows: `C:\Users\<you>\Documents\Ableton\User Library\Remote Scripts\AbletonMCP`

After copying it:

1. Open Ableton Live.
2. Go to `Settings` / `Preferences` > `Link, Tempo & MIDI`.
3. In a Control Surface slot, choose `AbletonMCP`.
4. Leave Live open while you use the MCP server.

## 2. Optional smoke test for the Live-side bridge

Before involving MCP, confirm the Remote Script TCP bridge is alive.

On the same machine as Ableton Live:

```bash
printf '{"type":"health_check","params":{}}\n' | nc localhost 9877
```

Expected response shape:

```json
{"status":"success","result":{"status":"ok","tempo":120.0,"is_playing":false,"track_count":8}}
```

If this does not work, fix the Live-side installation first. The MCP server will not work until this TCP bridge responds.

## 3. Run the MCP server locally without Docker

This repo requires Python `3.10+`.

Recommended command:

```bash
cd /Users/joshmclain/code/AbletonMCP_v2
uv run --python 3.11 ableton-mcp
```

Useful environment variables:

- `ABLETON_MCP_HOST`
  default: `localhost`
- `ABLETON_MCP_PORT`
  default: `9877`
- `ABLETON_MCP_CONNECT_TIMEOUT`
  default: `5.0`
- `ABLETON_MCP_RESPONSE_TIMEOUT`
  default: `30.0`
- `ABLETON_MCP_TRANSPORT`
  default: `stdio`

## 4. Build the Docker image

From the repo root:

```bash
docker build -t ableton-mcp-v2 .
```

The image uses:

- Python 3.11
- `stdio` transport by default
- `ABLETON_MCP_HOST=host.docker.internal` by default

That host default is important because Ableton Live runs on the host machine, not inside the container.

## 5. Run the MCP server in Docker

### macOS and Windows

```bash
docker run --rm -i \
  -e ABLETON_MCP_HOST=host.docker.internal \
  -e ABLETON_MCP_PORT=9877 \
  ableton-mcp-v2
```

### Linux

```bash
docker run --rm -i \
  --add-host=host.docker.internal:host-gateway \
  -e ABLETON_MCP_HOST=host.docker.internal \
  -e ABLETON_MCP_PORT=9877 \
  ableton-mcp-v2
```

## 6. Example MCP client configuration

Example `mcpServers` entry for a client that launches Docker-based stdio servers:

### macOS and Windows

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

### Linux

```json
{
  "mcpServers": {
    "ableton": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--add-host=host.docker.internal:host-gateway",
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

## 7. What tools are exposed right now

The current first-class MCP tools include:

- `health_check`
- `get_session_info`
- `get_current_song_time`
- `set_current_song_time`
- `set_tempo`
- `start_playback`
- `stop_playback`
- `get_all_track_names`
- `get_track_info`
- `create_midi_track`
- `create_audio_track`
- `create_clip`
- `get_clip_notes`
- `add_notes_to_clip`
- `get_arrangement_clips`
- `create_arrangement_midi_clip`
- `create_arrangement_audio_clip`
- `delete_arrangement_clip`
- `resize_arrangement_clip`
- `move_arrangement_clip`
- `add_notes_to_arrangement_clip`
- `get_arrangement_clip_notes`
- `duplicate_to_arrangement`
- `get_track_devices`
- `get_device_parameters`
- `set_device_parameter_by_name`
- `get_device_parameter_by_name`
- `get_browser_tree`
- `get_browser_items_at_path`
- `search_browser`
- `load_instrument_or_effect`
- `load_drum_kit`

There is also a development escape hatch:

- `ableton_raw_command`

That tool can call any cataloged command from [mcp_server/command_specs.py](/Users/joshmclain/code/AbletonMCP_v2/mcp_server/command_specs.py), but some commands are still marked `partial` or `unverified`.

## 8. Verified locally

The following commands have been verified against a real local Ableton Live 12 session on 2026-04-09:

- `health_check`
- `get_session_info`
- `get_current_song_time`
- `get_all_track_names`
- `get_track_info`
- `create_midi_track`
- `delete_track`
- `create_clip`
- `delete_clip`
- `get_clip_notes`
- `add_notes_to_clip`
- `get_arrangement_clips`
- `create_arrangement_midi_clip`
- `create_arrangement_audio_clip`
- `delete_arrangement_clip`
- `resize_arrangement_clip`
- `move_arrangement_clip`
- `add_notes_to_arrangement_clip`
- `get_arrangement_clip_notes`
- `duplicate_to_arrangement`
- `get_browser_tree`
- `get_browser_items_at_path`
- `search_browser`
- `load_instrument_or_effect`
- `load_drum_kit`

The session and arrangement note flows were validated as full round trips:
- create temporary clip
- add 3 MIDI notes
- read the same 3 notes back
- delete the temporary clip

Arrangement Batch 2 runtime validation also confirmed:
- audio import with `create_arrangement_audio_clip` using the absolute path `/System/Library/Sounds/Funk.aiff`
- cleanup with `delete_arrangement_clip`
- MIDI clip resize and move with note preservation
- session-to-arrangement duplication with note readback verification
- negative-case validation for missing or relative `file_path`, nonexistent audio files, ambiguous selectors, non-positive resize lengths, and audio clip move rejection

Browser and instrument loading validation also confirmed:
- browser discovery with `get_browser_tree`, `get_browser_items_at_path("instruments")`, `get_browser_items_at_path("drums")`, and `search_browser("drift", "instruments")`
- native instrument insertion with `load_instrument_or_effect(device_name="Drift")`
- browser URI instrument loading with the discovered built-in URI `query:Synths#Drift`
- drum-kit loading with the discovered preset URI `query:Drums#FileId_5422`
- cleanup-backed negative cases for missing load sources, duplicate load sources, invalid URIs, invalid `target_index`, blank search queries, unknown categories, missing browser paths, and generic `Drum Rack` URIs

Repeatable validation helper:

```bash
uv run --python 3.11 python scripts/validate_arrangement_batch_2.py \
  --audio-file /absolute/path/to/audio-file.wav
```

```bash
uv run --python 3.11 python scripts/validate_browser_loading_batch.py
```

Important current contract notes:
- `create_arrangement_audio_clip` requires an absolute existing `file_path`
- `delete_arrangement_clip`, `resize_arrangement_clip`, and `move_arrangement_clip` require exactly one selector: `clip_index` or `start_time`
- `move_arrangement_clip` is currently MIDI-only
- `get_browser_tree`, `get_browser_items_at_path`, and `search_browser` now share the normalized top-level category set: `all`, `instruments`, `audio_effects`, `midi_effects`, `drums`, `sounds`, `samples`, `packs`, `user_library`
- `search_browser` requires a non-empty query
- `load_instrument_or_effect` requires exactly one of `device_name`, `native_device_name`, or `uri`
- `load_instrument_or_effect` only accepts `target_index` for native device insertion and requires `target_index >= 0`
- `load_drum_kit` requires a loadable drum-kit preset URI and rejects the generic `Drum Rack` device entry
- undo behavior for these arrangement mutations is still not documented as verified

## 9. Common problems

### The MCP server starts but commands fail to connect

Usually means the Remote Script is not installed, not selected as a Control Surface, or Ableton Live is not open.

### Docker container cannot reach Ableton

Use `ABLETON_MCP_HOST=host.docker.internal`.
On Linux, also add:

```bash
--add-host=host.docker.internal:host-gateway
```

### Local Python run fails with dependency errors

Your system Python is probably older than `3.10`.
Use:

```bash
uv run --python 3.11 ableton-mcp
```

## 10. Current honesty note

This repo is ready to run locally and in Docker, but it is still in an audit-heavy stage.
The server is intentionally honest about command maturity:

- some commands are `confirmed`
- some commands are `likely-complete`
- some are `partial`
- some remain `unverified`

For the current maturity map, see [docs/command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md) and [mcp_server/command_specs.py](/Users/joshmclain/code/AbletonMCP_v2/mcp_server/command_specs.py).
