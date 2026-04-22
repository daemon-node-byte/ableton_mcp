# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python-first MCP server for Ableton Live 12. Two halves that must be changed in tandem:

1. **`AbletonMCP_Remote_Script/`** — a MIDI Remote Script that runs **inside Ableton Live**, exposing a newline-delimited JSON TCP bridge on `localhost:9877`. Domain behavior is split across `*_ops.py` mixins composed in `__init__.py`; dispatch is a long `elif` chain in `_dispatch`. Do not grow `__init__.py` further — add behavior to the matching mixin.
2. **`mcp_server/`** — the external Python process that MCP clients talk to. `server.py` exposes first-class tools over FastMCP, `client.py` is the TCP client for the bridge, `command_specs.py` is the **source of truth** for command contracts, stability labels, and which commands are promoted to first-class MCP tools.

These two halves share command names. Any new command must be added in **three places**: the relevant `*_ops.py` mixin, the `_dispatch` chain in `AbletonMCP_Remote_Script/__init__.py`, and `mcp_server/command_specs.py`. If you only want it reachable via `ableton_raw_command`, skip the FastMCP tool wrapper in `server.py`; otherwise add one that calls `_invoke(name, params)`.

The module-level FastMCP instance in `mcp_server/server.py` is exported under three names (`mcp`, `server`, `app`) so hosting platforms that infer the object by name all resolve to the same instance — do not rename or diverge them.

## Commands

Run tests (canonical):
```bash
uv run python -m unittest discover -s tests -q
```

Run a single test:
```bash
uv run python -m unittest tests.test_server -q
# or a single case:
uv run python -m unittest tests.test_server.TestName.test_method -q
```

Run the server locally over stdio (requires Ableton Live open with the Remote Script selected):
```bash
ABLETON_MCP_TRANSPORT=stdio uv run --python 3.11 ableton-mcp
```

Smoke-test the Live bridge directly:
```bash
printf '{"type":"health_check","params":{}}\n' | nc localhost 9877
```

Sync the Remote Script into Ableton and reload Live (macOS; quits and reopens Live):
```bash
./scripts/reload_ableton_remote_script.sh
```

Live-dependent validator batches live in `scripts/validate_*.py` and require an open Ableton session with a saved Live Set. They are not unit tests and must not be run unless Live is available; see `docs/install-and-use-mcp.md` §9 for the full list.

## Remote Script reload workflow

When a change in `AbletonMCP_Remote_Script/` must be tested in Live, run `scripts/reload_ableton_remote_script.sh` yourself — do not hand the reload step back to the user unless the scripted reload fails and you can name the blocker. The script rsyncs into `/Applications/Ableton Live 12 Suite.app/.../MIDI Remote Scripts/AbletonMCP_Remote_Script/`, quits Live, and relaunches it (optionally reopening the previous session if `ABLETON_SESSION_PATH` is set or if `get_session_path` returns one).

## Threading model inside the Remote Script

Anything that touches Live's API must run on Live's main thread. The TCP server runs in a worker thread and uses `_schedule_and_wait(lambda: ...)` to bounce work onto the main thread with an `8.0s` timeout. Read-only queries that are safe off-thread (e.g. `_health_check`, `_get_session_info`) call through directly; all mutations go through `_schedule_and_wait`. Preserve this pattern when adding dispatcher cases.

## Live Object Model is the authority

For any behavioral question about Live objects (racks, chains, Drum Racks, DrumPad, DrumChain, devices, mixer, browser), treat the Ableton Live Object Model as current ground truth. Use Context7 with library id `/websites/cycling74_apiref_lom` before making behavioral claims or changing a contract. Don't invent deep plugin control that Live does not expose — prefer a profile/alias layer over raw parameters (Serum 2 will eventually be a plugin profile, not special-case magic).

## Preservation rules (this repo is partially inherited)

The current command dispatcher is the best available map of intended features — some implementations may be incomplete, stubbed, or wrong. Apply these rules:

