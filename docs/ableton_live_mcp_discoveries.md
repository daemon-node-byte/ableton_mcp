# Ableton Live 12 MCP Server Research and Development Plan

Status: updated draft
Date: 2026-04-09
Target: Python-first MCP server for Ableton Live 12 with deep session, arrangement, device, and plugin control

## Live validation update

Local Ableton Live 12 runtime validation on 2026-04-09 confirmed that the current TCP bridge and MCP-backed Remote Script can successfully perform all of the following against a real running set:

- `health_check`
- `get_session_info`
- `get_current_song_time`
- `get_all_track_names`
- `get_track_info`
- `create_midi_track` followed by `delete_track`
- `create_clip` followed by `delete_clip`
- `add_notes_to_clip` plus `get_clip_notes`
- `get_arrangement_clips`
- `create_arrangement_midi_clip`
- `create_arrangement_audio_clip`
- `delete_arrangement_clip`
- `resize_arrangement_clip`
- `move_arrangement_clip`
- `add_notes_to_arrangement_clip`
- `get_arrangement_clip_notes`
- `duplicate_to_arrangement`

The note-write and note-read paths required real bug fixes during validation:

- note creation needed to use the Live Python binding shape that accepts `MidiNoteSpecification` when available
- `get_notes_extended(...)` needed the Live argument order `from_pitch, pitch_span, from_time, time_span`

These are now fixed in the current codebase and reflected in the command registry as `confirmed` for the commands listed above.

Additional arrangement-specific validation notes from this pass:
- audio import was verified with the absolute path `/System/Library/Sounds/Funk.aiff`
- `move_arrangement_clip` is now intentionally documented as MIDI-only
- negative cases were verified for missing or relative `file_path`, nonexistent audio files, ambiguous selectors, and non-positive resize lengths
- undo behavior remains intentionally undocumented until it is directly validated

## Executive summary

The first-pass assumption that current Ableton MCP servers are mostly limited to session-view control turned out to be incomplete.

There are now several distinct approaches in the ecosystem:

1. Custom Python Remote Script + MCP server
2. AbletonOSC-based MCP servers
3. ableton-js based MCP servers with stronger Arrangement View coverage
4. Workflow-oriented servers that combine Live control with music-generation features

The important conclusion is this:

- A fully featured Ableton MCP server is technically plausible.
- Arrangement View operations are already demonstrated by at least one existing project built on `ableton-js`.
- Deep device parameter control is broadly achievable.
- Third-party plugin control is possible to a point, but it depends on how much of the plugin parameter surface Live exposes through the Live Object Model and whether the plugin supports stable automatable parameters.
- Browser-based loading of devices and plugins is often the weak point in OSC-based stacks unless the Remote Script is extended.

That means we should not design from the assumption that arrangement editing is impossible. Instead, we should design from the assumption that Live API coverage is broad, but bridge choice matters a lot.

## Projects discovered

### 1. `ahujasid/ableton-mcp`
Approach:
- Python MCP server
- Custom Ableton Remote Script
- JSON over TCP socket

Observed strengths:
- Clean architecture for MCP server <-> Remote Script communication
- Session info, track creation, clip creation, MIDI note insertion, browser traversal, tempo, transport
- Device and browser loading support through custom script, not limited to stock OSC endpoints

Observed limitations:
- Appears focused primarily on Session View workflows
- No strong evidence of full arrangement clip creation/manipulation
- Limited device hierarchy modeling in the exposed tool surface
- No clear access control, auth, rollback, or transaction model

Takeaway:
- Good reference for Python architecture and direct Live integration
- Good proof that a custom Remote Script can expose more than standard OSC bridges
- Not enough alone as the model for a fully featured server

### 2. `Simon-Kansara/ableton-live-mcp-server`
Approach:
- Python MCP server
- `python-osc`
- Built on top of `AbletonOSC`

Observed strengths:
- Exhaustively maps available AbletonOSC addresses to MCP tools
- Simpler architecture because it reuses a mature OSC control surface
- Good for broad protocol coverage where AbletonOSC already exposes functionality

Observed limitations:
- Constrained by what AbletonOSC exposes
- Browser loading and other advanced operations depend on custom OSC extensions
- Likely weaker for custom high-level workflows unless wrapped carefully

