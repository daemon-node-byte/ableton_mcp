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
            return clip.get_notes_extended(0, clip.length, 0, 128)
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
