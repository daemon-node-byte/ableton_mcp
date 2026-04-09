from __future__ import absolute_import, print_function, unicode_literals

import argparse
import json
import sys

from mcp_server.client import AbletonCommandError, AbletonRemoteClient


DEFAULT_AUDIO_START = 64.0
DEFAULT_MIDI_START = 80.0
DEFAULT_MOVED_MIDI_START = 88.0
DEFAULT_DUPLICATED_START = 96.0


def _approx_equal(left, right, tolerance=0.001):
    return abs(float(left) - float(right)) <= tolerance


class ArrangementBatchValidator(object):
    def __init__(self, audio_file, host, port, connect_timeout, response_timeout):
        self.audio_file = audio_file
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
            "undo_behavior": "not exercised in the automated helper; still not documented as supported",
        }

    def call(self, command_name, params=None):
        return self.client.send_command(command_name, params or {})

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
                {"command": command_name, "status": "ok", "matched": expected_substring}
            )
            return
        raise AssertionError("Expected '{}' to fail".format(command_name))

    def require(self, condition, message):
        if not condition:
            raise AssertionError(message)

    def find_clip(self, clips, start_time):
        for clip in clips:
            if _approx_equal(clip["start_time"], start_time):
                return clip
        raise AssertionError("Expected clip at start_time {}".format(start_time))

    def track_clips(self, track_index):
        return self.call("get_arrangement_clips", {"track_index": track_index})["clips"]

    def safe_cleanup(self):
        for track_index in sorted(self.created_track_indices, reverse=True):
            try:
                self.call("delete_track", {"track_index": track_index})
            except Exception:
                pass

    def run(self):
        try:
            baseline = self.call("health_check", {})
            session_info = self.call("get_session_info", {})
            self.summary["baseline"] = {
                "health_check": baseline,
                "track_count": session_info["track_count"],
            }

            midi_track = self.call("create_midi_track", {})
            self.created_track_indices.append(midi_track["index"])
            audio_track = self.call("create_audio_track", {})
            self.created_track_indices.append(audio_track["index"])

            midi_track_index = midi_track["index"]
            audio_track_index = audio_track["index"]

            self.call(
                "set_track_name",
                {"track_index": midi_track_index, "name": "AbletonMCP Validation MIDI"},
            )
            self.call(
                "set_track_name",
                {"track_index": audio_track_index, "name": "AbletonMCP Validation Audio"},
            )

            audio_result = self.call(
                "create_arrangement_audio_clip",
                {
                    "track_index": audio_track_index,
                    "file_path": self.audio_file,
                    "start_time": DEFAULT_AUDIO_START,
                },
            )
            self.require(
                _approx_equal(audio_result["start_time"], DEFAULT_AUDIO_START),
                "Audio clip did not land at the requested start time",
            )
            audio_clips = self.track_clips(audio_track_index)
            audio_clip = self.find_clip(audio_clips, DEFAULT_AUDIO_START)
            self.require(audio_clip["is_audio_clip"], "Expected imported arrangement clip to be audio")
            self.summary["validated_commands"].append("create_arrangement_audio_clip")

            self.expect_error(
                "move_arrangement_clip",
                {
                    "track_index": audio_track_index,
                    "start_time": DEFAULT_AUDIO_START,
                    "new_start_time": DEFAULT_AUDIO_START + 8.0,
                },
                "MIDI clips only",
            )

            self.call(
                "delete_arrangement_clip",
                {"track_index": audio_track_index, "start_time": DEFAULT_AUDIO_START},
            )
            audio_clips_after_delete = self.track_clips(audio_track_index)
            self.require(
                not any(_approx_equal(clip["start_time"], DEFAULT_AUDIO_START) for clip in audio_clips_after_delete),
                "Audio arrangement clip was not deleted",
            )
            self.summary["validated_commands"].append("delete_arrangement_clip")

            midi_result = self.call(
                "create_arrangement_midi_clip",
                {"track_index": midi_track_index, "start_time": DEFAULT_MIDI_START, "length": 4.0},
            )
            self.require(
                _approx_equal(midi_result["start_time"], DEFAULT_MIDI_START),
                "MIDI arrangement clip did not land at the requested start time",
            )

            midi_notes = [
                {"pitch": 60, "time": 0.0, "duration": 0.5, "velocity": 100, "mute": False},
                {"pitch": 64, "time": 1.0, "duration": 0.5, "velocity": 100, "mute": False},
                {"pitch": 67, "time": 2.0, "duration": 0.5, "velocity": 100, "mute": False},
            ]
            self.call(
                "add_notes_to_arrangement_clip",
                {"track_index": midi_track_index, "start_time": DEFAULT_MIDI_START, "notes": midi_notes},
            )

            resized = self.call(
                "resize_arrangement_clip",
                {"track_index": midi_track_index, "start_time": DEFAULT_MIDI_START, "length": 6.0},
            )
            self.require(
                _approx_equal(resized["length"], 6.0),
                "Arrangement clip resize did not report the requested length",
            )
            self.summary["validated_commands"].append("resize_arrangement_clip")

            moved = self.call(
                "move_arrangement_clip",
                {
                    "track_index": midi_track_index,
                    "start_time": DEFAULT_MIDI_START,
                    "new_start_time": DEFAULT_MOVED_MIDI_START,
                },
            )
            self.require(
                _approx_equal(moved["start_time"], DEFAULT_MOVED_MIDI_START),
                "Arrangement MIDI clip did not move to the requested start time",
            )
            moved_notes = self.call(
                "get_arrangement_clip_notes",
                {"track_index": midi_track_index, "start_time": DEFAULT_MOVED_MIDI_START},
            )
            self.require(moved_notes["count"] == 3, "Expected 3 MIDI notes after moving the clip")
            self.require(
                [note["pitch"] for note in moved_notes["notes"]] == [60, 64, 67],
                "Moved MIDI clip did not preserve note data",
            )
            self.summary["validated_commands"].append("move_arrangement_clip")

            self.call("create_clip", {"track_index": midi_track_index, "slot_index": 0, "length": 4.0})
            self.call(
                "add_notes_to_clip",
                {"track_index": midi_track_index, "slot_index": 0, "notes": midi_notes},
            )
            duplicated = self.call(
                "duplicate_to_arrangement",
                {
                    "track_index": midi_track_index,
                    "slot_index": 0,
                    "start_time": DEFAULT_DUPLICATED_START,
                },
            )
            self.require(
                _approx_equal(duplicated["start_time"], DEFAULT_DUPLICATED_START),
                "duplicate_to_arrangement did not report the requested start time",
            )
            duplicated_notes = self.call(
                "get_arrangement_clip_notes",
                {"track_index": midi_track_index, "start_time": DEFAULT_DUPLICATED_START},
            )
            self.require(duplicated_notes["count"] == 3, "Expected 3 notes in duplicated arrangement clip")
            self.summary["validated_commands"].append("duplicate_to_arrangement")

            duplicated_clips = self.track_clips(midi_track_index)
            duplicated_clip = self.find_clip(duplicated_clips, DEFAULT_DUPLICATED_START)

            self.expect_error(
                "create_arrangement_audio_clip",
                {
                    "track_index": midi_track_index,
                    "file_path": self.audio_file,
                    "start_time": DEFAULT_AUDIO_START,
                },
                "is a MIDI track",
            )
            self.expect_error(
                "create_arrangement_audio_clip",
                {"track_index": audio_track_index, "start_time": DEFAULT_AUDIO_START},
                "requires 'file_path'",
            )
            self.expect_error(
                "create_arrangement_audio_clip",
                {
                    "track_index": audio_track_index,
                    "file_path": "relative-path.wav",
                    "start_time": DEFAULT_AUDIO_START,
                },
                "absolute path",
            )
            self.expect_error(
                "create_arrangement_audio_clip",
                {
                    "track_index": audio_track_index,
                    "file_path": "/tmp/ableton-mcp-missing-audio-file.wav",
                    "start_time": DEFAULT_AUDIO_START,
                },
                "does not exist",
            )
            self.expect_error(
                "resize_arrangement_clip",
                {"track_index": midi_track_index, "start_time": DEFAULT_DUPLICATED_START, "length": 0},
                "length must be > 0",
            )
            self.expect_error(
                "resize_arrangement_clip",
                {
                    "track_index": midi_track_index,
                    "clip_index": duplicated_clip["index"],
                    "start_time": DEFAULT_DUPLICATED_START,
                    "length": 2.0,
                },
                "exactly one",
            )

            self.call(
                "delete_arrangement_clip",
                {"track_index": midi_track_index, "clip_index": duplicated_clip["index"]},
            )
            self.call("delete_clip", {"track_index": midi_track_index, "slot_index": 0})
            self.call(
                "delete_arrangement_clip",
                {"track_index": midi_track_index, "start_time": DEFAULT_MOVED_MIDI_START},
            )

            remaining_midi_clips = self.track_clips(midi_track_index)
            self.require(remaining_midi_clips == [], "Expected disposable MIDI track to be empty after cleanup")

            return self.summary
        finally:
            self.safe_cleanup()


def main():
    parser = argparse.ArgumentParser(description="Validate Arrangement Batch 2 against a running Ableton bridge.")
    parser.add_argument("--audio-file", required=True, help="Absolute path to an audio file for import testing.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=9877)
    parser.add_argument("--connect-timeout", type=float, default=5.0)
    parser.add_argument("--response-timeout", type=float, default=30.0)
    args = parser.parse_args()

    if not args.audio_file.startswith("/"):
        parser.error("--audio-file must be an absolute path")

    validator = ArrangementBatchValidator(
        audio_file=args.audio_file,
        host=args.host,
        port=args.port,
        connect_timeout=args.connect_timeout,
        response_timeout=args.response_timeout,
    )
    summary = validator.run()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Arrangement Batch 2 validation failed: {}".format(exc), file=sys.stderr)
        raise
