# Ableton Live 12 Feasibility Spike, Steps 1 and 2

Status: concise archive
Date: 2026-04-09

## Why This Still Matters

This doc is the historical record of the arrangement feasibility spike.

It matters because arrangement control started as a research question and is now a validated project capability. The current setup, contracts, and validator commands live elsewhere:

- [install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md)
- [command-catalog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/command-catalog.md)

## What This Spike Was Testing

1. arrangement MIDI clip insertion
2. arrangement audio clip insertion

## What Was Proved

Arrangement MIDI flow:

- `create_arrangement_midi_clip` works on a MIDI track
- `add_notes_to_arrangement_clip` and `get_arrangement_clip_notes` round-trip correctly
- arrangement resize, move, and cleanup work in the validated slice

Arrangement audio flow:

- `create_arrangement_audio_clip` works with an absolute existing `file_path`
- `get_arrangement_clips` confirms placement
- `delete_arrangement_clip` cleans up correctly
- invalid file paths and wrong-track targets are rejected cleanly

Follow-on arrangement validation from later batches:

- `duplicate_to_arrangement` is now validated
- `move_arrangement_clip` is intentionally documented as MIDI-only

## What Remains Open

- undo behavior
- view and selection side effects
- overlap behavior on more complex timelines
- whether audio clip move should remain intentionally unsupported

## What This Means Now

Arrangement support in this repo is no longer just an ambitious idea.
It is a real, validated domain that should be preserved and improved carefully.

The next hard questions are narrower:

- deeper arrangement edge cases
- undo guarantees
- integration with broader device and browser workflows

## Related Docs

- [manual-validation-backlog.md](/Users/joshmclain/code/AbletonMCP_v2/docs/manual-validation-backlog.md)
- [install-and-use-mcp.md](/Users/joshmclain/code/AbletonMCP_v2/docs/install-and-use-mcp.md)
