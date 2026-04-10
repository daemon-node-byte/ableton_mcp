# Ableton MCP Server: Rack Management & Memory Bank Reference

## Overview
This document defines the architectural patterns and operational procedures for managing Ableton Live Racks through an MCP server. The server communicates with Ableton via a custom Remote Script using the LOM API over a TCP socket with JSON commands.

Critical LOM API Limitation: The Live Object Model cannot programmatically discover the contents of a Rack. You cannot ask Ableton "what devices are inside this Rack?" Any knowledge of a Rack's internal structure must be maintained externally.

Solution: The MCP server maintains a Memory Bank—human-readable Markdown files stored in the Ableton project folder—that catalogs all Racks created or modified through the MCP system.

1. The 16-Macro Limit and Rack Chaining Strategy
The Limitation
Each Rack (Audio Effect, MIDI Effect, or Instrument) exposes exactly 16 Macro Controls.

The Solution: Rack Chaining (Nesting)
You can nest Racks inside other Racks to multiply the available Macro controls. Each nested Rack retains its own 16 Macros, and the parent Rack can map its Macros to control the Macros of its children.

Rack Chaining Workflow (For MCP Automation)
When the LLM requests creation of a complex Rack with more than 16 controllable parameters:

```text
Step 1: Group each logical device unit into its own Rack
Step 2: Map that device's parameters to its local 16 Macros
Step 3: Group all sub-Racks into a parent "Master Rack"
Step 4: Map parent Macros to sub-Rack Macros as needed
Step 5: Document the entire hierarchy in the Memory Bank
```

Example Command Sequence (MCP to Ableton)

```json
// 1. Create Master Rack
{"command": "create_rack", "track": 0, "name": "Complex Texture Rack", "type": "audio_effect"}

// 2. Create Sub-Rack 1 (EQ Section)
{"command": "create_rack", "track": 0, "chain": 0, "name": "EQ Section", "type": "audio_effect"}
{"command": "add_device", "track": 0, "chain": 0, "device_index": 0, "device_name": "Eq8"}

// 3. Map EQ8 parameters to Sub-Rack 1's Macros
{"command": "map_to_macro", "rack_path": "chains 0", "macro_index": 0, "target_device": 0, "parameter": "Frequency A"}
{"command": "map_to_macro", "rack_path": "chains 0", "macro_index": 1, "target_device": 0, "parameter": "Gain A"}
{"command": "map_to_macro", "rack_path": "chains 0", "macro_index": 2, "target_device": 0, "parameter": "Q A"}

// 4. Create Sub-Rack 2 (Saturation Section)
{"command": "create_rack", "track": 0, "chain": 1, "name": "Saturation Section", "type": "audio_effect"}
{"command": "add_device", "track": 0, "chain": 1, "device_index": 0, "device_name": "Saturator"}

// 5. Map Saturator parameters to Sub-Rack 2's Macros
{"command": "map_to_macro", "rack_path": "chains 1", "macro_index": 0, "target_device": 0, "parameter": "Drive"}
{"command": "map_to_macro", "rack_path": "chains 1", "macro_index": 1, "target_device": 0, "parameter": "Output"}

// 6. (Optional) Map Master Rack Macros to Sub-Rack Macros
{"command": "map_macro_to_macro", "source_rack": "chains 0", "source_macro": 0, "target_rack": "master", "target_macro": 0}
```

2. Memory Bank Specification
The Memory Bank consists of Markdown files stored in the Ableton project folder under .ableton-mcp/memory/. This ensures the knowledge travels with the project and persists across sessions.

Directory Structure

```text
MyProject/
├── MyProject.als
├── Samples/
├── .ableton-mcp/
│   ├── memory/
│   │   ├── project.md           # Project overview, tempo, key, structure
│   │   ├── racks.md             # Catalog of all Racks in the project
│   │   ├── track_1.md           # Track-specific information
│   │   ├── track_2.md
│   │   └── sessions/
│   │       └── 2026-04-09.md    # Session logs and change history
│   └── config.json              # MCP configuration for this project
```

