import io
import os
import sys
import json
import uuid
import pytest
from unittest.mock import MagicMock, patch

# Ensure agent/wrapper and agent are in path with dummy env vars
os.environ.setdefault("COSMITUDE_USERNAME", "dummy_user")
os.environ.setdefault("COSMITUDE_PASSWORD", "dummy_pass")
os.environ.setdefault("COSMITUDE_SERVER_ID", "dummy_server")
os.environ.setdefault("COSMITUDE_FORUM_ID", "dummy_forum")
os.environ.setdefault("AGENT_API_KEY", "test_secret_key")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
AGENT_WRAPPER_DIR = os.path.join(PROJECT_ROOT, "agent", "wrapper")
if AGENT_WRAPPER_DIR not in sys.path:
    sys.path.insert(0, AGENT_WRAPPER_DIR)

import agent_server


class DummyHandler(agent_server.RealCosmitudeAgentHandler):
    """Subclass of RealCosmitudeAgentHandler for test harness without real sockets."""
    def __init__(self, method, path, headers=None, body=b""):
        self.command = method
        self.path = path
        self.headers = headers or {}
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        self.status = None
        self.response_headers = {}

    def send_response(self, code, message=None):
        self.status = code

    def send_header(self, keyword, value):
        self.response_headers[keyword] = value

    def end_headers(self):
        pass

    def get_json_body(self):
        val = self.wfile.getvalue()
        if not val:
            return None
        return json.loads(val.decode("utf-8"))


def test_agent_key_unauthorized():
    handler = DummyHandler("GET", "/broadcast/next", headers={"X-Agent-Key": "wrong"})
    handler.do_GET()
    assert handler.status == 401
    assert "Unauthorized" in handler.get_json_body().get("error", "")


def test_status_invalid_uuid():
    handler = DummyHandler("GET", "/broadcast/status/not-a-valid-uuid", headers={"X-Agent-Key": "test_secret_key"})
    handler.do_GET()
    assert handler.status == 400
    assert "must be a valid UUID" in handler.get_json_body().get("error", "")


def test_status_valid_uuid_not_found():
    random_uuid = str(uuid.uuid4())
    handler = DummyHandler("GET", f"/broadcast/status/{random_uuid}", headers={"X-Agent-Key": "test_secret_key"})
    handler.do_GET()
    assert handler.status == 404
    assert handler.get_json_body().get("error") == "Job not found"


def test_post_payload_too_large():
    # 65537 bytes (> 64KB)
    handler = DummyHandler(
        "POST",
        "/broadcast",
        headers={"X-Agent-Key": "test_secret_key", "Content-Length": "65537"},
        body=b"a" * 65537
    )
    handler.do_POST()
    assert handler.status == 413
    assert "Payload Too Large" in handler.get_json_body().get("error", "")


def test_broadcast_lock_concurrency():
    with agent_server.broadcast_lock:
        handler = DummyHandler(
            "POST",
            "/broadcast",
            headers={"X-Agent-Key": "test_secret_key", "Content-Length": "2"},
            body=b"{}"
        )
        handler.do_POST()
        assert handler.status == 409
        assert "currently active" in handler.get_json_body().get("error", "")
