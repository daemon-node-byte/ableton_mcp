"""Arrangement View clip operations."""

from __future__ import absolute_import, print_function, unicode_literals


class ArrangementOpsMixin(object):
    """Arrangement clip commands."""

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
        start_time = float(params["start_time"])
        length = float(params.get("length", 4.0))
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
        start_time = float(params["start_time"])
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
        clip = self._find_arrangement_clip(
            track,
            clip_index=params.get("clip_index"),
            start_time=params.get("start_time"),
        )
        track.delete_clip(clip)
        return {"ok": True}

    def _resize_arrangement_clip(self, params):
        track = self._get_track(params["track_index"])
        clip = self._find_arrangement_clip(
            track,
            clip_index=params.get("clip_index"),
            start_time=params.get("start_time"),
        )
        new_length = float(params["length"])
        clip.end_marker = clip.start_marker + new_length
        clip.loop_end = new_length
        return {
            "start_time": clip.start_time,
            "end_time": clip.end_time,
            "length": clip.length,
        }

    def _move_arrangement_clip(self, params):
        """Move an arrangement clip by recreating it at the new position."""
        track = self._get_track(params["track_index"])
        clip = self._find_arrangement_clip(
            track,
            clip_index=params.get("clip_index"),
            start_time=params.get("start_time"),
        )
        new_start_time = float(params["new_start_time"])
        is_midi_clip = clip.is_midi_clip
        length = clip.length
        stored_name = clip.name
        stored_color = clip.color
        stored_looping = clip.looping
        stored_loop_start = clip.loop_start
        stored_loop_end = clip.loop_end
        stored_notes = []

        if is_midi_clip:
            stored_notes = self._serialize_notes(self._get_clip_notes_raw(clip))

        track.delete_clip(clip)
        if is_midi_clip:
            new_clip = track.create_midi_clip(new_start_time, length)
        else:
            raise ValueError(
                "move_arrangement_clip for audio clips is still unverified because Live "
                "does not expose a direct move API and recreating audio clips requires file-path fidelity."
            )

        new_clip.name = stored_name
        new_clip.color = stored_color
        new_clip.looping = stored_looping
        new_clip.loop_start = stored_loop_start
        new_clip.loop_end = stored_loop_end

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
        note_objects = self._build_midi_notes(params.get("notes", []))
        clip.add_new_notes(note_objects)
        return {"added": len(note_objects)}

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
        start_time = float(params.get("start_time", self.song().current_song_time))
        track.duplicate_clip_to_arrangement(clip, start_time)
        return {
            "ok": True,
            "start_time": start_time,
            "source_track_index": int(params["track_index"]),
            "source_slot_index": int(params["slot_index"]),
        }
