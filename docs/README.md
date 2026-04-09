# Docs

This folder holds the project research, planning, and refactor-prep documents for AbletonMCP_v2.

## Current docs

- `ableton_live_mcp_discoveries.md`
  - broader research on the current Ableton MCP landscape and Live 12 capability assumptions

- `feasibility-spike-step-1-2.md`
  - focused notes for arrangement MIDI and arrangement audio feasibility review

- `api-comparison-and-codegen-prep.md`
  - compares the current Remote Script command surface against what Ableton Live 12 appears to expose, and frames the repo for code generation

- `command-catalog.md`
  - formal catalog of the current dispatcher command surface

- `remote-script-module-split-plan.md`
  - plan for splitting the monolithic Remote Script into domain modules safely

- `manual-validation-backlog.md`
  - prioritized Live 12 runtime validation backlog for the highest-risk domains

- `install-and-use-mcp.md`
  - practical instructions for installing the Remote Script, running the MCP server locally or in Docker, and wiring it into an MCP client

## Repo structure note

- `AGENTS.md` stays in the repo root on purpose so future agents and tooling can discover it immediately.
- Build-up docs live here in `docs/` so the repo root stays cleaner.
- `mcp_server/command_specs.py` is now the Python-side source of truth for command metadata, stability labels, and MCP exposure.

## Suggested reading order

1. `ableton_live_mcp_discoveries.md`
2. `api-comparison-and-codegen-prep.md`
3. `command-catalog.md`
4. `remote-script-module-split-plan.md`
5. `install-and-use-mcp.md`

If you are about to do implementation work, read `../AGENTS.md` first.
