from __future__ import absolute_import, print_function, unicode_literals

import unittest

from AbletonMCP_Remote_Script.core import CoreOpsMixin
from AbletonMCP_Remote_Script.rack_ops import RackOpsMixin


class _FakeValueParameter(object):
    def __init__(self, value):
        self.value = value


class _FakeParameter(object):
    def __init__(self, name, value, minimum=0.0, maximum=1.0, display_value=None):
        self.name = name
        self.value = value
        self.min = minimum
        self.max = maximum
        self._display_value = display_value or str(value)

    def __str__(self):
        return self._display_value


class _FakeMixerDevice(object):
    def __init__(self, volume=0.5, pan=0.0):
        self.volume = _FakeValueParameter(volume)
        self.panning = _FakeValueParameter(pan)


class _FakeChainDevice(object):
    def __init__(self, name, class_name="AudioEffectGroupDevice", is_active=True, parameter_count=1):
        self.name = name
        self.class_name = class_name
        self.is_active = is_active
        self.parameters = [_FakeParameter("Device On", 1.0)] * parameter_count


class _FakeChain(object):
    def __init__(self, name, devices=None, mute=False, solo=False, volume=0.5, pan=0.0):
        self.name = name
        self.devices = list(devices or [])
        self.mute = mute
        self.solo = solo
        self.mixer_device = _FakeMixerDevice(volume=volume, pan=pan)


class _FakeDrumChain(_FakeChain):
    def __init__(
        self,
        name,
        devices=None,
        mute=False,
        solo=False,
        volume=0.5,
        pan=0.0,
        in_note=36,
        out_note=36,
        choke_group=0,
    ):
        super(_FakeDrumChain, self).__init__(
            name,
            devices=devices,
            mute=mute,
            solo=solo,
            volume=volume,
            pan=pan,
        )
        self.in_note = in_note
        self.out_note = out_note
        self.choke_group = choke_group


class _FakeRackDevice(object):
    def __init__(self, name="Instrument Rack", parameters=None, chains=None):
        self.name = name
        self.parameters = list(parameters or [])
        self.chains = list(chains or [])
        self.can_have_chains = True
        self.can_have_drum_pads = False
        self.class_name = "AudioEffectGroupDevice"


class _FakeDrumPad(object):
    def __init__(self, note, name, chains=None, mute=False, solo=False):
        self.note = note
        self.name = name
        self.chains = list(chains or [])
        self.mute = mute
        self.solo = solo


class _ChainMuteFallbackPad(object):
    def __init__(self, note, name, chains=None):
        self.note = note
        self.name = name
        self.chains = list(chains or [])
        self._mute = False
        self.solo = False

    @property
    def mute(self):
        return False

    @mute.setter
    def mute(self, value):
        self._mute = bool(value)


class _FakeDrumRackDevice(_FakeRackDevice):
    def __init__(self, name="Drum Rack", parameters=None, chains=None, drum_pads=None, has_drum_pads=True):
        super(_FakeDrumRackDevice, self).__init__(name=name, parameters=parameters, chains=chains)
        self.can_have_drum_pads = True
        self.has_drum_pads = has_drum_pads
        self.drum_pads = list(drum_pads or [])
        self.class_name = "DrumGroupDevice"


class _FakePlainDevice(object):
    def __init__(self, name="Amp"):
        self.name = name
        self.parameters = [_FakeParameter("Device On", 1.0)]
        self.class_name = "MxDeviceAudioEffect"


class _FakeTrack(object):
    def __init__(self, devices):
        self.devices = list(devices)


class _FakeSong(object):
    def __init__(self, track):
        self.tracks = [track]


class RackHarness(RackOpsMixin, CoreOpsMixin):
    def __init__(self, track):
        self._song = _FakeSong(track)

    def song(self):
        return self._song


