"""Browser discovery and drum-kit loading tools."""

from __future__ import absolute_import, print_function, unicode_literals

from fastmcp import FastMCP

from .. import _registry


def get_browser_tree(category_type: str = "all"):
    return _registry.invoke("get_browser_tree", {"category_type": category_type})


def get_browser_items_at_path(path: str = ""):
    return _registry.invoke("get_browser_items_at_path", {"path": path})


def search_browser(query: str, category: str = "all"):
    return _registry.invoke("search_browser", {"query": query, "category": category})


def load_drum_kit(track_index: int, rack_uri: str):
    return _registry.invoke("load_drum_kit", {"track_index": track_index, "rack_uri": rack_uri})


_TOOLS = (
    get_browser_tree,
    get_browser_items_at_path,
    search_browser,
    load_drum_kit,
)


def register(mcp: FastMCP) -> None:
    for fn in _TOOLS:
        _registry.ableton_tool(mcp, fn.__name__)(fn)
