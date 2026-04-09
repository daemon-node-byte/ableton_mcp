"""Session clip and MIDI note operations."""

from __future__ import absolute_import, print_function, unicode_literals


class SessionClipOpsMixin(object):
    """Session View clip commands."""

    def _get_clip_info(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        return self._clip_to_dict(clip, int(params["slot_index"]))

    def _create_clip(self, params):
        slot = self._get_clip_slot(params["track_index"], params["slot_index"])
        if slot.has_clip:
            raise ValueError("Clip slot already has a clip")
        length = float(params.get("length", 4.0))
        slot.create_clip(length)
        return self._clip_to_dict(slot.clip, int(params["slot_index"]))

    def _delete_clip(self, params):
        slot = self._get_clip_slot(params["track_index"], params["slot_index"])
        if not slot.has_clip:
            raise ValueError("No clip to delete")
        slot.delete_clip()
        return {"ok": True}

    def _duplicate_clip(self, params):
        track = self._get_track(params["track_index"])
        source_index = int(params["slot_index"])
        destination_index = int(params.get("destination_slot_index", source_index + 1))
        track.duplicate_clip_slot(source_index)
        return {"ok": True, "destination_slot_index": destination_index}

    def _set_clip_name(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        clip.name = str(params["name"])
        return {"name": clip.name}

    def _set_clip_color(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        clip.color = int(params["color"])
        return {"color": clip.color}

    def _fire_clip(self, params):
        slot = self._get_clip_slot(params["track_index"], params["slot_index"])
        slot.fire()
        return {"ok": True}

    def _stop_clip(self, params):
        slot = self._get_clip_slot(params["track_index"], params["slot_index"])
        slot.stop()
        return {"ok": True}

    def _get_clip_notes(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        if not clip.is_midi_clip:
            raise ValueError("Clip is not a MIDI clip")
        notes = self._serialize_notes(self._get_clip_notes_raw(clip))
        return {"notes": notes, "count": len(notes)}

    def _add_notes_to_clip(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        if not clip.is_midi_clip:
            raise ValueError("Clip is not a MIDI clip")
        note_objects = self._build_midi_notes(params.get("notes", []))
        clip.add_new_notes(note_objects)
        return {"added": len(note_objects)}

    def _set_clip_notes(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        if not clip.is_midi_clip:
            raise ValueError("Clip is not a MIDI clip")
        clip.remove_notes_extended(0, clip.length, 0, 128)
        note_objects = self._build_midi_notes(params.get("notes", []))
        if note_objects:
            clip.add_new_notes(note_objects)
        return {"count": len(note_objects)}

    def _remove_notes_from_clip(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        if not clip.is_midi_clip:
            raise ValueError("Clip is not a MIDI clip")
        from_time = float(params.get("from_time", 0.0))
        time_span = float(params.get("time_span", clip.length))
        from_pitch = int(params.get("from_pitch", 0))
        pitch_span = int(params.get("pitch_span", 128))
        try:
            clip.remove_notes_extended(from_time, time_span, from_pitch, pitch_span)
        except AttributeError:
            clip.remove_notes(from_time, from_pitch, time_span, pitch_span)
        return {"ok": True}

    def _set_clip_loop(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        if "looping" in params:
            clip.looping = bool(params["looping"])
        if "loop_start" in params:
            clip.loop_start = float(params["loop_start"])
        if "loop_end" in params:
            clip.loop_end = float(params["loop_end"])
        return {
            "looping": clip.looping,
            "loop_start": clip.loop_start,
            "loop_end": clip.loop_end,
        }

    def _set_clip_markers(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        if "start_marker" in params:
            clip.start_marker = float(params["start_marker"])
        if "end_marker" in params:
            clip.end_marker = float(params["end_marker"])
        return {"start_marker": clip.start_marker, "end_marker": clip.end_marker}

    def _set_clip_gain(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        if not clip.is_audio_clip:
            raise ValueError("Clip is not an audio clip")
        clip.gain = float(params["gain"])
        return {"gain": clip.gain}

    def _set_clip_pitch(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        if not clip.is_audio_clip:
            raise ValueError("Clip is not an audio clip")
        if "coarse" in params:
            clip.pitch_coarse = int(params["coarse"])
        if "fine" in params:
            clip.pitch_fine = float(params["fine"])
        return {"pitch_coarse": clip.pitch_coarse, "pitch_fine": clip.pitch_fine}

    def _set_clip_warp_mode(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        if not clip.is_audio_clip:
            raise ValueError("Clip is not an audio clip")
        mode_map = {
            "beats": 0,
            "tones": 1,
            "texture": 2,
            "re-pitch": 3,
            "complex": 4,
            "rex": 5,
            "complex_pro": 6,
            "0": 0,
            "1": 1,
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
        }
        clip.warp_mode = mode_map.get(str(params.get("warp_mode", 0)).lower(), 0)
        return {"warp_mode": clip.warp_mode}

    def _quantize_clip(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        quantize_to = float(params.get("quantize_to", 1.0))
        amount = float(params.get("amount", 1.0))
        clip.quantize(quantize_to, amount)
        return {"ok": True}

    def _duplicate_clip_loop(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        clip.duplicate_loop()
        return {"ok": True, "length": clip.length}

    def _get_clip_automation(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        track = self._get_track(params["track_index"])
        device = track.devices[int(params.get("device_index", 0))]
        parameter = device.parameters[int(params.get("parameter_index", 0))]
        envelope = clip.automation_envelope(parameter)
        if envelope is None:
            return {"envelope": []}
        points = []
        for index in range(int(clip.length * 10)):
            current_time = index / 10.0
            if current_time <= clip.length:
                try:
                    points.append({"time": current_time, "value": envelope.value_at_time(current_time)})
                except Exception:
                    pass
        return {"envelope": points, "parameter": parameter.name}

    def _set_clip_automation(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        track = self._get_track(params["track_index"])
        device = track.devices[int(params.get("device_index", 0))]
        parameter = device.parameters[int(params.get("parameter_index", 0))]
        envelope = clip.automation_envelope(parameter)
        if envelope is None:
            envelope = clip.create_automation_envelope(parameter)
        envelope_data = params.get("envelope", [])
        envelope.clear_all_events()
        for point in envelope_data:
            envelope.insert_step(float(point["time"]), 0.0, float(point["value"]))
        return {"ok": True, "points_added": len(envelope_data)}

    def _clear_clip_automation(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        track = self._get_track(params["track_index"])
        device = track.devices[int(params.get("device_index", 0))]
        parameter = device.parameters[int(params.get("parameter_index", 0))]
        envelope = clip.automation_envelope(parameter)
        if envelope:
            envelope.clear_all_events()
        return {"ok": True}
