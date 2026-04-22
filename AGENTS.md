# AGENTS.md

Guidance for coding agents working in this repository. For a deeper tour of the architecture, see [CLAUDE.md](CLAUDE.md).

## Project

Python-first MCP server for Ableton Live 12. Two halves that must be changed in tandem:

1. **`AbletonMCP_Remote_Script/`** — MIDI Remote Script running inside Ableton. Exposes a newline-delimited JSON TCP bridge on `localhost:9877`. Domain behavior is split across `*_ops.py` mixins composed in `__init__.py`; dispatch is a long `elif` chain in `_dispatch`. Add behavior to the matching mixin, not to `__init__.py`.
2. **`mcp_server/`** — external Python process exposing MCP tools via FastMCP. Tool definitions live under `mcp_server/tools/<domain>.py`; `server.py` is the slim entrypoint. `mcp_server/command_specs.py` is the source of truth for command contracts, stability labels, and first-class MCP exposure.

Adding a new command means touching three places: the matching `*_ops.py` mixin, the `_dispatch` chain in the Remote Script, and `command_specs.py`. If it should be promoted as a first-class MCP tool, also add a function to the matching `mcp_server/tools/<domain>.py` module.

## Threading inside the Remote Script

Anything touching Live's API must run on Live's main thread. The TCP server runs in a worker thread and uses `_schedule_and_wait(lambda: ...)` to bounce mutations onto the main thread with an `8.0s` timeout. Safe read-only queries (e.g. `_health_check`, `_get_session_info`) call through directly. Preserve this pattern when adding dispatcher cases.

## Live Object Model is the authority

Treat the Ableton Live Object Model as ground truth for behavioral questions (racks, chains, Drum Racks, DrumPad, DrumChain, devices, mixer, browser). Use Context7 with library id `/websites/cycling74_apiref_lom` before making behavioral claims or changing contracts. Do not invent deep plugin control that Live does not expose — prefer a profile/alias layer over raw parameters.

## Remote Script reload workflow

When a Remote Script change must be tested in Live, run `scripts/reload_ableton_remote_script.sh` yourself — do not hand the reload step back to the user unless the scripted reload fails and you can name the blocker. The script rsyncs into the installed location, quits Live, and relaunches it (optionally reopening the previous session if `ABLETON_SESSION_PATH` is set or if `get_session_path` returns one).

## Preservation rules

- **Preserve the command surface.** Do not silently drop commands; do not rename public command names without a documented migration reason.
- **Keep request/response shapes stable** unless contract changes are explicitly documented in `docs/command-catalog.md` and `command_specs.py`.
- **Do not claim runtime correctness** for anything not directly validated in Live. Stability labels in `command_specs.py` (`confirmed`, `likely-complete`, `partial`, `stub`, `unverified`) are intentional — update them honestly.
- **Python 3.10+.** Keep dependencies minimal (currently only `fastmcp==3.2.0`).
- **Prefer refactors inside the mixins or `mcp_server/tools/<domain>.py`** over growing `__init__.py` or `server.py`.

## Docs that must stay in sync with the code

- [`mcp_server/command_specs.py`](mcp_server/command_specs.py) — authoritative contract + stability labels
- [`docs/command-catalog.md`](docs/command-catalog.md) — domain-grouped inventory and behavior notes
- [`docs/install-and-use-mcp.md`](docs/install-and-use-mcp.md) §8 (contract notes) if behavior-impacting contracts change
