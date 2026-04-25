# Install and Use AbletonMCP

Canonical setup and runtime usage guide across local `stdio`, local Docker, and remote HTTP deployments.

## Overview

AbletonMCP has two parts:

1. `AbletonMCP_Remote_Script`, which runs inside Ableton Live
2. the Python MCP server in `mcp_server`, which exposes tools over local `stdio` or remote HTTP

The Live-side bridge listens on TCP port `9877` by default.

## Prerequisites

- Ableton Live 12
- Python `3.10+`
- `uv` for the recommended local run flow
- Docker only if you want the containerized server
- an MCP client that can launch a `stdio` server process or connect to a remote MCP URL

## 1. Install the Remote Script

Copy [`AbletonMCP_Remote_Script`](../AbletonMCP_Remote_Script) into Ableton's MIDI Remote Scripts directory.

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
cd /path/to/AbletonMCP_v2
ABLETON_MCP_TRANSPORT=stdio \
uv run --python 3.11 ableton-mcp
```

Useful environment variables:

- `ABLETON_MCP_HOST` default: `localhost`
- `ABLETON_MCP_PORT` default: `9877`
- `ABLETON_MCP_CONNECT_TIMEOUT` default: `5.0`
- `ABLETON_MCP_RESPONSE_TIMEOUT` default: `30.0`
- `ABLETON_MCP_TRANSPORT` default: `stdio`
- supported transports: `stdio`, `http`, `streamable-http`, `sse`
- `ABLETON_MCP_BIND_HOST` default: `0.0.0.0`
- `ABLETON_MCP_HTTP_PATH` default: `/mcp/`
- `PORT` default for remote HTTP hosting: `8080`

Note:

- the Python server defaults to `stdio`
- the Docker image defaults to `streamable-http` so it can run on Cloud Run without extra wrapper commands

## 4. Docker Alternative

### Local Docker For a Desktop MCP Client (`stdio`)

Build:

```bash
docker build -t ableton-mcp-v2 .
```

Run:

```bash
docker run --rm -i \
  -e ABLETON_MCP_TRANSPORT=stdio \
  -e ABLETON_MCP_HOST=host.docker.internal \
  -e ABLETON_MCP_PORT=9877 \
  ableton-mcp-v2
```

On Linux, also add:

```bash
--add-host=host.docker.internal:host-gateway
```

### Local Docker For Remote HTTP Testing

```bash
docker run --rm -p 8080:8080 \
  -e ABLETON_MCP_TRANSPORT=streamable-http \
  -e PORT=8080 \
  -e ABLETON_MCP_HOST=host.docker.internal \
  -e ABLETON_MCP_PORT=9877 \
  ableton-mcp-v2
```

On Linux, also add:

```bash
--add-host=host.docker.internal:host-gateway
```

Remote MCP endpoint:

```text
http://localhost:8080/mcp/
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
        "ABLETON_MCP_TRANSPORT=stdio",
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

## 6. Google Cloud Run Deployment

For the full Docker-based Cloud Run deployment workflow, use [google-cloud-run-deployment.md](google-cloud-run-deployment.md).

Remote endpoint shape:

```text
https://<service-url>/mcp/
```

Important security note:

- the current Cloud Run guide intentionally uses a public unauthenticated endpoint
- that is a security risk and should be treated as an explicit tradeoff, not a safe default

## 7. Horizon Hosting

Horizon can host this server by inferring the module-level FastMCP object from `mcp_server/server.py`. No explicit object suffix is required — Horizon will discover one of `mcp`, `server`, or `app`; this repo exports all three names pointed at the same FastMCP instance.

Required environment variables:

- `ABLETON_MCP_HOST`: host or IP where the Ableton bridge is reachable
- `ABLETON_MCP_PORT`: bridge TCP port (default `9877`)

Optional environment variables:

- `ABLETON_MCP_CONNECT_TIMEOUT` default: `5.0`
- `ABLETON_MCP_RESPONSE_TIMEOUT` default: `30.0`

Horizon-owned settings to avoid overriding here:

- listener transport and bind lifecycle
- exposed service port (typically provided by the platform)

