"""Take lane operations for Live 12+."""

from __future__ import absolute_import, print_function, unicode_literals


class TakeLaneOpsMixin(object):
    """Take lane commands."""

    def _get_take_lane_track(self, params):
        track = self._get_track(params["track_index"])
        if not hasattr(track, "take_lanes"):
            raise ValueError("Take lanes are unavailable on this Live version")
        return track

    def _get_take_lane(self, track, lane_index):
        index = self._parse_non_negative_int(lane_index, "lane_index")
        take_lanes = list(getattr(track, "take_lanes", []) or [])
        if index >= len(take_lanes):
            raise ValueError(
                "Take lane index {} out of range for track with {} take lanes".format(index, len(take_lanes))
            )
        return take_lanes[index], index

    def _get_take_lanes(self, params):
        track = self._get_track(params["track_index"])
        if not hasattr(track, "take_lanes"):
            return {"take_lanes": [], "available": False}
        take_lanes = []
        for index, lane in enumerate(track.take_lanes):
            take_lanes.append({
                "index": index,
                "name": lane.name,
                "clip_count": len(lane.arrangement_clips) if hasattr(lane, "arrangement_clips") else 0,
            })
        return {"take_lanes": take_lanes, "available": True}

    def _create_take_lane(self, params):
        track = self._get_track(params["track_index"])
        if not hasattr(track, "create_take_lane"):
            raise ValueError("Take lane creation is unavailable in this Live version")
        lane = track.create_take_lane()
        return {"ok": True, "name": lane.name if lane is not None else "", "stability": "likely-complete"}

    def _set_take_lane_name(self, params):
        track = self._get_take_lane_track(params)
        lane, _lane_index = self._get_take_lane(track, params["lane_index"])
        lane.name = str(params["name"])
        return {"name": lane.name}

    def _create_midi_clip_in_lane(self, params):
        track = self._get_take_lane_track(params)
        if not bool(getattr(track, "has_midi_input", False)):
            raise ValueError("create_midi_clip_in_lane requires a MIDI track")
        lane, _lane_index = self._get_take_lane(track, params["lane_index"])
        if not hasattr(lane, "create_midi_clip"):
            raise ValueError("create_midi_clip is unavailable on this take lane")
        start_time = float(params.get("start_time", 0.0))
        length = float(params.get("length", 4.0))
        if start_time < 0.0:
            raise ValueError("start_time must be >= 0")
        if length <= 0.0:
            raise ValueError("length must be > 0")
        clip = lane.create_midi_clip(start_time, length)
        return {
            "start_time": clip.start_time,
            "end_time": clip.end_time,
            "length": clip.length,
            "name": clip.name,
        }

    def _get_clips_in_take_lane(self, params):
        track = self._get_take_lane_track(params)
        lane, _lane_index = self._get_take_lane(track, params["lane_index"])
        clips = self._get_arrangement_clips_for_container(lane)
        return {"clips": clips}

    def _delete_take_lane(self, params):
        track = self._get_take_lane_track(params)
        _lane, lane_index = self._get_take_lane(track, params["lane_index"])
        if hasattr(track, "delete_take_lane"):
            track.delete_take_lane(lane_index)
            return {"ok": True}
        raise ValueError("delete_take_lane is unavailable on this Live Python surface")