Takeaway:
- Good reference for broad tool generation from an existing OSC API
- Good for coverage and speed of implementation
- Not ideal if the goal is to own the full feature surface, especially advanced browser and deep custom workflows

### 3. `nozomi-koborinai/ableton-osc-mcp`
Approach:
- Go MCP server
- Uses stock `AbletonOSC`
- stdio MCP <-> UDP OSC <-> Live bridge

Observed strengths:
- Explicitly documents its limitations well
- Supports tempo, track creation, clip creation, note operations, device listing, firing clips, raw OSC messaging
- Useful as a reality check for what stock AbletonOSC gives you with minimal custom work

Observed limitations:
- Explicitly states that browser-based device loading is not supported by standard AbletonOSC
- Requires extending the Remote Script for `load_item()`-style browser loading
- Tool surface is narrower than a full production automation server

Takeaway:
- Helpful negative reference: shows where pure AbletonOSC starts to hit a ceiling
- Strong evidence that a fully featured server should not depend only on stock OSC endpoints

### 4. `uisato/ableton-mcp-extended`
Approach:
- Python MCP server
- Custom Remote Script
- Expanded workflow surface
- Includes some experimental UDP tooling for lower-latency control

Claimed strengths:
- Track management, scenes, clips, batch note edits, clip loop and follow actions
- Device parameter listing and batch parameter setting
- Browser navigation and loading by URI/path
- Audio import workflows
- Clip envelope and automation operations
- Mentions third-party VST support via Configure parameter flow
- Notes Arrangement View as a future area for fuller support

Observed caveats:
- Automation point placement is documented as imperfect
- Marketing language is stronger than the hard evidence available from surface docs
- Needs code review before trusting all claims as production-ready

Takeaway:
- Strong reference for feature ambition and tool taxonomy
- Good reference for batching, browser, audio import, and parameter workflows
- Less convincing as a proof of robust arrangement support

### 5. `FabianTinkl/AbletonMCP`
Approach:
- Python project
- Built around `AbletonOSC`
- Adds higher-level composition and genre workflow features

Observed strengths:
- More productized music-generation workflow
- Combines Live control with compositional logic, theory, and arrangement generation concepts
- Useful example of separating low-level Live control from high-level music tasks

Observed limitations:
- Focuses more on generative workflow than exhaustive DAW control
- Uses AbletonOSC, so likely inherits the same structural limitations for advanced unsupported actions

Takeaway:
- Good reference for workflow orchestration and high-level creative tools
- Not the right baseline for a control-complete server

### 6. `xiaolaa2/ableton-copilot-mcp`
Approach:
- MCP server built on `ableton-js`
- Node-based, not Python
- Emphasizes Arrangement View operations

Observed strengths:
- Strongest evidence discovered for arrangement-level control
- Claims support for:
  - creating empty MIDI clips in Arrangement View tracks
  - creating audio clips from sample file paths
  - duplicate/delete tracks
  - duplicate MIDI clips to specified tracks
  - note management in clips
  - recording track content based on time range
  - loading instruments, audio effects, and plugins
  - modifying device parameters
  - operation history and rollback support
- Tested on Live 12.1.10 according to the project docs

Observed limitations:
- Not Python-based
- Rollback currently appears partial, with note operations explicitly highlighted
- Warns that some direct manipulations may bypass normal Ableton undo expectations

Takeaway:
- This is the most important competitive reference found so far
- It directly proves that Arrangement View manipulation is not just theoretical
- We should study its capability model even if we do not copy its stack

### 7. `ideoforms/AbletonOSC`
This is not an MCP server, but it is a core dependency for multiple MCP servers.

Observed strengths:
- Very broad OSC API over Live
- Exposes track, clip, scene, device, parameter, and song operations
- Includes arrangement-related getters such as arrangement clip start times on tracks
- Mature and reused widely

Observed limitations:
- Its surface is still only what the OSC Remote Script authors chose to expose
- Advanced browser loading and some custom actions require extending the script
- It is a bridge layer, not a complete MCP product design

Takeaway:
- Still worth studying even if we do not build on OSC directly
- Useful as a capability catalog and fallback compatibility layer

## What the Ableton Live API suggests is possible

