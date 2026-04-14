from __future__ import absolute_import, print_function, unicode_literals

import json
import sys
import time

from mcp_server.client import AbletonCommandError, AbletonRemoteClient


PREFERRED_INSTRUMENTS = ("Drift", "Analog", "Operator")
PREFERRED_MIDI_EFFECTS = ("Arpeggiator", "Chord", "Pitch")
PREFERRED_AUDIO_EFFECTS = ("Utility", "EQ Eight", "Auto Filter")


def _approx_equal(left, right, tolerance=0.001):
    return abs(float(left) - float(right)) <= tolerance


class DeviceAuditBatchValidator(object):
    def __init__(self, host="localhost", port=9877, connect_timeout=5.0, response_timeout=30.0):
        self.client = AbletonRemoteClient(
            host=host,
            port=port,
            connect_timeout=connect_timeout,
            response_timeout=response_timeout,
        )
        self.created_track_indices = []
        self.original_selection = None
        self.summary = {
            "baseline": {},
            "validated_commands": [],
            "negative_cases": [],
            "discovered_targets": {},
            "observed_behavior": {},
            "cleanup": {
                "restored_selection": False,
                "deleted_tracks": [],
            },
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

    def wait_for_device_count(self, track_index, expected_count, timeout_seconds=12.0):
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            devices = self.track_devices(track_index)
            if len(devices) == expected_count:
                return devices
            time.sleep(0.25)
        raise AssertionError(
            "Timed out waiting for device count {} on track {} (last={})".format(
                expected_count, track_index, len(self.track_devices(track_index))
            )
        )

    def choose_device_name(self, items, preferred_names):
        loadable_names = [item["name"] for item in items if item.get("is_loadable")]
        for preferred_name in preferred_names:
            if preferred_name in loadable_names:
                return preferred_name
        if loadable_names:
            return loadable_names[0]
        raise AssertionError("No loadable device names discovered for {}".format(preferred_names))

    def find_device_index_by_name(self, track_index, name):
        for device in self.track_devices(track_index):
            if device["name"] == name:
                return int(device["index"])
        raise AssertionError("Device '{}' not found on track {}".format(name, track_index))

    def choose_parameter_target(self, track_index, device_indices):
        for device_index in device_indices:
            payload = self.call(
                "get_device_parameters",
                {"track_index": track_index, "device_index": device_index},
            )
            parameters = payload["parameters"]
            for parameter in parameters[1:]:
                if not parameter.get("is_enabled"):
                    continue
                if float(parameter["max"]) <= float(parameter["min"]):
                    continue
                if not parameter.get("is_quantized"):
                    return device_index, parameter, payload
            for parameter in parameters[1:]:
                if parameter.get("is_enabled") and float(parameter["max"]) > float(parameter["min"]):
                    return device_index, parameter, payload
        raise AssertionError("No writable non-activator parameter target found")

    def alternate_parameter_value(self, parameter, fraction=0.5):
        minimum = float(parameter["min"])
        maximum = float(parameter["max"])
        current = float(parameter["value"])
        if parameter.get("is_quantized"):
            if _approx_equal(current, minimum):
                return maximum
            return minimum
        candidate = minimum + ((maximum - minimum) * float(fraction))
        if _approx_equal(candidate, current):
            candidate = minimum + ((maximum - minimum) * 0.75)
        if _approx_equal(candidate, current):
            candidate = minimum
        if _approx_equal(candidate, current):
            candidate = maximum
        if _approx_equal(candidate, current):
            raise AssertionError("Unable to choose alternate value for parameter '{}'".format(parameter["name"]))
        return candidate

    def restore_selection(self):
        if not self.original_selection:
            return
        selection_type = self.original_selection.get("selection_type")
        if selection_type == "track" and self.original_selection.get("track_index") is not None:
            self.call("select_track", {"track_index": self.original_selection["track_index"]})
            self.summary["cleanup"]["restored_selection"] = True
            return
        if selection_type == "return_track" and self.original_selection.get("return_index") is not None:
            self.call("select_track", {"return_index": self.original_selection["return_index"]})
            self.summary["cleanup"]["restored_selection"] = True
            return
        if selection_type == "master_track":
            self.call("select_track", {"master": True})
            self.summary["cleanup"]["restored_selection"] = True

    def safe_cleanup(self):
        try:
            self.restore_selection()
        except Exception:
            pass
        for track_index in sorted(self.created_track_indices, reverse=True):
            try:
                self.call("delete_track", {"track_index": track_index})
                self.summary["cleanup"]["deleted_tracks"].append(track_index)
            except Exception:
                pass

    def run(self):
        try:
            health = self.call("health_check", {})
            session_info = self.call("get_session_info", {})
            self.original_selection = self.call("get_selected_track", {})
            self.summary["baseline"] = {
                "health_check": health,
                "track_count": session_info["track_count"],
                "selected_track": self.original_selection,
            }

            instrument_items = self.call("get_browser_items_at_path", {"path": "instruments"})["items"]
            midi_effect_items = self.call("get_browser_items_at_path", {"path": "midi_effects"})["items"]
            audio_effect_items = self.call("get_browser_items_at_path", {"path": "audio_effects"})["items"]
            instrument_name = self.choose_device_name(instrument_items, PREFERRED_INSTRUMENTS)
            midi_effect_name = self.choose_device_name(midi_effect_items, PREFERRED_MIDI_EFFECTS)
            audio_effect_name = self.choose_device_name(audio_effect_items, PREFERRED_AUDIO_EFFECTS)
            second_audio_effect_name = self.choose_device_name(
                [item for item in audio_effect_items if item["name"] != audio_effect_name],
                PREFERRED_AUDIO_EFFECTS,
            )
            self.summary["discovered_targets"] = {
                "instrument_name": instrument_name,
                "midi_effect_name": midi_effect_name,
                "audio_effect_name": audio_effect_name,
                "second_audio_effect_name": second_audio_effect_name,
            }

            track = self.call("create_midi_track", {})
            track_index = int(track["index"])
            self.created_track_indices.append(track_index)
            self.call("set_track_name", {"track_index": track_index, "name": "Device Audit Validation"})
            self.call("select_track", {"track_index": track_index})

            empty_devices = self.track_devices(track_index)
            includes_mixer = any("Mixer" in str(device.get("class_name", "")) for device in empty_devices)
            self.summary["observed_behavior"]["empty_track_devices"] = empty_devices
            self.summary["observed_behavior"]["track_devices_include_mixer"] = includes_mixer

            instrument_result = self.call(
                "load_instrument_or_effect",
                {"track_index": track_index, "device_name": instrument_name},
            )
            self.wait_for_device_count(track_index, len(empty_devices) + 1)

            instrument_index = self.find_device_index_by_name(track_index, instrument_name)
            midi_result = self.call(
                "load_instrument_or_effect",
                {
                    "track_index": track_index,
                    "device_name": midi_effect_name,
                    "target_index": instrument_index,
                },
            )
            self.wait_for_device_count(track_index, len(empty_devices) + 2)

            first_audio_result = self.call(
                "load_instrument_or_effect",
                {"track_index": track_index, "device_name": audio_effect_name},
            )
            self.wait_for_device_count(track_index, len(empty_devices) + 3)

            second_audio_result = self.call(
                "load_instrument_or_effect",
                {"track_index": track_index, "device_name": second_audio_effect_name},
            )
            loaded_devices = self.wait_for_device_count(track_index, len(empty_devices) + 4)
            self.mark_validated("load_instrument_or_effect")

            self.summary["observed_behavior"]["loaded_devices_before_mutation"] = loaded_devices
            self.summary["observed_behavior"]["load_results"] = {
                "instrument": instrument_result,
                "midi_effect": midi_result,
                "first_audio_effect": first_audio_result,
                "second_audio_effect": second_audio_result,
            }

            track_devices_result = self.call("get_track_devices", {"track_index": track_index})
            self.require(track_devices_result["devices"], "Expected devices after native insertion")
            self.mark_validated("get_track_devices")

            candidate_indices = [
                self.find_device_index_by_name(track_index, audio_effect_name),
                self.find_device_index_by_name(track_index, second_audio_effect_name),
                self.find_device_index_by_name(track_index, instrument_name),
            ]
            parameter_device_index, parameter_target, parameter_payload = self.choose_parameter_target(
                track_index,
                candidate_indices,
            )
            self.mark_validated("get_device_parameters")

            get_by_name_result = self.call(
                "get_device_parameter_by_name",
                {
                    "track_index": track_index,
                    "device_index": parameter_device_index,
                    "name": parameter_target["name"],
                },
            )
            self.require(
                int(get_by_name_result["index"]) == int(parameter_target["index"]),
                "get_device_parameter_by_name returned wrong parameter index",
            )
            self.mark_validated("get_device_parameter_by_name")

            first_value = self.alternate_parameter_value(parameter_target, fraction=0.25)
            set_by_index_result = self.call(
                "set_device_parameter",
                {
                    "track_index": track_index,
                    "device_index": parameter_device_index,
                    "parameter_index": parameter_target["index"],
                    "value": first_value,
                },
            )
            self.require(
                _approx_equal(set_by_index_result["value"], first_value),
                "set_device_parameter did not report applied value",
            )
            readback_after_index = self.call(
                "get_device_parameter_by_name",
                {
                    "track_index": track_index,
                    "device_index": parameter_device_index,
                    "name": parameter_target["name"],
                },
            )
            self.require(
                _approx_equal(readback_after_index["value"], first_value),
                "set_device_parameter did not round-trip via get_device_parameter_by_name",
            )
            self.mark_validated("set_device_parameter")

            second_value = self.alternate_parameter_value(readback_after_index, fraction=0.75)
            set_by_name_result = self.call(
                "set_device_parameter_by_name",
                {
                    "track_index": track_index,
                    "device_index": parameter_device_index,
                    "name": parameter_target["name"],
                    "value": second_value,
                },
            )
            self.require(
                _approx_equal(set_by_name_result["value"], second_value),
                "set_device_parameter_by_name did not report applied value",
            )
            readback_after_name = self.call(
                "get_device_parameters",
                {"track_index": track_index, "device_index": parameter_device_index},
            )
            self.require(
                _approx_equal(
                    readback_after_name["parameters"][int(parameter_target["index"])]["value"],
                    second_value,
                ),
                "set_device_parameter_by_name did not round-trip via get_device_parameters",
            )
            self.mark_validated("set_device_parameter_by_name")

            class_name_result = self.call(
                "get_device_class_name",
                {"track_index": track_index, "device_index": parameter_device_index},
            )
            self.require(class_name_result["class_name"], "get_device_class_name returned empty class_name")
            self.mark_validated("get_device_class_name")

            select_result = self.call(
                "select_device",
                {"track_index": track_index, "device_index": parameter_device_index},
            )
            self.require(select_result["ok"], "select_device did not return ok")
            selected_result = self.call("get_selected_device", {})
            self.require(selected_result["selected"], "get_selected_device did not report a selected device")
            self.require(
                int(selected_result["track_index"]) == track_index
                and int(selected_result["device_index"]) == int(parameter_device_index),
                "Selected device round-trip mismatch",
            )
            self.mark_validated("select_device")
            self.mark_validated("get_selected_device")

            toggle_before = self.call(
                "get_device_parameters",
                {"track_index": track_index, "device_index": parameter_device_index},
            )["parameters"][0]
            toggle_result = self.call(
                "toggle_device",
                {"track_index": track_index, "device_index": parameter_device_index},
            )
            toggle_after = self.call(
                "get_device_parameters",
                {"track_index": track_index, "device_index": parameter_device_index},
            )["parameters"][0]
            self.require(
                not _approx_equal(toggle_before["value"], toggle_after["value"]),
                "toggle_device did not change the activator parameter",
            )
            self.require(
                toggle_result["mode"] == "activator_parameter",
                "toggle_device did not report activator_parameter mode",
            )
            self.mark_validated("toggle_device")

            disable_result = self.call(
                "set_device_enabled",
                {"track_index": track_index, "device_index": parameter_device_index, "enabled": False},
            )
            disabled_after = self.call(
                "get_device_parameters",
                {"track_index": track_index, "device_index": parameter_device_index},
            )["parameters"][0]
            self.require(
                _approx_equal(disabled_after["value"], 0.0),
                "set_device_enabled(False) did not zero the activator parameter",
            )
            enable_result = self.call(
                "set_device_enabled",
                {"track_index": track_index, "device_index": parameter_device_index, "enabled": True},
            )
            enabled_after = self.call(
                "get_device_parameters",
                {"track_index": track_index, "device_index": parameter_device_index},
            )["parameters"][0]
            self.require(
                enabled_after["value"] > 0.5,
                "set_device_enabled(True) did not restore the activator parameter",
            )
            self.require(disable_result["mode"] == "activator_parameter", "Disable call returned wrong mode")
            self.require(enable_result["mode"] == "activator_parameter", "Enable call returned wrong mode")
            self.mark_validated("set_device_enabled")

            show_result = self.call(
                "show_plugin_window",
                {"track_index": track_index, "device_index": parameter_device_index},
            )
            hide_result = self.call(
                "hide_plugin_window",
                {"track_index": track_index, "device_index": parameter_device_index},
            )
            self.require(show_result["collapsed"] is False, "show_plugin_window did not expand the device view")
            self.require(hide_result["collapsed"] is True, "hide_plugin_window did not collapse the device view")
            self.mark_validated("show_plugin_window")
            self.mark_validated("hide_plugin_window")

            first_audio_index = self.find_device_index_by_name(track_index, audio_effect_name)
            second_audio_index = self.find_device_index_by_name(track_index, second_audio_effect_name)
            move_result = self.call(
                "move_device",
                {
                    "track_index": track_index,
                    "device_index": second_audio_index,
                    "new_index": first_audio_index,
                },
            )
            devices_after_move = self.track_devices(track_index)
            moved_second_audio_index = self.find_device_index_by_name(track_index, second_audio_effect_name)
            moved_first_audio_index = self.find_device_index_by_name(track_index, audio_effect_name)
            self.require(
                moved_second_audio_index <= moved_first_audio_index,
                "move_device did not move the second audio effect ahead of the first",
            )
            self.summary["observed_behavior"]["move_result"] = move_result
            self.summary["observed_behavior"]["devices_after_move"] = devices_after_move
            self.mark_validated("move_device")

            delete_target_index = self.find_device_index_by_name(track_index, second_audio_effect_name)
            device_count_before_delete = len(self.track_devices(track_index))
            delete_result = self.call(
                "delete_device",
                {"track_index": track_index, "device_index": delete_target_index},
            )
            devices_after_delete = self.wait_for_device_count(track_index, device_count_before_delete - 1)
            self.require(delete_result["ok"], "delete_device did not return ok")
            self.require(
                all(device["name"] != second_audio_effect_name for device in devices_after_delete),
                "delete_device did not remove the targeted device",
            )
            self.summary["observed_behavior"]["devices_after_delete"] = devices_after_delete
            self.mark_validated("delete_device")

            self.expect_error(
                "get_device_parameters",
                {"track_index": track_index, "device_index": 999},
                "Device index 999 out of range",
            )
            self.expect_error(
                "move_device",
                {"track_index": track_index, "device_index": 0, "new_index": 999},
                "out of range",
            )
            self.expect_error(
                "set_device_parameter",
                {
                    "track_index": track_index,
                    "device_index": parameter_device_index,
                    "parameter_index": parameter_target["index"],
                    "value": float(parameter_target["max"]) + 1.0,
                },
                "out of range",
            )

            return self.summary
        finally:
            self.safe_cleanup()


def main(argv=None):
    validator = DeviceAuditBatchValidator()
    try:
        summary = validator.run()
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "summary": validator.summary}, indent=2, sort_keys=True))
        return 1
    print(json.dumps({"ok": True, "summary": summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
