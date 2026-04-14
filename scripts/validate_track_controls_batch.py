from __future__ import absolute_import, print_function, unicode_literals

import json
import sys
import time

from mcp_server.client import AbletonCommandError, AbletonRemoteClient


def _approx_equal(left, right, tolerance=0.001):
    return abs(float(left) - float(right)) <= tolerance


class TrackControlBatchValidator(object):
    def __init__(self, host="localhost", port=9877, connect_timeout=5.0, response_timeout=30.0):
        self.client = AbletonRemoteClient(
            host=host,
            port=port,
            connect_timeout=connect_timeout,
            response_timeout=response_timeout,
        )
        self.created_track_indices = []
        self.original_selection = None
        self.original_return_state = None
        self.original_fold_state = None
        self.summary = {
            "baseline": {},
            "validated_commands": [],
            "skipped_commands": [],
            "negative_cases": [],
            "discovered_targets": {
                "return_track_index": None,
                "foldable_track_index": None,
            },
            "cleanup": {
                "restored_selection": False,
                "restored_return_state": False,
                "restored_fold_state": False,
                "deleted_tracks": [],
            },
            "fold_validation": {},
        }

    def call(self, command_name, params=None):
        return self.client.send_command(command_name, params or {})

    def call_with_main_thread_retry(self, command_name, params=None, attempts=3, delay_seconds=4.0):
        last_error = None
        for attempt in range(attempts):
            try:
                return self.call(command_name, params)
            except AbletonCommandError as exc:
                if "Timed out waiting for Ableton main thread" not in str(exc) or attempt == attempts - 1:
                    raise
                last_error = exc
                time.sleep(delay_seconds)
        raise last_error

    def require(self, condition, message):
        if not condition:
            raise AssertionError(message)

    def mark_validated(self, command_name):
        if command_name not in self.summary["validated_commands"]:
            self.summary["validated_commands"].append(command_name)

    def mark_skipped(self, command_names, reason):
        for command_name in command_names:
            if not any(item["command"] == command_name for item in self.summary["skipped_commands"]):
                self.summary["skipped_commands"].append({"command": command_name, "reason": reason})

    def track_info(self, track_index):
        return self.call("get_track_info", {"track_index": track_index})

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

    def find_foldable_track_index(self, track_count):
        for track_index in range(track_count):
            track = self.track_info(track_index)
            if track.get("is_foldable"):
                return track_index, track
        return None, None

    def find_group_child_indices(self, foldable_track_index, track_count):
        child_indices = []
        for track_index in range(int(foldable_track_index) + 1, int(track_count)):
            track = self.track_info(track_index)
            if not track.get("is_grouped"):
                if child_indices:
                    break
                continue
            child_indices.append(track_index)
        return child_indices

    def snapshot_track_visibility(self, track_indices):
        snapshot = []
        for track_index in list(track_indices or []):
            track = self.track_info(track_index)
            snapshot.append(
                {
                    "track_index": track_index,
                    "name": track.get("name"),
                    "is_grouped": bool(track.get("is_grouped")),
                    "is_visible": track.get("is_visible"),
                }
            )
        return snapshot

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

    def restore_return_state(self):
        if not self.original_return_state:
            return
        self.call(
            "set_return_volume",
            {
                "return_index": self.original_return_state["return_index"],
                "volume": self.original_return_state["volume"],
            },
        )
        self.call(
            "set_return_pan",
            {
                "return_index": self.original_return_state["return_index"],
                "pan": self.original_return_state["pan"],
            },
        )
        self.summary["cleanup"]["restored_return_state"] = True

    def restore_fold_state(self):
        if not self.original_fold_state:
            return
        command_name = "fold_track" if self.original_fold_state["fold_state"] else "unfold_track"
        self.call(command_name, {"track_index": self.original_fold_state["track_index"]})
        self.summary["cleanup"]["restored_fold_state"] = True

    def safe_cleanup(self):
        try:
            self.restore_return_state()
        except Exception:
            pass
        try:
            self.restore_fold_state()
        except Exception:
            pass
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

    def validate_regular_track_mutations(self, track_index):
        self.call("set_track_name", {"track_index": track_index, "name": "Track Control Validation"})
        self.mark_validated("set_track_name")
        info = self.track_info(track_index)
        self.require(info["name"] == "Track Control Validation", "Track name did not round-trip")

        color_result = self.call("set_track_color", {"track_index": track_index, "color": 16724787})
        self.mark_validated("set_track_color")
        info = self.track_info(track_index)
        self.require(int(info["color"]) == int(color_result["color"]), "Track color did not read back applied value")

        volume_result = self.call("set_track_volume", {"track_index": track_index, "volume": 0.61})
        self.mark_validated("set_track_volume")
        info = self.track_info(track_index)
        self.require(_approx_equal(info["volume"], volume_result["volume"]), "Track volume did not round-trip")

        pan_result = self.call("set_track_pan", {"track_index": track_index, "pan": -0.24})
        self.mark_validated("set_track_pan")
        info = self.track_info(track_index)
        self.require(_approx_equal(info["pan"], pan_result["pan"]), "Track pan did not round-trip")

        mute_result = self.call("set_track_mute", {"track_index": track_index, "mute": True})
        self.mark_validated("set_track_mute")
        info = self.track_info(track_index)
        self.require(bool(info["mute"]) is bool(mute_result["mute"]), "Track mute did not round-trip")

        solo_result = self.call("set_track_solo", {"track_index": track_index, "solo": True})
        self.mark_validated("set_track_solo")
        info = self.track_info(track_index)
        self.require(bool(info["solo"]) is bool(solo_result["solo"]), "Track solo did not reach target state")

        arm_result = self.call("set_track_arm", {"track_index": track_index, "arm": True})
        self.mark_validated("set_track_arm")
        info = self.track_info(track_index)
        self.require(bool(info.get("arm")) is bool(arm_result["arm"]), "Track arm did not round-trip")

    def validate_selection_commands(self, track_index, return_index):
        track_selection = self.call("select_track", {"track_index": track_index})
        selected_track = self.call("get_selected_track", {})
        self.require(track_selection["selection_type"] == "track", "Track selection returned wrong selection_type")
        self.require(selected_track["selection_type"] == "track", "Selected regular track not reported as track")
        self.require(int(selected_track["track_index"]) == int(track_index), "Selected track index mismatch")

        master_selection = self.call("select_track", {"master": True})
        selected_master = self.call("get_selected_track", {})
        self.require(master_selection["selection_type"] == "master_track", "Master selection returned wrong type")
        self.require(selected_master["selection_type"] == "master_track", "Selected master track not reported")

        if return_index is not None:
            return_selection = self.call("select_track", {"return_index": return_index})
            selected_return = self.call("get_selected_track", {})
            self.require(
                return_selection["selection_type"] == "return_track",
                "Return-track selection returned wrong type",
            )
            self.require(
                selected_return["selection_type"] == "return_track",
                "Selected return track not reported as return_track",
            )
            self.require(
                int(selected_return["return_index"]) == int(return_index),
                "Selected return-track index mismatch",
            )

        self.mark_validated("select_track")
        self.mark_validated("get_selected_track")

    def validate_return_commands(self, track_index, return_index):
        return_tracks = self.call("get_return_tracks", {})
        self.mark_validated("get_return_tracks")
        self.require(return_tracks["return_tracks"], "Expected at least one return track")
        self.require(int(return_tracks["return_tracks"][return_index]["index"]) == int(return_index), "Return index mismatch")

        return_info = self.call("get_return_track_info", {"return_index": return_index})
        self.mark_validated("get_return_track_info")
        self.require(
            return_info["name"] == return_tracks["return_tracks"][return_index]["name"],
            "Return-track info name mismatch",
        )

        self.original_return_state = {
            "return_index": return_index,
            "volume": float(return_info["volume"]),
            "pan": float(return_info["pan"]),
        }

        updated_volume = 0.58 if not _approx_equal(return_info["volume"], 0.58) else 0.42
        volume_result = self.call(
            "set_return_volume",
            {"return_index": return_index, "volume": updated_volume},
        )
        self.mark_validated("set_return_volume")
        return_info_after_volume = self.call("get_return_track_info", {"return_index": return_index})
        self.require(
            _approx_equal(return_info_after_volume["volume"], volume_result["volume"]),
            "Return volume did not round-trip",
        )

        updated_pan = -0.35 if not _approx_equal(return_info_after_volume["pan"], -0.35) else 0.35
        pan_result = self.call("set_return_pan", {"return_index": return_index, "pan": updated_pan})
        self.mark_validated("set_return_pan")
        return_info_after_pan = self.call("get_return_track_info", {"return_index": return_index})
        self.require(
            _approx_equal(return_info_after_pan["pan"], pan_result["pan"]),
            "Return pan did not round-trip",
        )

        track_info = self.track_info(track_index)
        self.require(track_info["sends"], "Expected sends on regular track when return tracks exist")
        send_target = 0.37 if not _approx_equal(track_info["sends"][0]["value"], 0.37) else 0.19
        send_result = self.call(
            "set_send_level",
            {"track_index": track_index, "send_index": 0, "level": send_target},
        )
        self.mark_validated("set_send_level")
        track_info_after_send = self.track_info(track_index)
        self.require(
            _approx_equal(track_info_after_send["sends"][0]["value"], send_result["level"]),
            "Send level did not round-trip",
        )

    def validate_fold_commands(self, foldable_track_index, initial_track_info, track_count):
        child_indices = self.find_group_child_indices(foldable_track_index, track_count)
        self.original_fold_state = {
            "track_index": foldable_track_index,
            "fold_state": bool(initial_track_info["fold_state"]),
        }
        self.summary["fold_validation"] = {
            "target_track": {
                "track_index": foldable_track_index,
                "name": initial_track_info.get("name"),
                "original_fold_state": bool(initial_track_info["fold_state"]),
            },
            "group_child_track_indices": child_indices,
            "selected_track_before": self.call("get_selected_track", {}),
            "child_visibility_before": self.snapshot_track_visibility(child_indices),
        }

        folded = self.call("fold_track", {"track_index": foldable_track_index})
        self.mark_validated("fold_track")
        folded_track = self.track_info(foldable_track_index)
        self.require(bool(folded["fold_state"]) is True, "fold_track did not report folded state")
        self.require(bool(folded_track["fold_state"]) is True, "fold_track did not stick")
        self.summary["fold_validation"]["selected_track_after_fold"] = self.call("get_selected_track", {})
        self.summary["fold_validation"]["child_visibility_after_fold"] = self.snapshot_track_visibility(child_indices)

        unfolded = self.call("unfold_track", {"track_index": foldable_track_index})
        self.mark_validated("unfold_track")
        unfolded_track = self.track_info(foldable_track_index)
        self.require(bool(unfolded["fold_state"]) is False, "unfold_track did not report unfolded state")
        self.require(bool(unfolded_track["fold_state"]) is False, "unfold_track did not stick")
        self.summary["fold_validation"]["selected_track_after_unfold"] = self.call("get_selected_track", {})
        self.summary["fold_validation"]["child_visibility_after_unfold"] = self.snapshot_track_visibility(child_indices)
        self.summary["fold_validation"]["visibility_readback_supported"] = any(
            item.get("is_visible") is not None
            for item in self.summary["fold_validation"]["child_visibility_before"]
            + self.summary["fold_validation"]["child_visibility_after_fold"]
            + self.summary["fold_validation"]["child_visibility_after_unfold"]
        )

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

            midi_track = self.call_with_main_thread_retry("create_midi_track", {})
            self.created_track_indices.append(midi_track["index"])
            self.validate_regular_track_mutations(midi_track["index"])

            return_tracks = self.call("get_return_tracks", {})
            return_index = None
            if return_tracks["return_tracks"]:
                return_index = int(return_tracks["return_tracks"][0]["index"])
                self.summary["discovered_targets"]["return_track_index"] = return_index
                self.validate_return_commands(midi_track["index"], return_index)
            else:
                self.mark_skipped(
                    [
                        "set_send_level",
                        "get_return_tracks",
                        "get_return_track_info",
                        "set_return_volume",
                        "set_return_pan",
                    ],
                    "Current Live Set has no existing return track",
                )

            self.validate_selection_commands(midi_track["index"], return_index)
            if return_index is None:
                self.mark_skipped(
                    ["select_track", "get_selected_track"],
                    "Return-track selector was not exercised because the current Live Set has no existing return track",
                )

            foldable_track_index, foldable_track_info = self.find_foldable_track_index(session_info["track_count"])
            if foldable_track_index is not None:
                self.summary["discovered_targets"]["foldable_track_index"] = foldable_track_index
                self.validate_fold_commands(
                    foldable_track_index,
                    foldable_track_info,
                    session_info["track_count"],
                )
            else:
                self.mark_skipped(
                    ["fold_track", "unfold_track"],
                    "Current Live Set has no existing foldable group track",
                )

            self.expect_error("select_track", {}, "exactly one")
            self.expect_error("select_track", {"track_index": midi_track["index"], "master": True}, "exactly one")
            self.expect_error("fold_track", {"track_index": midi_track["index"]}, "not foldable")
            return self.summary
        finally:
            self.safe_cleanup()


def main():
    validator = TrackControlBatchValidator()
    try:
        result = validator.run()
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc), "summary": validator.summary}, indent=2, sort_keys=True))
        raise
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(1)