- **Preserve the command surface.** Do not silently drop commands; do not rename public command names without a documented migration reason.
- **Keep request/response shapes stable** unless contract changes are explicitly documented in `docs/command-catalog.md` and `command_specs.py`.
- **Do not claim runtime correctness** for anything that has not been directly validated against Live. Stability labels in `command_specs.py` (`confirmed`, `likely-complete`, `partial`, `stub`, `unverified`) are intentional — update them honestly.
- **Python 3.10+**, keep dependencies minimal (currently only `fastmcp==3.2.0`).
- **Prefer refactors inside the mixins** over expanding `__init__.py`.

## Key contract landmines

These are non-obvious and worth re-reading before touching the relevant command:

- `select_track` requires **exactly one** of `track_index`, `return_index`, or `master=True`.
- `delete_arrangement_clip`, `resize_arrangement_clip`, `move_arrangement_clip` require **exactly one** of `clip_index` or `start_time`. `move_arrangement_clip` is MIDI-only by design — the stable audio-path error is intentional.
- `create_arrangement_audio_clip` requires an absolute existing `file_path`.
- `load_instrument_or_effect` requires exactly one of `device_name`, `native_device_name`, or `uri`; `target_index` is native-insertion only and must be `>= 0`. Native insertion is limited by `Track.insert_device`, which per LOM is native devices only.
- Browser roots are the normalized set: `all`, `instruments`, `audio_effects`, `midi_effects`, `drums`, `sounds`, `samples`, `packs`, `user_library`. `search_browser(category="all")` may time out — prefer category-scoped searches.
- `toggle_device` / `set_device_enabled` are **activator-parameter helpers on native devices**, not universal power switches.
- `show_plugin_window` / `hide_plugin_window` currently only toggle `Device.View.is_collapsed` — not plugin editor window control.
- System-owned rack addressing uses track-relative LOM-style paths: `devices 0`, `devices 0 chains 1`, `devices 0 chains 1 devices 2`.
- Shorthand device names (`Eq8`, `AutoFilter`) and shorthand EQ Eight parameter names (`Gain A`, `Frequency A`, `Q A`) are normalized to the validated Live names before use — keep the normalization in place when editing device/rack ops.
- `set_drum_rack_pad_note` remaps via `DrumChain.in_note`, requiring Live 12.3+. `DrumPad.note` is read-only. `set_drum_rack_pad_mute` falls back to chain mute when pad-level mute doesn't stick.
- Native macro-to-parameter and macro-to-macro authoring is **explicitly unsupported**; `apply_rack_blueprint` rejects `macro_mappings` / `macro_to_macro_mappings` with a stable unsupported error.
- `set_track_color` should be validated against the **applied/read-back** color, not the raw RGB — Live maps to the nearest chooser entry.

## Environment variables

Server (`mcp_server/server.py`, `mcp_server/client.py`):
- `ABLETON_MCP_TRANSPORT` — `stdio` (default), `http`, `streamable-http`, `sse`. The Docker image defaults to `streamable-http`.
- `ABLETON_MCP_HOST` / `ABLETON_MCP_PORT` — where to reach the Live bridge (default `localhost:9877`).
- `ABLETON_MCP_CONNECT_TIMEOUT` (`5.0`), `ABLETON_MCP_RESPONSE_TIMEOUT` (`30.0`).
- `ABLETON_MCP_BIND_HOST` (`0.0.0.0`), `ABLETON_MCP_HTTP_PATH` (`/mcp/`), `PORT` (`8080`) for remote HTTP transports.

Remote Script (`AbletonMCP_Remote_Script/__init__.py`):
- `ABLETON_MCP_PORT` — override TCP listen port (default `9877`).

## Docs to keep in sync

When the command surface changes materially, update:
- `mcp_server/command_specs.py` (authoritative contract + stability)
- `docs/command-catalog.md` (domain-grouped inventory)
- `docs/install-and-use-mcp.md` §10 (contract notes) and §8 (verified scope) if validation status changes
