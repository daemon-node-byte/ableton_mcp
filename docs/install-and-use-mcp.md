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

Direct Live validation through `2026-04-12` currently covers:

- connectivity and session inspection
- regular track mutation and selection
- return-track inspection, return mixer mutation, and send control in a set with existing return tracks
- Session View clip creation, note write, note read, and cleanup
- Arrangement View MIDI/audio clip creation, resize, move, delete, and duplication
- browser discovery and validated built-in loading for instruments, `sounds` presets, drum kits, MIDI effects, and audio effects
- confirmed current browser limitation for third-party plugin URI discovery on the validated surface: category-scoped searches for installed plugin target `Serum 2` produced no discoverable loadable URI, and `search_browser(category="all")` may time out
- top-level device inspection, selection, parameter read/write, activator-helper enable/disable, same-track reordering, deletion, and device-view collapse/expand on native devices
- positive `fold_track` / `unfold_track` round-trip on foldable group track `5-Group`, with the original `fold_state` restored during cleanup
- take-lane inspection, creation, rename, MIDI clip creation, and clip listing through first-class MCP tools
- system-owned Instrument Rack and Audio Effect Rack creation, chain insertion, built-in device insertion, and recursive structure readback
- exposed rack macro value read/write on a validated system-owned rack, plus stable rejection of native macro-authoring directives
- direct live-vs-Memory Bank comparison on an imported non-system-owned rack target (`808 Selector Rack.adg`) before and after `refresh_rack_memory_entry`
- nested device parameter read/write inside rack trees through track-relative LOM-style paths
- project-root Memory Bank reads and writes for saved Live Sets
- blueprint-driven rack creation with stable rejection of unsupported native macro-mapping directives
- rack, chain, and drum-rack inspection/mutation
- Drum Rack note remap via `DrumChain.in_note` on the validated Live build

For the full command surface and status map, use [docs/command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md) and [mcp_server/command_specs.py](/Users/joshmclain/code/AbletonMCP_v2/mcp_server/command_specs.py).

## 7. Validation Helpers

Canonical Python test command:

```bash
uv run python -m unittest discover -s tests -q
```

Arrangement batch:

```bash
uv run --python 3.11 python scripts/validate_arrangement_batch_2.py
```

Optional explicit audio input:

```bash
uv run --python 3.11 python scripts/validate_arrangement_batch_2.py \
  --audio-file /absolute/path/to/audio-file.wav
```

Browser and loading batch:

```bash
uv run --python 3.11 python scripts/validate_browser_loading_batch.py
```

Take-lane batch:

```bash
uv run --python 3.11 python scripts/validate_take_lanes_batch.py
```

Rack and drum batch:

```bash
uv run --python 3.11 python scripts/validate_rack_and_drum_batch.py
```

System-owned rack automation batch:

```bash
uv run --python 3.11 python scripts/validate_system_owned_racks_batch.py
```

Track control batch:

```bash
uv run --python 3.11 python scripts/validate_track_controls_batch.py
```

Device audit batch:

```bash
uv run --python 3.11 python scripts/validate_device_audit_batch.py
```

Macro and user-rack audit batch:

```bash
uv run --python 3.11 python scripts/validate_macro_and_user_rack_batch.py
```

Full user-rack pass with a manual target:

```bash
uv run --python 3.11 python scripts/validate_macro_and_user_rack_batch.py \
  --user-rack-track-index <track-index> \
  --user-rack-device-index <device-index>
```

The `2026-04-12` imported-rack comparison used browser-loaded preset `808 Selector Rack.adg` as the manual target and confirmed the expected pre-import vs post-import semantics.

## 8. Important Contract Notes

- `create_arrangement_audio_clip` requires an absolute existing `file_path`
- `delete_arrangement_clip`, `resize_arrangement_clip`, and `move_arrangement_clip` require exactly one selector: `clip_index` or `start_time`
- `move_arrangement_clip` is currently MIDI-only
- the arrangement residual validator now records `can_undo`/`can_redo` snapshots and side effects per audited mutation
- in the 2026-04-12 residual pass, mutate application was confirmed for `create_arrangement_audio_clip`, `resize_arrangement_clip`, `move_arrangement_clip` (MIDI path), and `duplicate_to_arrangement`, but undo/redo clip-state round-trip was not yet clean in the disposable-track flow because undo popped disposable track setup
- audio clip move remains intentionally unsupported and returned the stable MIDI-only error path in that pass
- `select_track` requires exactly one of `track_index`, `return_index`, or `master=True`
- `get_selected_track` returns `selection_type`, `name`, `index`, `track_index`, and `return_index`
- `set_track_color` should be validated against the applied/read-back color, not the raw requested RGB value, because Live maps track colors to the nearest chooser entry
- `set_track_arm` raises a stable error when the target cannot be armed
- `fold_track` and `unfold_track` are confirmed on the validated Live 12.3.7 set for foldable group track `5-Group`; they still raise stable errors for non-foldable tracks
- the current Python Remote Script surface did not expose child-track `is_visible` readback during the fold pass, so confirmation rests on `fold_state` round-trip plus grouped-child discovery
- `get_browser_tree`, `get_browser_items_at_path`, and `search_browser` share the normalized top-level category set:
  `all`, `instruments`, `audio_effects`, `midi_effects`, `drums`, `sounds`, `samples`, `packs`, `user_library`
