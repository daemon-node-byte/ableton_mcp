from __future__ import absolute_import, print_function, unicode_literals

import unittest

from AbletonMCP_Remote_Script.core import CoreOpsMixin
from AbletonMCP_Remote_Script.device_ops import DeviceOpsMixin


class _FakeParameter(object):
    def __init__(
        self,
        name="Device On",
        value=1.0,
        minimum=0.0,
        maximum=1.0,
        is_enabled=True,
        is_quantized=False,
    ):
        self.name = name
        self.value = value
        self.min = minimum
        self.max = maximum
        self.is_enabled = is_enabled
        self.is_quantized = is_quantized

    def __str__(self):
        return str(self.value)


class _FakeDeviceView(object):
    def __init__(self):
        self.is_collapsed = True


class _FakeDevice(object):
    def __init__(self, name, class_name="InstrumentDevice", parameters=None):
        self.name = name
        self.class_name = class_name
        self.type = 1
        self.is_active = True
        self.parameters = list(parameters or [_FakeParameter()])
        self.can_have_chains = False
        self.can_have_drum_pads = False
        self.view = _FakeDeviceView()


class _FakeTrackView(object):
    def __init__(self):
        self.selected_device = None


class _FakeTrack(object):
    def __init__(self, devices=None):
        self.devices = list(devices or [])
        self.view = _FakeTrackView()

    def delete_device(self, index):
        del self.devices[index]


class _FakeSongView(object):
    def __init__(self):
        self.selected_track = None
        self.selected_calls = []

    def select_device(self, device):
        self.selected_calls.append(device)


class _FakeSong(object):
    def __init__(self, tracks=None, supports_move_device=False):
        self.tracks = list(tracks or [])
        self.view = _FakeSongView()
        if supports_move_device:
            self.move_device = self._move_device

    def _move_device(self, device, target, target_position):
        source_track = None
        for track in self.tracks:
            if device in track.devices:
                source_track = track
                break
        if source_track is None:
            raise RuntimeError("device not found")
        source_track.devices.remove(device)
        insert_index = min(int(target_position), len(target.devices))
        target.devices.insert(insert_index, device)
        return insert_index


class DeviceHarness(DeviceOpsMixin, CoreOpsMixin):
    def __init__(self, song):
        self._song = song

    def song(self):
        return self._song


class _ProxyCloneTrack(object):
    def __init__(self, devices=None):
        self._devices = list(devices or [])

    @property
    def devices(self):
        clones = []
        for device in self._devices:
            clone = _FakeDevice(
                device.name,
                class_name=device.class_name,
                parameters=[_FakeParameter(
                    name=parameter.name,
                    value=parameter.value,
                    minimum=parameter.min,
                    maximum=parameter.max,
                    is_enabled=parameter.is_enabled,
                    is_quantized=parameter.is_quantized,
                ) for parameter in device.parameters],
            )
            clone.type = device.type
            clones.append(clone)
        return clones


class CoreResultHarness(CoreOpsMixin):
    def _device_is_plugin(self, device):
        return str(getattr(device, "class_name", "") or "") == "PluginDevice"

    def _device_plugin_flags(self, device):
        return {
            "is_vst": False,
            "is_au": False,
        }


