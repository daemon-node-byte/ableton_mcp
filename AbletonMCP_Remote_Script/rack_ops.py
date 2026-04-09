"""Rack, chain, and drum rack operations."""

from __future__ import absolute_import, print_function, unicode_literals


class RackOpsMixin(object):
    """Rack and chain commands."""

    def _get_rack_chains(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        if not hasattr(device, "chains"):
            raise ValueError("Device '{}' is not a rack".format(device.name))
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
        device = self._get_device(params["track_index"], params["device_index"])
        if not hasattr(device, "chains"):
            raise ValueError("Device '{}' is not a rack".format(device.name))
        macros = []
        for index, parameter in enumerate(device.parameters):
            if parameter.name.startswith("Macro") or (index < 8 and "Macro" in parameter.name):
                macros.append({
                    "index": index,
                    "name": parameter.name,
                    "value": round(float(parameter.value), 4),
                    "min": float(parameter.min),
                    "max": float(parameter.max),
                    "display_value": str(parameter),
                })
        return {"rack_name": device.name, "macros": macros}

    def _set_rack_macro(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        if not hasattr(device, "chains"):
            raise ValueError("Device '{}' is not a rack".format(device.name))
        macro_index = int(params["macro_index"])
        value = float(params["value"])
        macros = [parameter for parameter in device.parameters if parameter.name.startswith("Macro")]
        if macro_index < 0 or macro_index >= len(macros):
            raise ValueError("Macro index {} out of range".format(macro_index))
        parameter = macros[macro_index]
        parameter.value = max(parameter.min, min(parameter.max, value))
        return {"name": parameter.name, "value": float(parameter.value)}

    def _get_chain_devices(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        chain_index = int(params["chain_index"])
        if not hasattr(device, "chains"):
            raise ValueError("Device is not a rack")
        chains = device.chains
        if chain_index < 0 or chain_index >= len(chains):
            raise ValueError("Chain index {} out of range".format(chain_index))
        chain = chains[chain_index]
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
        device = self._get_device(params["track_index"], params["device_index"])
        chain_index = int(params["chain_index"])
        device.chains[chain_index].mute = bool(params["mute"])
        return {"mute": device.chains[chain_index].mute}

    def _set_chain_solo(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        chain_index = int(params["chain_index"])
        device.chains[chain_index].solo = bool(params["solo"])
        return {"solo": device.chains[chain_index].solo}

    def _set_chain_volume(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        chain_index = int(params["chain_index"])
        value = max(0.0, min(1.0, float(params["volume"])))
        device.chains[chain_index].mixer_device.volume.value = value
        return {"volume": device.chains[chain_index].mixer_device.volume.value}

    def _get_drum_rack_pads(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        if not hasattr(device, "drum_pads"):
            raise ValueError("Device '{}' is not a Drum Rack".format(device.name))
        pads = []
        for pad in device.drum_pads:
            pad_info = {
                "note": pad.note,
                "name": pad.name,
                "mute": pad.mute,
                "solo": pad.solo,
                "num_chains": len(pad.chains),
            }
            if pad.chains:
                pad_info["chain_devices"] = [
                    {"chain": chain.name, "devices": [chain_device.name for chain_device in chain.devices]}
                    for chain in pad.chains
                ]
            pads.append(pad_info)
        return {"drum_pads": pads, "count": len(pads)}

    def _set_drum_rack_pad_note(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        if not hasattr(device, "drum_pads"):
            raise ValueError("Device is not a Drum Rack")
        target_note = int(params["note"])
        new_note = int(params["new_note"])
        for pad in device.drum_pads:
            if pad.note == target_note:
                pad.note = new_note
                return {"note": pad.note}
        raise ValueError("Drum pad with note {} not found".format(target_note))

    def _set_drum_rack_pad_mute(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        target_note = int(params["note"])
        for pad in device.drum_pads:
            if pad.note == target_note:
                pad.mute = bool(params["mute"])
                return {"note": target_note, "mute": pad.mute}
        raise ValueError("Drum pad with note {} not found".format(target_note))

    def _set_drum_rack_pad_solo(self, params):
        device = self._get_device(params["track_index"], params["device_index"])
        target_note = int(params["note"])
        for pad in device.drum_pads:
            if pad.note == target_note:
                pad.solo = bool(params["solo"])
                return {"note": target_note, "solo": pad.solo}
        raise ValueError("Drum pad with note {} not found".format(target_note))