racks.md Format
This is the primary reference file for Rack knowledge.

```markdown
# Rack Catalog

Last Updated: 2026-04-09T14:30:00Z

## Rack: rack_001
- **Name**: Atmospheric Texture Rack
- **Track**: 2 (Bass)
- **Type**: Audio Effect Rack
- **Created**: 2026-04-09T10:15:00Z
- **Created By**: LLM (Claude)

### Macro Mappings

| Macro | Name | Target | Parameter | Range |
|-------|------|--------|-----------|-------|
| 0 | Texture Depth | Chain 1 / Erosion | Amount | 0-100% |
| 1 | Resonance | Chain 0 / EQ Eight | Q A | 0.1-18.0 |
| 2 | Drive Level | Chain 1 / Saturator | Drive | 0-30dB |
| 3 | Echo Mix | Chain 1 / Delay | Dry/Wet | 0-100% |

### Internal Structure
Atmospheric Texture Rack (Master)
├── Chain 0: EQ Section (Audio Effect Rack)
│ └── Device 0: EQ Eight
│ └── Macros Mapped: Resonance (→ Q A)
│
└── Chain 1: Texture Section (Audio Effect Rack)
├── Device 0: Erosion
│ └── Macros Mapped: Texture Depth (→ Amount)
├── Device 1: Saturator
│ └── Macros Mapped: Drive Level (→ Drive)
└── Device 2: Delay
└── Macros Mapped: Echo Mix (→ Dry/Wet)

### LOM Access Paths (For Direct Parameter Control)

| Macro Name | Full LOM Path |
|------------|---------------|
| Texture Depth | `live_set tracks 2 devices 0 chains 1 devices 0 parameters 2` |
| Resonance | `live_set tracks 2 devices 0 chains 0 devices 0 parameters 4` |
| Drive Level | `live_set tracks 2 devices 0 chains 1 devices 1 parameters 0` |
| Echo Mix | `live_set tracks 2 devices 0 chains 1 devices 2 parameters 7` |

### Macro-to-Macro Mappings (If Any)

| Parent Macro | Controls | Child Rack | Child Macro |
|--------------|----------|------------|-------------|
| Master Macro 0 | → | EQ Section | Macro 0 |
```

---
project.md Format


# Project: MyProject

- **File Path**: /Users/username/Music/Ableton/MyProject/MyProject.als
- **Project ID**: `myproject_abc123` (derived from file path hash)
- **Tempo**: 128 BPM
- **Key**: C Minor
- **Time Signature**: 4/4

## Track Overview

| Index | Name | Type | Color |
|-------|------|------|-------|
| 0 | Drums | MIDI | Orange |
| 1 | Bass | Audio | Blue |
| 2 | Pads | MIDI | Purple |
| 3 | FX Return | Return | Green |

## MCP-Created Elements

- Racks: 3 (see racks.md)
- Clips: 12
- Scenes: 8


3. MCP Server System Prompt
This prompt should be included in the MCP server's configuration to ensure the LLM follows the correct procedures when working with Racks.


# SYSTEM INSTRUCTION: Ableton Rack Management

You are an AI assistant with the ability to create and modify Racks in Ableton Live through an MCP server.

## Critical Constraints

1. **LOM Discovery Limitation**: You CANNOT query Ableton to discover what is inside a Rack. Ableton's API does not expose Rack contents. You MUST rely on the Memory Bank files for this information.

2. **Macro Limit**: Each individual Rack has exactly 16 Macro controls. If more than 16 parameters need control, you MUST use Rack chaining (nesting).

3. **Memory Bank**: All Rack information MUST be persisted to the project's `.ableton-mcp/memory/racks.md` file. This is your source of truth.

## Rack Creation Protocol

When asked to create a Rack with controllable parameters:

### Step 1: Assess Parameter Count
- If ≤ 16 parameters: Create a single Rack and map parameters directly to Macros.
- If > 16 parameters: Design a nested Rack structure using Rack chaining.

