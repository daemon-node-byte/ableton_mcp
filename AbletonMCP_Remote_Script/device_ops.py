"""Device and parameter operations."""

from __future__ import absolute_import, print_function, unicode_literals


PLUGIN_CLASS_NAMES = ("VstPlugInDevice", "Vst3PlugInDevice", "AuPlugInDevice")


class DeviceOpsMixin(object):
    """Device inspection and mutation commands."""

    def _get_track_devices(self, params):
        track = self._get_track(params["track_index"])
        devices = []
        for index, device in enumerate(track.devices):
            device_data = {
                "index": index,
                "name": device.name,
                "class_name": device.class_name,
                "type": device.type,
                "is_active": device.is_active,
                "num_parameters": len(device.parameters),
                "is_vst": device.class_name in ("VstPlugInDevice", "Vst3PlugInDevice"),
                "is_au": device.class_name == "AuPlugInDevice",
                "is_rack": "Rack" in device.class_name,
            }
            try:
                device_data["class_display_name"] = device.class_display_name
            except Exception:
                pass
            devices.append(device_data)
        return {"track_index": int(params["track_index"]), "devices": devices}

    def _get_device_parameters(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        parameters = []
        for index, parameter in enumerate(device.parameters):
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
            parameters.append(parameter_data)
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

    def _set_device_parameter(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        parameter_index = int(params["parameter_index"])
        if parameter_index < 0 or parameter_index >= len(device.parameters):
            raise ValueError("Parameter index {} out of range".format(parameter_index))
        parameter = device.parameters[parameter_index]
        if not parameter.is_enabled:
            raise ValueError("Parameter '{}' is not enabled".format(parameter.name))
        value = float(params["value"])
        if not (parameter.min <= value <= parameter.max):
            raise ValueError(
                "Value {} out of range [{}, {}] for '{}'".format(
                    value, parameter.min, parameter.max, parameter.name
                )
            )
        parameter.value = value
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
        matched = None
        for parameter in device.parameters:
            if parameter.name == name:
                matched = parameter
                break
        if matched is None:
            name_lower = name.lower()
            for parameter in device.parameters:
                if parameter.name.lower() == name_lower:
                    matched = parameter
                    break
        if matched is None:
            available = [parameter.name for parameter in device.parameters]
            raise ValueError(
                "Parameter '{}' not found in '{}'. Available: {}".format(
                    name, device.name, available[:20]
                )
            )
        if not (matched.min <= value <= matched.max):
            raise ValueError(
                "Value {} out of range [{}, {}] for '{}'".format(
                    value, matched.min, matched.max, matched.name
                )
            )
        matched.value = value
        return {
            "name": matched.name,
            "value": float(matched.value),
            "display_value": str(matched),
        }

    def _get_device_parameter_by_name(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        name = str(params["name"])
        for index, parameter in enumerate(device.parameters):
            if parameter.name == name or parameter.name.lower() == name.lower():
                return {
                    "index": index,
                    "name": parameter.name,
                    "value": float(parameter.value),
                    "min": float(parameter.min),
                    "max": float(parameter.max),
                    "display_value": str(parameter),
                    "is_quantized": parameter.is_quantized,
                    "is_enabled": parameter.is_enabled,
                }
        raise ValueError("Parameter '{}' not found in '{}'".format(name, device.name))

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
        device_name = str(params.get("device_name", params.get("native_device_name", ""))).strip()
        target_index = params.get("target_index")
        if device_name:
            if not hasattr(track, "insert_device"):
                raise ValueError("Track.insert_device is unavailable in this Live version")
            if target_index is None:
                track.insert_device(device_name)
            else:
                track.insert_device(device_name, int(target_index))
            return {
                "ok": True,
                "mode": "native_device_insert",
                "device_name": device_name,
                "track_index": int(params["track_index"]),
                "target_index": target_index,
            }

        uri = str(params.get("uri", "")).strip()
        if not uri:
            raise ValueError("Must provide either 'device_name' for native devices or 'uri' for browser loading")
        browser = self.application().browser
        browser_item = browser.get_item_by_uri(uri) if hasattr(browser, "get_item_by_uri") else None
        if browser_item is None:
            raise ValueError("Browser item not found for URI: {}".format(uri))
        self.song().view.selected_track = track
        browser.load_item(browser_item)
        return {
            "ok": True,
            "mode": "browser_uri_load",
            "uri": uri,
            "track_index": int(params["track_index"]),
            "stability": "unverified",
        }

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
