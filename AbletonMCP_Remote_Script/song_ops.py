"""Song, transport, locator, and session-level operations."""

from __future__ import absolute_import, print_function, unicode_literals


class SongOpsMixin(object):
    """Session and transport commands."""

    def _health_check(self):
        song = self.song()
        return {
            "status": "ok",
            "tempo": song.tempo,
            "is_playing": song.is_playing,
            "track_count": len(song.tracks),
        }

    def _get_session_info(self):
        song = self.song()
        tracks = []
        for index, track in enumerate(song.tracks):
            track_data = {
                "index": index,
                "name": track.name,
                "type": "midi" if track.has_midi_input else "audio",
                "color": track.color,
                "mute": track.mute,
                "solo": track.solo,
                "volume": round(track.mixer_device.volume.value, 4),
                "pan": round(track.mixer_device.panning.value, 4),
            }
            try:
                track_data["arm"] = track.arm
            except Exception:
                track_data["arm"] = False
            tracks.append(track_data)

        return_tracks = []
        for index, return_track in enumerate(song.return_tracks):
            return_tracks.append({
                "index": index,
                "name": return_track.name,
                "color": return_track.color,
                "mute": return_track.mute,
            })

        scenes = [{"index": index, "name": scene.name} for index, scene in enumerate(song.scenes)]

        return {
            "tempo": song.tempo,
            "signature_numerator": song.signature_numerator,
            "signature_denominator": song.signature_denominator,
            "is_playing": song.is_playing,
            "is_recording": song.record_mode,
            "current_song_time": round(song.current_song_time, 4),
            "loop_start": song.loop_start,
            "loop_length": song.loop_length,
            "loop_on": song.loop,
            "metronome": song.metronome,
            "track_count": len(song.tracks),
            "return_track_count": len(song.return_tracks),
            "scene_count": len(song.scenes),
            "tracks": tracks,
            "return_tracks": return_tracks,
            "scenes": scenes,
        }

    def _get_current_song_time(self):
        return {"current_song_time": round(self.song().current_song_time, 6)}

    def _set_current_song_time(self, params):
        self.song().current_song_time = float(params["time"])
        return {"current_song_time": self.song().current_song_time}

    def _set_tempo(self, params):
        tempo = float(params["tempo"])
        if not (20.0 <= tempo <= 999.0):
            raise ValueError("Tempo {} out of range [20, 999]".format(tempo))
        self.song().tempo = tempo
        return {"tempo": self.song().tempo}

    def _set_time_signature(self, params):
        numerator = int(params.get("numerator", 4))
        denominator = int(params.get("denominator", 4))
        self.song().signature_numerator = numerator
        self.song().signature_denominator = denominator
        return {"numerator": numerator, "denominator": denominator}

    def _start_playback(self):
        self.song().start_playing()
        return {"is_playing": True}

    def _stop_playback(self):
        self.song().stop_playing()
        return {"is_playing": False}

    def _continue_playback(self):
        self.song().continue_playing()
        return {"is_playing": True}

    def _start_recording(self):
        self.song().record_mode = 1
        return {"recording": True}

    def _stop_recording(self):
        self.song().record_mode = 0
        return {"recording": False}

    def _toggle_session_record(self):
        self.song().session_record = not self.song().session_record
        return {"session_record": self.song().session_record}

    def _toggle_arrangement_record(self):
        current = self.song().record_mode
        self.song().record_mode = 0 if current else 1
        return {"record_mode": self.song().record_mode}

    def _set_metronome(self, params):
        self.song().metronome = bool(params["enabled"])
        return {"metronome": self.song().metronome}

    def _tap_tempo(self):
        self.song().tap_tempo()
        return {"tempo": self.song().tempo}

    def _undo(self):
        self.song().undo()
        return {"ok": True}

    def _redo(self):
        self.song().redo()
        return {"ok": True}

    def _capture_midi(self):
        self.song().capture_midi()
        return {"ok": True}

    def _re_enable_automation(self):
        self.song().re_enable_automation()
        return {"ok": True}

    def _set_arrangement_loop(self, params):
        if "start" in params:
            self.song().loop_start = float(params["start"])
        if "length" in params:
            self.song().loop_length = float(params["length"])
        if "enabled" in params:
            self.song().loop = bool(params["enabled"])
        return {
            "loop_start": self.song().loop_start,
            "loop_length": self.song().loop_length,
            "loop_on": self.song().loop,
        }

    def _get_cpu_load(self):
        return {"cpu_load": self.application().average_process_usage}

    def _get_session_path(self):
        return {"path": self.song().file_path}

    def _get_locators(self):
        locators = []
        for index, locator in enumerate(self.song().cue_points):
            locators.append({"index": index, "name": locator.name, "time": locator.time})
        return {"locators": locators}

    def _create_locator(self, params):
        song = self.song()
        locator_time = float(params.get("time", song.current_song_time))
        locator_name = str(params.get("name", "Marker"))
        previous_time = song.current_song_time
        song.current_song_time = locator_time
        try:
            song.set_or_delete_cue()
            for cue in song.cue_points:
                if abs(cue.time - locator_time) < 0.001:
                    cue.name = locator_name
                    break
        finally:
            song.current_song_time = previous_time
        return {"ok": True, "time": locator_time, "name": locator_name}

    def _delete_locator(self, params):
        song = self.song()
        locator_index = int(params["locator_index"])
        cue_points = list(song.cue_points)
        if locator_index < 0 or locator_index >= len(cue_points):
            raise ValueError("Invalid locator index {}".format(locator_index))
        previous_time = song.current_song_time
        song.current_song_time = cue_points[locator_index].time
        try:
            song.set_or_delete_cue()
        finally:
            song.current_song_time = previous_time
        return {"ok": True}

    def _jump_to_time(self, params):
        self.song().current_song_time = float(params["time"])
        return {"current_song_time": self.song().current_song_time}

    def _jump_to_next_cue(self):
        self.song().jump_to_next_cue()
        return {"current_song_time": self.song().current_song_time}

    def _jump_to_prev_cue(self):
        self.song().jump_to_prev_cue()
        return {"current_song_time": self.song().current_song_time}

    def _set_punch_in(self, params):
        self.song().punch_in = bool(params["enabled"])
        return {"punch_in": self.song().punch_in}

    def _set_punch_out(self, params):
        self.song().punch_out = bool(params["enabled"])
        return {"punch_out": self.song().punch_out}

    def _trigger_back_to_arrangement(self):
        self.song().back_to_arranger = False
        return {"ok": True}

    def _get_back_to_arrangement(self):
        return {"back_to_arranger": self.song().back_to_arranger}

    def _set_session_automation_record(self, params):
        self.song().session_automation_record = bool(params["enabled"])
        return {"session_automation_record": self.song().session_automation_record}

    def _get_session_automation_record(self):
        return {"session_automation_record": self.song().session_automation_record}

    def _set_overdub(self, params):
        self.song().overdub = bool(params["enabled"])
        return {"overdub": self.song().overdub}

    def _stop_all_clips(self):
        self.song().stop_all_clips()
        return {"ok": True}

    def _get_arrangement_length(self):
        try:
            return {"arrangement_length": self.song().song_length}
        except Exception:
            max_end = 0.0
            for track in self.song().tracks:
                if hasattr(track, "arrangement_clips"):
                    for clip in track.arrangement_clips:
                        if clip.end_time > max_end:
                            max_end = clip.end_time
            return {"arrangement_length": max_end}