The Live Object Model documentation for Live 12.3.5 shows that the underlying API surface is broad enough for an ambitious server.

Important object classes visible in the Live Object Model include:
- `Song`
- `Song.View`
- `Track`
- `Track.View`
- `Clip`
- `Clip.View`
- `ClipSlot`
- `Scene`
- `CuePoint`
- `TakeLane`
- `Device`
- `PluginDevice`
- `RackDevice`
- `Chain`
- `DrumPad`
- `DeviceParameter`
- `MixerDevice`
- many specific native Ableton devices

This strongly suggests a ground-up server can expose more than basic clip launching.

### High-confidence capabilities

Based on current projects plus the Live Object Model structure, a Python MCP server should realistically be able to support:

#### Song and transport
- get/set tempo
- playback start/stop/continue
- loop ranges
- current arrangement position
- metronome and quantization settings
- cue points / locators
- view selection state

#### Track management
- create MIDI, audio, and return tracks
- delete, duplicate, rename tracks
- arm, solo, mute, volume, pan, sends
- group/fold state
- color and ordering
- routing inspection, possibly routing changes depending on API access details

#### Session View
- scene creation/deletion/launch
- clip slot creation
- clip creation and firing
- MIDI note insertion, deletion, replacement, quantization, transposition
- loop and launch settings
- follow actions where exposed

#### Arrangement View
- read arrangement clips on tracks
- likely create MIDI clips on arrangement tracks
- likely place audio clips onto arrangement timeline
- duplicate or move clips with appropriate API wrapper logic
- arrangement locators and time-range operations
- take lanes and comp-related workflows may be partially reachable

#### Devices and parameters
- enumerate device chains on tracks
- list parameters for devices
- set parameters, batch-set parameters
- navigate nested racks and chains if modeled carefully
- access mixer device and sends
- inspect automatable parameters

#### Native browser and loading
- browse categories and items
- load instruments/effects by URI/path if the bridge supports browser APIs
- import audio files to tracks or clip slots

#### Automation and envelopes
- write clip envelopes and automation points where API paths exist
- read automation/envelope state
- possibly arrangement automation, though this needs careful validation

## What is harder or uncertain

These areas are possible in principle or partially exposed, but require extra caution.

### 1. Third-party VST control, including Xfer Serum 2
This is feasible in a limited but useful sense.

What is likely possible:
- detect plugin device presence on a track
- enumerate automatable parameters exposed by Live for the plugin
- set those parameters by parameter id, index, or name
- batch-set macro or plugin parameters
- save known mappings for specific plugins like Serum 2

What is usually not guaranteed:
- direct access to the plugin's proprietary internal model beyond what Live exposes
- stable parameter naming/order across plugin versions and presets
- UI-level interactions inside the plugin window
- browser preset selection inside the plugin unless it is mapped to exposed parameters or automated externally

Practical implication for Serum 2:
- We should design a plugin adapter layer that works from Live-exposed parameter lists.
- For Serum 2 specifically, create a curated parameter map for commonly used controls, such as oscillators, filter cutoff, resonance, envelopes, LFO rates, FX macros, and macro controls, if they are exposed as automatable parameters in Live.
- We should not promise total deep editor control equivalent to scripting the Serum UI itself.

### 2. Browser loading of third-party plugins
This depends on bridge design.

- Stock AbletonOSC-based stacks often lack this unless extended.
- Custom Remote Script approaches can expose browser `load_item()` style functionality.
- A good architecture should separate "browser discovery" from "device insertion" so the implementation can evolve.

### 3. Undo and rollback
This matters a lot.

Existing projects show that some operations may bypass standard user expectations around undo.
For production use, we should not rely only on Ableton's own undo history. We should add:
- explicit operation journal
- preflight validation
- reversible action wrappers where possible
- snapshots for risky note and clip mutations

### 4. Realtime performance control
For live control of many parameters at high rate:
- stdio MCP is not enough by itself for smooth expressive control
- TCP command/response is fine for discrete actions
- high-frequency performance control may need a parallel UDP or OSC path, or a streaming layer

## Architectural options for a new Python server

### Option A. Build purely on AbletonOSC
Pros:
- Faster to start
- Broad existing command catalog
- Good compatibility and community familiarity

