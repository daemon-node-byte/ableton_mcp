"""Track, return track, and master channel operations."""

from __future__ import absolute_import, print_function, unicode_literals


class TrackOpsMixin(object):
    """Track and mixer commands."""

    def _get_return_track(self, return_index):
        return_tracks = self.song().return_tracks
        idx = int(return_index)
        if idx < 0 or idx >= len(return_tracks):
            raise ValueError("Return track index {} out of range".format(idx))
        return return_tracks[idx]

    def _parse_bool_param(self, value, field_name):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        normalized = str(value).strip().lower()
        if normalized in ("1", "true", "yes", "on"):
            return True
        if normalized in ("0", "false", "no", "off", ""):
            return False
        raise ValueError("{} must be a boolean".format(field_name))

    def _require_armable_track(self, track, track_index):
        idx = int(track_index)
        if hasattr(track, "can_be_armed") and not bool(track.can_be_armed):
            raise ValueError("Track index {} cannot be armed".format(idx))
        if not hasattr(track, "arm"):
            raise ValueError("Track index {} cannot be armed".format(idx))

    def _require_foldable_track(self, track, track_index):
        idx = int(track_index)
        if not getattr(track, "is_foldable", False):
            raise ValueError("Track index {} is not foldable".format(idx))
        if not hasattr(track, "fold_state"):
            raise ValueError("Track index {} is not foldable".format(idx))

    def _selected_track_payload(self, selected):
        song = self.song()
        for index, track in enumerate(song.tracks):
            if track == selected:
                return {
                    "selection_type": "track",
                    "name": track.name,
                    "index": index,
                    "track_index": index,
                    "return_index": None,
                }

        for index, track in enumerate(song.return_tracks):
            if track == selected:
                return {
                    "selection_type": "return_track",
                    "name": track.name,
                    "index": -1,
                    "track_index": None,
                    "return_index": index,
                }

        master_track = getattr(song, "master_track", None)
        if master_track is not None and master_track == selected:
            return {
                "selection_type": "master_track",
                "name": master_track.name,
                "index": -1,
                "track_index": None,
                "return_index": None,
            }

        return {
            "selection_type": "unknown",
            "name": selected.name if selected is not None and hasattr(selected, "name") else "",
            "index": -1,
            "track_index": None,
            "return_index": None,
        }

    def _resolve_selected_track_target(self, params):
        has_track_index = params.get("track_index") is not None
        has_return_index = params.get("return_index") is not None
        has_master = self._parse_bool_param(params.get("master", False), "master")
        selector_count = int(has_track_index) + int(has_return_index) + int(has_master)
        if selector_count != 1:
            raise ValueError("select_track requires exactly one of track_index, return_index, or master=True")

        if has_track_index:
            return self._get_track(params["track_index"])
        if has_return_index:
            return self._get_return_track(params["return_index"])
        return self.song().master_track

    def _get_track_info(self, params):
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
            }
            try:
                device_data["class_display_name"] = device.class_display_name
            except Exception:
                pass
            devices.append(device_data)

        clip_slots = []
        for index, slot in enumerate(track.clip_slots):
            slot_info = {"index": index, "has_clip": slot.has_clip}
            if slot.has_clip:
                clip = slot.clip
                slot_info.update({
                    "clip_name": clip.name,
                    "length": clip.length,
                    "is_playing": clip.is_playing,
                    "is_recording": clip.is_recording,
                    "color": clip.color,
                    "is_midi_clip": clip.is_midi_clip,
                    "is_audio_clip": clip.is_audio_clip,
                })
            clip_slots.append(slot_info)

        sends = []
        for index, send in enumerate(track.mixer_device.sends):
            sends.append({"index": index, "value": round(send.value, 4)})

        result = {
            "index": int(params["track_index"]),
            "name": track.name,
            "type": "midi" if track.has_midi_input else "audio",
            "color": track.color,
            "mute": track.mute,
            "solo": track.solo,
            "volume": round(track.mixer_device.volume.value, 4),
            "pan": round(track.mixer_device.panning.value, 4),
            "devices": devices,
            "clip_slots": clip_slots,
            "sends": sends,
        }
        try:
            result["arm"] = track.arm
        except Exception:
            result["arm"] = False
        try:
            result["is_foldable"] = track.is_foldable
            result["is_grouped"] = track.is_grouped
            result["fold_state"] = track.fold_state
        except Exception:
            pass
        try:
            result["input_routing_type"] = self._routing_display_name(track.input_routing_type)
            result["output_routing_type"] = self._routing_display_name(track.output_routing_type)
        except Exception:
            pass
        return result

    def _get_all_track_names(self):
        tracks = [{"index": index, "name": track.name} for index, track in enumerate(self.song().tracks)]
        return {"tracks": tracks}

    def _create_midi_track(self, params):
        index = int(params.get("index", -1))
        self.song().create_midi_track(index)
        created_index = len(self.song().tracks) - 1 if index == -1 else index
        return {"index": created_index, "name": self.song().tracks[created_index].name}

    def _create_audio_track(self, params):
        index = int(params.get("index", -1))
        self.song().create_audio_track(index)
        created_index = len(self.song().tracks) - 1 if index == -1 else index
        return {"index": created_index, "name": self.song().tracks[created_index].name}

    def _create_return_track(self):
        self.song().create_return_track()
        index = len(self.song().return_tracks) - 1
        return {"index": index, "name": self.song().return_tracks[index].name}

    def _delete_track(self, params):
        index = int(params["track_index"])
        self.song().delete_track(index)
        return {"deleted_index": index}

    def _duplicate_track(self, params):
        index = int(params["track_index"])
        self.song().duplicate_track(index)
        return {"original_index": index}

    def _set_track_name(self, params):
        track = self._get_track(params["track_index"])
        track.name = str(params["name"])
        return {"name": track.name}

    def _set_track_color(self, params):
        track = self._get_track(params["track_index"])
        track.color = int(params["color"])
        return {"color": track.color}

    def _set_track_volume(self, params):
        track = self._get_track(params["track_index"])
        value = max(0.0, min(1.0, float(params["volume"])))
        track.mixer_device.volume.value = value
        return {"volume": track.mixer_device.volume.value}

    def _set_track_pan(self, params):
        track = self._get_track(params["track_index"])
        value = max(-1.0, min(1.0, float(params["pan"])))
        track.mixer_device.panning.value = value
        return {"pan": track.mixer_device.panning.value}

    def _set_track_mute(self, params):
        track = self._get_track(params["track_index"])
        track.mute = bool(params["mute"])
        return {"mute": track.mute}

    def _set_track_solo(self, params):
        track = self._get_track(params["track_index"])
        track.solo = bool(params["solo"])
        return {"solo": track.solo}

    def _set_track_arm(self, params):
        track = self._get_track(params["track_index"])
        self._require_armable_track(track, params["track_index"])
        track.arm = bool(params["arm"])
        return {"arm": track.arm}

    def _set_track_monitoring(self, params):
        track = self._get_track(params["track_index"])
        mode_map = {"in": 0, "auto": 1, "off": 2, "0": 0, "1": 1, "2": 2}
        mode = mode_map.get(str(params.get("monitoring", "auto")).lower(), 1)
        track.current_monitoring_state = mode
        return {"monitoring": track.current_monitoring_state}

    def _freeze_track(self, params):
        track = self._get_track(params["track_index"])
        track.freeze()
        return {"ok": True}

    def _flatten_track(self, params):
        track = self._get_track(params["track_index"])
        track.flatten()
        return {"ok": True}

    def _fold_track(self, params):
        track = self._get_track(params["track_index"])
        self._require_foldable_track(track, params["track_index"])
        track.fold_state = True
        return {"fold_state": bool(track.fold_state)}

    def _unfold_track(self, params):
        track = self._get_track(params["track_index"])
        self._require_foldable_track(track, params["track_index"])
        track.fold_state = False
        return {"fold_state": bool(track.fold_state)}

    def _unarm_all(self):
        for track in self.song().tracks:
            try:
                track.arm = False
            except Exception:
                pass
        return {"ok": True}

    def _unsolo_all(self):
        for track in self.song().tracks:
            try:
                track.solo = False
            except Exception:
                pass
        return {"ok": True}

    def _unmute_all(self):
        for track in self.song().tracks:
            try:
                track.mute = False
            except Exception:
                pass
        return {"ok": True}

    def _set_track_delay(self, params):
        track = self._get_track(params["track_index"])
        delay_ms = float(params["delay_ms"])
        track.delay_in_ms = delay_ms
        return {"delay_ms": delay_ms}

    def _set_send_level(self, params):
        track = self._get_track(params["track_index"])
        send_index = int(params["send_index"])
        value = max(0.0, min(1.0, float(params["level"])))
        sends = track.mixer_device.sends
        if send_index < 0 or send_index >= len(sends):
            raise ValueError("Send index {} out of range".format(send_index))
        sends[send_index].value = value
        return {"send_index": send_index, "level": sends[send_index].value}

    def _get_return_tracks(self):
        return_tracks = []
        for index, track in enumerate(self.song().return_tracks):
            return_tracks.append({
                "index": index,
                "name": track.name,
                "color": track.color,
                "mute": track.mute,
                "volume": round(track.mixer_device.volume.value, 4),
                "pan": round(track.mixer_device.panning.value, 4),
            })
        return {"return_tracks": return_tracks}

    def _get_return_track_info(self, params):
        return_index = int(params["return_index"])
        track = self._get_return_track(return_index)
        return {
            "index": return_index,
            "name": track.name,
            "color": track.color,
            "mute": track.mute,
            "volume": round(track.mixer_device.volume.value, 4),
            "pan": round(track.mixer_device.panning.value, 4),
            "sends": [],
        }

    def _set_return_volume(self, params):
        track = self._get_return_track(params["return_index"])
        value = max(0.0, min(1.0, float(params["volume"])))
        track.mixer_device.volume.value = value
        return {"volume": track.mixer_device.volume.value}

    def _set_return_pan(self, params):
        track = self._get_return_track(params["return_index"])
        value = max(-1.0, min(1.0, float(params["pan"])))
        track.mixer_device.panning.value = value
        return {"pan": track.mixer_device.panning.value}

    def _set_track_input_routing(self, params):
        track = self._get_track(params["track_index"])
        routing_type = str(params.get("routing_type", ""))
        for available in track.available_input_routing_types:
            if self._routing_display_name(available) == routing_type:
                track.input_routing_type = available
                return {"input_routing_type": self._routing_display_name(track.input_routing_type)}
        raise ValueError("Routing type '{}' not found".format(routing_type))

    def _set_track_output_routing(self, params):
        track = self._get_track(params["track_index"])
        routing_type = str(params.get("routing_type", ""))
        for available in track.available_output_routing_types:
            if self._routing_display_name(available) == routing_type:
                track.output_routing_type = available
                return {"output_routing_type": self._routing_display_name(track.output_routing_type)}
        raise ValueError("Routing type '{}' not found".format(routing_type))

    def _get_track_input_routing(self, params):
        track = self._get_track(params["track_index"])
        available = [self._routing_display_name(routing) for routing in track.available_input_routing_types]
        return {
            "current_input_routing": self._routing_display_name(track.input_routing_type),
            "available_input_routing_types": available,
        }

    def _get_track_output_routing(self, params):
        track = self._get_track(params["track_index"])
        available = [self._routing_display_name(routing) for routing in track.available_output_routing_types]
        return {
            "current_output_routing": self._routing_display_name(track.output_routing_type),
            "available_output_routing_types": available,
        }

    def _select_track(self, params):
        track = self._resolve_selected_track_target(params)
        self.song().view.selected_track = track
        selected_payload = self._selected_track_payload(track)
        selected_payload["selected_track_index"] = (
            selected_payload["track_index"] if selected_payload["track_index"] is not None else -1
        )
        return selected_payload

    def _get_selected_track(self):
        return self._selected_track_payload(self.song().view.selected_track)

    def _get_master_info(self):
        master = self.song().master_track
        return {
            "volume": round(master.mixer_device.volume.value, 4),
            "pan": round(master.mixer_device.panning.value, 4),
            "output_meter_left": master.output_meter_left,
            "output_meter_right": master.output_meter_right,
        }

    def _set_master_volume(self, params):
        value = max(0.0, min(1.0, float(params["volume"])))
        self.song().master_track.mixer_device.volume.value = value
        return {"volume": self.song().master_track.mixer_device.volume.value}

    def _set_master_pan(self, params):
        value = max(-1.0, min(1.0, float(params["pan"])))
        self.song().master_track.mixer_device.panning.value = value
        return {"pan": self.song().master_track.mixer_device.panning.value}

    def _get_master_output_meter(self):
        master = self.song().master_track
        return {"left": master.output_meter_left, "right": master.output_meter_right}

    def _get_cue_volume(self):
        cue_volume = self.song().master_track.mixer_device.cue_volume.value
        return {"cue_volume": round(cue_volume, 4)}

    def _set_cue_volume(self, params):
        value = max(0.0, min(1.0, float(params["volume"])))
        self.song().master_track.mixer_device.cue_volume.value = value
        return {"cue_volume": self.song().master_track.mixer_device.cue_volume.value}
