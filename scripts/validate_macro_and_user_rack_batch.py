from __future__ import absolute_import, print_function, unicode_literals

import argparse
import json
import sys

from mcp_server.client import AbletonCommandError, AbletonRemoteClient


def _approx_equal(left, right, tolerance=0.001):
    return abs(float(left) - float(right)) <= tolerance


class MacroAndUserRackBatchValidator(object):
    def __init__(
        self,
        host="localhost",
        port=9877,
        connect_timeout=5.0,
        response_timeout=30.0,
        user_rack_track_index=None,
        user_rack_device_index=None,
    ):
        self.client = AbletonRemoteClient(
            host=host,
            port=port,
            connect_timeout=connect_timeout,
            response_timeout=response_timeout,
        )
        self.user_rack_track_index = user_rack_track_index
        self.user_rack_device_index = user_rack_device_index
        self.created_track_indices = []
        self.macro_restore_queue = []
        self.summary = {
            "baseline": {},
            "validated_commands": [],
            "skipped_checks": [],
            "negative_cases": [],
            "discovered_targets": {
                "system_owned_rack": None,
                "user_rack": None,
            },
            "macro_authoring_audit": {
                "lom_conclusion": (
                    "RackDevice exposes macro visibility, variations, and add/remove macro helpers, "
                    "but no documented native macro-to-parameter or macro-to-macro authoring API."
                )
            },
            "system_owned_rack_round_trip": {},
            "user_rack_audit": {},
            "cleanup": {
                "restored_macros": [],
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

    def mark_skipped(self, name, reason):
        self.summary["skipped_checks"].append({"name": name, "reason": reason})

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

    def choose_macro_target_value(self, macro_payload):
        minimum = float(macro_payload["min"])
        maximum = float(macro_payload["max"])
        current = float(macro_payload["value"])
        midpoint = minimum + ((maximum - minimum) / 2.0)
        if not _approx_equal(current, midpoint):
            return midpoint
        if not _approx_equal(current, maximum):
            return maximum
        return minimum

    def get_session_path(self):
        session_path = str(self.call("get_session_path").get("path", "") or "").strip()
        self.mark_validated("get_session_path")
        return session_path

    def get_inventory_if_available(self, session_path):
        if not str(session_path or "").strip():
            self.mark_skipped(
                "get_system_owned_racks",
                "Current Live Set is not saved, so Memory Bank inventory is unavailable",
            )
            return {"count": 0, "racks": []}
        inventory = self.call("get_system_owned_racks", {})
        self.mark_validated("get_system_owned_racks")
        return inventory

    def parse_top_level_device_index(self, rack_path):
        parts = str(rack_path or "").split()
        if len(parts) == 2 and parts[0] == "devices":
            return int(parts[1])
        return None

    def find_top_level_system_owned_rack(self, inventory):
        for entry in list(inventory.get("racks", []) or []):
            device_index = self.parse_top_level_device_index(entry.get("rack_path"))
            if device_index is None:
                continue
            if int(entry.get("macro_count", 0)) <= 0:
                continue
            try:
                devices = self.call("get_track_devices", {"track_index": int(entry["track_index"])})
            except AbletonCommandError:
                continue
            if device_index >= len(list(devices.get("devices", []) or [])):
                continue
            device_payload = list(devices.get("devices", []) or [])[device_index]
            if not bool(device_payload.get("is_rack")):
                continue
            return dict(entry, device_index=device_index, source="memory_bank")
        return None

    def create_disposable_system_owned_rack(self):
        track = self.call("create_audio_track", {})
        self.created_track_indices.append(track["index"])
        self.mark_validated("create_audio_track")
        self.call("set_track_name", {"track_index": track["index"], "name": "Macro Validation Rack"})
        rack = self.call(
            "create_rack",
            {"track_index": track["index"], "rack_type": "audio_effect", "name": "Macro Validation Rack"},
        )
        self.mark_validated("create_rack")
        return {
            "rack_id": rack["rack_id"],
            "name": rack["name"],
            "track_index": int(track["index"]),
            "device_index": int(rack["device_index"]),
            "rack_path": rack["rack_path"],
            "source": "disposable_created_rack",
        }

    def queue_macro_restore(self, track_index, device_index, macro_index, value):
        self.macro_restore_queue.append(
            {
                "track_index": int(track_index),
                "device_index": int(device_index),
                "macro_index": int(macro_index),
                "value": float(value),
            }
        )

    def restore_macros(self):
        for restore in reversed(self.macro_restore_queue):
            try:
                self.call(
                    "set_rack_macro",
                    {
                        "track_index": restore["track_index"],
                        "device_index": restore["device_index"],
                        "macro_index": restore["macro_index"],
                        "value": restore["value"],
                    },
                )
                self.summary["cleanup"]["restored_macros"].append(restore)
            except Exception:
                pass

    def delete_created_tracks(self):
        for track_index in sorted(self.created_track_indices, reverse=True):
            try:
                self.call("delete_track", {"track_index": track_index})
                self.summary["cleanup"]["deleted_tracks"].append(track_index)
            except Exception:
                pass

    def safe_cleanup(self):
        try:
            self.restore_macros()
        finally:
            self.delete_created_tracks()

    def validate_system_owned_macro_round_trip(self, inventory):
        target = self.find_top_level_system_owned_rack(inventory)
        if target is None:
            target = self.create_disposable_system_owned_rack()
        self.summary["discovered_targets"]["system_owned_rack"] = {
            "rack_id": target["rack_id"],
            "name": target["name"],
            "track_index": int(target["track_index"]),
            "device_index": int(target["device_index"]),
            "rack_path": target["rack_path"],
            "source": target["source"],
        }

        macros_before = self.call(
            "get_rack_macros",
            {
                "track_index": int(target["track_index"]),
                "device_index": int(target["device_index"]),
            },
        )
        self.mark_validated("get_rack_macros")
        self.require(macros_before["macros"], "System-owned rack did not expose any macros")
        target_macro = dict(macros_before["macros"][0])
        target_value = self.choose_macro_target_value(target_macro)
        self.queue_macro_restore(
            target["track_index"],
            target["device_index"],
            target_macro["index"],
            target_macro["value"],
        )

        set_result = self.call(
            "set_rack_macro",
            {
                "track_index": int(target["track_index"]),
                "device_index": int(target["device_index"]),
                "macro_index": int(target_macro["index"]),
                "value": target_value,
            },
        )
        self.mark_validated("set_rack_macro")
        macros_after = self.call(
            "get_rack_macros",
            {
                "track_index": int(target["track_index"]),
                "device_index": int(target["device_index"]),
            },
        )
        updated_macro = [
            macro for macro in list(macros_after["macros"]) if int(macro["index"]) == int(target_macro["index"])
        ][0]
        self.require(
            _approx_equal(updated_macro["value"], set_result["value"]),
            "System-owned rack macro did not round-trip",
        )

        structure = self.call(
            "get_rack_structure",
            {"track_index": int(target["track_index"]), "rack_path": target["rack_path"]},
        )
        self.mark_validated("get_rack_structure")

        self.summary["system_owned_rack_round_trip"] = {
            "rack_name": macros_before["rack_name"],
            "track_index": int(target["track_index"]),
            "device_index": int(target["device_index"]),
            "target_source": target["source"],
            "macro_index": int(target_macro["index"]),
            "original_value": float(target_macro["value"]),
            "validated_value": float(updated_macro["value"]),
            "restored_value": float(target_macro["value"]),
            "has_macro_mappings": bool(structure["rack"].get("has_macro_mappings")),
            "visible_macro_count": int(structure["rack"].get("visible_macro_count", len(macros_after["macros"]))),
        }

    def validate_unsupported_macro_authoring(self, session_path):
        if not str(session_path or "").strip():
            self.mark_skipped(
                "unsupported_macro_authoring_negative_cases",
                "Current Live Set is not saved, so apply_rack_blueprint cannot reach the unsupported-field validation path",
            )
            return

        disposable_track = self.call("create_audio_track", {})
        self.created_track_indices.append(disposable_track["index"])

        self.expect_error(
            "apply_rack_blueprint",
            {
                "blueprint": {
                    "track_index": disposable_track["index"],
                    "rack_type": "audio_effect",
                    "rack_name": "Rejected Mapping Rack",
                    "macro_mappings": [{"macro": 0, "parameter": "Gain A"}],
                    "chains": [{"name": "Only Chain"}],
                }
            },
            "Native macro mapping is not confirmed",
        )
        self.expect_error(
            "apply_rack_blueprint",
            {
                "blueprint": {
                    "track_index": disposable_track["index"],
                    "rack_type": "audio_effect",
                    "rack_name": "Rejected Macro To Macro Rack",
                    "macro_to_macro_mappings": [{"source_macro": 0, "target_macro": 1}],
                    "chains": [{"name": "Only Chain"}],
                }
            },
            "Native macro mapping is not confirmed",
        )

        self.summary["macro_authoring_audit"]["repo_contract"] = (
            "Explicitly unsupported. The negative cases hit the stable unsupported error path."
        )
        self.mark_validated("apply_rack_blueprint")

    def validate_user_rack(self, session_path):
        if self.user_rack_track_index is None or self.user_rack_device_index is None:
            self.summary["user_rack_audit"] = {
                "status": "skipped_missing_target",
                "conclusion": (
                    "No manual user-authored rack target was provided. User-rack semantics remain "
                    "inspection-only until a real imported/user-authored rack is compared before and after "
                    "refresh_rack_memory_entry."
                ),
            }
            self.mark_skipped(
                "user_rack_audit",
                "Pass --user-rack-track-index and --user-rack-device-index to validate a real imported/user-authored rack",
            )
            return

        if not str(session_path or "").strip():
            self.summary["user_rack_audit"] = {
                "status": "skipped_unsaved_session",
                "conclusion": (
                    "A manual imported/user-authored rack target was supplied, but the current Live Set is not "
                    "saved. refresh_rack_memory_entry cannot persist or compare authoritative Memory Bank metadata "
                    "until the set has a real session path."
                ),
            }
            self.mark_skipped(
                "user_rack_audit",
                "Save the Live Set first so refresh_rack_memory_entry can write project-root Memory Bank files",
            )
            return

        track_index = int(self.user_rack_track_index)
        device_index = int(self.user_rack_device_index)
        rack_path = "devices {}".format(device_index)
        devices = self.call("get_track_devices", {"track_index": track_index})
        self.mark_validated("get_track_devices")
        self.require(device_index < len(devices["devices"]), "user-rack device_index is out of range")
        target_device = devices["devices"][device_index]
        self.require(bool(target_device.get("is_rack")), "user-rack target is not a rack")

        structure = self.call("get_rack_structure", {"track_index": track_index, "rack_path": rack_path})
        self.mark_validated("get_rack_structure")
        macros = self.call("get_rack_macros", {"track_index": track_index, "device_index": device_index})
        self.mark_validated("get_rack_macros")

        refresh_result = self.call(
            "refresh_rack_memory_entry",
            {"track_index": track_index, "rack_path": rack_path},
        )
        self.mark_validated("refresh_rack_memory_entry")
        inventory_after_refresh = self.call("get_system_owned_racks", {})
        imported_entry = None
        for entry in list(inventory_after_refresh.get("racks", []) or []):
            if entry.get("rack_id") == refresh_result.get("rack_id"):
                imported_entry = entry
                break
        self.require(imported_entry is not None, "refresh_rack_memory_entry did not create a readable memory-bank entry")

        self.summary["discovered_targets"]["user_rack"] = {
            "track_index": track_index,
            "device_index": device_index,
            "rack_path": rack_path,
            "name": target_device.get("name"),
        }
        self.summary["user_rack_audit"] = {
            "status": "validated_with_manual_target",
            "track_index": track_index,
            "device_index": device_index,
            "rack_path": rack_path,
            "rack_name": structure["rack"].get("name"),
            "direct_macro_names": [macro.get("name") for macro in list(macros.get("macros", []) or [])],
            "direct_macro_count": len(list(macros.get("macros", []) or [])),
            "direct_has_macro_mappings": bool(structure["rack"].get("has_macro_mappings")),
            "direct_visible_macro_count": int(
                structure["rack"].get("visible_macro_count", len(list(macros.get("macros", []) or [])))
            ),
            "memory_bank_rack_id": refresh_result.get("rack_id"),
            "memory_bank_imported": bool(imported_entry.get("imported")),
            "memory_bank_macro_count": imported_entry.get("macro_count"),
            "memory_bank_notes": list(imported_entry.get("notes", []) or []),
            "conclusion": (
                "Live-side rack inspection is usable for direct structure and exposed macros, but authoritative "
                "repo-level semantic metadata is only established after refresh_rack_memory_entry imports the rack "
                "into the Memory Bank."
            ),
        }

    def run(self):
        try:
            health = self.call("health_check", {})
            session_info = self.call("get_session_info", {})
            session_path = self.get_session_path()
            inventory = self.get_inventory_if_available(session_path)
            self.summary["baseline"] = {
                "health_check": health,
                "session_path": session_path,
                "track_count": session_info["track_count"],
                "system_owned_rack_count": inventory["count"],
            }

            self.validate_system_owned_macro_round_trip(inventory)
            self.validate_unsupported_macro_authoring(session_path)
            self.validate_user_rack(session_path)
            return self.summary
        finally:
            self.safe_cleanup()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Validate rack macro behavior and user-rack semantics.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=9877)
    parser.add_argument("--connect-timeout", type=float, default=5.0)
    parser.add_argument("--response-timeout", type=float, default=30.0)
    parser.add_argument("--user-rack-track-index", type=int)
    parser.add_argument("--user-rack-device-index", type=int)
    args = parser.parse_args(argv)
    if (args.user_rack_track_index is None) != (args.user_rack_device_index is None):
        parser.error("--user-rack-track-index and --user-rack-device-index must be provided together")
    return args


def main(argv=None):
    args = parse_args(argv)
    validator = MacroAndUserRackBatchValidator(
        host=args.host,
        port=args.port,
        connect_timeout=args.connect_timeout,
        response_timeout=args.response_timeout,
        user_rack_track_index=args.user_rack_track_index,
        user_rack_device_index=args.user_rack_device_index,
    )
    try:
        result = validator.run()
    except Exception as exc:
        print(
            json.dumps(
                {"status": "error", "message": str(exc), "summary": validator.summary},
                indent=2,
                sort_keys=True,
            )
        )
        raise
    print(json.dumps({"status": "ok", "summary": result}, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(1)
