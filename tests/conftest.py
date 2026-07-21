import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "skills" / "kalodata" / "scripts")
)


class MockKalo(BaseHTTPRequestHandler):
    """Scriptable KaloData mock: responses keyed by path in server.responses."""

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        self._respond(body)

    def do_GET(self):
        self._respond({})

    def _respond(self, body):
        headers = {k.lower(): v for k, v in self.headers.items()}
        path = self.path.split("?")[0]
        self.server.requests.append((path, headers, body))
        payload = self.server.responses.get(path, {"success": True, "data": []})
        if callable(payload):
            payload = payload(body)
        raw = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


@pytest.fixture
def mock_server():
    server = HTTPServer(("127.0.0.1", 0), MockKalo)
    server.responses = {}
    server.requests = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()


@pytest.fixture
def env(monkeypatch, mock_server, tmp_path):
    monkeypatch.setenv("KALODATA_API_KEY", "test-key")
    monkeypatch.setenv("KALODATA_USER_ID", "12345")
    monkeypatch.setenv("KALODATA_BASE_URL", f"http://127.0.0.1:{mock_server.server_address[1]}")
    monkeypatch.setenv("KALODATA_CONFIG_DIR", str(tmp_path / "cfg"))
    return mock_server
