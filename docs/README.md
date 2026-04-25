# Docs

Practical references for AbletonMCP. Start with the top-level [README](../README.md) for a quick overview.

- **[install-and-use-mcp.md](install-and-use-mcp.md)** — setup, runtime usage, transports, Docker, Horizon hosting, environment variables, contract notes, and troubleshooting.
- **[command-catalog.md](command-catalog.md)** — every Remote Script command grouped by domain, with stability labels and behavior notes. Commands marked first-class are exposed as MCP tools; everything else is reachable through `ableton_raw_command(...)`.
- **[google-cloud-run-deployment.md](google-cloud-run-deployment.md)** — Docker-based deployment for a remote MCP endpoint.

Source of truth for parameter metadata and MCP exposure: [`mcp_server/command_specs.py`](../mcp_server/command_specs.py).
