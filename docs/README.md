# Docs

This folder holds the practical setup docs, the command reference, and the archived planning notes for AbletonMCP_v2.

## Start Here

- [README.md](/Users/joshmclain/code/AbletonMCP_v2/README.md)
  - project overview, current status, and quick-start summary
- [install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md)
  - canonical setup, runtime usage, validators, and troubleshooting
- [google-cloud-run-deployment.md](/Users/joshmclain/code/AbletonMCP_v2/docs/google-cloud-run-deployment.md)
  - Docker-based Google Cloud Run deployment for a remote MCP endpoint
- [command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md)
  - canonical command inventory grouped by domain

## Operational Docs

- [manual-validation-backlog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/manual-validation-backlog.md)
  - the next high-value Live validation targets

## Archived Research and Planning

- [ableton_live_mcp_discoveries.md](/Users/joshmclain/code/AbletonMCP_v2/docs/ableton_live_mcp_discoveries.md)
  - ecosystem research and long-range product reasoning
- [api-comparison-and-codegen-prep.md](/Users/joshmclain/code/AbletonMCP_v2/docs/api-comparison-and-codegen-prep.md)
  - why the current command surface was treated as a believable baseline
- [feasibility-spike-step-1-2.md](/Users/joshmclain/code/AbletonMCP_v2/docs/feasibility-spike-step-1-2.md)
  - historical record of the arrangement feasibility spike
- [remote-script-module-split-plan.md](/Users/joshmclain/code/AbletonMCP_v2/docs/remote-script-module-split-plan.md)
  - the preservation-first plan for continuing the Remote Script split

## Source of Truth Notes

- `mcp_server/command_specs.py` is the exact source of truth for MCP exposure, parameter metadata, and stability labels.
- `AGENTS.md` in the repo root is the implementation guidance for future agents and contributors.
