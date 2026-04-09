"""Shared helpers for the AbletonMCP Remote Script.

This module intentionally holds only cross-domain helpers that are reused by
the dispatcher-backed domain mixins.
"""

from __future__ import absolute_import, print_function, unicode_literals

try:
    import Live
except ImportError:
    Live = None


class CoreOpsMixin(object):
    """Shared object lookup and serialization helpers."""

    BROWSER_ROOT_NAMES = (
        "instruments",
        "audio_effects",
        "midi_effects",
        "drums",
        "sounds",
        "samples",
        "packs",
        "user_library",
    )

    def _get_track(self, track_index):
        tracks = self.song().tracks
        idx = int(track_index)
        if idx < 0 or idx >= len(tracks):
            raise ValueError("Track index {} out of range (0-{})".format(idx, len(tracks) - 1))
        return tracks[idx]

    def _get_clip_slot(self, track_index, slot_index):
        track = self._get_track(track_index)
        slots = track.clip_slots
        idx = int(slot_index)
        if idx < 0 or idx >= len(slots):
            raise ValueError("Clip slot {} out of range".format(idx))
        return slots[idx]

    def _get_clip(self, track_index, slot_index):
        slot = self._get_clip_slot(track_index, slot_index)
        if not slot.has_clip:
            raise ValueError("No clip in track {} slot {}".format(track_index, slot_index))
        return slot.clip

    def _get_device(self, track_index, device_index):
        track = self._get_track(track_index)
        idx = int(device_index)
        if idx < 0 or idx >= len(track.devices):
            raise ValueError("Device index {} out of range on track {}".format(idx, track_index))
        return track.devices[idx]

    def _clip_to_dict(self, clip, index=None):
        data = {
            "name": clip.name,
            "length": clip.length,
            "is_playing": clip.is_playing,
            "is_recording": clip.is_recording,
            "is_triggered": clip.is_triggered,
            "color": clip.color,
            "looping": clip.looping,
            "loop_start": clip.loop_start,
            "loop_end": clip.loop_end,
            "start_marker": clip.start_marker,
            "end_marker": clip.end_marker,
            "is_midi_clip": clip.is_midi_clip,
            "is_audio_clip": clip.is_audio_clip,
        }
        if index is not None:
            data["slot_index"] = index
        if clip.is_audio_clip:
            try:
                data["gain"] = clip.gain
                data["pitch_coarse"] = clip.pitch_coarse
                data["pitch_fine"] = clip.pitch_fine
                data["warping"] = clip.warping
                data["warp_mode"] = clip.warp_mode
            except Exception:
                pass
        return data

    def _get_arrangement_clips_for_container(self, container):
        clips = []
        if not hasattr(container, "arrangement_clips"):
            return clips
        for index, clip in enumerate(container.arrangement_clips):
            clips.append({
                "index": index,
                "name": clip.name,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "length": clip.length,
                "color": clip.color,
                "looping": clip.looping,
                "loop_start": clip.loop_start,
                "loop_end": clip.loop_end,
                "is_midi_clip": clip.is_midi_clip,
                "is_audio_clip": clip.is_audio_clip,
                "is_playing": clip.is_playing,
                "muted": clip.muted,
            })
        return clips

    def _find_arrangement_clip(self, container, clip_index=None, start_time=None):
        if not hasattr(container, "arrangement_clips"):
            raise ValueError("Target has no arrangement clips")
        arrangement_clips = list(container.arrangement_clips)
        if clip_index is not None:
            idx = int(clip_index)
            if idx < 0 or idx >= len(arrangement_clips):
                raise ValueError("Arrangement clip index {} out of range".format(idx))
            return arrangement_clips[idx]
        if start_time is not None:
            clip_start_time = float(start_time)
            for clip in arrangement_clips:
                if abs(clip.start_time - clip_start_time) < 0.001:
                    return clip
            raise ValueError("No arrangement clip found at start_time={}".format(clip_start_time))
        raise ValueError("Must provide clip_index or start_time")

    def _get_clip_notes_raw(self, clip):
        try:
            return clip.get_notes_extended(0, 128, 0.0, clip.length)
        except AttributeError:
            return clip.get_notes(0, 0, clip.length, 128)

    def _serialize_notes(self, raw_notes):
        notes = []
        if isinstance(raw_notes, dict):
            raw_notes = raw_notes.get("notes", [])
        for note in raw_notes:
            if isinstance(note, dict):
                notes.append({
                    "pitch": note["pitch"],
                    "time": note.get("time", note.get("start_time", 0.0)),
                    "duration": note["duration"],
                    "velocity": note.get("velocity", 100),
                    "mute": note.get("mute", False),
                })
            else:
                notes.append({
                    "pitch": note.pitch,
                    "time": note.start_time,
                    "duration": note.duration,
                    "velocity": note.velocity,
                    "mute": note.mute,
                })
        return notes

    def _build_midi_note(self, note_data):
        pitch = int(note_data["pitch"])
        start_time = float(note_data.get("time", note_data.get("start_time", 0.0)))
        duration = float(note_data.get("duration", 0.25))
        velocity = float(note_data.get("velocity", 100))
        mute = bool(note_data.get("mute", False))

        if Live is not None and hasattr(Live.Clip, "MidiNoteSpecification"):
            try:
                return Live.Clip.MidiNoteSpecification(
                    pitch=pitch,
                    start_time=start_time,
                    duration=duration,
                    velocity=velocity,
                    mute=mute,
                )
            except TypeError:
                return Live.Clip.MidiNoteSpecification(
                    pitch,
                    start_time,
                    duration,
                    velocity,
                    mute,
                )

        return {
            "pitch": pitch,
            "start_time": start_time,
            "duration": duration,
            "velocity": velocity,
            "mute": mute,
        }

    def _build_midi_notes(self, notes_data):
        notes = [self._build_midi_note(note) for note in notes_data]
        if Live is not None and hasattr(Live.Clip, "MidiNoteSpecification"):
            return tuple(notes)
        return notes

    def _routing_display_name(self, routing):
        if routing is None:
            return ""
        if hasattr(routing, "display_name"):
            return routing.display_name
        if isinstance(routing, dict):
            return routing.get("display_name", "")
        return str(routing)

    def _parse_non_negative_int(self, value, field_name):
        parsed_value = int(value)
        if parsed_value < 0:
            raise ValueError("{} must be >= 0".format(field_name))
        return parsed_value

    def _available_browser_roots(self):
        browser = self.application().browser
        roots = {}
        for root_name in self.BROWSER_ROOT_NAMES:
            root = getattr(browser, root_name, None)
            if root is not None:
                roots[root_name] = root
        return roots

    def _get_browser_root(self, category_name):
        normalized_name = str(category_name).strip().lower()
        roots = self._available_browser_roots()
        if normalized_name not in self.BROWSER_ROOT_NAMES:
            raise ValueError("Unknown browser category: {}".format(normalized_name))
        root = roots.get(normalized_name)
        if root is None:
            raise ValueError("Browser category '{}' is unavailable in this Live session".format(normalized_name))
        return root

    def _browser_item_uri(self, item):
        try:
            return str(getattr(item, "uri", "") or "")
        except Exception:
            return ""

    def _browser_item_children(self, item):
        try:
            return list(getattr(item, "children", []) or [])
        except Exception:
            return []

    def _prioritized_browser_roots_for_uri(self, browser_uri):
        roots = self._available_browser_roots()
        prioritized_names = []
        if browser_uri.startswith("query:Synths#"):
            prioritized_names.append("instruments")
        elif browser_uri.startswith("query:AudioFx#"):
            prioritized_names.append("audio_effects")
        elif browser_uri.startswith("query:MidiFx#"):
            prioritized_names.append("midi_effects")
        elif browser_uri.startswith("query:Drums#"):
            prioritized_names.append("drums")
        elif browser_uri.startswith("query:Sounds#"):
            prioritized_names.append("sounds")
        elif browser_uri.startswith("query:Samples#"):
            prioritized_names.append("samples")
        elif browser_uri.startswith("query:Packs#"):
            prioritized_names.append("packs")
        elif browser_uri.startswith("query:User"):
            prioritized_names.append("user_library")

        prioritized_roots = []
        for root_name in prioritized_names:
            root = roots.get(root_name)
            if root is not None:
                prioritized_roots.append(root)
        for root_name in self.BROWSER_ROOT_NAMES:
            root = roots.get(root_name)
            if root is not None and root not in prioritized_roots:
                prioritized_roots.append(root)
        return prioritized_roots

    def _resolve_browser_item_by_uri(self, uri, command_name):
        browser_uri = str(uri).strip()
        if not browser_uri:
            raise ValueError("{} requires a non-empty URI".format(command_name))
        browser = self.application().browser
        browser_item = None
        lookup = getattr(browser, "get_item_by_uri", None)
        if callable(lookup):
            browser_item = lookup(browser_uri)
        if browser_item is None:
            browser_item = self._find_browser_item_by_uri_fallback(browser_uri)
        if browser_item is None:
            raise ValueError("Browser item not found for URI: {}".format(browser_uri))
        return browser_item

    def _find_browser_item_by_uri_fallback(self, browser_uri):
        prioritized_roots = self._prioritized_browser_roots_for_uri(browser_uri)

        # Fast path for the common case where the URI points at a top-level item
        # under a known browser root.
        for root in prioritized_roots:
            for child in self._browser_item_children(root):
                if self._browser_item_uri(child) == browser_uri:
                    return child

        stack = list(prioritized_roots)
        seen = set()
        while stack:
            current = stack.pop()
            current_key = (self._browser_item_uri(current), getattr(current, "name", ""))
            if current_key in seen:
                continue
            seen.add(current_key)
            if current_key[0] == browser_uri:
                return current
            stack.extend(reversed(self._browser_item_children(current)))
        return None

    def _build_track_load_result(
        self,
        track,
        previous_devices,
        mode,
        track_index,
        requested_name=None,
        requested_uri=None,
        target_index=None,
    ):
        devices_after = list(track.devices)
        result = {
            "ok": True,
            "mode": mode,
            "track_index": int(track_index),
            "device_count_before": len(previous_devices),
            "device_count_after": len(devices_after),
            "loaded": len(devices_after) > len(previous_devices),
        }
        if requested_name is not None:
            result["requested_name"] = requested_name
        if requested_uri is not None:
            result["uri"] = requested_uri
        if target_index is not None:
            result["target_index"] = int(target_index)

        new_device_index = None
        new_device = None
        for index, device in enumerate(devices_after):
            if all(device is not previous_device for previous_device in previous_devices):
                new_device_index = index
                new_device = device
                break

        if new_device is None and len(devices_after) > len(previous_devices):
            inferred_index = len(devices_after) - 1 if target_index is None else min(int(target_index), len(devices_after) - 1)
            candidate = devices_after[inferred_index]
            if all(candidate is not previous_device for previous_device in previous_devices):
                new_device_index = inferred_index
                new_device = candidate

        if new_device is not None:
            result["device_index"] = new_device_index
            result["loaded_device_name"] = new_device.name
            result["class_name"] = new_device.class_name

        return result

    def _load_browser_item_onto_track(
        self,
        track,
        browser_item,
        mode,
        track_index,
        requested_name=None,
        requested_uri=None,
    ):
        previous_devices = list(track.devices)
        self.song().view.selected_track = track
        self.application().browser.load_item(browser_item)
        return self._build_track_load_result(
            track,
            previous_devices,
            mode=mode,
            track_index=track_index,
            requested_name=requested_name,
            requested_uri=requested_uri,
        )