class DeviceContractTests(unittest.TestCase):
    def test_get_track_devices_marks_plugindevice_as_plugin(self):
        track = _FakeTrack([_FakeDevice("Plugin", class_name="PluginDevice")])
        harness = DeviceHarness(_FakeSong([track]))
        result = harness._get_track_devices({"track_index": 0})
        self.assertTrue(result["devices"][0]["is_plugin"])
        self.assertFalse(result["devices"][0]["is_vst"])
        self.assertFalse(result["devices"][0]["is_au"])

    def test_get_device_parameters_marks_plugins_with_configure_note(self):
        track = _FakeTrack([_FakeDevice("Plugin", class_name="PluginDevice")])
        harness = DeviceHarness(_FakeSong([track]))
        result = harness._get_device_parameters({"track_index": 0, "device_index": 0})
        self.assertTrue(result["is_plugin"])
        self.assertIn("Configured", result["note"])

    def test_set_device_parameter_updates_value(self):
        parameter = _FakeParameter(name="Dry/Wet", value=0.2, minimum=0.0, maximum=1.0)
        track = _FakeTrack([_FakeDevice("Effect", parameters=[parameter])])
        harness = DeviceHarness(_FakeSong([track]))
        result = harness._set_device_parameter(
            {"track_index": 0, "device_index": 0, "parameter_index": 0, "value": 0.75}
        )
        self.assertEqual(0.75, result["value"])
        self.assertEqual(0.75, parameter.value)

    def test_set_device_parameter_rejects_disabled_and_out_of_range_values(self):
        disabled_parameter = _FakeParameter(name="Dry/Wet", is_enabled=False)
        disabled_track = _FakeTrack([_FakeDevice("Effect", parameters=[disabled_parameter])])
        disabled_harness = DeviceHarness(_FakeSong([disabled_track]))
        with self.assertRaisesRegex(ValueError, "not enabled"):
            disabled_harness._set_device_parameter(
                {"track_index": 0, "device_index": 0, "parameter_index": 0, "value": 0.5}
            )

        ranged_parameter = _FakeParameter(name="Dry/Wet", value=0.2, minimum=0.0, maximum=1.0)
        ranged_track = _FakeTrack([_FakeDevice("Effect", parameters=[ranged_parameter])])
        ranged_harness = DeviceHarness(_FakeSong([ranged_track]))
        with self.assertRaisesRegex(ValueError, "out of range"):
            ranged_harness._set_device_parameter(
                {"track_index": 0, "device_index": 0, "parameter_index": 0, "value": 2.0}
            )

    def test_toggle_device_uses_activator_parameter_helper(self):
        activator = _FakeParameter(name="Device On", value=1.0, is_quantized=True)
        track = _FakeTrack([_FakeDevice("Operator", parameters=[activator])])
        harness = DeviceHarness(_FakeSong([track]))
        result = harness._toggle_device({"track_index": 0, "device_index": 0})
        self.assertEqual("activator_parameter", result["mode"])
        self.assertEqual("Device On", result["parameter_name"])
        self.assertFalse(result["enabled"])
        self.assertEqual(0.0, activator.value)

    def test_set_device_enabled_uses_activator_parameter_helper(self):
        activator = _FakeParameter(name="Device On", value=0.0, is_quantized=True)
        track = _FakeTrack([_FakeDevice("Operator", parameters=[activator])])
        harness = DeviceHarness(_FakeSong([track]))
        result = harness._set_device_enabled({"track_index": 0, "device_index": 0, "enabled": True})
        self.assertEqual("activator_parameter", result["mode"])
        self.assertTrue(result["enabled"])
        self.assertEqual(1.0, activator.value)

    def test_get_selected_device_uses_selected_track_view_selected_device(self):
        first = _FakeDevice("EQ Eight", class_name="AudioEffectDevice")
        second = _FakeDevice("Operator", class_name="InstrumentDevice")
        track = _FakeTrack([first, second])
        song = _FakeSong([track])
        song.view.selected_track = track
        track.view.selected_device = second
        harness = DeviceHarness(song)
        result = harness._get_selected_device()
        self.assertTrue(result["selected"])
        self.assertEqual(0, result["track_index"])
        self.assertEqual(1, result["device_index"])
        self.assertEqual("Operator", result["name"])

    def test_move_device_uses_song_level_api_when_available(self):
        first = _FakeDevice("EQ Eight")
        second = _FakeDevice("Operator")
        third = _FakeDevice("Limiter")
        track = _FakeTrack([first, second, third])
        harness = DeviceHarness(_FakeSong([track], supports_move_device=True))
        result = harness._move_device({"track_index": 0, "device_index": 0, "new_index": 2})
        self.assertTrue(result["ok"])
        self.assertEqual(2, result["new_index"])
        self.assertEqual(["Operator", "Limiter", "EQ Eight"], [device.name for device in track.devices])

    def test_move_device_returns_stable_error_when_song_level_api_is_unavailable(self):
        track = _FakeTrack([_FakeDevice("EQ Eight"), _FakeDevice("Operator")])
        harness = DeviceHarness(_FakeSong([track], supports_move_device=False))
        with self.assertRaisesRegex(ValueError, "Song.move_device is unavailable"):
            harness._move_device({"track_index": 0, "device_index": 0, "new_index": 1})

    def test_show_and_hide_plugin_window_only_toggle_device_view_collapse(self):
        device = _FakeDevice("Plugin", class_name="PluginDevice")
        track = _FakeTrack([device])
        song = _FakeSong([track])
        harness = DeviceHarness(song)

        show_result = harness._show_plugin_window({"track_index": 0, "device_index": 0})
        self.assertFalse(device.view.is_collapsed)
        self.assertEqual("device_view_collapse", show_result["mode"])
        self.assertFalse(show_result["collapsed"])

        hide_result = harness._hide_plugin_window({"track_index": 0, "device_index": 0})
        self.assertTrue(device.view.is_collapsed)
        self.assertEqual("device_view_collapse", hide_result["mode"])
        self.assertTrue(hide_result["collapsed"])

    def test_build_track_load_result_matches_new_device_when_live_returns_fresh_wrappers(self):
        harness = CoreResultHarness()
        previous_devices = [
            _FakeDevice("Arpeggiator", class_name="MidiArpeggiator"),
            _FakeDevice("Drift", class_name="Drift"),
        ]
        track = _ProxyCloneTrack(
            previous_devices + [_FakeDevice("Utility", class_name="StereoGain")]
        )
        result = harness._build_track_load_result(
            track,
            previous_devices,
            mode="native_device_insert",
            track_index=0,
            requested_name="Utility",
        )
        self.assertEqual("Utility", result["loaded_device_name"])
        self.assertEqual("StereoGain", result["class_name"])
        self.assertEqual(2, result["device_index"])
