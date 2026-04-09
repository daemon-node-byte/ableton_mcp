from __future__ import absolute_import, print_function, unicode_literals

import tempfile
import unittest

from AbletonMCP_Remote_Script.arrangement_ops import ArrangementOpsMixin
from AbletonMCP_Remote_Script.core import CoreOpsMixin
from AbletonMCP_Remote_Script.song_ops import SongOpsMixin
from AbletonMCP_Remote_Script.take_lane_ops import TakeLaneOpsMixin


class _FakeClip(object):
    def __init__(
        self,
        start_time=0.0,
        end_time=4.0,
        length=4.0,
        name="Clip",
        is_midi_clip=True,
        is_audio_clip=False,
    ):
        self.start_time = start_time
        self.end_time = end_time
        self.length = length
        self.name = name
        self.color = 7
        self.looping = True
        self._loop_start = 0.0
        self._loop_end = length
        self._start_marker = 0.0
        self._end_marker = length
        self.is_midi_clip = is_midi_clip
        self.is_audio_clip = is_audio_clip
        self.notes_added = []

    @property
    def loop_start(self):
        return self._loop_start

    @loop_start.setter
    def loop_start(self, value):
        self._loop_start = float(value)

    @property
    def loop_end(self):
        return self._loop_end

    @loop_end.setter
    def loop_end(self, value):
        self._loop_end = float(value)
        self.length = self._loop_end - self._loop_start
        self.end_time = self.start_time + self.length

    @property
    def start_marker(self):
        return self._start_marker

    @start_marker.setter
    def start_marker(self, value):
        self._start_marker = float(value)
        self.length = self._end_marker - self._start_marker
        self.end_time = self.start_time + self.length

    @property
    def end_marker(self):
        return self._end_marker

    @end_marker.setter
    def end_marker(self, value):
        self._end_marker = float(value)
        self.length = self._end_marker - self._start_marker
        self.end_time = self.start_time + self.length

    def add_new_notes(self, notes):
        self.notes_added.extend(notes)

    def get_notes(self, from_time, from_pitch, time_span, pitch_span):
        return [
            {
                "pitch": 60,
                "start_time": 0.0,
                "duration": 0.5,
                "velocity": 100,
                "mute": False,
            }
        ]


class _FakeAudioTrack(object):
    has_midi_input = False

    def __init__(self):
        self.calls = []
        self.arrangement_clips = []

    def create_audio_clip(self, file_path, position):
        self.calls.append((file_path, position))
        clip = _FakeClip(
            start_time=position,
            end_time=position + 4.0,
            length=4.0,
            name="Audio Clip",
            is_midi_clip=False,
            is_audio_clip=True,
        )
        self.arrangement_clips.append(clip)
        return clip

    def delete_clip(self, clip):
        self.arrangement_clips.remove(clip)


class _FakeMidiTrack(object):
    has_midi_input = True

    def __init__(self, arrangement_clips=None):
        self.arrangement_clips = list(arrangement_clips or [])
        self.deleted_clips = []

    def create_midi_clip(self, start_time, length):
        clip = _FakeClip(start_time=start_time, end_time=start_time + length, length=length, name="Moved Clip")
        self.arrangement_clips.append(clip)
        return clip

    def delete_clip(self, clip):
        self.deleted_clips.append(clip)
        self.arrangement_clips.remove(clip)


class _ArrangementHarness(ArrangementOpsMixin, CoreOpsMixin):
    def __init__(self, track):
        self._track = track

    def _get_track(self, track_index):
        self.track_index = track_index
        return self._track

    def _get_clip(self, track_index, slot_index):
        return _FakeClip()

    def song(self):
        return type("Song", (), {"current_song_time": 0.0})()


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


class _CoreHarness(CoreOpsMixin):
    pass


class _FakeNotesClip(object):
    def __init__(self):
        self.extended_calls = []
        self.length = 4.0

    def get_notes_extended(self, from_pitch, pitch_span, from_time, time_span):
        self.extended_calls.append((from_pitch, pitch_span, from_time, time_span))
        return [{"pitch": 60, "start_time": 0.0, "duration": 0.5, "velocity": 100, "mute": False}]


