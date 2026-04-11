from __future__ import absolute_import, print_function, unicode_literals

import unittest

from AbletonMCP_Remote_Script.core import CoreOpsMixin
from AbletonMCP_Remote_Script.track_ops import TrackOpsMixin


class _FakeValueParameter(object):
    def __init__(self, value):
        self.value = value


class _FakeMixerDevice(object):
    def __init__(self, volume=0.5, pan=0.0, send_values=None):
        self.volume = _FakeValueParameter(volume)
        self.panning = _FakeValueParameter(pan)
        self.sends = [_FakeValueParameter(value) for value in list(send_values or [])]


class _FakeTrack(object):
    def __init__(
        self,
        name,
        color=7,
        mute=False,
        solo=False,
        arm=False,
        can_be_armed=True,
        is_foldable=False,
        fold_state=False,
        send_values=None,
    ):
        self.name = name
        self.color = color
        self.mute = mute
        self.solo = solo
        self.arm = arm
        self.can_be_armed = can_be_armed
        self.is_foldable = is_foldable
        self.fold_state = fold_state
        self.mixer_device = _FakeMixerDevice(send_values=send_values)
        self.devices = []
        self.clip_slots = []
        self.has_midi_input = True


class _FakeMasterTrack(object):
    def __init__(self, name="Master"):
        self.name = name


class _FakeSongView(object):
    def __init__(self):
        self.selected_track = None


class _FakeSong(object):
    def __init__(self, tracks, return_tracks=None, master_track=None):
        self.tracks = list(tracks)
        self.return_tracks = list(return_tracks or [])
        self.master_track = master_track or _FakeMasterTrack()
        self.view = _FakeSongView()


class TrackHarness(TrackOpsMixin, CoreOpsMixin):
    def __init__(self, song):
        self._song = song

    def song(self):
        return self._song


