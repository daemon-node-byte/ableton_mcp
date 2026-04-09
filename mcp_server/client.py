"""TCP client for the AbletonMCP Remote Script bridge."""

from __future__ import absolute_import, print_function, unicode_literals

import json
import os
import socket


DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9877
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_RESPONSE_TIMEOUT = 30.0


class AbletonClientError(Exception):
    """Base error for Python-side Ableton bridge failures."""


class AbletonTransportError(AbletonClientError):
    """Socket, timeout, or connection failures."""


class AbletonProtocolError(AbletonClientError):
    """Invalid or malformed protocol responses."""


class AbletonCommandError(AbletonClientError):
    """Structured command error returned by the Remote Script."""


class AbletonRemoteClient(object):
    """Simple newline-delimited JSON TCP client for the Remote Script."""

    def __init__(
        self,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        connect_timeout=DEFAULT_CONNECT_TIMEOUT,
        response_timeout=DEFAULT_RESPONSE_TIMEOUT,
    ):
        self.host = host
        self.port = int(port)
        self.connect_timeout = float(connect_timeout)
        self.response_timeout = float(response_timeout)

    @classmethod
    def from_env(cls):
        return cls(
            host=os.environ.get("ABLETON_MCP_HOST", DEFAULT_HOST),
            port=int(os.environ.get("ABLETON_MCP_PORT", str(DEFAULT_PORT))),
            connect_timeout=float(
                os.environ.get("ABLETON_MCP_CONNECT_TIMEOUT", str(DEFAULT_CONNECT_TIMEOUT))
            ),
            response_timeout=float(
                os.environ.get("ABLETON_MCP_RESPONSE_TIMEOUT", str(DEFAULT_RESPONSE_TIMEOUT))
            ),
        )

    def send_command(self, command_type, params=None):
        payload = {"type": command_type, "params": params or {}}
        try:
            sock = socket.create_connection((self.host, self.port), timeout=self.connect_timeout)
        except (OSError, socket.timeout) as exc:
            raise AbletonTransportError(
                "Failed to connect to Ableton Remote Script at {}:{}: {}".format(
                    self.host, self.port, exc
                )
            )

        try:
            sock.settimeout(self.response_timeout)
            with sock:
                sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
                file_handle = sock.makefile("r", encoding="utf-8")
                response_line = file_handle.readline()
                if not response_line:
                    raise AbletonProtocolError("No response received for command '{}'".format(command_type))
        except socket.timeout as exc:
            raise AbletonTransportError(
                "Timed out waiting for Ableton response to '{}': {}".format(command_type, exc)
            )
        except OSError as exc:
            raise AbletonTransportError(
                "Socket error while calling '{}': {}".format(command_type, exc)
            )

        try:
            response = json.loads(response_line)
        except ValueError as exc:
            raise AbletonProtocolError(
                "Invalid JSON response for '{}': {}".format(command_type, exc)
            )

        status = response.get("status")
        if status == "success":
            return response.get("result")
        if status == "error":
            raise AbletonCommandError(
                "Ableton command '{}' failed: {}".format(command_type, response.get("message", "Unknown error"))
            )
        raise AbletonProtocolError(
            "Unexpected response status for '{}': {}".format(command_type, response)
        )
