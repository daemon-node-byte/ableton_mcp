from __future__ import absolute_import, print_function, unicode_literals

import json
import sys
import time

from mcp_server.client import AbletonCommandError, AbletonRemoteClient


class RackAndDrumBatchValidator(object):
    def __init__(self, host="localhost", port=9877, connect_timeout=5.0, response_timeout=30.0):
        self.client = AbletonRemoteClient(
            host=host,
            port=port,
            connect_timeout=connect_timeout,
            response_timeout=response_timeout,
        )
        self.created_track_indices = []
        self.summary = {
            "baseline": {},
            "validated_commands": [],
            "negative_cases": [],
            "discovered_targets": {},
            "fallback_paths": {},
        }

    def call(self, command_name, params=None):
        return self.client.send_command(command_name, params or {})

    def require(self, condition, message):
        if not condition:
            raise AssertionError(message)

    def mark_validated(self, command_name):
        if command_name not in self.summary["validated_commands"]:
            self.summary["validated_commands"].append(command_name)

    def expect_error(self, command_name, params, expected_substring):
        try:
            self.call(command_name, params)
        except AbletonCommandError as exc:
            message = str(exc)
            if expected_substring not in message:
                raise AssertionError(
                    "Expected '{}' in error for '{}', got '{}'".format(
                        expected_substring, command_name, message
                    )
                )
            self.summary["negative_cases"].append(
                {"command": command_name, "matched": expected_substring, "status": "ok"}
            )
            return
        raise AssertionError("Expected '{}' to fail".format(command_name))

    def track_devices(self, track_index):
        return self.call("get_track_devices", {"track_index": track_index})["devices"]

    def wait_for_device_growth(self, track_index, previous_count, timeout_seconds=12.0):
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            devices = self.track_devices(track_index)
            if len(devices) > previous_count:
                return devices
            time.sleep(0.25)
        raise AssertionError(
            "Timed out waiting for device growth on track {} (previous_count={})".format(
                track_index, previous_count
            )
        )

    def pick_loadable_result(self, query, category, require_device=None):
        results = self.call("search_browser", {"query": query, "category": category})["results"]
        for result in results:
            if not result.get("is_loadable"):
                continue
            if require_device is not None and bool(result.get("is_device")) != bool(require_device):
                continue
            return result
        return None

    def pick_drum_kit_item(self):
        for item in self.call("get_browser_items_at_path", {"path": "drums"})["items"]:
            if item.get("is_loadable") and not item.get("is_device"):
                return item
        raise AssertionError("No loadable drum-kit preset URI was discovered")

    def choose_unused_note(self, pads, original_note):
        for pad in pads:
            if int(pad["note"]) == int(original_note):
                continue
            if int(pad.get("num_chains", 0)) == 0:
                return int(pad["note"])
        raise AssertionError("Unable to find an empty Drum Rack pad for remap validation")

    def find_pad_with_chains(self, pads):
        for pad in pads:
            if int(pad.get("num_chains", 0)) > 0:
                return pad
        raise AssertionError("No drum pad with at least one chain was discovered")

    def safe_cleanup(self):
        for track_index in sorted(self.created_track_indices, reverse=True):
            try:
                self.call("delete_track", {"track_index": track_index})
            except Exception:
                pass

    def load_rack_with_fallback(self, track_index, summary_key, browser_category, query, native_name):
        browser_item = self.pick_loadable_result(query, browser_category, require_device=False)
        previous_count = len(self.track_devices(track_index))
        if browser_item is not None:
            result = self.call(
                "load_instrument_or_effect",
                {"track_index": track_index, "uri": browser_item["uri"]},
            )
            expected_mode = "browser_uri_load"
            target_info = {"mode": "browser_uri_load", "uri": browser_item["uri"]}
        else:
            result = self.call(
                "load_instrument_or_effect",
                {"track_index": track_index, "device_name": native_name},
            )
            expected_mode = "native_device_insert"
            target_info = {"mode": "native_device_insert", "device_name": native_name}
            self.summary["fallback_paths"][summary_key] = "native_device_insert"

        devices = self.wait_for_device_growth(track_index, previous_count)
        self.require(result["mode"] == expected_mode, "{} load returned wrong mode".format(summary_key))
        self.require(len(devices) > previous_count, "{} load did not grow device count".format(summary_key))
        device_index = result.get("device_index", len(devices) - 1)
        self.require(devices[device_index]["is_rack"], "{} did not load as a rack".format(summary_key))
        return device_index, target_info

    def validate_rack_commands(self, track_index, device_index, label, require_chain=False):
        chain_result = self.call("get_rack_chains", {"track_index": track_index, "device_index": device_index})
        self.mark_validated("get_rack_chains")
        chains = chain_result["chains"]
        if require_chain:
            self.require(chains, "{} should expose at least one chain".format(label))

        macro_result = self.call("get_rack_macros", {"track_index": track_index, "device_index": device_index})
        self.mark_validated("get_rack_macros")
        if macro_result["macros"]:
            first_macro = macro_result["macros"][0]
            target_value = first_macro["max"] if first_macro["value"] != first_macro["max"] else first_macro["min"]
            set_macro_result = self.call(
                "set_rack_macro",
                {
                    "track_index": track_index,
                    "device_index": device_index,
                    "macro_index": first_macro["index"],
                    "value": target_value,
                },
            )
            self.mark_validated("set_rack_macro")
            self.require(
                abs(float(set_macro_result["value"]) - float(target_value)) < 0.0001,
                "{} macro write did not round-trip".format(label),
            )

            macros_after = self.call("get_rack_macros", {"track_index": track_index, "device_index": device_index})
            matching_macro = macros_after["macros"][first_macro["index"]]
            self.require(
                abs(float(matching_macro["value"]) - float(target_value)) < 0.0001,
                "{} macro readback did not match".format(label),
            )
        else:
            self.summary["fallback_paths"]["{}_macro_validation".format(label.lower().replace(" ", "_"))] = "no_macros"

        if not chains:
            self.summary["fallback_paths"]["{}_chain_validation".format(label.lower().replace(" ", "_"))] = "empty_shell"
            return False

        chain_index = chains[0]["index"]
        chain_devices = self.call(
            "get_chain_devices",
            {"track_index": track_index, "device_index": device_index, "chain_index": chain_index},
        )
        self.mark_validated("get_chain_devices")
        self.require("devices" in chain_devices, "{} chain device readback failed".format(label))

        self.call(
            "set_chain_mute",
            {"track_index": track_index, "device_index": device_index, "chain_index": chain_index, "mute": True},
        )
        self.mark_validated("set_chain_mute")
        self.call(
            "set_chain_solo",
            {"track_index": track_index, "device_index": device_index, "chain_index": chain_index, "solo": True},
        )
        self.mark_validated("set_chain_solo")
        self.call(
            "set_chain_volume",
            {"track_index": track_index, "device_index": device_index, "chain_index": chain_index, "volume": 0.42},
        )
        self.mark_validated("set_chain_volume")

        chains_after = self.call("get_rack_chains", {"track_index": track_index, "device_index": device_index})
        validated_chain = chains_after["chains"][chain_index]
        self.require(validated_chain["mute"] is True, "{} chain mute did not stick".format(label))
        self.require(validated_chain["solo"] is True, "{} chain solo did not stick".format(label))
        self.require(abs(float(validated_chain["volume"]) - 0.42) < 0.0001, "{} chain volume did not stick".format(label))

        self.expect_error(
            "get_chain_devices",
            {"track_index": track_index, "device_index": device_index, "chain_index": 999},
            "Chain index 999 out of range",
        )
        return True

    def validate_drum_commands(self, track_index, device_index):
        pad_result = self.call("get_drum_rack_pads", {"track_index": track_index, "device_index": device_index})
        self.mark_validated("get_drum_rack_pads")
        self.require(pad_result["count"] > 0, "Drum rack should expose at least one pad")
        self.require(pad_result["has_drum_pads"], "Drum rack should report top-level drum pads")

        target_pad = self.find_pad_with_chains(pad_result["drum_pads"])
        target_note = int(target_pad["note"])

        self.call(
            "set_drum_rack_pad_mute",
            {"track_index": track_index, "device_index": device_index, "note": target_note, "mute": True},
        )
        self.mark_validated("set_drum_rack_pad_mute")
        self.call(
            "set_drum_rack_pad_solo",
            {"track_index": track_index, "device_index": device_index, "note": target_note, "solo": True},
        )
        self.mark_validated("set_drum_rack_pad_solo")

        pads_after_toggle = self.call("get_drum_rack_pads", {"track_index": track_index, "device_index": device_index})
        updated_pad = [pad for pad in pads_after_toggle["drum_pads"] if int(pad["note"]) == target_note][0]
        self.require(updated_pad["mute"] is True, "Drum-pad mute did not stick")
        self.require(updated_pad["solo"] is True, "Drum-pad solo did not stick")

        new_note = self.choose_unused_note(pads_after_toggle["drum_pads"], target_note)
        remap_result = self.call(
            "set_drum_rack_pad_note",
            {"track_index": track_index, "device_index": device_index, "note": target_note, "new_note": new_note},
        )
        self.mark_validated("set_drum_rack_pad_note")
        self.require(remap_result["note"] == new_note, "Drum-pad remap returned the wrong note")

        pads_after_remap = self.call("get_drum_rack_pads", {"track_index": track_index, "device_index": device_index})
        destination_pad = [pad for pad in pads_after_remap["drum_pads"] if int(pad["note"]) == new_note][0]
        self.require(int(destination_pad.get("num_chains", 0)) > 0, "Drum-pad remap destination pad is empty")
        chain_input_notes = destination_pad.get("chain_input_notes", [])
        self.require(chain_input_notes, "Drum-pad remap destination pad is missing chain input notes")
        self.require(
            all(int(chain_note) == new_note for chain_note in chain_input_notes),
            "Drum-pad remap did not update all chain input notes",
        )
        if "effective_note" in destination_pad:
            self.require(int(destination_pad["effective_note"]) == new_note, "Drum-pad effective note did not update")

        self.expect_error(
            "set_drum_rack_pad_note",
            {"track_index": track_index, "device_index": device_index, "note": 999, "new_note": 48},
            "Drum pad with note 999 not found",
        )

    def run(self):
        try:
            health = self.call("health_check", {})
            session_info = self.call("get_session_info", {})
            browser_tree = self.call("get_browser_tree", {"category_type": "all"})
            drum_kit_item = self.pick_drum_kit_item()

            self.summary["baseline"] = {
                "health_check": health,
                "track_count": session_info["track_count"],
            }

            self.require("instruments" in browser_tree, "Browser tree missing instruments")
            self.require("audio_effects" in browser_tree, "Browser tree missing audio_effects")
            self.require("drums" in browser_tree, "Browser tree missing drums")

            instrument_track = self.call("create_midi_track", {})
            self.created_track_indices.append(instrument_track["index"])
            audio_rack_track = self.call("create_audio_track", {})
            self.created_track_indices.append(audio_rack_track["index"])
            drum_track = self.call("create_midi_track", {})
            self.created_track_indices.append(drum_track["index"])

            self.call("set_track_name", {"track_index": instrument_track["index"], "name": "Rack Batch Instrument Rack"})
            self.call("set_track_name", {"track_index": audio_rack_track["index"], "name": "Rack Batch Audio Effect Rack"})
            self.call("set_track_name", {"track_index": drum_track["index"], "name": "Rack Batch Drum Rack"})

            instrument_device_index, instrument_target = self.load_rack_with_fallback(
                instrument_track["index"],
                "instrument_rack",
                "instruments",
                "Instrument Rack",
                "Instrument Rack",
            )
            audio_rack_device_index, audio_rack_target = self.load_rack_with_fallback(
                audio_rack_track["index"],
                "audio_effect_rack",
                "audio_effects",
                "Audio Effect Rack",
                "Audio Effect Rack",
            )

            drum_before = len(self.track_devices(drum_track["index"]))
            drum_result = self.call(
                "load_drum_kit",
                {"track_index": drum_track["index"], "rack_uri": drum_kit_item["uri"]},
            )
            drum_devices = self.wait_for_device_growth(drum_track["index"], drum_before)
            self.require(drum_result["mode"] == "drum_kit_load", "Drum kit load returned wrong mode")
            self.require(len(drum_devices) > drum_before, "Drum kit load did not grow device count")
            drum_device_index = drum_result.get("device_index", len(drum_devices) - 1)

            self.summary["discovered_targets"] = {
                "instrument_rack": instrument_target,
                "audio_effect_rack": audio_rack_target,
                "drum_kit_uri": drum_kit_item["uri"],
            }

            self.validate_rack_commands(instrument_track["index"], instrument_device_index, "Instrument Rack")
            self.validate_rack_commands(audio_rack_track["index"], audio_rack_device_index, "Audio Effect Rack")
            self.validate_rack_commands(drum_track["index"], drum_device_index, "Drum Rack", require_chain=True)
            self.validate_drum_commands(drum_track["index"], drum_device_index)

            return self.summary
        finally:
            self.safe_cleanup()


def main():
    validator = RackAndDrumBatchValidator()
    summary = validator.run()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Rack/drum batch validation failed: {}".format(exc), file=sys.stderr)
        raise