Cons:
- Hard ceiling for custom capabilities
- Browser/device insertion and deeper arrangement workflows may require patching the script anyway
- More awkward for rich typed abstractions

Recommendation:
- Not preferred as the only foundation

### Option B. Build a custom Python Remote Script and Python MCP server
Pros:
- Full control over protocol and exposed capabilities
- Best fit for a Python-first codebase
- Easier to model strongly typed high-level operations
- Best path for browser loading, device tree modeling, auth, and transaction support

Cons:
- More implementation work
- Must build and maintain your own coverage of Live APIs
- Live Remote Script development can be finicky

Recommendation:
- Best primary direction if Python is a hard requirement

### Option C. Hybrid architecture: custom Python MCP server plus multiple bridge backends
This is the most attractive architecture.

Design the MCP layer around capability interfaces, then support multiple bridge implementations:
- `custom_remote_script` backend for full-fidelity operations
- optional `abletonosc` backend for compatibility and rapid bring-up
- possibly future `ableton-js` inspired backend concepts, even if not directly reused

Pros:
- Lets us ship early with basic compatibility while building the richer backend
- Avoids locking the tool layer to one transport
- Supports testing and fallback

Cons:
- More design discipline required up front

Recommendation:
- Strongly recommended

## Recommended product direction

Build a Python MCP server with a custom Python Remote Script as the main backend, but architect it with backend abstraction from day one.

Reason:
- The fully featured goal depends on going beyond stock AbletonOSC limitations.
- Current evidence shows arrangement manipulation is possible.
- Python remains the preferred implementation language.
- A backend abstraction lets us adopt ideas from AbletonOSC and ableton-js without coupling to them.

## Recommended capability model

### Tier 1. Stable core
- song/session info
- transport
- track CRUD
- scene CRUD
- session clip CRUD
- MIDI note CRUD
- device enumeration
- parameter enumeration and set
- browser navigation
- native device/effect load

### Tier 2. Advanced composition and arrangement
- arrangement MIDI clip insertion
- arrangement audio clip insertion
- clip duplicate/move/split/consolidate style helpers where feasible
- locators/cue points
- time-range rendering/recording helpers
- automation and envelopes

### Tier 3. Power-user device and plugin workflows
- nested rack and chain traversal
- chain activation and chain selector control
- rack macro mapping inspection
- plugin parameter profile system
- Serum 2 adapter profile
- batch parameter scenes

### Tier 4. Safety and operability
- auth and local access control
- allowlist for plugin loading
- journaling and rollback
- dry-run mode for destructive edits
- audit logs
- structured errors and preflight validation

## Proposed Python code architecture

```text
ableton_live_mcp/
  server/
    app.py
    protocol/
      schemas.py
      errors.py
    tools/
      song.py
      transport.py
      tracks.py
      session_clips.py
      arrangement.py
      devices.py
      browser.py
      automation.py
      plugins.py
      safety.py
    services/
      command_router.py
      transaction_manager.py
      audit_log.py
      capability_registry.py
  backends/
    base.py
    custom_remote_script/
      client.py
      commands.py
      capabilities.py
    abletonosc/
      client.py
      mapper.py
      capabilities.py
  remote_script/
    AbletonMCP/
      __init__.py
      song_ops.py
      track_ops.py
      arrangement_ops.py
      device_ops.py
      browser_ops.py
      automation_ops.py
      plugin_ops.py
  plugin_profiles/
    serum2.yaml
  docs/
    research.md
    api-design.md
    tool-catalog.md
    implementation-plan.md
```

## Development priorities revised from the first draft

### Phase 0. Research and validation spike
Goal: validate the risky assumptions before committing to a full implementation.

Tasks:
1. Build a tiny experimental Python Remote Script that can:
   - enumerate tracks
   - enumerate arrangement clips on a track
   - create a MIDI clip in arrangement if available through the chosen API path
   - enumerate plugin parameters on a selected device
2. Test with Live 12 on macOS and Windows if possible
3. Test with a track containing Xfer Serum 2
4. Record:
   - parameter count
   - parameter naming stability
   - whether macros and plugin parameters are both visible
   - whether arrangement insertion is reliable

Deliverable:
- feasibility report with exact Live API operations confirmed in practice

