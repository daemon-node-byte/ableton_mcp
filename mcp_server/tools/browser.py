"""Browser discovery and drum-kit loading tools."""

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from .. import _registry
from ._params import TrackIndex


_BROWSER_ROOTS = (
    "all",
    "instruments",
    "audio_effects",
    "midi_effects",
    "drums",
    "sounds",
    "samples",
    "packs",
    "user_library",
)
_BROWSER_ROOTS_LIST = ", ".join("'{}'".format(root) for root in _BROWSER_ROOTS)


CategoryType = Annotated[
    str,
    Field(
        default="all",
        description=(
            "Top-level browser category. One of: " + _BROWSER_ROOTS_LIST + "."
        ),
    ),
]
BrowserPath = Annotated[
    str,
    Field(
        default="",
        description=(
            "Slash-separated path under one of the normalized browser roots, "
            "e.g. 'instruments/Operator' or 'drums/Drum Rack'. Empty string returns the root listing."
        ),
    ),
]
BrowserQuery = Annotated[
    str,
    Field(description="Non-empty search string. Case-insensitive substring match.", min_length=1),
]
BrowserSearchCategory = Annotated[
    str,
    Field(
        default="all",
        description=(
            "Limit search to one root: " + _BROWSER_ROOTS_LIST + ". "
            "category='all' may time out on large libraries — prefer category-scoped searches."
        ),
    ),
]
RackUri = Annotated[
    str,
    Field(
        description=(
            "Browser URI for a Drum Rack preset (discovered via search_browser or get_browser_items_at_path). "
            "Generic 'Drum Rack' device entries are rejected."
        ),
        min_length=1,
    ),
]


def get_browser_tree(category_type: CategoryType = "all"):
    return _registry.invoke("get_browser_tree", {"category_type": category_type})


def get_browser_items_at_path(path: BrowserPath = ""):
    return _registry.invoke("get_browser_items_at_path", {"path": path})


def search_browser(query: BrowserQuery, category: BrowserSearchCategory = "all"):
    return _registry.invoke("search_browser", {"query": query, "category": category})


def load_drum_kit(track_index: TrackIndex, rack_uri: RackUri):
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