class RemoteScriptContractTests(unittest.TestCase):
    def test_create_arrangement_audio_clip_uses_file_path_and_start_time(self):
        track = _FakeAudioTrack()
        harness = _ArrangementHarness(track)
        with tempfile.NamedTemporaryFile(suffix=".wav") as temp_audio_file:
            result = harness._create_arrangement_audio_clip(
                {"track_index": 2, "file_path": temp_audio_file.name, "start_time": 16.0}
            )
        self.assertEqual([(temp_audio_file.name, 16.0)], track.calls)
        self.assertEqual(temp_audio_file.name, result["file_path"])
        self.assertEqual(16.0, result["start_time"])

    def test_create_arrangement_audio_clip_requires_absolute_existing_path(self):
        track = _FakeAudioTrack()
        harness = _ArrangementHarness(track)
        with self.assertRaisesRegex(ValueError, "absolute path"):
            harness._create_arrangement_audio_clip(
                {"track_index": 2, "file_path": "relative.wav", "start_time": 16.0}
            )
        with self.assertRaisesRegex(ValueError, "does not exist"):
            harness._create_arrangement_audio_clip(
                {"track_index": 2, "file_path": "/tmp/ableton-mcp-missing.wav", "start_time": 16.0}
            )

    def test_delete_arrangement_clip_requires_exact_selector(self):
        clip = _FakeClip(start_time=8.0)
        track = _FakeMidiTrack([clip])
        harness = _ArrangementHarness(track)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            harness._delete_arrangement_clip({"track_index": 0})
        with self.assertRaisesRegex(ValueError, "not both"):
            harness._delete_arrangement_clip({"track_index": 0, "clip_index": 0, "start_time": 8.0})

    def test_resize_arrangement_clip_requires_positive_length(self):
        clip = _FakeClip(start_time=8.0, length=4.0, end_time=12.0)
        track = _FakeMidiTrack([clip])
        harness = _ArrangementHarness(track)
        with self.assertRaisesRegex(ValueError, "length must be > 0"):
            harness._resize_arrangement_clip({"track_index": 0, "start_time": 8.0, "length": 0.0})
        result = harness._resize_arrangement_clip({"track_index": 0, "start_time": 8.0, "length": 6.0})
        self.assertEqual(6.0, result["length"])
        self.assertEqual(14.0, result["end_time"])

    def test_move_arrangement_clip_rejects_audio_clips(self):
        clip = _FakeClip(
            start_time=8.0,
            length=4.0,
            end_time=12.0,
            is_midi_clip=False,
            is_audio_clip=True,
        )
        track = _FakeAudioTrack()
        track.arrangement_clips.append(clip)
        harness = _ArrangementHarness(track)
        with self.assertRaisesRegex(ValueError, "MIDI clips only"):
            harness._move_arrangement_clip({"track_index": 0, "start_time": 8.0, "new_start_time": 16.0})

    def test_move_arrangement_clip_restores_notes_for_midi_clips(self):
        clip = _FakeClip(start_time=8.0, length=4.0, end_time=12.0)
        track = _FakeMidiTrack([clip])
        harness = _ArrangementHarness(track)
        result = harness._move_arrangement_clip({"track_index": 0, "start_time": 8.0, "new_start_time": 16.0})
        self.assertEqual(16.0, result["start_time"])
        self.assertEqual(1, result["notes_restored"])
        self.assertEqual(1, len(track.arrangement_clips))
        self.assertEqual(16.0, track.arrangement_clips[0].start_time)
        self.assertEqual(1, len(track.arrangement_clips[0].notes_added))

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

    def test_build_midi_note_returns_live_note_dict_shape(self):
        harness = _CoreHarness()
        note = harness._build_midi_note(
            {"pitch": 60, "time": 1.5, "duration": 0.25, "velocity": 99, "mute": True}
        )
        self.assertEqual(
            {
                "pitch": 60,
                "start_time": 1.5,
                "duration": 0.25,
                "velocity": 99.0,
                "mute": True,
            },
            note,
        )

    def test_build_midi_notes_returns_list_payload(self):
        harness = _CoreHarness()
        payload = harness._build_midi_notes(
            [{"pitch": 60, "time": 0.0, "duration": 0.5, "velocity": 100, "mute": False}]
        )
        self.assertEqual(
            [
                {
                    "pitch": 60,
                    "start_time": 0.0,
                    "duration": 0.5,
                    "velocity": 100.0,
                    "mute": False,
                }
            ],
            payload,
        )

    def test_get_clip_notes_raw_uses_live_extended_argument_order(self):
        harness = _CoreHarness()
        clip = _FakeNotesClip()
        result = harness._get_clip_notes_raw(clip)
        self.assertEqual([(0, 128, 0.0, 4.0)], clip.extended_calls)
        self.assertEqual(60, result[0]["pitch"])
