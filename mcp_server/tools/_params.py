"""Shared Annotated parameter aliases for MCP tool signatures.

These reusable aliases pair common contracts (range, semantics) with the
descriptions agents see in tool schemas. Domain modules import them so the
rules captured in CLAUDE.md (volume clamps, beat times, return-track lookup,
etc.) are encoded once at the schema layer.
"""

import json
from typing import Annotated, Optional

from pydantic import BeforeValidator, Field


def _coerce_json(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


JsonCoerce = BeforeValidator(_coerce_json)


TrackIndex = Annotated[
    int,
    Field(description="0-based index of a regular track in the set's track list.", ge=0),
]
OptionalTrackInsertIndex = Annotated[
    Optional[int],
    Field(
        default=None,
        description="Optional 0-based insertion position. Omit (or pass null) to append at the end.",
        ge=0,
    ),
]
ReturnIndex = Annotated[
    int,
    Field(description="0-based index of a return track in the set's return list.", ge=0),
]
DeviceIndex = Annotated[
    int,
    Field(
        description=(
            "0-based index of a device in track.devices on the validated Python Remote Script surface. "
            "On that surface track.devices excludes the mixer device."
        ),
        ge=0,
    ),
]
ChainIndex = Annotated[
    int,
    Field(description="0-based index of a chain inside a rack device's chains list.", ge=0),
]
SlotIndex = Annotated[
    int,
    Field(description="0-based clip slot index in a track's clip_slots (Session View row).", ge=0),
]
LaneIndex = Annotated[
    int,
    Field(description="0-based take-lane index on the track.", ge=0),
]
ParameterIndex = Annotated[
    int,
    Field(description="0-based device parameter index.", ge=0),
]
MacroIndex = Annotated[
    int,
    Field(description="0-based rack macro index (typically 0..15 for stock racks).", ge=0),
]

DevicePath = Annotated[
    str,
    Field(
        description=(
            "Track-relative LOM-style device path, e.g. 'devices 0' for a top-level device, "
            "or 'devices 0 chains 1 devices 2' for a device nested inside a system-owned rack chain."
        ),
        min_length=1,
    ),
]
RackPath = Annotated[
    str,
    Field(
        description=(
            "Track-relative LOM-style path that points at a rack device, e.g. 'devices 0' or "
            "'devices 0 chains 1 devices 2'."
        ),
        min_length=1,
    ),
]
ChainPath = Annotated[
    str,
    Field(
        description=(
            "Track-relative LOM-style path that points at a rack chain, e.g. 'devices 0 chains 1' "
            "or 'devices 0 chains 1 devices 2 chains 0'."
        ),
        min_length=1,
    ),
]

NormalizedVolume = Annotated[
    float,
    Field(
        description="Volume in normalized mixer units (0.0..1.0; ~0.85 is 0 dB). Out-of-range values are clamped.",
        ge=0.0,
        le=1.0,
    ),
]
Pan = Annotated[
    float,
    Field(
        description="Pan from -1.0 (full left) to 1.0 (full right); 0.0 is center. Out-of-range values are clamped.",
        ge=-1.0,
        le=1.0,
    ),
]
SendIndex = Annotated[
    int,
    Field(description="0-based index of a send slot (matches the set's return-track ordering).", ge=0),
]
SendLevel = Annotated[
    float,
    Field(description="Send level in normalized units (0.0..1.0). Out-of-range values are clamped.", ge=0.0, le=1.0),
]
TrackColor = Annotated[
    int,
    Field(
        description=(
            "Live packed color integer (0xRRGGBB; 0..0xFFFFFF). "
            "Live snaps to the nearest chooser entry, so the read-back color may differ from the requested one."
        ),
        ge=0,
        le=0xFFFFFF,
    ),
]
TrackName = Annotated[
    str,
    Field(description="Track name (non-empty).", min_length=1, max_length=200),
]

BeatTime = Annotated[
    float,
    Field(description="Position in Arrangement beats (>= 0).", ge=0.0),
]
OptionalBeatTime = Annotated[
    Optional[float],
    Field(default=None, description="Position in Arrangement beats (>= 0).", ge=0.0),
]
BeatLength = Annotated[
    float,
    Field(description="Length in beats. Must be > 0.", gt=0.0),
]

MidiNote = Annotated[
    int,
    Field(description="MIDI note number (0..127; middle C = 60).", ge=0, le=127),
]

ParameterValue = Annotated[
    float,
    Field(description="Parameter value (passed through to Live; clamped per parameter's documented range)."),
]

Mute = Annotated[bool, Field(description="True to mute, False to unmute.")]
Solo = Annotated[bool, Field(description="True to solo, False to unsolo.")]
Arm = Annotated[bool, Field(description="True to arm for recording, False to disarm.")]


__all__ = [
    "Arm",
    "BeatLength",
    "BeatTime",
    "ChainIndex",
    "ChainPath",
    "DeviceIndex",
    "DevicePath",
    "JsonCoerce",
    "LaneIndex",
    "MacroIndex",
    "MidiNote",
    "Mute",
    "NormalizedVolume",
    "OptionalBeatTime",
    "OptionalTrackInsertIndex",
    "Pan",
    "ParameterIndex",
    "ParameterValue",
    "RackPath",
    "ReturnIndex",
    "SendIndex",
    "SendLevel",
    "SlotIndex",
    "Solo",
    "TrackColor",
    "TrackIndex",
    "TrackName",
]