- `search_browser` requires a non-empty query
- category-scoped browser search is the confirmed path for the validated build
- `search_browser(category="all")` may be too expensive for plugin discovery on the validated build and can time out
- `load_instrument_or_effect` requires exactly one of `device_name`, `native_device_name`, or `uri`
- `load_instrument_or_effect` only accepts `target_index` for native insertion and requires `target_index >= 0`
- native `device_name` / `native_device_name` insertion is limited by `Track.insert_device`, which the LOM documents as native Live devices only
- discovered built-in `sounds` preset URIs are now part of the confirmed browser-loading slice
- third-party plugin URI loading is not currently discoverable through the validated normalized browser roots; the blocker on the 2026-04-12 pass was browser-surface exposure, not the raw `load_instrument_or_effect` command shape
- top-level `device_index` currently follows the observed `track.devices` ordering from the validated Python Remote Script surface; on Live 12.3.7 this excluded the mixer device on a fresh disposable MIDI track
- `toggle_device` and `set_device_enabled` are confirmed as activator-parameter helpers on native devices, not universal device power setters
- `move_device` is confirmed for same-track top-level native-device reordering on the validated Live 12.3.7 build
- `show_plugin_window` and `hide_plugin_window` are confirmed only for `Device.View.is_collapsed` collapse/expand behavior, not plugin editor window control
- `load_drum_kit` requires a loadable drum-kit preset URI and rejects the generic `Drum Rack` device entry
- generic `Instrument Rack` and `Audio Effect Rack` device entries may load as empty shells with zero chains in the current Live library
- `set_send_level`, `get_return_tracks`, `get_return_track_info`, `set_return_volume`, and `set_return_pan` are confirmed in sets that already contain at least one return track
- `get_take_lanes`, `create_take_lane`, `set_take_lane_name`, `create_midi_clip_in_lane`, and `get_clips_in_take_lane` are first-class MCP tools and the confirmed take-lane core on the validated Live 12.3.7 build
- `delete_take_lane` is not part of the confirmed core: `Track.delete_take_lane` is not documented in the LOM and was unavailable on the validated Python Remote Script surface, so the command currently fails with a stable error when unavailable
- system-owned rack addressing uses track-relative LOM-style paths such as `devices 0`, `devices 0 chains 1`, and `devices 0 chains 1 devices 2`
- `create_rack`, `insert_rack_chain`, `insert_device_in_chain`, `apply_rack_blueprint`, `write_memory_bank`, and `refresh_rack_memory_entry` require a saved Live Set when they need project-root Memory Bank persistence
- shorthand native device names such as `Eq8` and `AutoFilter` are normalized to the validated Live device names before insertion
- EQ Eight shorthand parameter names such as `Gain A`, `Frequency A`, and `Q A` are normalized to the validated Live parameter names during nested rack tuning
- `get_rack_macros` and `set_rack_macro` are confirmed only for already-exposed macros
- the LOM-backed contract for this repo treats native macro-to-parameter authoring and macro-to-macro authoring as explicitly unsupported
- imported/user-authored racks are directly validated for live structure and already-exposed macro inspection before import, but authoritative repo-level semantic metadata still begins only after `refresh_rack_memory_entry`
- `apply_rack_blueprint` rejects `macro_mappings`, `macro_to_macro_mappings`, and similar native macro-authoring requests with a stable unsupported error in this pass
- top-level Drum Racks expose `drum_pads`; inner Drum Racks return zero pad entries
- `DrumPad.note` is treated as read-only
- `set_drum_rack_pad_note` remaps via `DrumChain.in_note`, so this repo targets Live 12.3+ for drum-pad note remap support
- `set_drum_rack_pad_note` readback is validated on the destination pad after remap
- `set_drum_rack_pad_mute` falls back to chain mute when pad-level mute does not stick in Live

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