class TrackOpsContractTests(unittest.TestCase):
    def build_harness(self):
        return TrackHarness(
            _FakeSong(
                tracks=[
                    _FakeTrack("Track 1", send_values=[0.25, 0.5]),
                    _FakeTrack("Group Track", is_foldable=True, fold_state=False),
                    _FakeTrack("Unarmable", can_be_armed=False),
                ],
                return_tracks=[
                    _FakeTrack("Return A", send_values=[]),
                    _FakeTrack("Return B", send_values=[]),
                ],
            )
        )

    def test_track_name_color_mute_and_solo_mutations_update_target_track(self):
        harness = self.build_harness()
        self.assertEqual({"name": "Bass"}, harness._set_track_name({"track_index": 0, "name": "Bass"}))
        self.assertEqual({"color": 16711935}, harness._set_track_color({"track_index": 0, "color": 16711935}))
        self.assertEqual({"mute": True}, harness._set_track_mute({"track_index": 0, "mute": True}))
        self.assertEqual({"solo": True}, harness._set_track_solo({"track_index": 0, "solo": True}))
        self.assertEqual("Bass", harness.song().tracks[0].name)
        self.assertEqual(16711935, harness.song().tracks[0].color)
        self.assertTrue(harness.song().tracks[0].mute)
        self.assertTrue(harness.song().tracks[0].solo)

    def test_track_volume_and_pan_clamp_to_supported_ranges(self):
        harness = self.build_harness()
        volume_result = harness._set_track_volume({"track_index": 0, "volume": 2.5})
        pan_result = harness._set_track_pan({"track_index": 0, "pan": -3.0})
        self.assertEqual(1.0, volume_result["volume"])
        self.assertEqual(-1.0, pan_result["pan"])

    def test_set_track_arm_requires_armable_target(self):
        harness = self.build_harness()
        success_result = harness._set_track_arm({"track_index": 0, "arm": True})
        self.assertEqual({"arm": True}, success_result)
        with self.assertRaisesRegex(ValueError, "cannot be armed"):
            harness._set_track_arm({"track_index": 2, "arm": True})

    def test_fold_and_unfold_require_foldable_track(self):
        harness = self.build_harness()
        self.assertEqual({"fold_state": True}, harness._fold_track({"track_index": 1}))
        self.assertTrue(harness.song().tracks[1].fold_state)
        self.assertEqual({"fold_state": False}, harness._unfold_track({"track_index": 1}))
        self.assertFalse(harness.song().tracks[1].fold_state)
        with self.assertRaisesRegex(ValueError, "not foldable"):
            harness._fold_track({"track_index": 0})
        with self.assertRaisesRegex(ValueError, "not foldable"):
            harness._unfold_track({"track_index": 0})

    def test_set_send_level_clamps_and_checks_bounds(self):
        harness = self.build_harness()
        result = harness._set_send_level({"track_index": 0, "send_index": 1, "level": 9.0})
        self.assertEqual({"send_index": 1, "level": 1.0}, result)
        with self.assertRaisesRegex(ValueError, "Send index 9 out of range"):
            harness._set_send_level({"track_index": 0, "send_index": 9, "level": 0.1})

    def test_return_track_enumeration_and_info_use_stable_lookup(self):
        harness = self.build_harness()
        result = harness._get_return_tracks()
        self.assertEqual(2, len(result["return_tracks"]))
        self.assertEqual("Return A", result["return_tracks"][0]["name"])
        info = harness._get_return_track_info({"return_index": 1})
        self.assertEqual(1, info["index"])
        self.assertEqual("Return B", info["name"])
        with self.assertRaisesRegex(ValueError, "Return track index 4 out of range"):
            harness._get_return_track_info({"return_index": 4})

    def test_return_volume_and_pan_clamp_and_check_bounds(self):
        harness = self.build_harness()
        volume_result = harness._set_return_volume({"return_index": 0, "volume": 3.0})
        pan_result = harness._set_return_pan({"return_index": 1, "pan": -9.0})
        self.assertEqual(1.0, volume_result["volume"])
        self.assertEqual(-1.0, pan_result["pan"])
        with self.assertRaisesRegex(ValueError, "Return track index 9 out of range"):
            harness._set_return_volume({"return_index": 9, "volume": 0.5})
        with self.assertRaisesRegex(ValueError, "Return track index 9 out of range"):
            harness._set_return_pan({"return_index": 9, "pan": 0.2})

    def test_select_track_requires_exactly_one_selector(self):
        harness = self.build_harness()
        with self.assertRaisesRegex(ValueError, "exactly one"):
            harness._select_track({})
        with self.assertRaisesRegex(ValueError, "exactly one"):
            harness._select_track({"track_index": 0, "master": True})
        with self.assertRaisesRegex(ValueError, "exactly one"):
            harness._select_track({"track_index": 0, "return_index": 0})

    def test_select_track_supports_track_return_and_master_targets(self):
        harness = self.build_harness()
        regular_result = harness._select_track({"track_index": 0})
        self.assertEqual("track", regular_result["selection_type"])
        self.assertEqual(0, regular_result["selected_track_index"])
        self.assertEqual(harness.song().tracks[0], harness.song().view.selected_track)

        return_result = harness._select_track({"return_index": 1})
        self.assertEqual("return_track", return_result["selection_type"])
        self.assertEqual(-1, return_result["selected_track_index"])
        self.assertEqual(1, return_result["return_index"])
        self.assertEqual(harness.song().return_tracks[1], harness.song().view.selected_track)

        master_result = harness._select_track({"master": True})
        self.assertEqual("master_track", master_result["selection_type"])
        self.assertEqual(-1, master_result["selected_track_index"])
        self.assertEqual(harness.song().master_track, harness.song().view.selected_track)

    def test_get_selected_track_distinguishes_track_return_master_and_unknown(self):
        harness = self.build_harness()

        harness.song().view.selected_track = harness.song().tracks[0]
        track_result = harness._get_selected_track()
        self.assertEqual(
            {
                "selection_type": "track",
                "name": "Track 1",
                "index": 0,
                "track_index": 0,
                "return_index": None,
            },
            track_result,
        )

        harness.song().view.selected_track = harness.song().return_tracks[0]
        return_result = harness._get_selected_track()
        self.assertEqual("return_track", return_result["selection_type"])
        self.assertEqual(-1, return_result["index"])
        self.assertEqual(0, return_result["return_index"])

        harness.song().view.selected_track = harness.song().master_track
        master_result = harness._get_selected_track()
        self.assertEqual("master_track", master_result["selection_type"])
        self.assertEqual("Master", master_result["name"])

        class _UnknownSelection(object):
            name = "Ghost"

        harness.song().view.selected_track = _UnknownSelection()
        unknown_result = harness._get_selected_track()
        self.assertEqual(
            {
                "selection_type": "unknown",
                "name": "Ghost",
                "index": -1,
                "track_index": None,
                "return_index": None,
            },
            unknown_result,
        )
