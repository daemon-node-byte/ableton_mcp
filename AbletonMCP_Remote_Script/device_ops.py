"""Device and parameter operations."""

from __future__ import absolute_import, print_function, unicode_literals

import re


PLUGIN_CLASS_NAMES = ("VstPlugInDevice", "Vst3PlugInDevice", "AuPlugInDevice")
NATIVE_DEVICE_NAME_ALIASES = {
    "eq8": "EQ Eight",
    "eq eight": "EQ Eight",
    "autofilter": "Auto Filter",
    "auto filter": "Auto Filter",
    "instrument rack": "Instrument Rack",
    "audio effect rack": "Audio Effect Rack",
}


class DeviceOpsMixin(object):
    """Device inspection and mutation commands."""

    def _canonical_native_device_name(self, device_name):
        normalized = str(device_name or "").strip()
        if not normalized:
            return normalized
        alias = NATIVE_DEVICE_NAME_ALIASES.get(normalized.lower())
        return alias or normalized

    def _device_is_rack(self, device):
        class_name = str(getattr(device, "class_name", "") or "")
        if getattr(device, "can_have_chains", False):
            return True
        if getattr(device, "can_have_drum_pads", False):
            return True
        return "Rack" in class_name or "GroupDevice" in class_name

    def _device_parameter_to_dict(self, parameter, index):
        parameter_data = {
            "index": index,
            "name": parameter.name,
            "value": round(float(parameter.value), 6),
            "min": float(parameter.min),
            "max": float(parameter.max),
            "display_value": str(parameter),
            "is_quantized": parameter.is_quantized,
            "is_enabled": parameter.is_enabled,
        }
        try:
            parameter_data["automation_state"] = parameter.automation_state
        except Exception:
            pass
        return parameter_data

    def _device_describe(self, device, index=None, path=None):
        device_data = {
            "name": device.name,
            "class_name": device.class_name,
            "type": device.type,
            "is_active": device.is_active,
            "num_parameters": len(device.parameters),
            "is_vst": device.class_name in ("VstPlugInDevice", "Vst3PlugInDevice"),
            "is_au": device.class_name == "AuPlugInDevice",
            "is_rack": self._device_is_rack(device),
        }
        if index is not None:
            device_data["index"] = index
        if path is not None:
            device_data["path"] = path
        try:
            device_data["class_display_name"] = device.class_display_name
        except Exception:
            pass
        return device_data

    def _device_parameters_payload(self, device):
        parameters = []
        for index, parameter in enumerate(device.parameters):
            parameters.append(self._device_parameter_to_dict(parameter, index))
        return {
            "device_name": device.name,
            "class_name": device.class_name,
            "is_vst": device.class_name in ("VstPlugInDevice", "Vst3PlugInDevice"),
            "is_au": device.class_name == "AuPlugInDevice",
            "parameter_count": len(parameters),
            "parameters": parameters,
            "note": (
                "For VST/AU plugins, parameters must first be Configured in Ableton "
                "(click Configure button on the device) to appear here."
            ) if device.class_name in PLUGIN_CLASS_NAMES else "",
        }

    def _device_find_parameter_by_name(self, device, name):
        exact_match = None
        casefold_match = None
        name_lower = str(name).lower()
        for index, parameter in enumerate(device.parameters):
            if parameter.name == name:
                exact_match = (index, parameter)
                break
            if casefold_match is None and parameter.name.lower() == name_lower:
                casefold_match = (index, parameter)
        if exact_match is not None:
            return exact_match
        if casefold_match is not None:
            return casefold_match

        eq8_match = self._device_find_eq8_parameter_alias(device, name)
        if eq8_match is not None:
            return eq8_match

        available = [parameter.name for parameter in device.parameters]
        raise ValueError(
            "Parameter '{}' not found in '{}'. Available: {}".format(
                name, device.name, available[:20]
            )
        )

    def _device_find_eq8_parameter_alias(self, device, name):
        class_name = str(getattr(device, "class_name", "") or "")
        if class_name.lower() != "eq8":
            return None
        match = re.match(r"^(?:(\d+)\s+)?(frequency|gain|q|resonance)\s+([ab])$", str(name).strip(), re.I)
        if not match:
            return None

        band_number = match.group(1) or "1"
        parameter_kind = match.group(2).lower()
        channel_name = match.group(3).upper()
        if parameter_kind == "q":
            parameter_kind = "resonance"
        candidate_name = "{} {} {}".format(
            band_number,
            parameter_kind.title(),
            channel_name,
        )
        for index, parameter in enumerate(device.parameters):
            if parameter.name.lower() == candidate_name.lower():
                return index, parameter
        return None

    def _device_set_parameter_value(self, parameter, value):
        if not parameter.is_enabled:
            raise ValueError("Parameter '{}' is not enabled".format(parameter.name))
        if not (parameter.min <= value <= parameter.max):
            raise ValueError(
                "Value {} out of range [{}, {}] for '{}'".format(
                    value, parameter.min, parameter.max, parameter.name
                )
            )
        parameter.value = value

    def _get_track_devices(self, params):
        track = self._get_track(params["track_index"])
        devices = []
        for index, device in enumerate(track.devices):
            devices.append(self._device_describe(device, index=index))
        return {"track_index": int(params["track_index"]), "devices": devices}

    def _get_device_parameters(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        return self._device_parameters_payload(device)

    def _set_device_parameter(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        parameter_index = int(params["parameter_index"])
        if parameter_index < 0 or parameter_index >= len(device.parameters):
            raise ValueError("Parameter index {} out of range".format(parameter_index))
        parameter = device.parameters[parameter_index]
        value = float(params["value"])
        self._device_set_parameter_value(parameter, value)
        return {
            "parameter_index": parameter_index,
            "name": parameter.name,
            "value": float(parameter.value),
            "display_value": str(parameter),
        }

    def _set_device_parameter_by_name(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        name = str(params["name"])
        value = float(params["value"])
        _, matched = self._device_find_parameter_by_name(device, name)
        self._device_set_parameter_value(matched, value)
        return {
            "name": matched.name,
            "value": float(matched.value),
            "display_value": str(matched),
        }

    def _get_device_parameter_by_name(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        name = str(params["name"])
        index, parameter = self._device_find_parameter_by_name(device, name)
        return self._device_parameter_to_dict(parameter, index)

    def _toggle_device(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        device.parameters[0].value = 0.0 if device.parameters[0].value > 0.5 else 1.0
        return {"is_active": device.is_active}

    def _set_device_enabled(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        enabled = bool(params["enabled"])
        device.parameters[0].value = 1.0 if enabled else 0.0
        return {"is_active": device.is_active}

    def _delete_device(self, params):
        track = self._get_track(params["track_index"])
        index = int(params["device_index"])
        track.delete_device(index)
        return {"ok": True, "deleted_index": index}

    def _move_device(self, params):
        track = self._get_track(params["track_index"])
        from_index = int(params["device_index"])
        to_index = int(params["new_index"])
        track.move_device(from_index, to_index)
        return {"ok": True, "new_index": to_index}

    def _show_plugin_window(self, params):
        """Best-effort only: this manipulates device-chain visibility, not true plugin UI."""
        device = self._get_device(params["track_index"], params["device_index"])
        self.song().view.select_device(device)
        if hasattr(device, "view"):
            device.view.is_collapsed = False
        return {
            "ok": True,
            "device_name": device.name,
            "mode": "device_view_collapse",
            "stability": "partial",
        }

    def _hide_plugin_window(self, params):
        """Best-effort only: this manipulates device-chain visibility, not true plugin UI."""
        device = self._get_device(params["track_index"], params["device_index"])
        if hasattr(device, "view"):
            device.view.is_collapsed = True
        return {
            "ok": True,
            "device_name": device.name,
            "mode": "device_view_collapse",
            "stability": "partial",
        }

    def _load_instrument_or_effect(self, params):
        track = self._get_track(params["track_index"])
        sources = []
        for field_name in ("device_name", "native_device_name", "uri"):
            field_value = str(params.get(field_name, "")).strip()
            if field_value:
                sources.append((field_name, field_value))
        if len(sources) != 1:
            raise ValueError(
                "load_instrument_or_effect requires exactly one of 'device_name', 'native_device_name', or 'uri'"
            )

        target_index = params.get("target_index")
        if target_index is not None:
            target_index = self._parse_non_negative_int(target_index, "target_index")

        source_name, source_value = sources[0]
        if source_name in ("device_name", "native_device_name"):
            device_name = self._canonical_native_device_name(source_value)
            if not hasattr(track, "insert_device"):
                raise ValueError("Track.insert_device is unavailable in this Live version")
            if target_index is not None and target_index > len(track.devices):
                raise ValueError(
                    "target_index {} out of range for track with {} devices".format(
                        target_index, len(track.devices)
                    )
                )
            previous_devices = list(track.devices)
            try:
                if target_index is None:
                    track.insert_device(device_name)
                else:
                    track.insert_device(device_name, target_index)
            except Exception as exc:
                raise ValueError("Failed to insert device '{}': {}".format(device_name, exc))
            result = self._build_track_load_result(
                track,
                previous_devices,
                mode="native_device_insert",
                track_index=params["track_index"],
                requested_name=device_name,
                target_index=target_index,
            )
            result["device_name"] = device_name
            return result

        if target_index is not None:
            raise ValueError("target_index is only supported with native device insertion")
        uri = source_value
        browser_item = self._resolve_browser_item_by_uri(uri, "load_instrument_or_effect")
        if not getattr(browser_item, "is_loadable", False):
            raise ValueError("load_instrument_or_effect requires a loadable browser item URI")
        result = self._load_browser_item_onto_track(
            track,
            browser_item,
            mode="browser_uri_load",
            track_index=params["track_index"],
            requested_uri=uri,
        )
        result["stability"] = "likely-complete"
        return result

    def _get_device_class_name(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        return {"class_name": device.class_name, "name": device.name}

    def _select_device(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        self.song().view.select_device(device)
        return {"ok": True, "device_name": device.name}

    def _get_selected_device(self):
        try:
            selected = self.song().view.selected_device
            if selected is None:
                return {"selected": False}
            for track_index, track in enumerate(self.song().tracks):
                for device_index, device in enumerate(track.devices):
                    if device == selected:
                        return {
                            "selected": True,
                            "track_index": track_index,
                            "device_index": device_index,
                            "name": device.name,
                            "class_name": device.class_name,
                        }
        except Exception as exc:
            return {"selected": False, "error": str(exc)}
        return {"selected": False}