class RackOpsContractTests(unittest.TestCase):
    def test_get_rack_chains_returns_chain_state_and_devices(self):
        rack = _FakeRackDevice(
            chains=[
                _FakeChain(
                    "Chain A",
                    devices=[_FakeChainDevice("EQ Eight"), _FakeChainDevice("Compressor")],
                    mute=False,
                    solo=True,
                    volume=0.75,
                    pan=-0.1,
                )
            ]
        )
        harness = RackHarness(_FakeTrack([rack]))
        result = harness._get_rack_chains({"track_index": 0, "device_index": 0})
        self.assertEqual("Instrument Rack", result["rack_name"])
        self.assertEqual(1, len(result["chains"]))
        self.assertEqual("Chain A", result["chains"][0]["name"])
        self.assertEqual(["EQ Eight", "Compressor"], result["chains"][0]["devices"])
        self.assertEqual(0.75, result["chains"][0]["volume"])

    def test_get_rack_macros_uses_stable_macro_indices(self):
        rack = _FakeRackDevice(
            parameters=[
                _FakeParameter("Device On", 1.0),
                _FakeParameter("Macro 1", 0.25, display_value="25%"),
                _FakeParameter("Gain", 0.8),
                _FakeParameter("Macro 2", 0.5, display_value="50%"),
            ]
        )
        harness = RackHarness(_FakeTrack([rack]))
        result = harness._get_rack_macros({"track_index": 0, "device_index": 0})
        self.assertEqual([0, 1], [macro["index"] for macro in result["macros"]])
        self.assertEqual([1, 3], [macro["parameter_index"] for macro in result["macros"]])
        self.assertEqual(["Macro 1", "Macro 2"], [macro["name"] for macro in result["macros"]])

    def test_set_rack_macro_clamps_by_macro_index(self):
        rack = _FakeRackDevice(
            parameters=[
                _FakeParameter("Device On", 1.0),
                _FakeParameter("Macro 1", 0.25, minimum=0.0, maximum=1.0),
                _FakeParameter("Macro 2", 0.5, minimum=0.0, maximum=1.0),
            ]
        )
        harness = RackHarness(_FakeTrack([rack]))
        result = harness._set_rack_macro(
            {"track_index": 0, "device_index": 0, "macro_index": 1, "value": 4.0}
        )
        self.assertEqual(1, result["index"])
        self.assertEqual(1.0, result["value"])
        self.assertEqual(1.0, rack.parameters[2].value)

    def test_get_chain_devices_returns_child_devices(self):
        rack = _FakeRackDevice(
            chains=[_FakeChain("Chain A", devices=[_FakeChainDevice("Chorus-Ensemble", parameter_count=3)])]
        )
        harness = RackHarness(_FakeTrack([rack]))
        result = harness._get_chain_devices({"track_index": 0, "device_index": 0, "chain_index": 0})
        self.assertEqual("Chain A", result["chain_name"])
        self.assertEqual("Chorus-Ensemble", result["devices"][0]["name"])
        self.assertEqual(3, result["devices"][0]["num_parameters"])

    def test_chain_mutations_update_selected_chain(self):
        chain = _FakeChain("Chain A", volume=0.2)
        rack = _FakeRackDevice(chains=[chain])
        harness = RackHarness(_FakeTrack([rack]))
        self.assertEqual({"mute": True}, harness._set_chain_mute({"track_index": 0, "device_index": 0, "chain_index": 0, "mute": True}))
        self.assertEqual({"solo": True}, harness._set_chain_solo({"track_index": 0, "device_index": 0, "chain_index": 0, "solo": True}))
        volume_result = harness._set_chain_volume(
            {"track_index": 0, "device_index": 0, "chain_index": 0, "volume": 1.5}
        )
        self.assertEqual(1.0, volume_result["volume"])
        self.assertTrue(chain.mute)
        self.assertTrue(chain.solo)
        self.assertEqual(1.0, chain.mixer_device.volume.value)

    def test_get_drum_rack_pads_includes_chain_input_notes(self):
        drum_rack = _FakeDrumRackDevice(
            drum_pads=[
                _FakeDrumPad(
                    36,
                    "Kick",
                    chains=[_FakeDrumChain("Kick Chain", devices=[_FakeChainDevice("Simpler")], in_note=36)],
                )
            ]
        )
        harness = RackHarness(_FakeTrack([drum_rack]))
        result = harness._get_drum_rack_pads({"track_index": 0, "device_index": 0})
        self.assertTrue(result["has_drum_pads"])
        self.assertEqual(1, result["count"])
        self.assertEqual([36], result["drum_pads"][0]["chain_input_notes"])
        self.assertEqual(36, result["drum_pads"][0]["effective_note"])

    def test_set_drum_rack_pad_note_updates_chain_in_notes(self):
        drum_chain = _FakeDrumChain("Kick Chain", devices=[_FakeChainDevice("Simpler")], in_note=36)
        drum_rack = _FakeDrumRackDevice(drum_pads=[_FakeDrumPad(36, "Kick", chains=[drum_chain])])
        harness = RackHarness(_FakeTrack([drum_rack]))
        result = harness._set_drum_rack_pad_note(
            {"track_index": 0, "device_index": 0, "note": 36, "new_note": 48}
        )
        self.assertEqual(48, result["note"])
        self.assertEqual("drum_chain_in_note", result["mode"])
        self.assertEqual(1, result["updated_chains"])
        self.assertEqual(48, drum_chain.in_note)

    def test_set_drum_rack_pad_mute_and_solo_update_pad(self):
        pad = _FakeDrumPad(36, "Kick", chains=[_FakeDrumChain("Kick Chain", devices=[_FakeChainDevice("Simpler")])])
        drum_rack = _FakeDrumRackDevice(drum_pads=[pad])
        harness = RackHarness(_FakeTrack([drum_rack]))
        self.assertEqual(
            {"note": 36, "mute": True},
            harness._set_drum_rack_pad_mute({"track_index": 0, "device_index": 0, "note": 36, "mute": True}),
        )
        self.assertEqual(
            {"note": 36, "solo": True},
            harness._set_drum_rack_pad_solo({"track_index": 0, "device_index": 0, "note": 36, "solo": True}),
        )
        self.assertTrue(pad.mute)
        self.assertTrue(pad.solo)

    def test_set_drum_rack_pad_mute_falls_back_to_chain_mute(self):
        chain = _FakeDrumChain("Kick Chain", devices=[_FakeChainDevice("Simpler")], mute=False)
        pad = _ChainMuteFallbackPad(36, "Kick", chains=[chain])
        drum_rack = _FakeDrumRackDevice(drum_pads=[pad])
        harness = RackHarness(_FakeTrack([drum_rack]))
        result = harness._set_drum_rack_pad_mute({"track_index": 0, "device_index": 0, "note": 36, "mute": True})
        self.assertEqual({"note": 36, "mute": True}, result)
        self.assertTrue(chain.mute)

    def test_non_rack_device_is_rejected(self):
        harness = RackHarness(_FakeTrack([_FakePlainDevice()]))
        with self.assertRaisesRegex(ValueError, "is not a rack"):
            harness._get_rack_chains({"track_index": 0, "device_index": 0})

    def test_invalid_chain_index_is_a_stable_value_error(self):
        rack = _FakeRackDevice(chains=[_FakeChain("Chain A")])
        harness = RackHarness(_FakeTrack([rack]))
        with self.assertRaisesRegex(ValueError, "Chain index 4 out of range"):
            harness._get_chain_devices({"track_index": 0, "device_index": 0, "chain_index": 4})

    def test_non_drum_rack_device_is_rejected(self):
        harness = RackHarness(_FakeTrack([_FakePlainDevice()]))
        with self.assertRaisesRegex(ValueError, "is not a Drum Rack"):
            harness._get_drum_rack_pads({"track_index": 0, "device_index": 0})

    def test_missing_drum_pad_note_raises_value_error(self):
        drum_rack = _FakeDrumRackDevice(drum_pads=[_FakeDrumPad(36, "Kick")])
        harness = RackHarness(_FakeTrack([drum_rack]))
        with self.assertRaisesRegex(ValueError, "Drum pad with note 40 not found"):
            harness._set_drum_rack_pad_mute({"track_index": 0, "device_index": 0, "note": 40, "mute": True})

    def test_empty_pad_remap_requires_chains(self):
        drum_rack = _FakeDrumRackDevice(drum_pads=[_FakeDrumPad(36, "Empty Pad", chains=[])])
        harness = RackHarness(_FakeTrack([drum_rack]))
        with self.assertRaisesRegex(ValueError, "at least one chain"):
            harness._set_drum_rack_pad_note({"track_index": 0, "device_index": 0, "note": 36, "new_note": 48})

    def test_pad_remap_requires_live_12_3_in_note_support(self):
        chain_without_in_note = _FakeChain("Kick Chain", devices=[_FakeChainDevice("Simpler")])
        drum_rack = _FakeDrumRackDevice(drum_pads=[_FakeDrumPad(36, "Kick", chains=[chain_without_in_note])])
        harness = RackHarness(_FakeTrack([drum_rack]))
        with self.assertRaisesRegex(ValueError, "Live 12.3\\+"):
            harness._set_drum_rack_pad_note({"track_index": 0, "device_index": 0, "note": 36, "new_note": 48})