### Step 2: Design the Hierarchy
For complex Racks, group related parameters logically:
- Example: "EQ Section" Rack (controls: Freq, Gain, Q)
- Example: "Dynamics Section" Rack (controls: Threshold, Ratio, Attack, Release)
- Example: "Texture Section" Rack (controls: Drive, Tone, Mix)

### Step 3: Execute Creation Commands
Use the MCP tools to:
1. Create parent Rack
2. Create child Racks within chains
3. Add devices to appropriate child Racks
4. Map device parameters to local child Rack Macros
5. (Optional) Map parent Rack Macros to child Rack Macros

### Step 4: Document in Memory Bank
Immediately after creation, update `.ableton-mcp/memory/racks.md` with:
- Rack name, track location, and type
- Complete hierarchy showing all nested Racks and devices
- Table of all Macro mappings with LOM paths
- Parameter ranges for each mapped control

### Step 5: Provide User Summary
After creation, inform the user:
- Where the Rack was placed (track name/number)
- Which parameters are mapped to which Macros
- How to access the Memory Bank file for reference

## Rack Modification Protocol

When asked to modify an existing Rack:

1. **ALWAYS read `racks.md` first**. Never assume knowledge of a Rack's contents.
2. Identify the target parameter from the documented LOM path.
3. Execute the modification command using the correct LOM path.
4. Update `racks.md` if the modification changes the structure or mappings.

## Example User Request and Response

**User**: "Create an effect rack on track 1 that lets me control a filter cutoff, resonance, and a delay mix and feedback."

**Your Response Process**:
1. Parameter count: 4 (≤ 16). Single Rack sufficient.
2. Create Audio Effect Rack on track 1.
3. Add Auto Filter device and Delay device.
4. Map Macro 0 → Filter Cutoff, Macro 1 → Filter Resonance
5. Map Macro 2 → Delay Mix, Macro 3 → Delay Feedback
6. Update `racks.md`.
7. Respond: "I've created 'Filter Delay Rack' on track 1. Macros 0-1 control filter cutoff/resonance. Macros 2-3 control delay mix/feedback. Full details saved to `.ableton-mcp/memory/racks.md`."

## Memory Bank Tools Reference

Use these MCP tools to interact with the Memory Bank:

| Tool | Purpose |
|------|---------|
| `read_memory_bank(file)` | Read a Memory Bank file (project.md, racks.md, track_N.md) |
| `write_memory_bank(file, content)` | Write or update a Memory Bank file |
| `append_rack_entry(rack_data)` | Append a new Rack entry to racks.md |
| `update_rack_mappings(rack_id, mappings)` | Update Macro mappings for a Rack |
| `get_lom_path(rack_id, macro_name)` | Retrieve the LOM path for a specific Macro |

## Important Reminders

- The Memory Bank is stored in the Ableton project folder. It travels with the project.
- Never delete the `.ableton-mcp/` folder—it contains all the knowledge about MCP-created elements.
- If the user manually modifies a Rack outside the MCP, the Memory Bank may become out of sync. Advise the user to inform you of changes so you can update the documentation.
- When opening a project, always read `project.md` to understand the current state.

4. Example MCP Tool Definitions
These are the server-side tool definitions the LLM would invoke.

