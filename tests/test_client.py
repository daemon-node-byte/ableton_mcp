from __future__ import absolute_import, print_function, unicode_literals

import json
import socketserver
import threading
import time
import unittest

from mcp_server.client import (
    AbletonCommandError,
    AbletonProtocolError,
    AbletonRemoteClient,
    AbletonTransportError,
)


class _OneShotTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


class _RequestHandler(socketserver.StreamRequestHandler):
    response_line = json.dumps({"status": "success", "result": {"ok": True}}) + "\n"
    response_delay = 0.0
    received_payload = None

    def handle(self):
        request_line = self.rfile.readline().decode("utf-8").strip()
        if request_line:
            self.__class__.received_payload = json.loads(request_line)
        if self.__class__.response_delay:
            time.sleep(self.__class__.response_delay)
        if self.__class__.response_line is not None:
            self.wfile.write(self.__class__.response_line.encode("utf-8"))


class AbletonRemoteClientTests(unittest.TestCase):
    def _start_server(self, response_line, response_delay=0.0):
        _RequestHandler.response_line = response_line
        _RequestHandler.response_delay = response_delay
        _RequestHandler.received_payload = None
        server = _OneShotTCPServer(("127.0.0.1", 0), _RequestHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, thread

    def test_success_response_returns_result(self):
        server, thread = self._start_server(json.dumps({"status": "success", "result": {"tempo": 120}}) + "\n")
        try:
            client = AbletonRemoteClient(host="127.0.0.1", port=server.server_address[1])
            result = client.send_command("set_tempo", {"tempo": 120})
            self.assertEqual({"tempo": 120}, result)
            self.assertEqual(
                {"type": "set_tempo", "params": {"tempo": 120}},
                _RequestHandler.received_payload,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

    def test_error_response_raises_command_error(self):
        server, thread = self._start_server(json.dumps({"status": "error", "message": "boom"}) + "\n")
        try:
            client = AbletonRemoteClient(host="127.0.0.1", port=server.server_address[1])
            with self.assertRaises(AbletonCommandError):
                client.send_command("health_check", {})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

    def test_invalid_json_raises_protocol_error(self):
        server, thread = self._start_server("{not-json}\n")
        try:
            client = AbletonRemoteClient(host="127.0.0.1", port=server.server_address[1])
            with self.assertRaises(AbletonProtocolError):
                client.send_command("health_check", {})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

    def test_timeout_raises_transport_error(self):
        server, thread = self._start_server(
            json.dumps({"status": "success", "result": {"ok": True}}) + "\n",
            response_delay=0.25,
        )
        try:
            client = AbletonRemoteClient(
                host="127.0.0.1",
                port=server.server_address[1],
                response_timeout=0.05,
            )
            with self.assertRaises(AbletonTransportError):
                client.send_command("health_check", {})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)