### Phase 1. Core Python bridge
- command channel between MCP server and custom Remote Script
- typed request/response protocol
- session, transport, track, scene, session clip, note, device enumeration
- browser navigation and native device loading

### Phase 2. Arrangement control
- arrangement clip read/create/update/delete where feasible
- duplicate/move helpers
- locators / cue points
- timeline utilities
- arrangement-focused tests

### Phase 3. Device tree and plugin control
- nested rack traversal
- parameter introspection
- batch parameter setting
- plugin profile layer
- Serum 2 profile and curated aliases

### Phase 4. Safety layer
- access control model
- local auth token
- per-tool permission classes
- dry-run / preview mode
- transaction journal and rollback helpers

### Phase 5. Realtime extensions
- optional low-latency side channel for dense parameter automation
- throttling, smoothing, and burst batching

## Specific plan for Serum 2 support

We should treat Serum 2 support as a plugin-profile project, not a generic plugin magic feature.

### Objectives
- detect Serum 2 device instance on a track
- enumerate and cache exposed parameters
- normalize parameter identifiers to stable aliases
- expose musician-friendly tool names for common controls

### Example alias families
- `serum2.osc_a.level`
- `serum2.osc_a.wavetable_pos`
- `serum2.osc_b.level`
- `serum2.filter.cutoff`
- `serum2.filter.resonance`
- `serum2.env1.attack`
- `serum2.env1.decay`
- `serum2.lfo1.rate`
- `serum2.fx.reverb.mix`
- `serum2.macro1`

### Important caveat
This will only be as complete as the automatable parameters Live exposes for Serum 2. If a function is not exposed as a Live parameter, it should be marked unsupported rather than hacked around.

## Gaps in the current ecosystem our server should intentionally solve

1. Reliable Arrangement View editing in a Python-first stack
2. Deep nested device and rack introspection
3. Clear plugin parameter access model for third-party VSTs
4. Safety and rollback discipline
5. Better typed tool design instead of just thin endpoint wrappers
6. Better separation of low-level control from high-level music workflows

## Revised roadmap

### Weeks 1-2: feasibility spike
- prototype arrangement clip operations
- validate device parameter enumeration on native devices and Serum 2
- test browser loading paths
- define request/response schema

### Weeks 3-5: core backend and MCP tool layer
- implement custom Remote Script backend
- stable tool catalog for song, tracks, clips, notes, devices
- capability negotiation between MCP and backend

### Weeks 6-8: arrangement and automation
- arrangement clip operations
- locator support
- automation/envelope support
- operation journaling

### Weeks 9-10: plugins and racks
- nested rack traversal
- plugin parameter profiles
- Serum 2 support package
- plugin allowlist and access controls

### Weeks 11-12: production hardening
- test matrix for Live 12 versions
- dry-run and rollback improvements
- docs and examples
- release candidate

## Final recommendation

Do not build the new server as just another thin wrapper over stock AbletonOSC.

Instead:
- build a Python MCP server
- build a custom Python Remote Script backend for full control
- design the server with backend abstraction so OSC-style compatibility remains possible
- use `ableton-copilot-mcp` as the strongest reference for arrangement ambition
- use `ahujasid/ableton-mcp` and `uisato/ableton-mcp-extended` as references for Python-side architecture and tool breadth
- use `AbletonOSC` as a capability catalog and optional fallback bridge

This gives the best chance of delivering a Python-based Ableton Live 12 MCP server that is genuinely more complete than current offerings.

## Sources reviewed

- `ahujasid/ableton-mcp`
- `Simon-Kansara/ableton-live-mcp-server`
- `nozomi-koborinai/ableton-osc-mcp`
- `uisato/ableton-mcp-extended`
- `FabianTinkl/AbletonMCP`
- `xiaolaa2/ableton-copilot-mcp`
- `ideoforms/AbletonOSC`
- Cycling '74 Live Object Model documentation for Live 12.3.5

## Suggested next step

The next best move is not more broad research. It is a focused feasibility spike against Live 12:

1. arrangement MIDI clip insertion
2. arrangement audio clip insertion
3. nested device tree traversal
4. Serum 2 parameter discovery and alias mapping
5. browser loading of a native effect, native instrument, and a plugin if possible

That spike will answer the remaining hard questions faster than another documentation pass.
