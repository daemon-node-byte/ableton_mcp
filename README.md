# AbletonMCP

[![Version v0.1.0-beta](https://img.shields.io/badge/version-v0.1.0--beta-blue)](README.md)
[![Ableton Live 12](https://img.shields.io/badge/Ableton%20Live-12-000000)](docs/install-and-use-mcp.md)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](docs/install-and-use-mcp.md)
[![MCP stdio](https://img.shields.io/badge/MCP-stdio-2E8B57)](docs/install-and-use-mcp.md)
[![Docker Ready](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](docs/install-and-use-mcp.md)
[![Core Flows Verified](https://img.shields.io/badge/Live%20Validation-core%20flows%20verified-brightgreen)](docs/command-catalog.md)
[![Status Audit Heavy](https://img.shields.io/badge/status-audit--heavy-orange)](docs/manual-validation-backlog.md)

AbletonMCP is a Python-first MCP server for Ableton Live 12.

It has two parts:
- an Ableton Live Remote Script that runs inside Live and exposes a TCP bridge
- a Python MCP server that talks to that bridge and exposes tools over `stdio`

## Why This Project Exists

The docs in [docs/ableton_live_mcp_discoveries.md](/Users/joshmclain/code/AbletonMCP_v2/docs/ableton_live_mcp_discoveries.md) show the gap this project is trying to close:

- many existing Ableton MCP servers are constrained by stock `AbletonOSC` endpoints
- Session View control is common, but deeper Arrangement View editing is less reliable
- browser loading, device insertion, and plugin-facing workflows are often the weak point
- there is room for a Python-first server that owns more of the feature surface through a custom Remote Script

This project is aimed at giving MCP clients a broader and more practical Ableton Live 12 control surface, especially for:
- session control
- arrangement control
- tracks, clips, and MIDI notes
- devices, racks, chains, and macros
- browser-driven loading
- future plugin-oriented workflows

## Current Architecture

- [AbletonMCP_Remote_Script](/Users/joshmclain/code/AbletonMCP_v2/AbletonMCP_Remote_Script) runs inside Ableton Live
- [mcp_server](/Users/joshmclain/code/AbletonMCP_v2/mcp_server) provides the MCP server
- the Remote Script listens on TCP port `9877` by default
- the MCP server uses `stdio` transport by default
- Docker packaging is included for a more portable runtime

The current source of truth for command metadata and maturity is [mcp_server/command_specs.py](/Users/joshmclain/code/AbletonMCP_v2/mcp_server/command_specs.py). The broader audit context lives in [docs/command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md).

## Prerequisites

Based on [docs/install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md):

- Ableton Live 12
- Python `3.10+` for local runs
- `uv` if you want the recommended local Python workflow
- Docker Desktop or Docker Engine if you want the containerized MCP server
- an MCP client that can launch a `stdio` server process

## Installation and Setup (local hosting only)

### 1. Install the Ableton Remote Script

Copy [AbletonMCP_Remote_Script](/Users/joshmclain/code/AbletonMCP_v2/AbletonMCP_Remote_Script) into Ableton's Remote Scripts directory and rename the installed folder to `AbletonMCP`.

Typical paths from the docs:

- macOS: `/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts/AbletonMCP`
- Windows: `C:\Users\<you>\Documents\Ableton\User Library\Remote Scripts\AbletonMCP`

Then in Ableton Live:

1. Open `Settings` / `Preferences` > `Link, Tempo & MIDI`.
2. In a Control Surface slot, choose `AbletonMCP`.
3. Leave Live open while using the MCP server.

### 2. Smoke test the Live-side bridge

On the same machine as Ableton Live:

```bash
printf '{"type":"health_check","params":{}}\n' | nc localhost 9877
```

You should get a JSON response with `status: "success"`.

### 3. Run the MCP server locally

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

### 4. Run with Docker

Build:

```bash
docker build -t ableton-mcp-v2 .
```

Run on macOS and Windows:

```bash
docker run --rm -i \
  -e ABLETON_MCP_HOST=host.docker.internal \
  -e ABLETON_MCP_PORT=9877 \
  ableton-mcp-v2
```

Run on Linux:

```bash
docker run --rm -i \
  --add-host=host.docker.internal:host-gateway \
  -e ABLETON_MCP_HOST=host.docker.internal \
  -e ABLETON_MCP_PORT=9877 \
  ableton-mcp-v2
```

For more detailed setup, see [docs/install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md).

## Feature Status

### Working and verified in Live 12

The following commands are documented as locally verified on `2026-04-09` in [docs/install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md) and [docs/command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md):

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

Verified note round trips:

- Session View: create temporary MIDI clip, add 3 notes, read the same 3 notes back, delete the clip
- Arrangement View: create temporary arrangement MIDI clip, add 3 notes, read the same 3 notes back, delete the clip

Verified arrangement editing and import flow:

- Audio import: inserted `/System/Library/Sounds/Funk.aiff` onto a disposable audio track with `create_arrangement_audio_clip`, confirmed placement with `get_arrangement_clips`, then removed it with `delete_arrangement_clip`
- MIDI edit flow: resized and moved a disposable arrangement MIDI clip, confirmed note preservation after the move, then cleaned it up
- Session-to-arrangement flow: duplicated a disposable Session View MIDI clip into Arrangement View and confirmed the duplicated note data with `get_arrangement_clip_notes`

Verified browser discovery and built-in loading flow:

- Browser discovery: confirmed `get_browser_tree`, `get_browser_items_at_path("instruments")`, `get_browser_items_at_path("drums")`, and `search_browser("drift", "instruments")` against the running Live browser
- Native insert: loaded `Drift` onto a disposable MIDI track with `load_instrument_or_effect(device_name="Drift")` and confirmed device growth with `get_track_devices`
- Browser URI instrument load: loaded the discovered URI `query:Synths#Drift` onto a disposable MIDI track with `load_instrument_or_effect(uri=...)`
- Drum-kit load: loaded the discovered preset URI `query:Drums#FileId_5422` with `load_drum_kit` and confirmed device growth with `get_track_devices`

Verified negative cases:

- `create_arrangement_audio_clip` rejects MIDI tracks, missing `file_path`, relative paths, and nonexistent absolute paths
- `resize_arrangement_clip` rejects non-positive lengths and ambiguous selectors
- `move_arrangement_clip` is now explicitly documented as MIDI-only in this pass
- `search_browser` rejects blank queries
- `load_instrument_or_effect` rejects missing or duplicate load sources, invalid URIs, and invalid `target_index`
- `load_drum_kit` rejects the generic `Drum Rack` device URI

Repeatable validation helper:

```bash
uv run --python 3.11 python scripts/validate_arrangement_batch_2.py \
  --audio-file /absolute/path/to/audio-file.wav
```

```bash
uv run --python 3.11 python scripts/validate_browser_loading_batch.py
```

### Exposed now, but not yet verified end to end

These are already part of the current MCP surface or dispatcher, but the docs still treat them as `likely-complete`, `partial`, or otherwise provisional:

- transport and song controls such as `set_tempo`, `start_playback`, `stop_playback`, `set_current_song_time`
- track creation beyond the verified MIDI track flow, such as `create_audio_track`
- device inspection and parameter commands such as `get_track_devices`, `get_device_parameters`, `set_device_parameter_by_name`, `get_device_parameter_by_name`
- a larger set of clip, scene, rack, browser, take lane, and view commands in the Remote Script dispatcher
- raw access to the broader command surface through `ableton_raw_command(...)`

### Not yet complete or still in the validation backlog

From [docs/manual-validation-backlog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/manual-validation-backlog.md), the main unfinished or not-yet-validated areas are:

- third-party plugin and non-validated browser URI loading beyond the now-confirmed built-in instrument and drum-kit flows
- broader effect-loading behavior beyond the validated built-in instrument path
- take lane workflows
- plugin-window behavior
- remaining arrangement undo behavior and any future audio-clip move strategy

## First-Class MCP Tools

The current first-class MCP tools are:

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

Everything else in the current command catalog is still reachable through `ableton_raw_command(...)`, but not all of it should be treated as production-ready yet.

## Docs Map

- [docs/install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md): installation and usage
- [docs/command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md): command surface and status
- [docs/manual-validation-backlog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/manual-validation-backlog.md): next validation targets
- [docs/ableton_live_mcp_discoveries.md](/Users/joshmclain/code/AbletonMCP_v2/docs/ableton_live_mcp_discoveries.md): research and motivation
- [docs/README.md](/Users/joshmclain/code/AbletonMCP_v2/docs/README.md): guide to the docs folder
