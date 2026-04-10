from __future__ import absolute_import, print_function, unicode_literals

import os
import tempfile
import unittest

from AbletonMCP_Remote_Script.core import CoreOpsMixin
from AbletonMCP_Remote_Script.device_ops import DeviceOpsMixin
from AbletonMCP_Remote_Script.memory_bank_ops import MemoryBankOpsMixin
from AbletonMCP_Remote_Script.rack_ops import RackOpsMixin


class _FakeValueParameter(object):
    def __init__(self, value):
        self.value = value


class _FakeParameter(object):
    def __init__(self, name, value, minimum=0.0, maximum=1.0, display_value=None, quantized=False):
        self.name = name
        self.value = value
        self.min = minimum
        self.max = maximum
        self.is_quantized = quantized
        self.is_enabled = True
        self._display_value = display_value or str(value)

    def __str__(self):
        return self._display_value


class _FakeMixerDevice(object):
    def __init__(self, volume=0.5, pan=0.0):
        self.volume = _FakeValueParameter(volume)
        self.panning = _FakeValueParameter(pan)


class _FakeDevice(object):
    def __init__(self, name, class_name, device_type, parameters):
        self.name = name
        self.class_name = class_name
        self.type = device_type
        self.parameters = list(parameters)
        self.is_active = True
        self.can_have_chains = False
        self.can_have_drum_pads = False


class _FakeRackDevice(_FakeDevice):
    def __init__(self, name, device_type, class_name):
        parameters = [_FakeParameter("Device On", 1.0)]
        for macro_index in range(1, 9):
            parameters.append(
                _FakeParameter(
                    "Macro {}".format(macro_index),
                    0.0,
                    minimum=0.0,
                    maximum=1.0,
                    display_value="0%",
                )
            )
        super(_FakeRackDevice, self).__init__(name, class_name, device_type, parameters)
        self.can_have_chains = True
        self.visible_macro_count = 8
        self.has_macro_mappings = False
        self.chains = []
        self.return_chains = []

    def insert_chain(self, index=None):
        if index is None:
            index = len(self.chains)
        self.chains.insert(index, _FakeChain("Chain {}".format(index + 1)))


class _FakeChain(object):
    def __init__(self, name, devices=None):
        self.name = name
        self.devices = list(devices or [])
        self.mute = False
        self.solo = False
        self.mixer_device = _FakeMixerDevice()

    def insert_device(self, native_device_name, target_index=None):
        device = _make_native_device(native_device_name)
        if target_index is None:
            self.devices.append(device)
        else:
            self.devices.insert(target_index, device)


class _FakeTrack(object):
    def __init__(self, name, has_midi_input=True, devices=None, color=7):
        self.name = name
        self.has_midi_input = has_midi_input
        self.devices = list(devices or [])
        self.color = color

    def insert_device(self, native_device_name, target_index=None):
        device = _make_native_device(native_device_name)
        if target_index is None:
            self.devices.append(device)
        else:
            self.devices.insert(target_index, device)


class _FakeSong(object):
    def __init__(self, tracks, file_path):
        self.tracks = list(tracks)
        self.file_path = file_path
        self.tempo = 120.0
        self.signature_numerator = 4
        self.signature_denominator = 4


def _make_native_device(native_device_name):
    if native_device_name == "Instrument Rack":
        return _FakeRackDevice("Instrument Rack", 1, "InstrumentGroupDevice")
    if native_device_name == "Audio Effect Rack":
        return _FakeRackDevice("Audio Effect Rack", 2, "AudioEffectGroupDevice")
    if native_device_name in ("Eq8", "EQ Eight"):
        return _FakeDevice(
            "EQ Eight",
            "Eq8",
            2,
            [
                _FakeParameter("Device On", 1.0),
                _FakeParameter("1 Frequency A", 500.0, minimum=20.0, maximum=20000.0),
                _FakeParameter("1 Gain A", 0.0, minimum=-15.0, maximum=15.0),
                _FakeParameter("1 Resonance A", 1.0, minimum=0.3, maximum=12.0),
            ],
        )
    if native_device_name == "Saturator":
        return _FakeDevice(
            "Saturator",
            "Saturator",
            2,
            [
                _FakeParameter("Device On", 1.0),
                _FakeParameter("Drive", 0.0, minimum=0.0, maximum=30.0),
                _FakeParameter("Output", 0.0, minimum=-24.0, maximum=24.0),
            ],
        )
    if native_device_name == "Delay":
        return _FakeDevice(
            "Delay",
            "Delay",
            2,
            [
                _FakeParameter("Device On", 1.0),
                _FakeParameter("Feedback", 0.35, minimum=0.0, maximum=0.95),
                _FakeParameter("Dry/Wet", 0.25, minimum=0.0, maximum=1.0),
            ],
        )
    if native_device_name == "Utility":
        return _FakeDevice(
            "Utility",
            "Utility",
            2,
            [
                _FakeParameter("Device On", 1.0),
                _FakeParameter("Gain", 0.0, minimum=-35.0, maximum=35.0),
            ],
        )
    if native_device_name == "Auto Filter":
        return _FakeDevice(
            "Auto Filter",
            "AutoFilter",
            2,
            [
                _FakeParameter("Device On", 1.0),
                _FakeParameter("Frequency", 600.0, minimum=20.0, maximum=20000.0),
                _FakeParameter("Resonance", 1.0, minimum=0.2, maximum=10.0),
            ],
        )
    if native_device_name == "Drift":
        return _FakeDevice(
            "Drift",
            "Drift",
            1,
            [
                _FakeParameter("Device On", 1.0),
                _FakeParameter("Filter Freq", 1200.0, minimum=20.0, maximum=20000.0),
            ],
        )
    raise ValueError("Unknown native device '{}'".format(native_device_name))


