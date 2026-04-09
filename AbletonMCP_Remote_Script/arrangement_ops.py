"""Arrangement View clip operations."""

from __future__ import absolute_import, print_function, unicode_literals

import os


class ArrangementOpsMixin(object):
    """Arrangement clip commands."""

    def _require_non_negative_time(self, value, field_name):
        numeric_value = float(value)
        if numeric_value < 0.0:
            raise ValueError("{} must be >= 0".format(field_name))
        return numeric_value

    def _require_exact_arrangement_selector(self, params, command_name):
        has_clip_index = params.get("clip_index") is not None
        has_start_time = params.get("start_time") is not None
        if has_clip_index and has_start_time:
            raise ValueError(
                "{} requires exactly one of 'clip_index' or 'start_time', not both".format(command_name)
            )
        if not has_clip_index and not has_start_time:
            raise ValueError(
                "{} requires exactly one of 'clip_index' or 'start_time'".format(command_name)
            )
        return {
            "clip_index": params.get("clip_index") if has_clip_index else None,
            "start_time": params.get("start_time") if has_start_time else None,
        }

    def _ensure_move_target_is_clear(self, track, current_clip, new_start_time, length):
        new_end_time = new_start_time + float(length)
        for arrangement_clip in getattr(track, "arrangement_clips", []):
            if arrangement_clip == current_clip:
                continue
            if arrangement_clip.start_time < new_end_time and arrangement_clip.end_time > new_start_time:
                raise ValueError(
                    "Cannot move clip to {} because it overlaps existing clip '{}' [{} - {}]".format(
                        new_start_time,
                        arrangement_clip.name,
                        arrangement_clip.start_time,
                        arrangement_clip.end_time,
                    )
                )

    def _get_arrangement_clips(self, params):
        track = self._get_track(params["track_index"])
        clips = self._get_arrangement_clips_for_container(track)
        return {"track_index": int(params["track_index"]), "clips": clips}

    def _get_all_arrangement_clips(self):
        tracks = []
        for index, track in enumerate(self.song().tracks):
            clips = self._get_arrangement_clips_for_container(track)
            if clips:
                tracks.append({"track_index": index, "track_name": track.name, "clips": clips})
        return {"tracks": tracks}

    def _create_arrangement_midi_clip(self, params):
        track = self._get_track(params["track_index"])
        if not track.has_midi_input:
            raise ValueError("Track {} is not a MIDI track".format(params["track_index"]))
        start_time = self._require_non_negative_time(params["start_time"], "start_time")
        length = float(params.get("length", 4.0))
        if length <= 0.0:
            raise ValueError("length must be > 0")
        clip = track.create_midi_clip(start_time, length)
        return {
            "start_time": clip.start_time,
            "end_time": clip.end_time,
            "length": clip.length,
            "name": clip.name,
        }

    def _create_arrangement_audio_clip(self, params):
        track = self._get_track(params["track_index"])
        if track.has_midi_input:
            raise ValueError("Track {} is a MIDI track, not audio".format(params["track_index"]))
        file_path = str(params.get("file_path", ""))
        if not file_path:
            raise ValueError(
                "create_arrangement_audio_clip requires 'file_path'. "
                "Live does not support start_time/length-only arrangement audio clip creation."
            )
        if not os.path.isabs(file_path):
            raise ValueError("file_path must be an absolute path")
        if not os.path.isfile(file_path):
            raise ValueError("file_path does not exist: {}".format(file_path))
        start_time = self._require_non_negative_time(params["start_time"], "start_time")
        clip = track.create_audio_clip(file_path, start_time)
        return {
            "start_time": clip.start_time,
            "end_time": clip.end_time,
            "length": clip.length,
            "name": clip.name,
            "file_path": file_path,
        }

    def _delete_arrangement_clip(self, params):
        track = self._get_track(params["track_index"])
        selector = self._require_exact_arrangement_selector(params, "delete_arrangement_clip")
        clip = self._find_arrangement_clip(
            track,
            clip_index=selector["clip_index"],
            start_time=selector["start_time"],
        )
        track.delete_clip(clip)
        return {"ok": True}

    def _resize_arrangement_clip(self, params):
        track = self._get_track(params["track_index"])
        selector = self._require_exact_arrangement_selector(params, "resize_arrangement_clip")
        clip = self._find_arrangement_clip(
            track,
            clip_index=selector["clip_index"],
            start_time=selector["start_time"],
        )
        new_length = float(params["length"])
        if new_length <= 0.0:
            raise ValueError("length must be > 0")
        clip.end_marker = clip.start_marker + new_length
        clip.loop_end = clip.loop_start + new_length
        return {
            "start_time": clip.start_time,
            "end_time": clip.end_time,
            "length": clip.length,
        }

    def _move_arrangement_clip(self, params):
        """Move an arrangement clip by recreating it at the new position."""
        track = self._get_track(params["track_index"])
        selector = self._require_exact_arrangement_selector(params, "move_arrangement_clip")
        clip = self._find_arrangement_clip(
            track,
            clip_index=selector["clip_index"],
            start_time=selector["start_time"],
        )
        new_start_time = self._require_non_negative_time(params["new_start_time"], "new_start_time")
        is_midi_clip = clip.is_midi_clip
        length = clip.length
        stored_name = clip.name
        stored_color = clip.color
        stored_looping = clip.looping
        stored_loop_start = clip.loop_start
        stored_loop_end = clip.loop_end
        stored_start_marker = clip.start_marker
        stored_end_marker = clip.end_marker
        stored_notes = []

        if not is_midi_clip:
            raise ValueError(
                "move_arrangement_clip currently supports MIDI clips only. "
                "Audio clip moves remain unsupported because Live does not expose a direct move API."
            )
        stored_notes = self._serialize_notes(self._get_clip_notes_raw(clip))
        self._ensure_move_target_is_clear(track, clip, new_start_time, length)

        track.delete_clip(clip)
        new_clip = track.create_midi_clip(new_start_time, length)

        new_clip.name = stored_name
        new_clip.color = stored_color
        new_clip.looping = stored_looping
        new_clip.loop_start = stored_loop_start
        new_clip.loop_end = stored_loop_end
        new_clip.start_marker = stored_start_marker
        new_clip.end_marker = stored_end_marker

        if stored_notes:
            new_clip.add_new_notes(self._build_midi_notes(stored_notes))

        return {
            "start_time": new_clip.start_time,
            "end_time": new_clip.end_time,
            "length": new_clip.length,
            "notes_restored": len(stored_notes),
        }

    def _add_notes_to_arrangement_clip(self, params):
        track = self._get_track(params["track_index"])
        clip = self._find_arrangement_clip(
            track,
            clip_index=params.get("clip_index"),
            start_time=params.get("start_time"),
        )
        if not clip.is_midi_clip:
            raise ValueError("Arrangement clip is not a MIDI clip")
        note_payload = self._build_midi_notes(params.get("notes", []))
        clip.add_new_notes(note_payload)
        return {"added": len(note_payload)}

    def _get_arrangement_clip_notes(self, params):
        track = self._get_track(params["track_index"])
        clip = self._find_arrangement_clip(
            track,
            clip_index=params.get("clip_index"),
            start_time=params.get("start_time"),
        )
        if not clip.is_midi_clip:
            raise ValueError("Arrangement clip is not a MIDI clip")
        notes = self._serialize_notes(self._get_clip_notes_raw(clip))
        return {"notes": notes, "count": len(notes)}

    def _duplicate_to_arrangement(self, params):
        clip = self._get_clip(params["track_index"], params["slot_index"])
        track = self._get_track(params["track_index"])
        start_time = self._require_non_negative_time(
            params.get("start_time", self.song().current_song_time),
            "start_time",
        )
        track.duplicate_clip_to_arrangement(clip, start_time)
        return {
            "ok": True,
            "start_time": start_time,
            "source_track_index": int(params["track_index"]),
            "source_slot_index": int(params["slot_index"]),
        }
