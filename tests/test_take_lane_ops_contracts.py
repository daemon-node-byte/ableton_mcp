from __future__ import absolute_import, print_function, unicode_literals

import unittest

from AbletonMCP_Remote_Script.core import CoreOpsMixin
from AbletonMCP_Remote_Script.take_lane_ops import TakeLaneOpsMixin


class _FakeClip(object):
    def __init__(self, start_time=0.0, length=4.0, name=""):
        self.start_time = start_time
        self.length = length
        self.end_time = start_time + length
        self.name = name
        self.color = 9611263
        self.looping = True
        self.loop_start = 0.0
        self.loop_end = length
        self.is_midi_clip = True
        self.is_audio_clip = False
        self.is_playing = False
        self.muted = False


class _FakeTakeLane(object):
    def __init__(self, name="Lane", can_create_clip=True):
        self.name = name
        self.arrangement_clips = []
        if can_create_clip:
            self.create_midi_clip = self._create_midi_clip

    def _create_midi_clip(self, start_time, length):
        clip = _FakeClip(start_time=start_time, length=length)
        self.arrangement_clips.append(clip)
        return clip


class _FakeTakeLaneTrack(object):
    def __init__(self, take_lanes=None, has_midi_input=True, expose_take_lanes=True, expose_delete=False):
        self.has_midi_input = has_midi_input
        self.create_take_lane_called = False
        self.deleted_lane_indices = []
        if expose_take_lanes:
            self.take_lanes = list(take_lanes or [])
        if expose_delete:
            self.delete_take_lane = self._delete_take_lane

    def create_take_lane(self):
        self.create_take_lane_called = True
        lane = _FakeTakeLane("Lane")
        self.take_lanes.append(lane)
        return lane

    def _delete_take_lane(self, lane_index):
        self.deleted_lane_indices.append(lane_index)
        del self.take_lanes[lane_index]


class _TakeLaneHarness(TakeLaneOpsMixin, CoreOpsMixin):
    def __init__(self, track):
        self._track = track

    def _get_track(self, track_index):
        self.track_index = track_index
        return self._track


class TakeLaneOpsContractTests(unittest.TestCase):
    def test_get_take_lanes_reports_unavailable_when_surface_missing(self):
        harness = _TakeLaneHarness(_FakeTakeLaneTrack(expose_take_lanes=False))
        self.assertEqual({"take_lanes": [], "available": False}, harness._get_take_lanes({"track_index": 0}))

    def test_create_take_lane_uses_track_api(self):
        track = _FakeTakeLaneTrack()
        harness = _TakeLaneHarness(track)
        result = harness._create_take_lane({"track_index": 0})
        self.assertTrue(track.create_take_lane_called)
        self.assertEqual({"ok": True, "name": "Lane", "stability": "likely-complete"}, result)

    def test_set_take_lane_name_updates_lane(self):
        track = _FakeTakeLaneTrack(take_lanes=[_FakeTakeLane("Original")])
        harness = _TakeLaneHarness(track)
        result = harness._set_take_lane_name({"track_index": 0, "lane_index": 0, "name": "Renamed"})
        self.assertEqual({"name": "Renamed"}, result)
        self.assertEqual("Renamed", track.take_lanes[0].name)

    def test_take_lane_commands_raise_stable_error_for_bad_lane_index(self):
        track = _FakeTakeLaneTrack(take_lanes=[_FakeTakeLane("Only Lane")])
        harness = _TakeLaneHarness(track)
        for command in (
            lambda: harness._set_take_lane_name({"track_index": 0, "lane_index": 3, "name": "Nope"}),
            lambda: harness._create_midi_clip_in_lane({"track_index": 0, "lane_index": 3}),
            lambda: harness._get_clips_in_take_lane({"track_index": 0, "lane_index": 3}),
            lambda: harness._delete_take_lane({"track_index": 0, "lane_index": 3}),
        ):
            with self.assertRaisesRegex(ValueError, "Take lane index 3 out of range"):
                command()

    def test_create_midi_clip_in_lane_requires_midi_track(self):
        track = _FakeTakeLaneTrack(take_lanes=[_FakeTakeLane("Audio Lane")], has_midi_input=False)
        harness = _TakeLaneHarness(track)
        with self.assertRaisesRegex(ValueError, "requires a MIDI track"):
            harness._create_midi_clip_in_lane({"track_index": 0, "lane_index": 0})

    def test_create_midi_clip_in_lane_validates_times(self):
        track = _FakeTakeLaneTrack(take_lanes=[_FakeTakeLane("Lane")])
        harness = _TakeLaneHarness(track)
        with self.assertRaisesRegex(ValueError, "start_time must be >= 0"):
            harness._create_midi_clip_in_lane({"track_index": 0, "lane_index": 0, "start_time": -1.0})
        with self.assertRaisesRegex(ValueError, "length must be > 0"):
            harness._create_midi_clip_in_lane({"track_index": 0, "lane_index": 0, "length": 0.0})

    def test_create_midi_clip_in_lane_returns_clip_payload(self):
        track = _FakeTakeLaneTrack(take_lanes=[_FakeTakeLane("Lane")])
        harness = _TakeLaneHarness(track)
        result = harness._create_midi_clip_in_lane(
            {"track_index": 0, "lane_index": 0, "start_time": 8.0, "length": 2.0}
        )
        self.assertEqual({"start_time": 8.0, "end_time": 10.0, "length": 2.0, "name": ""}, result)

    def test_get_clips_in_take_lane_serializes_arrangement_clips(self):
        lane = _FakeTakeLane("Lane")
        lane.arrangement_clips.append(_FakeClip(start_time=8.0, length=2.0, name="Take 1"))
        track = _FakeTakeLaneTrack(take_lanes=[lane])
        harness = _TakeLaneHarness(track)
        result = harness._get_clips_in_take_lane({"track_index": 0, "lane_index": 0})
        self.assertEqual(1, len(result["clips"]))
        self.assertEqual("Take 1", result["clips"][0]["name"])
        self.assertEqual(8.0, result["clips"][0]["start_time"])

    def test_delete_take_lane_uses_track_api_when_available(self):
        track = _FakeTakeLaneTrack(take_lanes=[_FakeTakeLane("Lane")], expose_delete=True)
        harness = _TakeLaneHarness(track)
        result = harness._delete_take_lane({"track_index": 0, "lane_index": 0})
        self.assertEqual({"ok": True}, result)
        self.assertEqual([0], track.deleted_lane_indices)
        self.assertEqual([], track.take_lanes)

    def test_delete_take_lane_raises_stable_error_when_unavailable(self):
        track = _FakeTakeLaneTrack(take_lanes=[_FakeTakeLane("Lane")], expose_delete=False)
        harness = _TakeLaneHarness(track)
        with self.assertRaisesRegex(ValueError, "delete_take_lane is unavailable"):
            harness._delete_take_lane({"track_index": 0, "lane_index": 0})


if __name__ == "__main__":
    unittest.main()
