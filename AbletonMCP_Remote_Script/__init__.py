# AbletonMCP v2 Remote Script
# Runs inside Ableton Live as a MIDI Remote Script.
# Listens on TCP port 9877, receives JSON commands, executes them via the Live API.
#
# Installation:
#   Copy this entire folder to:
#   macOS: ~/Music/Ableton/User Library/Remote Scripts/AbletonMCP/
#   Windows: \Users\[username]\Documents\Ableton\User Library\Remote Scripts\AbletonMCP\
#   Then add AbletonMCP as a Control Surface in Preferences > Link/MIDI.

from __future__ import absolute_import, print_function, unicode_literals

import json
import os
import queue
import socket
import threading
import traceback

from .arrangement_ops import ArrangementOpsMixin
from .browser_ops import BrowserOpsMixin
from .core import CoreOpsMixin
from .device_ops import DeviceOpsMixin
from .rack_ops import RackOpsMixin
from .scene_ops import SceneOpsMixin
from .session_clip_ops import SessionClipOpsMixin
from .song_ops import SongOpsMixin
from .take_lane_ops import TakeLaneOpsMixin
from .track_ops import TrackOpsMixin
from .view_ops import ViewOpsMixin

try:
    from _Framework.ControlSurface import ControlSurface
except ImportError:
    ControlSurface = object


HOST = "localhost"
PORT = int(os.environ.get("ABLETON_MCP_PORT", "9877"))
CLIENT_TIMEOUT = 300.0
SCHEDULE_TIMEOUT = 8.0


def create_instance(c_instance):
    return AbletonMCP(c_instance)


