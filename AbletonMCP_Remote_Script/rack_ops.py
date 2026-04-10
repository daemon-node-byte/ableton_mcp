"""Rack, chain, and drum rack operations."""

from __future__ import absolute_import, print_function, unicode_literals


class RackOpsMixin(object):
    """Rack and chain commands."""

    def _rack_resolve_rack_device(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        can_have_chains = getattr(device, "can_have_chains", None)
        if can_have_chains is False or not hasattr(device, "chains"):
            raise ValueError("Device '{}' is not a rack".format(device.name))
        return device

    def _rack_collect_macro_parameters(self, device):
        macros = []
        parameters = list(getattr(device, "parameters", []) or [])
        for parameter_index, parameter in enumerate(parameters):
            parameter_name = str(getattr(parameter, "name", ""))
            if parameter_name.startswith("Macro") or (len(macros) < 8 and "Macro" in parameter_name):
                macros.append((len(macros), parameter_index, parameter))
        return macros

    def _rack_resolve_chain(self, params):
        device = self._rack_resolve_rack_device(params)
        chain_index = int(params["chain_index"])
        chains = list(getattr(device, "chains", []) or [])
        if chain_index < 0 or chain_index >= len(chains):
            raise ValueError("Chain index {} out of range".format(chain_index))
        return device, chains[chain_index]

    def _rack_resolve_drum_rack_device(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        can_have_drum_pads = getattr(device, "can_have_drum_pads", None)
        if can_have_drum_pads is False or not hasattr(device, "drum_pads"):
            raise ValueError("Device '{}' is not a Drum Rack".format(device.name))
        return device

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

    def _get_rack_chains(self, params):
        device = self._rack_resolve_rack_device(params)
        chains = []
        for index, chain in enumerate(device.chains):
            chains.append({
                "index": index,
                "name": chain.name,
                "mute": chain.mute,
                "solo": chain.solo if hasattr(chain, "solo") else False,
                "volume": round(chain.mixer_device.volume.value, 4) if hasattr(chain, "mixer_device") else 1.0,
                "pan": round(chain.mixer_device.panning.value, 4) if hasattr(chain, "mixer_device") else 0.0,
                "num_devices": len(chain.devices),
                "devices": [child_device.name for child_device in chain.devices],
            })
        return {"rack_name": device.name, "chains": chains}

    def _get_rack_macros(self, params):
        device = self._rack_resolve_rack_device(params)
        macros = []
        for macro_index, parameter_index, parameter in self._rack_collect_macro_parameters(device):
            macros.append({
                "index": macro_index,
                "parameter_index": parameter_index,
                "name": parameter.name,
                "value": round(float(parameter.value), 4),
                "min": float(parameter.min),
                "max": float(parameter.max),
                "display_value": str(parameter),
            })
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
        for index, chain_device in enumerate(chain.devices):
            devices.append({
                "index": index,
                "name": chain_device.name,
                "class_name": chain_device.class_name,
                "is_active": chain_device.is_active,
                "num_parameters": len(chain_device.parameters),
            })
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

        # The Live Object Model documents DrumPad.note as read-only. Live 12.3+
        # exposes DrumChain.in_note for chain-backed remap on Drum Rack pads.
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
