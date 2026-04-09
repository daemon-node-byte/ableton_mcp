from __future__ import absolute_import, print_function, unicode_literals

import json
import sys
import time

from mcp_server.client import AbletonCommandError, AbletonRemoteClient


PREFERRED_NATIVE_INSTRUMENTS = ("Drift", "Analog", "Operator")


class BrowserLoadingBatchValidator(object):
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
        }

    def call(self, command_name, params=None):
        return self.client.send_command(command_name, params or {})

    def require(self, condition, message):
        if not condition:
            raise AssertionError(message)

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

    def pick_native_instrument_name(self, instrument_items):
        available_names = [item["name"] for item in instrument_items if item.get("is_loadable")]
        for preferred_name in PREFERRED_NATIVE_INSTRUMENTS:
            if preferred_name in available_names:
                return preferred_name
        if available_names:
            return available_names[0]
        raise AssertionError("No loadable native instrument names were discovered")

    def safe_cleanup(self):
        for track_index in sorted(self.created_track_indices, reverse=True):
            try:
                self.call("delete_track", {"track_index": track_index})
            except Exception:
                pass

    def run(self):
        try:
            health = self.call("health_check", {})
            session_info = self.call("get_session_info", {})
            browser_tree = self.call("get_browser_tree", {"category_type": "all"})
            instrument_items = self.call("get_browser_items_at_path", {"path": "instruments"})["items"]
            drum_items = self.call("get_browser_items_at_path", {"path": "drums"})["items"]
            drift_search = self.call("search_browser", {"query": "drift", "category": "instruments"})

            self.summary["baseline"] = {
                "health_check": health,
                "track_count": session_info["track_count"],
            }

            self.require("instruments" in browser_tree and browser_tree["instruments"], "Browser tree missing instruments")
            self.require("drums" in browser_tree and browser_tree["drums"], "Browser tree missing drums")
            self.require("audio_effects" in browser_tree, "Browser tree missing audio_effects")
            self.summary["validated_commands"].extend(
                ["get_browser_tree", "get_browser_items_at_path", "search_browser"]
            )

            native_name = self.pick_native_instrument_name(instrument_items)
            uri_item = None
            if drift_search["results"]:
                uri_item = drift_search["results"][0]
            else:
                loadable_instrument_items = [item for item in instrument_items if item.get("is_loadable")]
                if not loadable_instrument_items:
                    raise AssertionError("No loadable instrument URIs were discovered")
                uri_item = loadable_instrument_items[0]

            drum_kit_item = None
            for item in drum_items:
                if item.get("is_loadable") and not item.get("is_device"):
                    drum_kit_item = item
                    break
            if drum_kit_item is None:
                raise AssertionError("No loadable drum-kit preset URI was discovered")

            self.summary["discovered_targets"] = {
                "native_instrument_name": native_name,
                "instrument_uri": uri_item["uri"],
                "drum_kit_uri": drum_kit_item["uri"],
            }

            native_track = self.call("create_midi_track", {})
            self.created_track_indices.append(native_track["index"])
            uri_track = self.call("create_midi_track", {})
            self.created_track_indices.append(uri_track["index"])
            drum_track = self.call("create_midi_track", {})
            self.created_track_indices.append(drum_track["index"])

            self.call("set_track_name", {"track_index": native_track["index"], "name": "Browser Batch Native"})
            self.call("set_track_name", {"track_index": uri_track["index"], "name": "Browser Batch URI"})
            self.call("set_track_name", {"track_index": drum_track["index"], "name": "Browser Batch Drums"})

            native_before = len(self.track_devices(native_track["index"]))
            native_result = self.call(
                "load_instrument_or_effect",
                {"track_index": native_track["index"], "device_name": native_name},
            )
            native_devices = self.wait_for_device_growth(native_track["index"], native_before)
            self.require(native_result["mode"] == "native_device_insert", "Native insert returned wrong mode")
            self.require(len(native_devices) > native_before, "Native instrument insert did not grow device count")

            uri_before = len(self.track_devices(uri_track["index"]))
            uri_result = self.call(
                "load_instrument_or_effect",
                {"track_index": uri_track["index"], "uri": uri_item["uri"]},
            )
            uri_devices = self.wait_for_device_growth(uri_track["index"], uri_before)
            self.require(uri_result["mode"] == "browser_uri_load", "URI load returned wrong mode")
            self.require(len(uri_devices) > uri_before, "Browser URI instrument load did not grow device count")

            drum_before = len(self.track_devices(drum_track["index"]))
            drum_result = self.call(
                "load_drum_kit",
                {"track_index": drum_track["index"], "rack_uri": drum_kit_item["uri"]},
            )
            drum_devices = self.wait_for_device_growth(drum_track["index"], drum_before)
            self.require(drum_result["mode"] == "drum_kit_load", "Drum kit load returned wrong mode")
            self.require(len(drum_devices) > drum_before, "Drum kit load did not grow device count")

            self.summary["validated_commands"].extend(
                ["load_instrument_or_effect:native", "load_instrument_or_effect:uri", "load_drum_kit"]
            )

            self.expect_error(
                "load_instrument_or_effect",
                {"track_index": native_track["index"]},
                "exactly one",
            )
            self.expect_error(
                "load_instrument_or_effect",
                {"track_index": native_track["index"], "device_name": native_name, "uri": uri_item["uri"]},
                "exactly one",
            )
            self.expect_error(
                "load_instrument_or_effect",
                {"track_index": native_track["index"], "uri": "query:Synths#DoesNotExist"},
                "Browser item not found",
            )
            self.expect_error(
                "load_instrument_or_effect",
                {"track_index": native_track["index"], "device_name": native_name, "target_index": -1},
                "target_index must be >=",
            )
            self.expect_error(
                "get_browser_tree",
                {"category_type": "not_a_real_category"},
                "Unknown browser category",
            )
            self.expect_error(
                "get_browser_items_at_path",
                {"path": "instruments/Definitely Missing"},
                "not found",
            )
            self.expect_error(
                "search_browser",
                {"query": "   ", "category": "all"},
                "non-empty query",
            )
            self.expect_error(
                "load_drum_kit",
                {"track_index": drum_track["index"], "rack_uri": "query:Drums#Drum%20Rack"},
                "drum-kit preset URI",
            )

            return self.summary
        finally:
            self.safe_cleanup()


def main():
    validator = BrowserLoadingBatchValidator()
    summary = validator.run()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Browser/loading batch validation failed: {}".format(exc), file=sys.stderr)
        raise
