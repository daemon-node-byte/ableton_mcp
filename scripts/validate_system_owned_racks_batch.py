from __future__ import absolute_import, print_function, unicode_literals

import json
import os
import sys

from mcp_server.client import AbletonCommandError, AbletonRemoteClient


class SystemOwnedRackBatchValidator(object):
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
            "memory_bank": {},
            "created_paths": {},
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

    def safe_cleanup(self):
        for track_index in sorted(self.created_track_indices, reverse=True):
            try:
                self.call("delete_track", {"track_index": track_index})
            except Exception:
                pass

    def pick_parameter_name(self, parameter_payload, candidates):
        parameters = list(parameter_payload["parameters"])
        for candidate in candidates:
            candidate_lower = candidate.lower()
            for parameter in parameters:
                if parameter["name"].lower() == candidate_lower:
                    return parameter["name"]
        for candidate in candidates:
            candidate_lower = candidate.lower()
            for parameter in parameters:
                if candidate_lower in parameter["name"].lower():
                    return parameter["name"]
        for parameter in parameters:
            if parameter["name"] != "Device On":
                return parameter["name"]
        raise AssertionError("No writable parameter was discovered on '{}'".format(parameter_payload["device_name"]))

    def choose_target_value(self, parameter):
        minimum = float(parameter["min"])
        maximum = float(parameter["max"])
        current = float(parameter["value"])
        midpoint = minimum + ((maximum - minimum) / 2.0)
        if abs(current - midpoint) > 0.0001:
            return midpoint
        return maximum if abs(current - maximum) > 0.0001 else minimum

    def find_chain(self, structure, chain_name):
        for chain in list(structure.get("chains", []) or []):
            if chain["name"] == chain_name:
                return chain
        raise AssertionError("Unable to find chain '{}'".format(chain_name))

    def find_device(self, chain, device_name):
        for device in list(chain.get("devices", []) or []):
            if device["name"] == device_name:
                return device
        raise AssertionError("Unable to find device '{}'".format(device_name))

    def validate_memory_bank_files(self, session_path):
        project_root = os.path.dirname(session_path)
        memory_root = os.path.join(project_root, ".ableton-mcp", "memory")
        today_file = os.path.join(memory_root, "sessions")
        self.require(os.path.isdir(memory_root), "Memory Bank root was not created")
        self.require(os.path.exists(os.path.join(memory_root, "project.md")), "project.md was not created")
        self.require(os.path.exists(os.path.join(memory_root, "racks.md")), "racks.md was not created")
        self.require(os.path.isdir(today_file), "sessions/ directory was not created")
        self.summary["memory_bank"]["root"] = memory_root

    def run(self):
        try:
            health = self.call("health_check")
            session_path_result = self.call("get_session_path")
            self.mark_validated("get_session_path")
            session_path = str(session_path_result.get("path", "") or "").strip()
            self.require(session_path, "The current Live Set must be saved before validating system-owned racks")
            self.require(os.path.exists(session_path), "Saved Live Set path does not exist: {}".format(session_path))

            self.summary["baseline"] = {"health_check": health, "session_path": session_path}

            midi_track = self.call("create_midi_track")
            audio_track = self.call("create_audio_track")
            blueprint_track = self.call("create_audio_track")
            self.created_track_indices.extend([midi_track["index"], audio_track["index"], blueprint_track["index"]])

            self.call("set_track_name", {"track_index": midi_track["index"], "name": "System Rack MIDI"})
            self.call("set_track_name", {"track_index": audio_track["index"], "name": "System Rack Audio"})
            self.call("set_track_name", {"track_index": blueprint_track["index"], "name": "System Rack Blueprint"})

            instrument_rack = self.call(
                "create_rack",
                {"track_index": midi_track["index"], "rack_type": "instrument", "name": "Lead Rack"},
            )
            self.mark_validated("create_rack")
            instrument_chain = self.call(
                "insert_rack_chain",
                {"track_index": midi_track["index"], "rack_path": instrument_rack["rack_path"], "name": "Voice"},
            )
            self.mark_validated("insert_rack_chain")
            drift_device = self.call(
                "insert_device_in_chain",
                {
                    "track_index": midi_track["index"],
                    "chain_path": instrument_chain["chain_path"],
                    "native_device_name": "Drift",
                },
            )
            self.mark_validated("insert_device_in_chain")
            nested_fx_rack = self.call(
                "create_rack",
                {
                    "track_index": midi_track["index"],
                    "rack_type": "audio_effect",
                    "name": "Lead FX",
                    "target_path": instrument_chain["chain_path"],
                },
            )
            nested_chain = self.call(
                "insert_rack_chain",
                {"track_index": midi_track["index"], "rack_path": nested_fx_rack["rack_path"], "name": "FX"},
            )
            utility_device = self.call(
                "insert_device_in_chain",
                {
                    "track_index": midi_track["index"],
                    "chain_path": nested_chain["chain_path"],
                    "native_device_name": "Utility",
                },
            )

            instrument_structure = self.call(
                "get_rack_structure",
                {"track_index": midi_track["index"], "rack_path": instrument_rack["rack_path"]},
            )
            self.mark_validated("get_rack_structure")
            voice_chain = self.find_chain(instrument_structure["rack"], "Voice")
            self.require(
                any(device["path"] == nested_fx_rack["rack_path"] for device in list(voice_chain["devices"] or [])),
                "Nested rack path was not returned by get_rack_structure",
            )

            drift_parameters = self.call(
                "get_device_parameters_at_path",
                {"track_index": midi_track["index"], "device_path": drift_device["device_path"]},
            )
            self.mark_validated("get_device_parameters_at_path")
            drift_parameter_name = self.pick_parameter_name(drift_parameters, ["Filter Freq", "Frequency"])
            drift_parameter = [p for p in drift_parameters["parameters"] if p["name"] == drift_parameter_name][0]
            self.call(
                "set_device_parameter_by_name_at_path",
                {
                    "track_index": midi_track["index"],
                    "device_path": drift_device["device_path"],
                    "name": drift_parameter_name,
                    "value": self.choose_target_value(drift_parameter),
                },
            )
            self.mark_validated("set_device_parameter_by_name_at_path")

            utility_parameters = self.call(
                "get_device_parameters_at_path",
                {"track_index": midi_track["index"], "device_path": utility_device["device_path"]},
            )
            utility_parameter_name = self.pick_parameter_name(utility_parameters, ["Gain"])
            utility_parameter = [p for p in utility_parameters["parameters"] if p["name"] == utility_parameter_name][0]
            self.call(
                "set_device_parameter_at_path",
                {
                    "track_index": midi_track["index"],
                    "device_path": utility_device["device_path"],
                    "parameter_index": utility_parameter["index"],
                    "value": self.choose_target_value(utility_parameter),
                },
            )
            self.mark_validated("set_device_parameter_at_path")

            audio_rack = self.call(
                "create_rack",
                {"track_index": audio_track["index"], "rack_type": "audio_effect", "name": "Mix Rack"},
            )
            eq_chain = self.call(
                "insert_rack_chain",
                {"track_index": audio_track["index"], "rack_path": audio_rack["rack_path"], "name": "EQ"},
            )
            texture_chain = self.call(
                "insert_rack_chain",
                {"track_index": audio_track["index"], "rack_path": audio_rack["rack_path"], "name": "Texture"},
            )
            self.call(
                "insert_device_in_chain",
                {
                    "track_index": audio_track["index"],
                    "chain_path": eq_chain["chain_path"],
                    "native_device_name": "Eq8",
                    "device_name": "Tone EQ",
                },
            )
            self.call(
                "insert_device_in_chain",
                {
                    "track_index": audio_track["index"],
                    "chain_path": texture_chain["chain_path"],
                    "native_device_name": "Saturator",
                },
            )
            self.call(
                "insert_device_in_chain",
                {
                    "track_index": audio_track["index"],
                    "chain_path": texture_chain["chain_path"],
                    "native_device_name": "Delay",
                },
            )
            self.call(
                "insert_device_in_chain",
                {
                    "track_index": audio_track["index"],
                    "chain_path": texture_chain["chain_path"],
                    "native_device_name": "Utility",
                },
            )

            rack_chains = self.call(
                "get_rack_chains",
                {"track_index": audio_track["index"], "device_index": audio_rack["device_index"]},
            )
            self.mark_validated("get_rack_chains")
            self.require(len(rack_chains["chains"]) == 2, "Audio rack should expose exactly two chains")
            self.call(
                "set_chain_mute",
                {
                    "track_index": audio_track["index"],
                    "device_index": audio_rack["device_index"],
                    "chain_index": 0,
                    "mute": True,
                },
            )
            self.mark_validated("set_chain_mute")
            self.call(
                "set_chain_solo",
                {
                    "track_index": audio_track["index"],
                    "device_index": audio_rack["device_index"],
                    "chain_index": 1,
                    "solo": True,
                },
            )
            self.mark_validated("set_chain_solo")
            self.call(
                "set_chain_volume",
                {
                    "track_index": audio_track["index"],
                    "device_index": audio_rack["device_index"],
                    "chain_index": 1,
                    "volume": 0.37,
                },
            )
            self.mark_validated("set_chain_volume")
            chain_devices = self.call(
                "get_chain_devices",
                {
                    "track_index": audio_track["index"],
                    "device_index": audio_rack["device_index"],
                    "chain_index": 0,
                },
            )
            self.mark_validated("get_chain_devices")
            self.require(chain_devices["devices"], "EQ chain should contain devices")

            audio_macros = self.call(
                "get_rack_macros",
                {"track_index": audio_track["index"], "device_index": audio_rack["device_index"]},
            )
            self.mark_validated("get_rack_macros")
            self.require(audio_macros["macros"], "Created Audio Effect Rack should expose macros")
            self.call(
                "set_rack_macro",
                {
                    "track_index": audio_track["index"],
                    "device_index": audio_rack["device_index"],
                    "macro_index": audio_macros["macros"][0]["index"],
                    "value": audio_macros["macros"][0]["max"],
                },
            )
            self.mark_validated("set_rack_macro")

            blueprint_result = self.call(
                "apply_rack_blueprint",
                {
                    "blueprint": {
                        "track_index": blueprint_track["index"],
                        "rack_type": "audio_effect",
                        "rack_name": "Blueprint Rack",
                        "chains": [
                            {
                                "name": "EQ",
                                "devices": [
                                    {
                                        "native_device_name": "Eq8",
                                        "device_name": "Blueprint EQ",
                                        "parameter_values": {"Gain A": 2.0},
                                    }
                                ],
                            },
                            {
                                "name": "Texture",
                                "devices": [
                                    {"native_device_name": "Saturator", "parameter_values": {"Drive": 0.4}},
                                    {"native_device_name": "Delay", "parameter_values": {"Dry/Wet": 0.4}},
                                ],
                            },
                        ],
                    }
                },
            )
            self.mark_validated("apply_rack_blueprint")
            self.require(blueprint_result["created_chains"] == 2, "Blueprint rack did not create two chains")

            system_owned = self.call("get_system_owned_racks")
            self.mark_validated("get_system_owned_racks")
            self.require(system_owned["count"] >= 3, "Expected at least three tracked system-owned racks")

            refresh_result = self.call(
                "refresh_rack_memory_entry",
                {"track_index": audio_track["index"], "rack_path": audio_rack["rack_path"]},
            )
            self.mark_validated("refresh_rack_memory_entry")
            self.require(refresh_result["rack_id"], "refresh_rack_memory_entry did not return a rack_id")

            self.call("write_memory_bank", {"file_name": "validator-notes.md", "content": "# Validator Notes\n"})
            self.mark_validated("write_memory_bank")
            validator_notes = self.call("read_memory_bank", {"file_name": "validator-notes.md"})
            self.mark_validated("read_memory_bank")
            self.require("Validator Notes" in validator_notes, "write/read_memory_bank did not round-trip")
            self.call("append_rack_entry", {"rack_data": "## Validator Append\n- ok"})
            self.mark_validated("append_rack_entry")
            racks_md = self.call("read_memory_bank", {"file_name": "racks.md"})
            self.require("Validator Append" in racks_md, "append_rack_entry did not append to racks.md")

            self.expect_error(
                "apply_rack_blueprint",
                {
                    "blueprint": {
                        "track_index": blueprint_track["index"],
                        "rack_type": "audio_effect",
                        "rack_name": "Rejected Rack",
                        "macro_mappings": [{"macro": 0, "parameter": "Gain A"}],
                        "chains": [{"name": "Only Chain"}],
                    }
                },
                "Native macro mapping is not confirmed",
            )

            self.validate_memory_bank_files(session_path)
            self.summary["created_paths"] = {
                "instrument_rack_path": instrument_rack["rack_path"],
                "nested_fx_rack_path": nested_fx_rack["rack_path"],
                "audio_rack_path": audio_rack["rack_path"],
                "blueprint_rack_path": blueprint_result["rack_path"],
            }
            return self.summary
        finally:
            self.safe_cleanup()


def main():
    validator = SystemOwnedRackBatchValidator()
    summary = validator.run()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("System-owned rack validation failed: {}".format(exc), file=sys.stderr)
        raise
