"""Rack, chain, nested-path, and drum-rack operations."""

from __future__ import absolute_import, print_function, unicode_literals


RACK_NATIVE_NAMES = {
    "instrument": "Instrument Rack",
    "audio_effect": "Audio Effect Rack",
}

RACK_TYPE_LABELS = {
    1: "instrument",
    2: "audio_effect",
    4: "midi_effect",
}

TRACK_RELATIVE_SEGMENTS = ("devices", "chains", "return_chains")


class RackOpsMixin(object):
    """Rack and chain commands."""

    def _rack_device_type_name(self, device):
        if getattr(device, "can_have_drum_pads", False):
            return "drum_rack"
        return RACK_TYPE_LABELS.get(getattr(device, "type", None), "unknown")

    def _rack_describe_device(self, device, index=None, path=None):
        if hasattr(self, "_device_describe"):
            return self._device_describe(device, index=index, path=path)
        device_data = {
            "name": device.name,
            "class_name": device.class_name,
            "type": getattr(device, "type", 0),
            "is_active": getattr(device, "is_active", True),
            "num_parameters": len(getattr(device, "parameters", []) or []),
            "is_vst": getattr(device, "class_name", "") in ("VstPlugInDevice", "Vst3PlugInDevice"),
            "is_au": getattr(device, "class_name", "") == "AuPlugInDevice",
            "is_rack": bool(getattr(device, "can_have_chains", False) or getattr(device, "can_have_drum_pads", False)),
        }
        if index is not None:
            device_data["index"] = index
        if path is not None:
            device_data["path"] = path
        return device_data

    def _rack_device_is_rack(self, device):
        if hasattr(self, "_device_is_rack"):
            return self._device_is_rack(device)
        return bool(getattr(device, "can_have_chains", False) or getattr(device, "can_have_drum_pads", False))

    def _rack_validate_rack_device(self, device):
        can_have_chains = getattr(device, "can_have_chains", None)
        if can_have_chains is False or not hasattr(device, "chains"):
            raise ValueError("Device '{}' is not a rack".format(device.name))
        return device

    def _rack_validate_drum_rack_device(self, device):
        can_have_drum_pads = getattr(device, "can_have_drum_pads", None)
        if can_have_drum_pads is False or not hasattr(device, "drum_pads"):
            raise ValueError("Device '{}' is not a Drum Rack".format(device.name))
        return device

    def _rack_resolve_rack_device(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        return self._rack_validate_rack_device(device)

    def _rack_collect_macro_parameters(self, device):
        macros = []
        parameters = list(getattr(device, "parameters", []) or [])
        visible_macro_count = getattr(device, "visible_macro_count", None)
        for parameter_index, parameter in enumerate(parameters):
            parameter_name = str(getattr(parameter, "name", ""))
            if parameter_name.startswith("Macro") or (len(macros) < 8 and "Macro" in parameter_name):
                macros.append((len(macros), parameter_index, parameter))
        if visible_macro_count is not None:
            try:
                macros = macros[: int(visible_macro_count)]
            except Exception:
                pass
        return macros

    def _rack_join_path(self, base_path, segment_name, index):
        if base_path:
            return "{} {} {}".format(base_path, segment_name, int(index))
        return "{} {}".format(segment_name, int(index))

    def _rack_parse_track_relative_path(self, path, field_name):
        normalized = str(path or "").strip()
        if not normalized:
            raise ValueError("{} is required".format(field_name))
        parts = normalized.split()
        if len(parts) % 2 != 0:
            raise ValueError("Invalid LOM-style path '{}'".format(normalized))

        segments = []
        for offset in range(0, len(parts), 2):
            segment_name = parts[offset]
            if segment_name not in TRACK_RELATIVE_SEGMENTS:
                raise ValueError("Unsupported path segment '{}' in '{}'".format(segment_name, normalized))
            try:
                segment_index = self._parse_non_negative_int(parts[offset + 1], field_name)
            except ValueError:
                raise ValueError("Invalid LOM-style path '{}'".format(normalized))
            segments.append((segment_name, segment_index))
        return normalized, segments

    def _rack_list_child_objects(self, container, segment_name, context_path):
        if segment_name == "devices":
            if not hasattr(container, "devices"):
                raise ValueError("Path segment 'devices' is invalid at '{}'".format(context_path))
            return list(getattr(container, "devices", []) or []), "device"
        if segment_name == "chains":
            if not hasattr(container, "chains"):
                raise ValueError("Path segment 'chains' is invalid at '{}'".format(context_path))
            return list(getattr(container, "chains", []) or []), "chain"
        if segment_name == "return_chains":
            if not hasattr(container, "return_chains"):
                raise ValueError("Path segment 'return_chains' is invalid at '{}'".format(context_path))
            return list(getattr(container, "return_chains", []) or []), "chain"
        raise ValueError("Unsupported path segment '{}'".format(segment_name))

    def _rack_resolve_track_relative_path(self, track_index, path, field_name="path"):
        normalized, segments = self._rack_parse_track_relative_path(path, field_name)
        current = self._get_track(track_index)
        current_kind = "track"
        current_path = "track"

        for segment_name, segment_index in segments:
            children, child_kind = self._rack_list_child_objects(current, segment_name, current_path)
            if segment_index < 0 or segment_index >= len(children):
                raise ValueError(
                    "{} index {} out of range at '{}'".format(segment_name, segment_index, current_path)
                )
            current = children[segment_index]
            current_kind = child_kind
            current_path = self._rack_join_path("" if current_path == "track" else current_path, segment_name, segment_index)

        return {
            "object": current,
            "kind": current_kind,
            "path": normalized,
            "segments": segments,
        }

    def _rack_resolve_device_path(self, track_index, device_path, field_name="device_path"):
        resolved = self._rack_resolve_track_relative_path(track_index, device_path, field_name=field_name)
        if resolved["kind"] != "device":
            raise ValueError("{} '{}' does not resolve to a device".format(field_name, resolved["path"]))
        return resolved["object"], resolved["path"]

    def _rack_resolve_chain_path(self, track_index, chain_path, field_name="chain_path"):
        resolved = self._rack_resolve_track_relative_path(track_index, chain_path, field_name=field_name)
        if resolved["kind"] != "chain":
            raise ValueError("{} '{}' does not resolve to a chain".format(field_name, resolved["path"]))
        return resolved["object"], resolved["path"]

    def _rack_resolve_chain(self, params):
        device = self._rack_resolve_rack_device(params)
        chain_index = int(params["chain_index"])
        chains = list(getattr(device, "chains", []) or [])
        if chain_index < 0 or chain_index >= len(chains):
            raise ValueError("Chain index {} out of range".format(chain_index))
        return device, chains[chain_index]

    def _rack_resolve_drum_rack_device(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        return self._rack_validate_drum_rack_device(device)

    def _rack_find_drum_pad(self, device, target_note, require_top_level=False):
        pads = list(getattr(device, "drum_pads", []) or [])
        has_drum_pads = getattr(device, "has_drum_pads", None)
        if require_top_level and has_drum_pads is False and not pads:
            raise ValueError("Device '{}' has no drum pads; top-level Drum Rack required".format(device.name))
        for pad in pads:
            if int(getattr(pad, "note", -1)) == int(target_note):
                return pad
        raise ValueError("Drum pad with note {} not found".format(int(target_note)))

    def _rack_pad_effective_mute(self, pad):
        pad_mute = bool(getattr(pad, "mute", False))
        pad_chains = list(getattr(pad, "chains", []) or [])
        if pad_mute:
            return True
        if pad_chains and all(bool(getattr(chain, "mute", False)) for chain in pad_chains):
            return True
        return False

    def _rack_pad_effective_solo(self, pad):
        pad_solo = bool(getattr(pad, "solo", False))
        pad_chains = list(getattr(pad, "chains", []) or [])
        if pad_solo:
            return True
        if pad_chains and any(bool(getattr(chain, "solo", False)) for chain in pad_chains):
            return True
        return False

    def _rack_visible_macro_count(self, device, macros):
        visible_macro_count = getattr(device, "visible_macro_count", None)
        if visible_macro_count is None:
            return len(macros)
        try:
            return int(visible_macro_count)
        except Exception:
            return len(macros)

    def _rack_macro_to_dict(self, macro_index, parameter_index, parameter):
        return {
            "index": macro_index,
            "parameter_index": parameter_index,
            "name": parameter.name,
            "value": round(float(parameter.value), 4),
            "min": float(parameter.min),
            "max": float(parameter.max),
            "display_value": str(parameter),
        }

    def _rack_serialize_chain_state(self, chain, index, path):
        devices = []
        for device_index, chain_device in enumerate(list(getattr(chain, "devices", []) or [])):
            devices.append(
                self._rack_describe_device(
                    chain_device,
                    index=device_index,
                    path=self._rack_join_path(path, "devices", device_index),
                )
            )
        return {
            "index": index,
            "path": path,
            "name": chain.name,
            "mute": chain.mute,
            "solo": chain.solo if hasattr(chain, "solo") else False,
            "volume": round(chain.mixer_device.volume.value, 4) if hasattr(chain, "mixer_device") else 1.0,
            "pan": round(chain.mixer_device.panning.value, 4) if hasattr(chain, "mixer_device") else 0.0,
            "num_devices": len(devices),
            "devices": [device["name"] for device in devices],
            "device_details": devices,
        }

    def _rack_serialize_device_tree(self, device, path):
        device_payload = self._rack_describe_device(device, path=path)
        device_payload["parameters"] = []
        macros = self._rack_collect_macro_parameters(device)
        if macros:
            device_payload["macros"] = [
                self._rack_macro_to_dict(macro_index, parameter_index, parameter)
                for macro_index, parameter_index, parameter in macros
            ]
        if self._rack_device_is_rack(device):
            rack_device = self._rack_validate_rack_device(device)
            device_payload["rack_type"] = self._rack_device_type_name(rack_device)
            device_payload["visible_macro_count"] = self._rack_visible_macro_count(rack_device, macros)
            device_payload["has_macro_mappings"] = bool(
                getattr(rack_device, "has_macro_mappings", bool(device_payload.get("macros")))
            )
            device_payload["chains"] = []
            for chain_index, chain in enumerate(list(getattr(rack_device, "chains", []) or [])):
                chain_path = self._rack_join_path(path, "chains", chain_index)
                device_payload["chains"].append(self._rack_serialize_chain_tree(chain, chain_index, chain_path))
            device_payload["return_chains"] = []
            for chain_index, chain in enumerate(list(getattr(rack_device, "return_chains", []) or [])):
                chain_path = self._rack_join_path(path, "return_chains", chain_index)
                device_payload["return_chains"].append(
                    self._rack_serialize_chain_tree(chain, chain_index, chain_path)
                )
        return device_payload

    def _rack_serialize_chain_tree(self, chain, index, path):
        chain_payload = {
            "index": index,
            "path": path,
            "name": chain.name,
            "mute": bool(getattr(chain, "mute", False)),
            "solo": bool(getattr(chain, "solo", False)),
            "volume": round(chain.mixer_device.volume.value, 4) if hasattr(chain, "mixer_device") else 1.0,
            "pan": round(chain.mixer_device.panning.value, 4) if hasattr(chain, "mixer_device") else 0.0,
            "devices": [],
        }
        for device_index, chain_device in enumerate(list(getattr(chain, "devices", []) or [])):
            device_path = self._rack_join_path(path, "devices", device_index)
            chain_payload["devices"].append(self._rack_serialize_device_tree(chain_device, device_path))
        return chain_payload

    def _rack_reject_unsupported_mapping_fields(self, value):
        unsupported_fields = ("macro_mappings", "macro_to_macro_mappings", "map_to_macro", "map_macro_to_macro")
        if isinstance(value, dict):
            for key, child_value in value.items():
                if key in unsupported_fields:
                    raise ValueError(
                        "Native macro mapping is not confirmed in this repo yet; '{}' is unsupported".format(key)
                    )
                self._rack_reject_unsupported_mapping_fields(child_value)
        elif isinstance(value, list):
            for child_value in value:
                self._rack_reject_unsupported_mapping_fields(child_value)

    def _rack_validate_blueprint(self, blueprint, require_track_index):
        if not isinstance(blueprint, dict):
            raise ValueError("blueprint must be an object")
        self._rack_reject_unsupported_mapping_fields(blueprint)
        if require_track_index and "track_index" not in blueprint:
            raise ValueError("blueprint.track_index is required")
        if "rack_type" not in blueprint:
            raise ValueError("blueprint.rack_type is required")
        if "rack_name" not in blueprint:
            raise ValueError("blueprint.rack_name is required")
        chains = blueprint.get("chains")
        if not isinstance(chains, list) or not chains:
            raise ValueError("blueprint.chains must be a non-empty list")

        for chain in chains:
            if not isinstance(chain, dict):
                raise ValueError("Each chain blueprint must be an object")
            if "name" not in chain:
                raise ValueError("Each chain blueprint requires 'name'")
            devices = chain.get("devices", [])
            if not isinstance(devices, list):
                raise ValueError("Chain '{}' devices must be a list".format(chain["name"]))
            for device_spec in devices:
                if not isinstance(device_spec, dict):
                    raise ValueError("Each device blueprint must be an object")
                has_native_device = "native_device_name" in device_spec
                has_nested_rack = "rack" in device_spec
                if has_native_device == has_nested_rack:
                    raise ValueError(
                        "Each device blueprint must define exactly one of 'native_device_name' or 'rack'"
                    )
                if has_native_device:
                    parameter_values = device_spec.get("parameter_values", {})
                    if not isinstance(parameter_values, dict):
                        raise ValueError("parameter_values must be an object when provided")
                if has_nested_rack:
                    nested_blueprint = dict(device_spec["rack"])
                    self._rack_validate_blueprint(nested_blueprint, require_track_index=False)

    def _rack_require_saved_session_for_system_write(self):
        if hasattr(self, "_memory_require_saved_session_path"):
            self._memory_require_saved_session_path()

    def _rack_register_system_owned_rack(self, track_index, rack_path, rack_type, blueprint=None, macro_labels=None):
        if hasattr(self, "_memory_register_system_owned_rack"):
            return self._memory_register_system_owned_rack(
                track_index,
                rack_path,
                rack_type,
                blueprint=blueprint,
                macro_labels=macro_labels,
            )
        return None

    def _rack_refresh_related_memory_entries(self, track_index, changed_path):
        if hasattr(self, "_memory_refresh_related_rack_entries"):
            self._memory_refresh_related_rack_entries(track_index, changed_path)

    def _rack_lookup_system_owned_entry(self, track_index, rack_path):
        if hasattr(self, "_memory_find_rack_entry_by_path"):
            return self._memory_find_rack_entry_by_path(track_index, rack_path)
        return None

    def _rack_create_native_rack(self, params):
        track_index = int(params["track_index"])
        rack_type = str(params["rack_type"]).strip().lower()
        native_name = RACK_NATIVE_NAMES.get(rack_type)
        if native_name is None:
            raise ValueError("Unsupported rack_type '{}'; expected instrument or audio_effect".format(rack_type))
        if hasattr(self, "_canonical_native_device_name"):
            native_name = self._canonical_native_device_name(native_name)

        track = self._get_track(track_index)
        target_path = str(params.get("target_path", "") or "").strip()
        if target_path:
            target_chain, resolved_chain_path = self._rack_resolve_chain_path(track_index, target_path, "target_path")
            if not hasattr(target_chain, "insert_device"):
                raise ValueError("Chain '{}' does not support device insertion".format(target_chain.name))
            previous_count = len(list(getattr(target_chain, "devices", []) or []))
            try:
                target_chain.insert_device(native_name)
            except Exception as exc:
                raise ValueError("Failed to insert device '{}': {}".format(native_name, exc))
            device_index = len(list(getattr(target_chain, "devices", []) or [])) - 1
            if device_index < previous_count:
                device_index = previous_count
            device = list(getattr(target_chain, "devices", []) or [])[device_index]
            rack_path = self._rack_join_path(resolved_chain_path, "devices", device_index)
        else:
            if not hasattr(track, "insert_device"):
                raise ValueError("Track '{}' does not support device insertion".format(track.name))
            try:
                track.insert_device(native_name)
            except Exception as exc:
                raise ValueError("Failed to insert device '{}': {}".format(native_name, exc))
            device_index = len(track.devices) - 1
            device = track.devices[device_index]
            rack_path = "devices {}".format(device_index)

        device.name = str(params["name"])
        self._rack_validate_rack_device(device)
        return {
            "track_index": track_index,
            "rack_type": rack_type,
            "rack_path": rack_path,
            "device_index": device_index,
            "device": device,
            "target_path": target_path,
        }

    def _get_rack_chains(self, params):
        device = self._rack_resolve_rack_device(params)
        chains = []
        for index, chain in enumerate(list(getattr(device, "chains", []) or [])):
            chains.append(self._rack_serialize_chain_state(chain, index, "chains {}".format(index)))
        return {"rack_name": device.name, "chains": chains}

    def _get_rack_macros(self, params):
        device = self._rack_resolve_rack_device(params)
        macros = []
        for macro_index, parameter_index, parameter in self._rack_collect_macro_parameters(device):
            macros.append(self._rack_macro_to_dict(macro_index, parameter_index, parameter))
        return {"rack_name": device.name, "macros": macros}

    def _set_rack_macro(self, params):
        device = self._rack_resolve_rack_device(params)
        macro_index = int(params["macro_index"])
        value = float(params["value"])
        macros = self._rack_collect_macro_parameters(device)
        if macro_index < 0 or macro_index >= len(macros):
            raise ValueError("Macro index {} out of range".format(macro_index))
        _, parameter_index, parameter = macros[macro_index]
        parameter.value = max(parameter.min, min(parameter.max, value))
        return {
            "index": macro_index,
            "parameter_index": parameter_index,
            "name": parameter.name,
            "value": float(parameter.value),
        }

    def _get_chain_devices(self, params):
        _, chain = self._rack_resolve_chain(params)
        devices = []
        for index, chain_device in enumerate(list(getattr(chain, "devices", []) or [])):
            devices.append(self._rack_describe_device(chain_device, index=index))
        return {"chain_name": chain.name, "devices": devices}

    def _set_chain_mute(self, params):
        _, chain = self._rack_resolve_chain(params)
        chain.mute = bool(params["mute"])
        return {"mute": chain.mute}

    def _set_chain_solo(self, params):
        _, chain = self._rack_resolve_chain(params)
        chain.solo = bool(params["solo"])
        return {"solo": chain.solo}

    def _set_chain_volume(self, params):
        _, chain = self._rack_resolve_chain(params)
        if not hasattr(chain, "mixer_device") or not hasattr(chain.mixer_device, "volume"):
            raise ValueError("Chain '{}' does not expose mixer volume".format(chain.name))
        value = max(0.0, min(1.0, float(params["volume"])))
        chain.mixer_device.volume.value = value
        return {"volume": chain.mixer_device.volume.value}

    def _get_drum_rack_pads(self, params):
        device = self._rack_resolve_drum_rack_device(params)
        pads = []
        for pad in list(getattr(device, "drum_pads", []) or []):
            pad_chains = list(getattr(pad, "chains", []) or [])
            pad_info = {
                "note": pad.note,
                "name": pad.name,
                "mute": self._rack_pad_effective_mute(pad),
                "solo": self._rack_pad_effective_solo(pad),
                "num_chains": len(pad_chains),
            }
            if pad_chains:
                chain_devices = []
                chain_input_notes = []
                for chain in pad_chains:
                    chain_info = {
                        "chain": chain.name,
                        "devices": [chain_device.name for chain_device in chain.devices],
                    }
                    if hasattr(chain, "in_note"):
                        chain_info["in_note"] = int(chain.in_note)
                        chain_input_notes.append(int(chain.in_note))
                    if hasattr(chain, "out_note"):
                        chain_info["out_note"] = int(chain.out_note)
                    if hasattr(chain, "choke_group"):
                        chain_info["choke_group"] = int(chain.choke_group)
                    chain_devices.append(chain_info)
                pad_info["chain_devices"] = chain_devices
                if chain_input_notes:
                    pad_info["chain_input_notes"] = chain_input_notes
                    if len(set(chain_input_notes)) == 1:
                        pad_info["effective_note"] = chain_input_notes[0]
            pads.append(pad_info)
        return {
            "drum_pads": pads,
            "count": len(pads),
            "has_drum_pads": bool(getattr(device, "has_drum_pads", len(pads) > 0)),
        }

    def _set_drum_rack_pad_note(self, params):
        device = self._rack_resolve_drum_rack_device(params)
        target_note = int(params["note"])
        new_note = int(params["new_note"])
        pad = self._rack_find_drum_pad(device, target_note, require_top_level=True)
        pad_chains = list(getattr(pad, "chains", []) or [])
        if not pad_chains:
            raise ValueError("Drum pad note remap requires a pad with at least one chain")
        for chain in pad_chains:
            if not hasattr(chain, "in_note"):
                raise ValueError("set_drum_rack_pad_note requires Live 12.3+ DrumChain.in_note support")

        for chain in pad_chains:
            chain.in_note = new_note
        return {
            "note": new_note,
            "mode": "drum_chain_in_note",
            "updated_chains": len(pad_chains),
        }

    def _set_drum_rack_pad_mute(self, params):
        device = self._rack_resolve_drum_rack_device(params)
        target_note = int(params["note"])
        pad = self._rack_find_drum_pad(device, target_note)
        desired_mute = bool(params["mute"])
        pad.mute = desired_mute
        if self._rack_pad_effective_mute(pad) != desired_mute:
            for chain in list(getattr(pad, "chains", []) or []):
                if hasattr(chain, "mute"):
                    chain.mute = desired_mute
        return {"note": target_note, "mute": self._rack_pad_effective_mute(pad)}

    def _set_drum_rack_pad_solo(self, params):
        device = self._rack_resolve_drum_rack_device(params)
        target_note = int(params["note"])
        pad = self._rack_find_drum_pad(device, target_note)
        desired_solo = bool(params["solo"])
        pad.solo = desired_solo
        if self._rack_pad_effective_solo(pad) != desired_solo:
            for chain in list(getattr(pad, "chains", []) or []):
                if hasattr(chain, "solo"):
                    chain.solo = desired_solo
        return {"note": target_note, "solo": self._rack_pad_effective_solo(pad)}

    def _create_rack(self, params):
        self._rack_require_saved_session_for_system_write()
        creation = self._rack_create_native_rack(params)
        rack_id = self._rack_register_system_owned_rack(
            creation["track_index"],
            creation["rack_path"],
            creation["rack_type"],
            blueprint=params.get("blueprint"),
            macro_labels=params.get("macro_labels"),
        )
        self._rack_refresh_related_memory_entries(creation["track_index"], creation["rack_path"])
        return {
            "rack_id": rack_id,
            "track_index": creation["track_index"],
            "rack_type": creation["rack_type"],
            "name": creation["device"].name,
            "rack_path": creation["rack_path"],
            "device_index": creation["device_index"],
        }

    def _insert_rack_chain(self, params):
        self._rack_require_saved_session_for_system_write()
        track_index = int(params["track_index"])
        rack_device, rack_path = self._rack_resolve_device_path(track_index, params["rack_path"], "rack_path")
        rack_device = self._rack_validate_rack_device(rack_device)
        chain_name = str(params["name"])
        chain_index = params.get("index")
        if chain_index is not None:
            chain_index = self._parse_non_negative_int(chain_index, "index")
        chains_before = list(getattr(rack_device, "chains", []) or [])
        if chain_index is not None and chain_index > len(chains_before):
            raise ValueError("Chain index {} out of range".format(chain_index))
        if not hasattr(rack_device, "insert_chain"):
            raise ValueError("Rack '{}' does not support chain insertion".format(rack_device.name))
        try:
            if chain_index is None:
                rack_device.insert_chain()
            else:
                rack_device.insert_chain(chain_index)
        except Exception as exc:
            raise ValueError("Failed to insert chain into '{}': {}".format(rack_device.name, exc))

        chains_after = list(getattr(rack_device, "chains", []) or [])
        if not chains_after:
            raise ValueError("Rack '{}' did not expose any chains after insertion".format(rack_device.name))
        if chain_index is None:
            chain_index = len(chains_after) - 1
        chain = chains_after[chain_index]
        chain.name = chain_name
        chain_path = self._rack_join_path(rack_path, "chains", chain_index)
        self._rack_refresh_related_memory_entries(track_index, chain_path)
        return {
            "track_index": track_index,
            "rack_path": rack_path,
            "chain_index": chain_index,
            "chain_path": chain_path,
            "name": chain.name,
        }

    def _insert_device_in_chain(self, params):
        self._rack_require_saved_session_for_system_write()
        track_index = int(params["track_index"])
        chain, chain_path = self._rack_resolve_chain_path(track_index, params["chain_path"], "chain_path")
        native_device_name = str(params["native_device_name"]).strip()
        if not native_device_name:
            raise ValueError("native_device_name is required")
        if hasattr(self, "_canonical_native_device_name"):
            native_device_name = self._canonical_native_device_name(native_device_name)
        target_index = params.get("target_index")
        if target_index is not None:
            target_index = self._parse_non_negative_int(target_index, "target_index")
        devices_before = list(getattr(chain, "devices", []) or [])
        if target_index is not None and target_index > len(devices_before):
            raise ValueError("target_index {} out of range".format(target_index))
        if not hasattr(chain, "insert_device"):
            raise ValueError("Chain '{}' does not support device insertion".format(chain.name))
        try:
            if target_index is None:
                chain.insert_device(native_device_name)
            else:
                chain.insert_device(native_device_name, target_index)
        except Exception as exc:
            raise ValueError("Failed to insert device '{}': {}".format(native_device_name, exc))

        devices_after = list(getattr(chain, "devices", []) or [])
        if not devices_after:
            raise ValueError("Chain '{}' did not expose any devices after insertion".format(chain.name))
        device_index = target_index if target_index is not None else len(devices_after) - 1
        device = devices_after[device_index]
        device_name = str(params.get("device_name", "") or "").strip()
        if device_name:
            device.name = device_name
        device_path = self._rack_join_path(chain_path, "devices", device_index)
        self._rack_refresh_related_memory_entries(track_index, device_path)
        result = self._rack_describe_device(device, index=device_index, path=device_path)
        result["track_index"] = track_index
        result["chain_path"] = chain_path
        result["device_path"] = device_path
        return result

    def _get_rack_structure(self, params):
        track_index = int(params["track_index"])
        rack_device, rack_path = self._rack_resolve_device_path(track_index, params["rack_path"], "rack_path")
        rack_device = self._rack_validate_rack_device(rack_device)
        structure = self._rack_serialize_device_tree(rack_device, rack_path)
        result = {"track_index": track_index, "rack_path": rack_path, "rack": structure}
        entry = self._rack_lookup_system_owned_entry(track_index, rack_path)
        if entry is not None:
            result["rack_id"] = entry["rack_id"]
        return result

    def _get_device_parameters_at_path(self, params):
        track_index = int(params["track_index"])
        device, device_path = self._rack_resolve_device_path(track_index, params["device_path"], "device_path")
        payload = self._device_parameters_payload(device)
        payload["track_index"] = track_index
        payload["device_path"] = device_path
        return payload

    def _set_device_parameter_at_path(self, params):
        track_index = int(params["track_index"])
        device, device_path = self._rack_resolve_device_path(track_index, params["device_path"], "device_path")
        parameter_index = int(params["parameter_index"])
        if parameter_index < 0 or parameter_index >= len(device.parameters):
            raise ValueError("Parameter index {} out of range".format(parameter_index))
        parameter = device.parameters[parameter_index]
        value = float(params["value"])
        self._device_set_parameter_value(parameter, value)
        self._rack_refresh_related_memory_entries(track_index, device_path)
        return {
            "track_index": track_index,
            "device_path": device_path,
            "parameter_index": parameter_index,
            "name": parameter.name,
            "value": float(parameter.value),
            "display_value": str(parameter),
        }

    def _set_device_parameter_by_name_at_path(self, params):
        track_index = int(params["track_index"])
        device, device_path = self._rack_resolve_device_path(track_index, params["device_path"], "device_path")
        parameter_name = str(params["name"])
        value = float(params["value"])
        parameter_index, parameter = self._device_find_parameter_by_name(device, parameter_name)
        self._device_set_parameter_value(parameter, value)
        self._rack_refresh_related_memory_entries(track_index, device_path)
        return {
            "track_index": track_index,
            "device_path": device_path,
            "parameter_index": parameter_index,
            "name": parameter.name,
            "value": float(parameter.value),
            "display_value": str(parameter),
        }

    def _apply_rack_blueprint_to_rack(self, track_index, rack_path, blueprint, stats):
        for chain_blueprint in blueprint["chains"]:
            chain_result = self._insert_rack_chain(
                {
                    "track_index": track_index,
                    "rack_path": rack_path,
                    "name": chain_blueprint["name"],
                }
            )
            chain_path = chain_result["chain_path"]
            stats["created_chains"] += 1

            for device_blueprint in chain_blueprint.get("devices", []):
                if "native_device_name" in device_blueprint:
                    device_result = self._insert_device_in_chain(
                        {
                            "track_index": track_index,
                            "chain_path": chain_path,
                            "native_device_name": device_blueprint["native_device_name"],
                            "device_name": device_blueprint.get("device_name"),
                        }
                    )
                    stats["created_devices"] += 1
                    for parameter_name, parameter_value in sorted(
                        dict(device_blueprint.get("parameter_values", {})).items()
                    ):
                        self._set_device_parameter_by_name_at_path(
                            {
                                "track_index": track_index,
                                "device_path": device_result["device_path"],
                                "name": parameter_name,
                                "value": parameter_value,
                            }
                        )
                    continue

                nested_blueprint = dict(device_blueprint["rack"])
                nested_blueprint.setdefault("track_index", track_index)
                nested_result = self._create_rack(
                    {
                        "track_index": track_index,
                        "rack_type": nested_blueprint["rack_type"],
                        "name": nested_blueprint["rack_name"],
                        "target_path": chain_path,
                        "blueprint": nested_blueprint,
                        "macro_labels": nested_blueprint.get("macro_labels"),
                    }
                )
                stats["created_racks"] += 1
                self._apply_rack_blueprint_to_rack(
                    track_index,
                    nested_result["rack_path"],
                    nested_blueprint,
                    stats,
                )

    def _apply_rack_blueprint(self, params):
        self._rack_require_saved_session_for_system_write()
        blueprint = params.get("blueprint")
        self._rack_validate_blueprint(blueprint, require_track_index=True)
        track_index = int(blueprint["track_index"])
        root_result = self._create_rack(
            {
                "track_index": track_index,
                "rack_type": blueprint["rack_type"],
                "name": blueprint["rack_name"],
                "blueprint": blueprint,
                "macro_labels": blueprint.get("macro_labels"),
            }
        )
        stats = {"created_racks": 1, "created_chains": 0, "created_devices": 0}
        self._apply_rack_blueprint_to_rack(track_index, root_result["rack_path"], blueprint, stats)
        structure = self._get_rack_structure({"track_index": track_index, "rack_path": root_result["rack_path"]})
        result = dict(root_result)
        result.update(stats)
        result["structure"] = structure["rack"]
        return result