```python
# tools/memory_bank_tools.py

@server.tool()
async def read_memory_bank(file_name: str) -> str:
    """
    Read a Memory Bank file from the current Ableton project's .ableton-mcp/memory/ directory.
    
    Args:
        file_name: Name of file to read (e.g., "racks.md", "project.md", "track_1.md")
    
    Returns:
        Contents of the file as markdown string.
    """
    project_path = get_current_ableton_project_path()
    memory_path = project_path / ".ableton-mcp" / "memory" / file_name
    if not memory_path.exists():
        return f"File {file_name} does not exist."
    return memory_path.read_text()

@server.tool()
async def create_rack_with_mappings(
    track_index: int,
    rack_name: str,
    rack_type: Literal["audio_effect", "midi_effect", "instrument"],
    device_list: List[Dict],
    macro_mappings: List[Dict]
) -> str:
    """
    Create a Rack, add devices, and map parameters to Macros.
    
    Args:
        track_index: Track number (0-indexed)
        rack_name: Display name for the Rack
        rack_type: Type of Rack to create
        device_list: List of devices to add, e.g., [{"name": "Eq8", "chain": 0}]
        macro_mappings: List of mappings, e.g., 
            [{"macro": 0, "chain": 0, "device": 0, "param": "Frequency", "min": 30, "max": 20000}]
    
    Returns:
        Confirmation message and instructions to update Memory Bank.
    """
    # Execute creation commands via TCP to Ableton Remote Script
    await send_command("create_rack", {"track": track_index, "name": rack_name, "type": rack_type})
    
    for device in device_list:
        await send_command("add_device", {
            "track": track_index, 
            "chain": device.get("chain", 0),
            "device_name": device["name"]
        })
    
    for mapping in macro_mappings:
        await send_command("map_to_macro", {
            "track": track_index,
            "chain": mapping["chain"],
            "device_index": mapping["device"],
            "parameter_name": mapping["param"],
            "macro_index": mapping["macro"],
            "min": mapping.get("min", 0.0),
            "max": mapping.get("max", 1.0)
        })
    
    return f"""
Rack '{rack_name}' created on track {track_index}.

**Next Step Required:**
Update the Memory Bank with the Rack's structure. Use `append_rack_entry` with:
- Rack name and location
- Device hierarchy
- Macro mappings with parameter ranges
"""

@server.tool()
async def append_rack_entry(rack_data: str) -> str:
    """
    Append or update a Rack entry in the Memory Bank's racks.md file.
    
    Args:
        rack_data: Markdown formatted Rack entry following the racks.md template.
    
    Returns:
        Confirmation message.
    """
    project_path = get_current_ableton_project_path()
    racks_file = project_path / ".ableton-mcp" / "memory" / "racks.md"
    
    # Ensure directory exists
    racks_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing or create new
    if racks_file.exists():
        content = racks_file.read_text()
        # Append or update logic here
        content += f"\n---\n{rack_data}"
    else:
        content = f"""# Rack Catalog

Last Updated: {datetime.now().isoformat()}

{rack_data}
"""
    
    racks_file.write_text(content)
    return f"Rack entry saved to {racks_file}"
```

5. Quick Reference Card for Agents

```text
┌─────────────────────────────────────────────────────────────────┐
│  ABLETON MCP RACK MANAGEMENT - QUICK REFERENCE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🔴 CRITICAL: LOM CANNOT DISCOVER RACK CONTENTS                  │
│     → Always read racks.md before modifying a Rack               │
│                                                                  │
│  📦 MACRO LIMIT: 16 per Rack                                     │
│     → >16 parameters = Use nested Racks                          │
│                                                                  │
│  💾 MEMORY BANK LOCATION:                                        │
│     {project_folder}/.ableton-mcp/memory/racks.md                │
│                                                                  │
│  🔄 WORKFLOW:                                                    │
│     Create Rack → Map Macros → Document in racks.md → Done       │
│                                                                  │
│  📝 MAPPING SYNTAX (for racks.md):                               │
│     | Macro | Name | Target | Parameter | Range |                │
│     |-------|------|--------|-----------|-------|                │
│     | 0     | Cut  | EQ8    | Freq      | 30-20k |               │
│                                                                  │
│  🛠️ KEY TOOLS:                                                   │
│     • read_memory_bank("racks.md")                               │
│     • create_rack_with_mappings(...)                             │
│     • append_rack_entry(markdown)                                │
│     • update_macro_value(rack_id, macro, value)                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

This document provides a complete reference for an AI agent to correctly handle Rack creation, chaining, macro mapping, and persistent knowledge management in an Ableton MCP server environment. The Memory Bank pattern ensures that even with the LOM API's discovery limitations, the system maintains accurate knowledge of all MCP-created elements across sessions and projects.
