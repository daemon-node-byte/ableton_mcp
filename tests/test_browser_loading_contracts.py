from __future__ import absolute_import, print_function, unicode_literals

import unittest

from AbletonMCP_Remote_Script.browser_ops import BrowserOpsMixin
from AbletonMCP_Remote_Script.core import CoreOpsMixin
from AbletonMCP_Remote_Script.device_ops import DeviceOpsMixin


class _FakeParameter(object):
    def __init__(self):
        self.value = 1.0
        self.min = 0.0
        self.max = 1.0
        self.is_quantized = False
        self.is_enabled = True
        self.name = "Device On"

    def __str__(self):
        return "On"


class _FakeDevice(object):
    def __init__(self, name, class_name="InstrumentDevice", can_have_chains=False, can_have_drum_pads=False):
        self.name = name
        self.class_name = class_name
        self.type = 1
        self.is_active = True
        self.parameters = [_FakeParameter()]
        self.can_have_chains = can_have_chains
        self.can_have_drum_pads = can_have_drum_pads


class _FakeTrack(object):
    has_midi_input = True

    def __init__(self):
        self.devices = []

    def insert_device(self, device_name, target_index=None):
        device = _FakeDevice(device_name)
        if target_index is None:
            self.devices.append(device)
            return
        if target_index > len(self.devices):
            raise IndexError("target index out of range")
        self.devices.insert(target_index, device)


class _FakeSongView(object):
    def __init__(self):
        self.selected_track = None


class _FakeSong(object):
    def __init__(self):
        self.view = _FakeSongView()


class _FakeBrowserItem(object):
    def __init__(self, name, uri, is_loadable=False, is_device=False, children=None):
        self.name = name
        self.uri = uri
        self.is_loadable = is_loadable
        self.is_device = is_device
        self.children = list(children or [])


class _FakeUri(object):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class _FakeBrowser(object):
    def __init__(self):
        self.instruments = _FakeBrowserItem(
            "Instruments",
            "root:instruments",
            children=[
                _FakeBrowserItem("Drift", "query:Synths#Drift", is_loadable=True, is_device=True),
                _FakeBrowserItem("Operator", "query:Synths#Operator", is_loadable=True, is_device=True),
            ],
        )
        self.audio_effects = _FakeBrowserItem(
            "Audio Effects",
            "root:audio_effects",
            children=[_FakeBrowserItem("Amp", "query:AudioFx#Amp", is_loadable=True, is_device=True)],
        )
        self.midi_effects = _FakeBrowserItem(
            "MIDI Effects",
            "root:midi_effects",
            children=[_FakeBrowserItem("Arpeggiator", "query:MidiFx#Arpeggiator", is_loadable=True, is_device=True)],
        )
        self.drums = _FakeBrowserItem(
            "Drums",
            "root:drums",
            children=[
                _FakeBrowserItem("Drum Rack", "query:Drums#Drum%20Rack", is_loadable=True, is_device=True),
                _FakeBrowserItem("505 Core Kit.adg", "query:Drums#FileId_5422", is_loadable=True, is_device=False),
            ],
        )
        self.sounds = _FakeBrowserItem(
            "Sounds",
            "root:sounds",
            children=[_FakeBrowserItem("Pad", "query:Sounds#Pad", is_loadable=False, is_device=False)],
        )
        self.samples = _FakeBrowserItem(
            "Samples",
            "root:samples",
            children=[_FakeBrowserItem("Kick", "query:Samples#Kick", is_loadable=True, is_device=False)],
        )
        self.packs = _FakeBrowserItem("Packs", "root:packs", children=[])
        self.user_library = _FakeBrowserItem("User Library", "root:user_library", children=[])
        self.loaded_items = []

    def get_item_by_uri(self, uri):
        stack = [
            self.instruments,
            self.audio_effects,
            self.midi_effects,
            self.drums,
            self.sounds,
            self.samples,
            self.packs,
            self.user_library,
        ]
        while stack:
            current = stack.pop()
            if current.uri == uri:
                return current
            stack.extend(reversed(getattr(current, "children", [])))
        return None

    def load_item(self, item):
        self.loaded_items.append(item.uri)


class _FakeApplication(object):
    def __init__(self):
        self.browser = _FakeBrowser()


class BrowserDeviceHarness(BrowserOpsMixin, DeviceOpsMixin, CoreOpsMixin):
    def __init__(self):
        self._application = _FakeApplication()
        self._song = _FakeSong()
        self._track = _FakeTrack()

        def _load_item(item):
            self._application.browser.loaded_items.append(item.uri)
            selected_track = self._song.view.selected_track
            selected_track.devices.append(_FakeDevice(item.name))

        self._application.browser.load_item = _load_item

    def application(self):
        return self._application

    def song(self):
        return self._song

    def _get_track(self, track_index):
        self.requested_track_index = track_index
        return self._track