class AbletonMCP(
    CoreOpsMixin,
    SongOpsMixin,
    TrackOpsMixin,
    SessionClipOpsMixin,
    ArrangementOpsMixin,
    SceneOpsMixin,
    DeviceOpsMixin,
    RackOpsMixin,
    BrowserOpsMixin,
    TakeLaneOpsMixin,
    ViewOpsMixin,
    ControlSurface,
):
    """AbletonMCP v2 Remote Script for Ableton Live 12."""

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.log_message("AbletonMCP v2 initializing...")
        self._server_sock = None
        self._server_thread = None
        self._client_threads = []
        self._threads_lock = threading.Lock()
        self._running = False
        self._start_server()
        self.show_message("AbletonMCP v2: listening on port {}".format(PORT))
        self.log_message("AbletonMCP v2 initialized on port {}".format(PORT))

    def disconnect(self):
        self.log_message("AbletonMCP v2 disconnecting...")
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(2.0)
        ControlSurface.disconnect(self)
        self.log_message("AbletonMCP v2 disconnected")

    def _start_server(self):
        try:
            self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_sock.bind((HOST, PORT))
            self._server_sock.listen(5)
            self._running = True
            self._server_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self._server_thread.start()
            self.log_message("TCP server started on {}:{}".format(HOST, PORT))
        except Exception as exc:
            self.log_message("Failed to start server: {}".format(exc))
            self.show_message("AbletonMCP v2 ERROR: {}".format(exc))

    def _accept_loop(self):
        self._server_sock.settimeout(1.0)
        while self._running:
            try:
                client_sock, addr = self._server_sock.accept()
                self.log_message("Client connected from {}".format(addr))
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, addr),
                    daemon=True,
                )
                thread.start()
                with self._threads_lock:
                    self._client_threads = [current for current in self._client_threads if current.is_alive()]
                    self._client_threads.append(thread)
            except socket.timeout:
                continue
            except Exception as exc:
                if self._running:
                    self.log_message("Accept error: {}".format(exc))

    def _handle_client(self, sock, addr):
        sock.settimeout(CLIENT_TIMEOUT)
        try:
            file_handle = sock.makefile("r", encoding="utf-8")
            for line in file_handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    command = json.loads(line)
                except json.JSONDecodeError as exc:
                    self._send(sock, {"status": "error", "message": "Invalid JSON: {}".format(exc)})
                    continue
                response = self._process_command(command)
                self._send(sock, response)
        except socket.timeout:
            self.log_message("Client {} timed out".format(addr))
        except Exception as exc:
            self.log_message("Client {} error: {}".format(addr, exc))
            self.log_message(traceback.format_exc())
        finally:
            try:
                sock.close()
            except Exception:
                pass
            self.log_message("Client {} disconnected".format(addr))

    def _send(self, sock, data):
        try:
            sock.sendall((json.dumps(data) + "\n").encode("utf-8"))
        except Exception as exc:
            self.log_message("Send error: {}".format(exc))

    def _schedule_and_wait(self, func, timeout=SCHEDULE_TIMEOUT):
        result_queue = queue.Queue()

        def _scheduled():
            try:
                result_queue.put(("ok", func()))
            except Exception as exc:
                result_queue.put(("err", str(exc) + "\n" + traceback.format_exc()))

        self.schedule_message(0, _scheduled)
        try:
            status, value = result_queue.get(timeout=timeout)
        except queue.Empty:
            raise RuntimeError("Timed out waiting for Ableton main thread")
        if status == "err":
            raise RuntimeError(value)
        return value

    def _process_command(self, command):
        cmd_type = command.get("type", "")
        params = command.get("params", {})
        try:
            result = self._dispatch(cmd_type, params)
            return {"status": "success", "result": result}
        except Exception as exc:
            self.log_message("Command '{}' error: {}".format(cmd_type, exc))
            return {"status": "error", "message": str(exc)}

    def _dispatch(self, cmd_type, params):  # noqa: C901
        if cmd_type == "health_check":
            return self._health_check()
        elif cmd_type == "get_session_info":
            return self._get_session_info()
        elif cmd_type == "get_current_song_time":
            return self._get_current_song_time()
        elif cmd_type == "set_current_song_time":
            return self._schedule_and_wait(lambda: self._set_current_song_time(params))
        elif cmd_type == "set_tempo":
            return self._schedule_and_wait(lambda: self._set_tempo(params))
        elif cmd_type == "set_time_signature":
            return self._schedule_and_wait(lambda: self._set_time_signature(params))
        elif cmd_type == "start_playback":
            return self._schedule_and_wait(lambda: self._start_playback())
        elif cmd_type == "stop_playback":
            return self._schedule_and_wait(lambda: self._stop_playback())
        elif cmd_type == "continue_playback":
            return self._schedule_and_wait(lambda: self._continue_playback())
        elif cmd_type == "start_recording":
            return self._schedule_and_wait(lambda: self._start_recording())
        elif cmd_type == "stop_recording":
            return self._schedule_and_wait(lambda: self._stop_recording())
        elif cmd_type == "toggle_session_record":
            return self._schedule_and_wait(lambda: self._toggle_session_record())
        elif cmd_type == "toggle_arrangement_record":
            return self._schedule_and_wait(lambda: self._toggle_arrangement_record())
        elif cmd_type == "set_metronome":
            return self._schedule_and_wait(lambda: self._set_metronome(params))
        elif cmd_type == "tap_tempo":
            return self._schedule_and_wait(lambda: self._tap_tempo())
        elif cmd_type == "undo":
            return self._schedule_and_wait(lambda: self._undo())
        elif cmd_type == "redo":
            return self._schedule_and_wait(lambda: self._redo())
        elif cmd_type == "capture_midi":
            return self._schedule_and_wait(lambda: self._capture_midi())
        elif cmd_type == "re_enable_automation":
            return self._schedule_and_wait(lambda: self._re_enable_automation())
        elif cmd_type == "set_arrangement_loop":
            return self._schedule_and_wait(lambda: self._set_arrangement_loop(params))
        elif cmd_type == "get_cpu_load":
            return self._get_cpu_load()
        elif cmd_type == "get_session_path":
            return self._get_session_path()
        elif cmd_type == "get_locators":
            return self._get_locators()
        elif cmd_type == "create_locator":
            return self._schedule_and_wait(lambda: self._create_locator(params))
        elif cmd_type == "delete_locator":
            return self._schedule_and_wait(lambda: self._delete_locator(params))
        elif cmd_type == "jump_to_time":
            return self._schedule_and_wait(lambda: self._jump_to_time(params))
        elif cmd_type == "jump_to_next_cue":
            return self._schedule_and_wait(lambda: self._jump_to_next_cue())
        elif cmd_type == "jump_to_prev_cue":
            return self._schedule_and_wait(lambda: self._jump_to_prev_cue())
        elif cmd_type == "set_punch_in":
            return self._schedule_and_wait(lambda: self._set_punch_in(params))
        elif cmd_type == "set_punch_out":
            return self._schedule_and_wait(lambda: self._set_punch_out(params))
        elif cmd_type == "trigger_back_to_arrangement":
            return self._schedule_and_wait(lambda: self._trigger_back_to_arrangement())
        elif cmd_type == "get_back_to_arrangement":
            return self._get_back_to_arrangement()
        elif cmd_type == "set_session_automation_record":
            return self._schedule_and_wait(lambda: self._set_session_automation_record(params))
        elif cmd_type == "get_session_automation_record":
            return self._get_session_automation_record()
        elif cmd_type == "set_overdub":
            return self._schedule_and_wait(lambda: self._set_overdub(params))
        elif cmd_type == "stop_all_clips":
            return self._schedule_and_wait(lambda: self._stop_all_clips())
        elif cmd_type == "get_track_info":
            return self._get_track_info(params)
        elif cmd_type == "get_all_track_names":
            return self._get_all_track_names()
        elif cmd_type == "create_midi_track":
            return self._schedule_and_wait(lambda: self._create_midi_track(params))
        elif cmd_type == "create_audio_track":
            return self._schedule_and_wait(lambda: self._create_audio_track(params))
        elif cmd_type == "create_return_track":
            return self._schedule_and_wait(lambda: self._create_return_track())
        elif cmd_type == "delete_track":
            return self._schedule_and_wait(lambda: self._delete_track(params))
        elif cmd_type == "duplicate_track":
            return self._schedule_and_wait(lambda: self._duplicate_track(params))
        elif cmd_type == "set_track_name":
            return self._schedule_and_wait(lambda: self._set_track_name(params))
        elif cmd_type == "set_track_color":
            return self._schedule_and_wait(lambda: self._set_track_color(params))
        elif cmd_type == "set_track_volume":
            return self._schedule_and_wait(lambda: self._set_track_volume(params))
        elif cmd_type == "set_track_pan":
            return self._schedule_and_wait(lambda: self._set_track_pan(params))
        elif cmd_type == "set_track_mute":
            return self._schedule_and_wait(lambda: self._set_track_mute(params))
        elif cmd_type == "set_track_solo":
            return self._schedule_and_wait(lambda: self._set_track_solo(params))
        elif cmd_type == "set_track_arm":
            return self._schedule_and_wait(lambda: self._set_track_arm(params))
        elif cmd_type == "set_track_monitoring":
            return self._schedule_and_wait(lambda: self._set_track_monitoring(params))
        elif cmd_type == "freeze_track":
            return self._schedule_and_wait(lambda: self._freeze_track(params))
        elif cmd_type == "flatten_track":
            return self._schedule_and_wait(lambda: self._flatten_track(params))
        elif cmd_type == "fold_track":
            return self._schedule_and_wait(lambda: self._fold_track(params))
        elif cmd_type == "unfold_track":
            return self._schedule_and_wait(lambda: self._unfold_track(params))
        elif cmd_type == "unarm_all":
            return self._schedule_and_wait(lambda: self._unarm_all())
        elif cmd_type == "unsolo_all":
            return self._schedule_and_wait(lambda: self._unsolo_all())
        elif cmd_type == "unmute_all":
            return self._schedule_and_wait(lambda: self._unmute_all())
        elif cmd_type == "set_track_delay":
            return self._schedule_and_wait(lambda: self._set_track_delay(params))
        elif cmd_type == "set_send_level":
            return self._schedule_and_wait(lambda: self._set_send_level(params))
        elif cmd_type == "get_return_tracks":
            return self._get_return_tracks()
        elif cmd_type == "get_return_track_info":
            return self._get_return_track_info(params)
        elif cmd_type == "set_return_volume":
            return self._schedule_and_wait(lambda: self._set_return_volume(params))
        elif cmd_type == "set_return_pan":
            return self._schedule_and_wait(lambda: self._set_return_pan(params))
        elif cmd_type == "set_track_input_routing":
            return self._schedule_and_wait(lambda: self._set_track_input_routing(params))
        elif cmd_type == "set_track_output_routing":
            return self._schedule_and_wait(lambda: self._set_track_output_routing(params))
        elif cmd_type == "get_track_input_routing":
            return self._get_track_input_routing(params)
        elif cmd_type == "get_track_output_routing":
            return self._get_track_output_routing(params)
        elif cmd_type == "select_track":
            return self._schedule_and_wait(lambda: self._select_track(params))
        elif cmd_type == "get_selected_track":
            return self._get_selected_track()
        elif cmd_type == "get_master_info":
            return self._get_master_info()
        elif cmd_type == "set_master_volume":
            return self._schedule_and_wait(lambda: self._set_master_volume(params))
        elif cmd_type == "set_master_pan":
            return self._schedule_and_wait(lambda: self._set_master_pan(params))
        elif cmd_type == "get_master_output_meter":
            return self._get_master_output_meter()
        elif cmd_type == "get_cue_volume":
            return self._get_cue_volume()
        elif cmd_type == "set_cue_volume":
            return self._schedule_and_wait(lambda: self._set_cue_volume(params))
        elif cmd_type == "get_clip_info":
            return self._get_clip_info(params)
        elif cmd_type == "create_clip":
            return self._schedule_and_wait(lambda: self._create_clip(params))
        elif cmd_type == "delete_clip":
            return self._schedule_and_wait(lambda: self._delete_clip(params))
        elif cmd_type == "duplicate_clip":
            return self._schedule_and_wait(lambda: self._duplicate_clip(params))
        elif cmd_type == "set_clip_name":
            return self._schedule_and_wait(lambda: self._set_clip_name(params))
        elif cmd_type == "set_clip_color":
            return self._schedule_and_wait(lambda: self._set_clip_color(params))
        elif cmd_type == "fire_clip":
            return self._schedule_and_wait(lambda: self._fire_clip(params))
        elif cmd_type == "stop_clip":
            return self._schedule_and_wait(lambda: self._stop_clip(params))
        elif cmd_type == "get_clip_notes":
            return self._get_clip_notes(params)
        elif cmd_type == "add_notes_to_clip":
            return self._schedule_and_wait(lambda: self._add_notes_to_clip(params))
        elif cmd_type == "set_clip_notes":
            return self._schedule_and_wait(lambda: self._set_clip_notes(params))
        elif cmd_type == "remove_notes_from_clip":
            return self._schedule_and_wait(lambda: self._remove_notes_from_clip(params))
        elif cmd_type == "set_clip_loop":
            return self._schedule_and_wait(lambda: self._set_clip_loop(params))
        elif cmd_type == "set_clip_markers":
            return self._schedule_and_wait(lambda: self._set_clip_markers(params))
        elif cmd_type == "set_clip_gain":
            return self._schedule_and_wait(lambda: self._set_clip_gain(params))
        elif cmd_type == "set_clip_pitch":
            return self._schedule_and_wait(lambda: self._set_clip_pitch(params))
        elif cmd_type == "set_clip_warp_mode":
            return self._schedule_and_wait(lambda: self._set_clip_warp_mode(params))
        elif cmd_type == "quantize_clip":
            return self._schedule_and_wait(lambda: self._quantize_clip(params))
        elif cmd_type == "duplicate_clip_loop":
            return self._schedule_and_wait(lambda: self._duplicate_clip_loop(params))
        elif cmd_type == "get_clip_automation":
            return self._get_clip_automation(params)
        elif cmd_type == "set_clip_automation":
            return self._schedule_and_wait(lambda: self._set_clip_automation(params))
        elif cmd_type == "clear_clip_automation":
            return self._schedule_and_wait(lambda: self._clear_clip_automation(params))
        elif cmd_type == "get_arrangement_clips":
            return self._get_arrangement_clips(params)
        elif cmd_type == "get_all_arrangement_clips":
            return self._get_all_arrangement_clips()
        elif cmd_type == "create_arrangement_midi_clip":
            return self._schedule_and_wait(lambda: self._create_arrangement_midi_clip(params))
        elif cmd_type == "create_arrangement_audio_clip":
            return self._schedule_and_wait(lambda: self._create_arrangement_audio_clip(params))
        elif cmd_type == "delete_arrangement_clip":
            return self._schedule_and_wait(lambda: self._delete_arrangement_clip(params))
        elif cmd_type == "resize_arrangement_clip":
            return self._schedule_and_wait(lambda: self._resize_arrangement_clip(params))
        elif cmd_type == "move_arrangement_clip":
            return self._schedule_and_wait(lambda: self._move_arrangement_clip(params))
        elif cmd_type == "add_notes_to_arrangement_clip":
            return self._schedule_and_wait(lambda: self._add_notes_to_arrangement_clip(params))
        elif cmd_type == "get_arrangement_clip_notes":
            return self._get_arrangement_clip_notes(params)
        elif cmd_type == "duplicate_to_arrangement":
            return self._schedule_and_wait(lambda: self._duplicate_to_arrangement(params))
        elif cmd_type == "get_all_scenes":
            return self._get_all_scenes()
        elif cmd_type == "create_scene":
            return self._schedule_and_wait(lambda: self._create_scene(params))
        elif cmd_type == "delete_scene":
            return self._schedule_and_wait(lambda: self._delete_scene(params))
        elif cmd_type == "fire_scene":
            return self._schedule_and_wait(lambda: self._fire_scene(params))
        elif cmd_type == "stop_scene":
            return self._schedule_and_wait(lambda: self._stop_scene(params))
        elif cmd_type == "set_scene_name":
            return self._schedule_and_wait(lambda: self._set_scene_name(params))
        elif cmd_type == "set_scene_color":
            return self._schedule_and_wait(lambda: self._set_scene_color(params))
        elif cmd_type == "duplicate_scene":
            return self._schedule_and_wait(lambda: self._duplicate_scene(params))
        elif cmd_type == "select_scene":
            return self._schedule_and_wait(lambda: self._select_scene(params))
        elif cmd_type == "get_selected_scene":
            return self._get_selected_scene()
        elif cmd_type == "get_track_devices":
            return self._get_track_devices(params)
        elif cmd_type == "get_device_parameters":
            return self._get_device_parameters(params)
        elif cmd_type == "set_device_parameter":
            return self._schedule_and_wait(lambda: self._set_device_parameter(params))
        elif cmd_type == "set_device_parameter_by_name":
            return self._schedule_and_wait(lambda: self._set_device_parameter_by_name(params))
        elif cmd_type == "get_device_parameter_by_name":
            return self._get_device_parameter_by_name(params)
        elif cmd_type == "toggle_device":
            return self._schedule_and_wait(lambda: self._toggle_device(params))
        elif cmd_type == "set_device_enabled":
            return self._schedule_and_wait(lambda: self._set_device_enabled(params))
        elif cmd_type == "delete_device":
            return self._schedule_and_wait(lambda: self._delete_device(params))
        elif cmd_type == "move_device":
            return self._schedule_and_wait(lambda: self._move_device(params))
        elif cmd_type == "show_plugin_window":
            return self._schedule_and_wait(lambda: self._show_plugin_window(params))
        elif cmd_type == "hide_plugin_window":
            return self._schedule_and_wait(lambda: self._hide_plugin_window(params))
        elif cmd_type == "load_instrument_or_effect":
            return self._schedule_and_wait(lambda: self._load_instrument_or_effect(params))
        elif cmd_type == "get_device_class_name":
            return self._get_device_class_name(params)
        elif cmd_type == "select_device":
            return self._schedule_and_wait(lambda: self._select_device(params))
        elif cmd_type == "get_selected_device":
            return self._get_selected_device()
        elif cmd_type == "get_rack_chains":
            return self._get_rack_chains(params)
        elif cmd_type == "get_rack_macros":
            return self._get_rack_macros(params)
        elif cmd_type == "set_rack_macro":
            return self._schedule_and_wait(lambda: self._set_rack_macro(params))
        elif cmd_type == "get_chain_devices":
            return self._get_chain_devices(params)
        elif cmd_type == "set_chain_mute":
            return self._schedule_and_wait(lambda: self._set_chain_mute(params))
        elif cmd_type == "set_chain_solo":
            return self._schedule_and_wait(lambda: self._set_chain_solo(params))
        elif cmd_type == "set_chain_volume":
            return self._schedule_and_wait(lambda: self._set_chain_volume(params))
        elif cmd_type == "get_drum_rack_pads":
            return self._get_drum_rack_pads(params)
        elif cmd_type == "set_drum_rack_pad_note":
            return self._schedule_and_wait(lambda: self._set_drum_rack_pad_note(params))
        elif cmd_type == "set_drum_rack_pad_mute":
            return self._schedule_and_wait(lambda: self._set_drum_rack_pad_mute(params))
        elif cmd_type == "set_drum_rack_pad_solo":
            return self._schedule_and_wait(lambda: self._set_drum_rack_pad_solo(params))
        elif cmd_type == "get_browser_tree":
            return self._get_browser_tree(params)
        elif cmd_type == "get_browser_items_at_path":
            return self._get_browser_items_at_path(params)
        elif cmd_type == "search_browser":
            return self._search_browser(params)
        elif cmd_type == "load_drum_kit":
            return self._schedule_and_wait(lambda: self._load_drum_kit(params))
        elif cmd_type == "get_take_lanes":
            return self._get_take_lanes(params)
        elif cmd_type == "create_take_lane":
            return self._schedule_and_wait(lambda: self._create_take_lane(params))
        elif cmd_type == "set_take_lane_name":
            return self._schedule_and_wait(lambda: self._set_take_lane_name(params))
        elif cmd_type == "create_midi_clip_in_lane":
            return self._schedule_and_wait(lambda: self._create_midi_clip_in_lane(params))
        elif cmd_type == "get_clips_in_take_lane":
            return self._get_clips_in_take_lane(params)
        elif cmd_type == "delete_take_lane":
            return self._schedule_and_wait(lambda: self._delete_take_lane(params))
        elif cmd_type == "get_current_view":
            return self._get_current_view()
        elif cmd_type == "focus_view":
            return self._schedule_and_wait(lambda: self._focus_view(params))
        elif cmd_type == "show_arrangement_view":
            return self._schedule_and_wait(lambda: self._focus_view({"view": "Arranger"}))
        elif cmd_type == "show_session_view":
            return self._schedule_and_wait(lambda: self._focus_view({"view": "Session"}))
        elif cmd_type == "show_detail_view":
            return self._schedule_and_wait(lambda: self._show_detail_view(params))
        elif cmd_type == "get_arrangement_length":
            return self._get_arrangement_length()
        raise ValueError("Unknown command: {}".format(cmd_type))
