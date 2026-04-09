from __future__ import absolute_import, print_function, unicode_literals

import unittest

from AbletonMCP_Remote_Script.arrangement_ops import ArrangementOpsMixin
from AbletonMCP_Remote_Script.song_ops import SongOpsMixin
from AbletonMCP_Remote_Script.take_lane_ops import TakeLaneOpsMixin


class _FakeClip(object):
    def __init__(self, start_time=0.0, end_time=4.0, length=4.0, name="Clip"):
        self.start_time = start_time
        self.end_time = end_time
        self.length = length
        self.name = name


class _FakeAudioTrack(object):
    has_midi_input = False

    def __init__(self):
        self.calls = []

    def create_audio_clip(self, file_path, position):
        self.calls.append((file_path, position))
        return _FakeClip(start_time=position, end_time=position + 4.0, length=4.0, name="Audio Clip")


class _ArrangementHarness(ArrangementOpsMixin):
    def __init__(self, track):
        self._track = track

    def _get_track(self, track_index):
        self.track_index = track_index
        return self._track


class _FakeLane(object):
    def __init__(self, name):
        self.name = name


class _FakeTakeLaneTrack(object):
    def __init__(self):
        self.create_take_lane_called = False

    def create_take_lane(self):
        self.create_take_lane_called = True
        return _FakeLane("Comp Lane 1")


class _TakeLaneHarness(TakeLaneOpsMixin):
    def __init__(self, track):
        self._track = track

    def _get_track(self, track_index):
        self.track_index = track_index
        return self._track


class _FakeApplication(object):
    average_process_usage = 13.37


class _SongHarness(SongOpsMixin):
    def application(self):
        return _FakeApplication()


class RemoteScriptContractTests(unittest.TestCase):
    def test_create_arrangement_audio_clip_uses_file_path_and_start_time(self):
        track = _FakeAudioTrack()
        harness = _ArrangementHarness(track)
        result = harness._create_arrangement_audio_clip(
            {"track_index": 2, "file_path": "/tmp/test.wav", "start_time": 16.0}
        )
        self.assertEqual([("/tmp/test.wav", 16.0)], track.calls)
        self.assertEqual("/tmp/test.wav", result["file_path"])
        self.assertEqual(16.0, result["start_time"])

    def test_create_take_lane_uses_track_api(self):
        track = _FakeTakeLaneTrack()
        harness = _TakeLaneHarness(track)
        result = harness._create_take_lane({"track_index": 1})
        self.assertTrue(track.create_take_lane_called)
        self.assertEqual("Comp Lane 1", result["name"])
        self.assertTrue(result["ok"])

    def test_get_cpu_load_uses_application_average_process_usage(self):
        harness = _SongHarness()
        result = harness._get_cpu_load()
        self.assertEqual({"cpu_load": 13.37}, result)