class _SystemRackHarness(RackOpsMixin, DeviceOpsMixin, MemoryBankOpsMixin, CoreOpsMixin):
    def __init__(self, song):
        self._song = song

    def song(self):
        return self._song


class SystemOwnedRackContractTests(unittest.TestCase):
    def build_harness(self, saved=True):
        self.temp_dir = tempfile.TemporaryDirectory()
        session_path = os.path.join(self.temp_dir.name, "Project.als") if saved else ""
        if saved:
            with open(session_path, "w") as file_handle:
                file_handle.write("fake set")
        song = _FakeSong(
            [
                _FakeTrack("Rack MIDI", has_midi_input=True),
                _FakeTrack("Rack Audio", has_midi_input=False),
            ],
            session_path,
        )
        return _SystemRackHarness(song)

    def tearDown(self):
        temp_dir = getattr(self, "temp_dir", None)
        if temp_dir is not None:
            temp_dir.cleanup()

    def test_create_rack_creates_memory_bank_entry(self):
        harness = self.build_harness(saved=True)
        result = harness._create_rack({"track_index": 0, "rack_type": "instrument", "name": "Lead Rack"})
        self.assertEqual("devices 0", result["rack_path"])
        self.assertTrue(result["rack_id"].startswith("rack_"))
        rack_inventory = harness._get_system_owned_racks()
        self.assertEqual(1, rack_inventory["count"])
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir.name, ".ableton-mcp", "memory", "racks.md")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir.name, ".ableton-mcp", "memory", "project.md")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir.name, ".ableton-mcp", "memory", "track_0.md")))

    def test_create_rack_requires_saved_session_for_memory_bank(self):
        harness = self.build_harness(saved=False)
        with self.assertRaisesRegex(ValueError, "saving the Live Set first"):
            harness._create_rack({"track_index": 0, "rack_type": "instrument", "name": "Unsaved Rack"})

    def test_insert_chain_and_device_support_nested_path_resolution(self):
        harness = self.build_harness(saved=True)
        rack_result = harness._create_rack({"track_index": 1, "rack_type": "audio_effect", "name": "FX Rack"})
        chain_result = harness._insert_rack_chain(
            {"track_index": 1, "rack_path": rack_result["rack_path"], "name": "Tone Chain"}
        )
        device_result = harness._insert_device_in_chain(
            {
                "track_index": 1,
                "chain_path": chain_result["chain_path"],
                "native_device_name": "Eq8",
                "device_name": "Tone EQ",
            }
        )
        parameter_payload = harness._get_device_parameters_at_path(
            {"track_index": 1, "device_path": device_result["device_path"]}
        )
        self.assertEqual("Tone EQ", parameter_payload["device_name"])
        self.assertEqual(device_result["device_path"], parameter_payload["device_path"])
        self.assertIn("1 Frequency A", [parameter["name"] for parameter in parameter_payload["parameters"]])

    def test_set_device_parameter_commands_at_path_update_values(self):
        harness = self.build_harness(saved=True)
        rack_result = harness._create_rack({"track_index": 1, "rack_type": "audio_effect", "name": "FX Rack"})
        chain_result = harness._insert_rack_chain(
            {"track_index": 1, "rack_path": rack_result["rack_path"], "name": "Tone Chain"}
        )
        device_result = harness._insert_device_in_chain(
            {"track_index": 1, "chain_path": chain_result["chain_path"], "native_device_name": "Eq8"}
        )
        by_name = harness._set_device_parameter_by_name_at_path(
            {
                "track_index": 1,
                "device_path": device_result["device_path"],
                "name": "Gain A",
                "value": 6.0,
            }
        )
        by_index = harness._set_device_parameter_at_path(
            {
                "track_index": 1,
                "device_path": device_result["device_path"],
                "parameter_index": 1,
                "value": 1200.0,
            }
        )
        self.assertEqual("1 Gain A", by_name["name"])
        self.assertEqual(6.0, by_name["value"])
        self.assertEqual("1 Frequency A", by_index["name"])
        self.assertEqual(1200.0, by_index["value"])

    def test_get_rack_structure_returns_recursive_paths(self):
        harness = self.build_harness(saved=True)
        root_rack = harness._create_rack({"track_index": 0, "rack_type": "instrument", "name": "Synth Rack"})
        root_chain = harness._insert_rack_chain(
            {"track_index": 0, "rack_path": root_rack["rack_path"], "name": "Main Chain"}
        )
        nested_rack = harness._create_rack(
            {
                "track_index": 0,
                "rack_type": "audio_effect",
                "name": "Nested FX",
                "target_path": root_chain["chain_path"],
            }
        )
        nested_chain = harness._insert_rack_chain(
            {"track_index": 0, "rack_path": nested_rack["rack_path"], "name": "Nested Chain"}
        )
        harness._insert_device_in_chain(
            {
                "track_index": 0,
                "chain_path": nested_chain["chain_path"],
                "native_device_name": "Saturator",
            }
        )
        structure = harness._get_rack_structure({"track_index": 0, "rack_path": root_rack["rack_path"]})
        nested_device = structure["rack"]["chains"][0]["devices"][0]
        self.assertEqual(root_rack["rack_path"], structure["rack_path"])
        self.assertEqual(nested_rack["rack_path"], nested_device["path"])
        self.assertEqual("audio_effect", nested_device["rack_type"])
        self.assertEqual(
            "{} chains 0 devices 0".format(nested_rack["rack_path"]),
            nested_device["chains"][0]["devices"][0]["path"],
        )

    def test_apply_rack_blueprint_builds_system_owned_rack_tree(self):
        harness = self.build_harness(saved=True)
        result = harness._apply_rack_blueprint(
            {
                "blueprint": {
                    "track_index": 1,
                    "rack_type": "audio_effect",
                    "rack_name": "Mix Rack",
                    "macro_labels": ["Tone", "Drive"],
                    "chains": [
                        {
                            "name": "EQ",
                            "devices": [
                                {
                                    "native_device_name": "Eq8",
                                    "device_name": "Tone EQ",
                                    "parameter_values": {"Gain A": 3.0},
                                }
                            ],
                        },
                        {
                            "name": "Texture",
                            "devices": [
                                {"native_device_name": "Saturator", "parameter_values": {"Drive": 8.0}},
                                {"native_device_name": "Delay", "parameter_values": {"Dry/Wet": 0.45}},
                            ],
                        },
                    ],
                }
            }
        )
        self.assertEqual(1, result["created_racks"])
        self.assertEqual(2, result["created_chains"])
        self.assertEqual(3, result["created_devices"])
        inventory = harness._get_system_owned_racks()
        self.assertEqual(1, inventory["count"])
        self.assertEqual("Mix Rack", inventory["racks"][0]["name"])
        self.assertEqual(["Tone", "Drive"], inventory["racks"][0]["macro_labels"])

    def test_apply_rack_blueprint_rejects_macro_mapping_requests(self):
        harness = self.build_harness(saved=True)
        with self.assertRaisesRegex(ValueError, "Native macro mapping is not confirmed"):
            harness._apply_rack_blueprint(
                {
                    "blueprint": {
                        "track_index": 1,
                        "rack_type": "audio_effect",
                        "rack_name": "Mix Rack",
                        "macro_mappings": [{"macro": 0, "parameter": "Gain A"}],
                        "chains": [{"name": "EQ"}],
                    }
                }
            )

    def test_path_resolution_rejects_invalid_segments_and_ranges(self):
        harness = self.build_harness(saved=True)
        root_rack = harness._create_rack({"track_index": 0, "rack_type": "instrument", "name": "Synth Rack"})
        with self.assertRaisesRegex(ValueError, "Unsupported path segment"):
            harness._get_rack_structure({"track_index": 0, "rack_path": "widgets 0"})
        with self.assertRaisesRegex(ValueError, "does not resolve to a chain"):
            harness._insert_device_in_chain(
                {"track_index": 0, "chain_path": root_rack["rack_path"], "native_device_name": "Eq8"}
            )
        with self.assertRaisesRegex(ValueError, "devices index 99 out of range"):
            harness._get_device_parameters_at_path({"track_index": 0, "device_path": "devices 99"})

    def test_memory_bank_read_write_and_refresh_support_import_flow(self):
        harness = self.build_harness(saved=True)
        harness._write_memory_bank({"file_name": "notes.md", "content": "# Notes\n"})
        self.assertEqual("# Notes\n", harness._read_memory_bank({"file_name": "notes.md"}))
        harness._append_rack_entry({"rack_data": "## Manual Rack\n- note"})
        self.assertIn("Manual Rack", harness._read_memory_bank({"file_name": "racks.md"}))

        harness.song().tracks[0].insert_device("Instrument Rack")
        refresh = harness._refresh_rack_memory_entry({"track_index": 0, "rack_path": "devices 0"})
        self.assertTrue(refresh["rack_id"].startswith("rack_"))
        inventory = harness._get_system_owned_racks()
        self.assertEqual(1, inventory["count"])
        self.assertTrue(inventory["racks"][0]["imported"])
