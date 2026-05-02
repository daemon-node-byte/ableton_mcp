"""Memory Bank persistence tools."""

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from .. import _registry
from ._params import RackPath, TrackIndex


MemoryBankFileName = Annotated[
    str,
    Field(
        description=(
            "Memory Bank filename (e.g. 'racks.md', 'session.md'). "
            "Resolved relative to the current Live Set's project-root '.ableton-mcp/memory/' directory."
        ),
        min_length=1,
        max_length=200,
    ),
]
MemoryBankContent = Annotated[
    str,
    Field(description="Markdown content to write. Overwrites the target file in full."),
]
RackEntry = Annotated[
    str,
    Field(
        description=(
            "Rack-note record (markdown blob) appended to the project Memory Bank's racks.md inventory."
        ),
        min_length=1,
    ),
]


def read_memory_bank(file_name: MemoryBankFileName):
    return _registry.invoke("read_memory_bank", {"file_name": file_name})


def write_memory_bank(file_name: MemoryBankFileName, content: MemoryBankContent):
    return _registry.invoke(
        "write_memory_bank",
        {"file_name": file_name, "content": content},
    )


def append_rack_entry(rack_data: RackEntry):
    return _registry.invoke("append_rack_entry", {"rack_data": rack_data})


def get_system_owned_racks():
    return _registry.invoke("get_system_owned_racks", {})


def refresh_rack_memory_entry(track_index: TrackIndex, rack_path: RackPath):
    return _registry.invoke(
        "refresh_rack_memory_entry",
        {"track_index": track_index, "rack_path": rack_path},
    )


_TOOLS = (
    read_memory_bank,
    write_memory_bank,
    append_rack_entry,
    get_system_owned_racks,
    refresh_rack_memory_entry,
)


def register(mcp: FastMCP) -> None:
    for fn in _TOOLS:
        _registry.ableton_tool(mcp, fn.__name__)(fn)