class BrowserLoadingContractTests(unittest.TestCase):
    def test_get_track_devices_marks_group_devices_as_racks(self):
        harness = BrowserDeviceHarness()
        harness._track.devices.append(
            _FakeDevice("Instrument Rack", class_name="InstrumentGroupDevice", can_have_chains=True)
        )
        result = harness._get_track_devices({"track_index": 0})
        self.assertTrue(result["devices"][0]["is_rack"])

    def test_get_browser_tree_all_includes_available_categories(self):
        harness = BrowserDeviceHarness()
        result = harness._get_browser_tree({"category_type": "all"})
        self.assertIn("instruments", result)
        self.assertIn("samples", result)
        self.assertIn("drums", result)

    def test_get_browser_items_and_search_share_normalized_categories(self):
        harness = BrowserDeviceHarness()
        items = harness._get_browser_items_at_path({"path": "samples"})
        self.assertEqual("Kick", items["items"][0]["name"])
        result = harness._search_browser({"query": "kick", "category": "samples"})
        self.assertEqual(1, result["count"])
        self.assertEqual("Kick", result["results"][0]["name"])

    def test_search_browser_rejects_blank_queries(self):
        harness = BrowserDeviceHarness()
        with self.assertRaisesRegex(ValueError, "non-empty query"):
            harness._search_browser({"query": "   ", "category": "all"})

    def test_load_instrument_or_effect_requires_exactly_one_source(self):
        harness = BrowserDeviceHarness()
        with self.assertRaisesRegex(ValueError, "exactly one"):
            harness._load_instrument_or_effect({"track_index": 0})
        with self.assertRaisesRegex(ValueError, "exactly one"):
            harness._load_instrument_or_effect(
                {"track_index": 0, "device_name": "Drift", "uri": "query:Synths#Drift"}
            )

    def test_load_instrument_or_effect_rejects_invalid_target_index(self):
        harness = BrowserDeviceHarness()
        with self.assertRaisesRegex(ValueError, "target_index must be >= 0"):
            harness._load_instrument_or_effect({"track_index": 0, "device_name": "Drift", "target_index": -1})
        with self.assertRaisesRegex(ValueError, "out of range"):
            harness._load_instrument_or_effect({"track_index": 0, "device_name": "Drift", "target_index": 3})

    def test_load_instrument_or_effect_rejects_missing_uri(self):
        harness = BrowserDeviceHarness()
        with self.assertRaisesRegex(ValueError, "Browser item not found"):
            harness._load_instrument_or_effect({"track_index": 0, "uri": "query:Synths#Missing"})

    def test_load_instrument_or_effect_returns_device_metadata_for_native_insert(self):
        harness = BrowserDeviceHarness()
        result = harness._load_instrument_or_effect({"track_index": 0, "device_name": "Drift"})
        self.assertEqual("native_device_insert", result["mode"])
        self.assertEqual(0, result["device_count_before"])
        self.assertEqual(1, result["device_count_after"])
        self.assertEqual("Drift", result["loaded_device_name"])

    def test_load_instrument_or_effect_returns_device_metadata_for_uri_load(self):
        harness = BrowserDeviceHarness()
        result = harness._load_instrument_or_effect({"track_index": 0, "uri": "query:Synths#Operator"})
        self.assertEqual("browser_uri_load", result["mode"])
        self.assertEqual("query:Synths#Operator", result["uri"])
        self.assertEqual(1, result["device_count_after"])
        self.assertEqual("Operator", result["loaded_device_name"])

    def test_load_instrument_or_effect_supports_built_in_audio_effect_uris(self):
        harness = BrowserDeviceHarness()
        result = harness._load_instrument_or_effect({"track_index": 0, "uri": "query:AudioFx#Amp"})
        self.assertEqual("browser_uri_load", result["mode"])
        self.assertEqual("query:AudioFx#Amp", result["uri"])
        self.assertEqual("Amp", result["loaded_device_name"])

    def test_load_instrument_or_effect_supports_built_in_midi_effect_uris(self):
        harness = BrowserDeviceHarness()
        result = harness._load_instrument_or_effect({"track_index": 0, "uri": "query:MidiFx#Arpeggiator"})
        self.assertEqual("browser_uri_load", result["mode"])
        self.assertEqual("query:MidiFx#Arpeggiator", result["uri"])
        self.assertEqual("Arpeggiator", result["loaded_device_name"])

    def test_load_instrument_or_effect_falls_back_to_browser_tree_when_direct_lookup_is_missing(self):
        harness = BrowserDeviceHarness()
        harness.application().browser.get_item_by_uri = None
        result = harness._load_instrument_or_effect({"track_index": 0, "uri": "query:Synths#Operator"})
        self.assertEqual("browser_uri_load", result["mode"])
        self.assertEqual("Operator", result["loaded_device_name"])

    def test_load_instrument_or_effect_fallback_stringifies_browser_item_uris(self):
        harness = BrowserDeviceHarness()
        harness.application().browser.get_item_by_uri = None
        harness.application().browser.instruments.children[1].uri = _FakeUri("query:Synths#Operator")
        result = harness._load_instrument_or_effect({"track_index": 0, "uri": "query:Synths#Operator"})
        self.assertEqual("browser_uri_load", result["mode"])
        self.assertEqual("Operator", result["loaded_device_name"])

    def test_load_drum_kit_rejects_generic_device_entries(self):
        harness = BrowserDeviceHarness()
        with self.assertRaisesRegex(ValueError, "drum-kit preset URI"):
            harness._load_drum_kit({"track_index": 0, "rack_uri": "query:Drums#Drum%20Rack"})

    def test_load_drum_kit_returns_device_metadata(self):
        harness = BrowserDeviceHarness()
        result = harness._load_drum_kit({"track_index": 0, "rack_uri": "query:Drums#FileId_5422"})
        self.assertEqual("drum_kit_load", result["mode"])
        self.assertEqual("query:Drums#FileId_5422", result["loaded"])
        self.assertEqual(1, result["device_count_after"])
