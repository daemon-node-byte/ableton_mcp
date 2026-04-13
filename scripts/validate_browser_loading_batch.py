from __future__ import absolute_import, print_function, unicode_literals

import json
import sys
import time

from mcp_server.client import AbletonCommandError, AbletonRemoteClient, AbletonTransportError


PREFERRED_NATIVE_INSTRUMENTS = ("Drift", "Analog", "Operator")


class BrowserLoadingBatchValidator(object):
    def __init__(self, host="localhost", port=9877, connect_timeout=5.0, response_timeout=30.0):
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.response_timeout = response_timeout
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
            "content_classes_tested": [],
            "third_party_search_audit": {"plugin_targets": [], "searches": [], "limitations": []},
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

    def call_with_timeout(self, command_name, params=None, response_timeout=None):
        client = AbletonRemoteClient(
            host=self.host,
            port=self.port,
            connect_timeout=self.connect_timeout,
            response_timeout=response_timeout if response_timeout is not None else self.response_timeout,
        )
        return client.send_command(command_name, params or {})

    def pick_native_instrument_name(self, instrument_items):
        available_names = [item["name"] for item in instrument_items if item.get("is_loadable")]
        for preferred_name in PREFERRED_NATIVE_INSTRUMENTS:
            if preferred_name in available_names:
                return preferred_name
        if available_names:
            return available_names[0]
        raise AssertionError("No loadable native instrument names were discovered")

    def pick_loadable_browser_item(self, items, label, require_device=None):
        matches = []
        for item in items:
            if not item.get("is_loadable"):
                continue
            if require_device is not None and bool(item.get("is_device")) != bool(require_device):
                continue
            matches.append(item)
        if matches:
            return matches[0]
        raise AssertionError("No loadable {} were discovered".format(label))

    def pick_loadable_search_result(self, query, category, label):
        result = self.call("search_browser", {"query": query, "category": category})
        if result["results"]:
            for item in result["results"]:
                if item.get("is_loadable"):
                    return item
        raise AssertionError("No loadable {} were discovered for query '{}'".format(label, query))

    def discover_plugin_targets(self, session_info):
        targets = []
        for track in list(session_info.get("tracks", []) or []):
            try:
                devices = self.call("get_track_devices", {"track_index": int(track["index"])})
            except Exception:
                continue
            for device in list(devices.get("devices", []) or []):
                if not bool(device.get("is_plugin")):
                    continue
                name = str(device.get("name") or "").strip()
                if not name:
                    continue
                queries = [name]
                if name.endswith(" 2"):
                    queries.append(name.rsplit(" ", 1)[0])
                targets.append(
                    {
                        "track_index": int(track["index"]),
                        "track_name": track.get("name"),
                        "device_index": int(device.get("index", -1)),
                        "device_name": name,
                        "queries": queries,
                    }
                )
        return targets

    def audit_third_party_searches(self, plugin_targets):
        audit = {"plugin_targets": plugin_targets, "searches": [], "limitations": []}
        categories = ("instruments", "audio_effects", "sounds", "user_library", "packs")
        discovered_uri = None
        for target in plugin_targets:
            for query in target["queries"]:
                for category in categories:
                    try:
                        result = self.call_with_timeout(
                            "search_browser",
                            {"query": query, "category": category},
                            response_timeout=6.0,
                        )
                        entry = {
                            "query": query,
                            "category": category,
                            "count": int(result.get("count", 0)),
                            "timed_out": False,
                        }
                        if result.get("results"):
                            first_result = result["results"][0]
                            entry["first_result_name"] = first_result.get("name")
                            entry["first_result_uri"] = first_result.get("uri")
                            entry["first_result_loadable"] = bool(first_result.get("is_loadable"))
                            if discovered_uri is None:
                                for item in result["results"]:
                                    if item.get("is_loadable"):
                                        discovered_uri = item
                                        break
                        audit["searches"].append(entry)
                    except AbletonTransportError as exc:
                        audit["searches"].append(
                            {
                                "query": query,
                                "category": category,
                                "timed_out": True,
                                "message": str(exc),
                            }
                        )
                        audit["limitations"].append(
                            "search_browser(category='{}') timed out for query '{}' on the validated build".format(
                                category, query
                            )
                        )
            primary_query = target["queries"][0]
            try:
                all_result = self.call_with_timeout(
                    "search_browser",
                    {"query": primary_query, "category": "all"},
                    response_timeout=8.0,
                )
                audit["searches"].append(
                    {
                        "query": primary_query,
                        "category": "all",
                        "count": int(all_result.get("count", 0)),
                        "timed_out": False,
                    }
                )
            except AbletonTransportError as exc:
                audit["searches"].append(
                    {
                        "query": primary_query,
                        "category": "all",
                        "timed_out": True,
                        "message": str(exc),
                    }
                )
                audit["limitations"].append(
                    "search_browser(category='all') timed out for query '{}' on the validated build".format(
                        primary_query
                    )
                )
        if discovered_uri is None and plugin_targets:
            audit["limitations"].append(
                "No discoverable third-party plugin URI was surfaced through the current normalized browser roots for {}".format(
                    ", ".join(target["device_name"] for target in plugin_targets)
                )
            )
        return audit, discovered_uri

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
            audio_effect_items = self.call("get_browser_items_at_path", {"path": "audio_effects"})["items"]
            midi_effect_items = self.call("get_browser_items_at_path", {"path": "midi_effects"})["items"]
            drum_items = self.call("get_browser_items_at_path", {"path": "drums"})["items"]
            sounds_items = self.call("get_browser_items_at_path", {"path": "sounds"})["items"]
            drift_search = self.call("search_browser", {"query": "drift", "category": "instruments"})
            sounds_search_item = self.pick_loadable_search_result("pad", "sounds", "sound preset URIs")
            plugin_targets = self.discover_plugin_targets(session_info)
            third_party_audit, third_party_uri_item = self.audit_third_party_searches(plugin_targets)

            self.summary["baseline"] = {
                "health_check": health,
                "track_count": session_info["track_count"],
            }

            self.require("instruments" in browser_tree and browser_tree["instruments"], "Browser tree missing instruments")
            self.require("drums" in browser_tree and browser_tree["drums"], "Browser tree missing drums")
            self.require("audio_effects" in browser_tree, "Browser tree missing audio_effects")
            self.require("midi_effects" in browser_tree, "Browser tree missing midi_effects")
            self.require("sounds" in browser_tree, "Browser tree missing sounds")
            self.require(bool(sounds_items), "Sounds browser root returned no items")
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

            drum_kit_item = self.pick_loadable_browser_item(
                drum_items,
                "drum-kit preset URIs",
                require_device=False,
            )
            audio_effect_item = self.pick_loadable_browser_item(
                audio_effect_items,
                "built-in audio effects",
                require_device=True,
            )
            midi_effect_item = self.pick_loadable_browser_item(
                midi_effect_items,
                "built-in MIDI effects",
                require_device=True,
            )

            self.summary["discovered_targets"] = {
                "native_instrument_name": native_name,
                "instrument_uri": uri_item["uri"],
                "sounds_uri": sounds_search_item["uri"],
                "drum_kit_uri": drum_kit_item["uri"],
                "audio_effect_uri": audio_effect_item["uri"],
                "midi_effect_uri": midi_effect_item["uri"],
            }
            if third_party_uri_item is not None:
                self.summary["discovered_targets"]["third_party_uri"] = third_party_uri_item["uri"]
            self.summary["third_party_search_audit"] = third_party_audit
            self.summary["content_classes_tested"] = [
                "native_device_insert",
                "instrument_uri",
                "sounds_preset_uri",
                "drum_kit_preset_uri",
                "midi_effect_uri",
                "audio_effect_uri",
                "third_party_uri_discovery_limit",
            ]

            native_track = self.call("create_midi_track", {})
            self.created_track_indices.append(native_track["index"])
            uri_track = self.call("create_midi_track", {})
            self.created_track_indices.append(uri_track["index"])
            sounds_track = self.call("create_midi_track", {})
            self.created_track_indices.append(sounds_track["index"])
            drum_track = self.call("create_midi_track", {})
            self.created_track_indices.append(drum_track["index"])
            midi_effect_track = self.call("create_midi_track", {})
            self.created_track_indices.append(midi_effect_track["index"])
            audio_effect_track = self.call("create_audio_track", {})
            self.created_track_indices.append(audio_effect_track["index"])

            self.call("set_track_name", {"track_index": native_track["index"], "name": "Browser Batch Native"})
            self.call("set_track_name", {"track_index": uri_track["index"], "name": "Browser Batch URI"})
            self.call("set_track_name", {"track_index": sounds_track["index"], "name": "Browser Batch Sounds"})
            self.call("set_track_name", {"track_index": drum_track["index"], "name": "Browser Batch Drums"})
            self.call(
                "set_track_name",
                {"track_index": midi_effect_track["index"], "name": "Browser Batch MIDI Effects"},
            )
            self.call(
                "set_track_name",
                {"track_index": audio_effect_track["index"], "name": "Browser Batch Audio Effects"},
            )

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

            sounds_before = len(self.track_devices(sounds_track["index"]))
            sounds_result = self.call(
                "load_instrument_or_effect",
                {"track_index": sounds_track["index"], "uri": sounds_search_item["uri"]},
            )
            sounds_devices = self.wait_for_device_growth(sounds_track["index"], sounds_before)
            self.require(sounds_result["mode"] == "browser_uri_load", "Sounds preset load returned wrong mode")
            self.require(len(sounds_devices) > sounds_before, "Sounds preset load did not grow device count")

            drum_before = len(self.track_devices(drum_track["index"]))
            drum_result = self.call(
                "load_drum_kit",
                {"track_index": drum_track["index"], "rack_uri": drum_kit_item["uri"]},
            )
            drum_devices = self.wait_for_device_growth(drum_track["index"], drum_before)
            self.require(drum_result["mode"] == "drum_kit_load", "Drum kit load returned wrong mode")
            self.require(len(drum_devices) > drum_before, "Drum kit load did not grow device count")

            midi_effect_before = len(self.track_devices(midi_effect_track["index"]))
            midi_effect_result = self.call(
                "load_instrument_or_effect",
                {"track_index": midi_effect_track["index"], "uri": midi_effect_item["uri"]},
            )
            midi_effect_devices = self.wait_for_device_growth(midi_effect_track["index"], midi_effect_before)
            self.require(
                midi_effect_result["mode"] == "browser_uri_load",
                "MIDI effect load returned wrong mode",
            )
            self.require(
                len(midi_effect_devices) > midi_effect_before,
                "Built-in MIDI effect load did not grow device count",
            )

            audio_effect_before = len(self.track_devices(audio_effect_track["index"]))
            audio_effect_result = self.call(
                "load_instrument_or_effect",
                {"track_index": audio_effect_track["index"], "uri": audio_effect_item["uri"]},
            )
            audio_effect_devices = self.wait_for_device_growth(audio_effect_track["index"], audio_effect_before)
            self.require(
                audio_effect_result["mode"] == "browser_uri_load",
                "Audio effect load returned wrong mode",
            )
            self.require(
                len(audio_effect_devices) > audio_effect_before,
                "Built-in audio effect load did not grow device count",
            )

            self.summary["validated_commands"].extend(
                [
                    "load_instrument_or_effect:native",
                    "load_instrument_or_effect:uri",
                    "load_instrument_or_effect:sounds_uri",
                    "load_drum_kit",
                    "load_instrument_or_effect:midi_effect_uri",
                    "load_instrument_or_effect:audio_effect_uri",
                ]
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
                {"track_index": uri_track["index"], "uri": uri_item["uri"], "target_index": 0},
                "only supported with native device insertion",
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
