from __future__ import absolute_import, print_function, unicode_literals

import json
import sys

from mcp_server.client import AbletonCommandError, AbletonRemoteClient


class TakeLaneBatchValidator(object):
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
            "take_lane_round_trip": {},
            "delete_take_lane_audit": {},
            "cleanup": {"deleted_tracks": []},
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
            return str(exc)
        raise AssertionError("Expected '{}' to fail".format(command_name))

    def safe_cleanup(self):
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
            self.summary["baseline"] = {
                "health_check": health,
                "track_count": session_info["track_count"],
            }

            midi_track = self.call("create_midi_track", {})
            midi_track_index = int(midi_track["index"])
            self.created_track_indices.append(midi_track_index)
            self.call("set_track_name", {"track_index": midi_track_index, "name": "Take Lane Validation MIDI"})

            initial_lanes = self.call("get_take_lanes", {"track_index": midi_track_index})
            self.mark_validated("get_take_lanes")
            self.require(initial_lanes["available"], "Take lanes should be available on the validated build")
            self.require(initial_lanes["take_lanes"] == [], "Disposable MIDI track should start with no take lanes")

            created_lane = self.call("create_take_lane", {"track_index": midi_track_index})
            self.mark_validated("create_take_lane")
            lanes_after_create = self.call("get_take_lanes", {"track_index": midi_track_index})
            self.require(len(lanes_after_create["take_lanes"]) == 1, "create_take_lane did not add one take lane")

            renamed_lane = self.call(
                "set_take_lane_name",
                {"track_index": midi_track_index, "lane_index": 0, "name": "Validator Lane"},
            )
            self.mark_validated("set_take_lane_name")
            lanes_after_rename = self.call("get_take_lanes", {"track_index": midi_track_index})
            self.require(lanes_after_rename["take_lanes"][0]["name"] == "Validator Lane", "Take lane rename failed")

            created_clip = self.call(
                "create_midi_clip_in_lane",
                {"track_index": midi_track_index, "lane_index": 0, "start_time": 8.0, "length": 2.0},
            )
            self.mark_validated("create_midi_clip_in_lane")
            lane_clips = self.call("get_clips_in_take_lane", {"track_index": midi_track_index, "lane_index": 0})
            self.mark_validated("get_clips_in_take_lane")
            self.require(len(lane_clips["clips"]) == 1, "Expected one take-lane clip after clip creation")
            clip_payload = lane_clips["clips"][0]
            self.require(bool(clip_payload["is_midi_clip"]), "Take-lane clip should be MIDI on the MIDI track")
            self.require(abs(float(clip_payload["start_time"]) - 8.0) < 0.001, "Unexpected take-lane clip start_time")
            self.require(abs(float(clip_payload["length"]) - 2.0) < 0.001, "Unexpected take-lane clip length")

            delete_error = self.expect_error(
                "delete_take_lane",
                {"track_index": midi_track_index, "lane_index": 0},
                "delete_take_lane is unavailable on this Live Python surface",
            )
            lanes_after_delete_audit = self.call("get_take_lanes", {"track_index": midi_track_index})

            self.summary["take_lane_round_trip"] = {
                "track_index": midi_track_index,
                "created_lane_name": created_lane["name"],
                "renamed_lane_name": renamed_lane["name"],
                "lane_count_before": len(initial_lanes["take_lanes"]),
                "lane_count_after_create": len(lanes_after_create["take_lanes"]),
                "clip_count_after_create": len(lane_clips["clips"]),
                "created_clip": created_clip,
                "readback_clip": clip_payload,
            }
            self.summary["delete_take_lane_audit"] = {
                "status": "unavailable_on_validated_python_surface",
                "error": delete_error,
                "lane_count_after_audit": len(lanes_after_delete_audit["take_lanes"]),
            }

            return self.summary
        finally:
            self.safe_cleanup()


def main():
    validator = TakeLaneBatchValidator()
    try:
        result = validator.run()
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc), "summary": validator.summary}, indent=2))
        raise
    print(json.dumps({"status": "ok", "summary": result}, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(1)
