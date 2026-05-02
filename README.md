# AbletonMCP

[![Version v1.0.0](https://img.shields.io/badge/version-v1.0.0-blue?style=for-the-badge)](pyproject.toml)
[![Ableton Live 12](https://img.shields.io/badge/Ableton%20Live-12-000000?style=for-the-badge)](docs/install-and-use-mcp.md)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white&style=for-the-badge)](docs/install-and-use-mcp.md)
[![MCP stdio](https://img.shields.io/badge/MCP-stdio-2E8B57?style=for-the-badge)](docs/install-and-use-mcp.md)
[![Docker Ready](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white&style=for-the-badge)](docs/install-and-use-mcp.md)
[![Coverage](https://img.shields.io/badge/coverage-74%25-yellow?style=for-the-badge)](#regenerating-badges)
[![CodeScene Code Health](https://img.shields.io/badge/CodeScene-9.6%2F10-brightgreen?style=for-the-badge)](#regenerating-badges)

AbletonMCP turns Ableton Live 12 into an MCP server. An in-Live Remote Script exposes a TCP bridge, and a Python FastMCP server translates that into MCP tools your AI client can call: track and mixer control, Session and Arrangement clips, MIDI notes, browser loading, devices and rack parameters, take lanes, drum racks, and a project-root Memory Bank.

## Quick Start

### 1. Install the Remote Script

Copy [`AbletonMCP_Remote_Script/`](AbletonMCP_Remote_Script) into Ableton's MIDI Remote Scripts directory:

- **macOS:** `/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/MIDI Remote Scripts/AbletonMCP_Remote_Script`
- **Windows:** `C:\Users\<you>\Documents\Ableton\User Library\Remote Scripts\AbletonMCP_Remote_Script`

In Ableton: **Settings → Link, Tempo & MIDI**, select `AbletonMCP_Remote_Script` as a Control Surface.

### 2. Smoke-test the bridge

With Ableton Live open:

```bash
printf '{"type":"health_check","params":{}}\n' | nc localhost 9877
```

You should see `{"status":"success","result":{"status":"ok","tempo":...,...}}`.

### 3. Run the MCP server

```bash
uv run --python 3.11 ableton-mcp
```

That starts the server on `stdio`. For HTTP, Docker, or remote deployment, see [docs/install-and-use-mcp.md](docs/install-and-use-mcp.md).

### 4. Connect your MCP client

Example `mcpServers` entry (Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "ableton": {
      "command": "uv",
      "args": ["run", "--python", "3.11", "ableton-mcp"],
      "cwd": "/absolute/path/to/AbletonMCP_v2"
    }
  }
}
```

Alternatively, use the Docker image (see the install guide).

## Example Prompts

Keep prompts short and specific — explicit track, slot, and device indexes produce the most reliable results.

- "List all track names."
- "Create a MIDI track named Bass Ideas."
- "Set track 2 volume to 0.72."
- "Create a 4-beat MIDI clip on track 2 slot 0."
- "Create an arrangement MIDI clip on track 2 at 33.0 for 8.0 beats."
- "Search the browser for Drift in instruments."
- "Load the built-in instrument Drift on track 2."
- "List devices on track 2. Show parameters for device 0."
- "Create an Instrument Rack named Bass Stack on track 2."
- "Create a take lane on track 2."

## Docs

- **[Install and use](docs/install-and-use-mcp.md)** — setup, transports, Docker, Horizon hosting, environment variables, contract notes, and troubleshooting.
- **[Command catalog](docs/command-catalog.md)** — the in-depth reference: every command grouped by domain, with stability labels and behavior notes.
- **[`mcp_server/command_specs.py`](mcp_server/command_specs.py)** — machine-readable source of truth for parameter metadata, stability, and first-class MCP exposure.

## What's in the Box

- **[`AbletonMCP_Remote_Script/`](AbletonMCP_Remote_Script)** — runs inside Ableton Live; exposes a newline-delimited JSON TCP bridge on `localhost:9877`.
- **[`mcp_server/`](mcp_server)** — the external FastMCP server. 79 first-class MCP tools plus `ableton_raw_command` for anything else in the catalog.

## License

MIT. See [LICENSE](LICENSE).