Networking requirement:

- Horizon runtime must be able to reach `ABLETON_MCP_HOST:ABLETON_MCP_PORT`
- if that route is not reachable, all tool calls will fail with transport errors even when Horizon startup is healthy

Hosted validation playbook:

1. invoke `health_check` to confirm the MCP tool surface is active
2. invoke `get_session_info` to confirm bridge connectivity and Ableton-side state access
3. if calls fail with a timeout, increase `ABLETON_MCP_CONNECT_TIMEOUT` and verify the network route
4. if calls fail with connection refused, verify Remote Script is active and bridge host/port are correct
5. if calls fail with DNS or host lookup errors, use a reachable IP or fix runtime DNS for `ABLETON_MCP_HOST`

## 8. Contract Notes

Non-obvious behaviors to keep in mind. For the full per-command catalog, see [command-catalog.md](command-catalog.md).

- `create_arrangement_audio_clip` requires an absolute existing `file_path`.
- `delete_arrangement_clip`, `resize_arrangement_clip`, and `move_arrangement_clip` require exactly one selector: `clip_index` or `start_time`.
- `move_arrangement_clip` is currently MIDI-only.
- `select_track` requires exactly one of `track_index`, `return_index`, or `master=True`.
- `get_selected_track` returns `selection_type`, `name`, `index`, `track_index`, and `return_index`.
- `set_track_color` is validated against the applied/read-back color, not the raw requested RGB value, because Live maps track colors to the nearest chooser entry.
- `set_track_arm` raises a stable error when the target cannot be armed.
- `fold_track` / `unfold_track` raise stable errors for non-foldable tracks.
- `get_browser_tree`, `get_browser_items_at_path`, and `search_browser` share the normalized top-level category set: `all`, `instruments`, `audio_effects`, `midi_effects`, `drums`, `sounds`, `samples`, `packs`, `user_library`.
- `search_browser` requires a non-empty query; `search_browser(category="all")` may time out — prefer category-scoped searches.
- `load_instrument_or_effect` requires exactly one of `device_name`, `native_device_name`, or `uri`; `target_index` is native-insertion only and must be `>= 0`. Native insertion is limited by `Track.insert_device`, which per LOM is native Live devices only.
- `toggle_device` and `set_device_enabled` are activator-parameter helpers on native devices, not universal power switches.
- `show_plugin_window` and `hide_plugin_window` toggle `Device.View.is_collapsed`, not plugin editor window control.
- `load_drum_kit` requires a loadable drum-kit preset URI and rejects the generic `Drum Rack` device entry.
- Generic `Instrument Rack` and `Audio Effect Rack` device entries may load as empty shells.
- `set_send_level`, `get_return_tracks`, `get_return_track_info`, `set_return_volume`, and `set_return_pan` require the set to contain at least one return track.
- System-owned rack addressing uses track-relative LOM-style paths such as `devices 0`, `devices 0 chains 1`, `devices 0 chains 1 devices 2`.
- `create_rack`, `insert_rack_chain`, `insert_device_in_chain`, `apply_rack_blueprint`, `write_memory_bank`, and `refresh_rack_memory_entry` require a saved Live Set when they need project-root Memory Bank persistence.
- Shorthand native device names (`Eq8`, `AutoFilter`) are normalized to validated Live device names before insertion. EQ Eight shorthand parameter names (`Gain A`, `Frequency A`, `Q A`) are normalized during nested rack tuning.
- `get_rack_macros` and `set_rack_macro` are confirmed only for already-exposed macros. Native macro-to-parameter and macro-to-macro authoring is explicitly unsupported — `apply_rack_blueprint` rejects such directives with a stable unsupported error.
- Top-level Drum Racks expose `drum_pads`; inner Drum Racks return zero pad entries. `DrumPad.note` is read-only; `set_drum_rack_pad_note` remaps via `DrumChain.in_note` (Live 12.3+). `set_drum_rack_pad_mute` falls back to chain mute when pad-level mute does not stick.
- `delete_take_lane` is not part of the confirmed core: `Track.delete_take_lane` is not documented in the LOM and the command fails with a stable error when unavailable.

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
