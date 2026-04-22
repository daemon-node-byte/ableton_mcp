"""Memory Bank persistence tools."""

from __future__ import absolute_import, print_function, unicode_literals

from fastmcp import FastMCP

from .. import _registry


def read_memory_bank(file_name: str):
    return _registry.invoke("read_memory_bank", {"file_name": file_name})


def write_memory_bank(file_name: str, content: str):
    return _registry.invoke(
        "write_memory_bank",
        {"file_name": file_name, "content": content},
    )


def append_rack_entry(rack_data: str):
    return _registry.invoke("append_rack_entry", {"rack_data": rack_data})


def get_system_owned_racks():
    return _registry.invoke("get_system_owned_racks", {})


def refresh_rack_memory_entry(track_index: int, rack_path: str):
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
