"""Device inspection, parameter access, and loading tools."""

from __future__ import absolute_import, print_function, unicode_literals

from typing import Optional

from fastmcp import FastMCP

from .. import _registry


def get_track_devices(track_index: int):
    return _registry.invoke("get_track_devices", {"track_index": track_index})


def get_device_parameters(track_index: int, device_index: int):
    return _registry.invoke(
        "get_device_parameters",
        {"track_index": track_index, "device_index": device_index},
    )


def set_device_parameter_by_name(track_index: int, device_index: int, name: str, value: float):
    return _registry.invoke(
        "set_device_parameter_by_name",
        {"track_index": track_index, "device_index": device_index, "name": name, "value": value},
    )


def get_device_parameter_by_name(track_index: int, device_index: int, name: str):
    return _registry.invoke(
        "get_device_parameter_by_name",
        {"track_index": track_index, "device_index": device_index, "name": name},
    )


def get_device_parameters_at_path(track_index: int, device_path: str):
    return _registry.invoke(
        "get_device_parameters_at_path",
        {"track_index": track_index, "device_path": device_path},
    )


def set_device_parameter_at_path(
    track_index: int,
    device_path: str,
    parameter_index: int,
    value: float,
):
    return _registry.invoke(
        "set_device_parameter_at_path",
        {
            "track_index": track_index,
            "device_path": device_path,
            "parameter_index": parameter_index,
            "value": value,
        },
    )


def set_device_parameter_by_name_at_path(
    track_index: int,
    device_path: str,
    name: str,
    value: float,
):
    return _registry.invoke(
        "set_device_parameter_by_name_at_path",
        {"track_index": track_index, "device_path": device_path, "name": name, "value": value},
    )


def load_instrument_or_effect(
    track_index: int,
    device_name: Optional[str] = None,
    native_device_name: Optional[str] = None,
    uri: Optional[str] = None,
    target_index: Optional[int] = None,
):
    params = {"track_index": track_index}
    if device_name is not None:
        params["device_name"] = device_name
    if native_device_name is not None:
        params["native_device_name"] = native_device_name
    if uri is not None:
        params["uri"] = uri
    if target_index is not None:
        params["target_index"] = target_index
    return _registry.invoke("load_instrument_or_effect", params)


_TOOLS = (
    get_track_devices,
    get_device_parameters,
    set_device_parameter_by_name,
    get_device_parameter_by_name,
    get_device_parameters_at_path,
    set_device_parameter_at_path,
    set_device_parameter_by_name_at_path,
    load_instrument_or_effect,
)


def register(mcp: FastMCP) -> None:
    for fn in _TOOLS:
        _registry.ableton_tool(mcp, fn.__name__)(fn)
