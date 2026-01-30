#!/usr/bin/env python3
"""Mock RoundTrip Authentication (RTA) backend for Red5 Pro.

A development/testing server that implements the RTA API expected by
Red5 Pro's RoundTripAuthValidator.  It approves all well-formed requests
unconditionally -- no real credential validation is performed.

Configuration is via environment variables (see DEFAULTS below).
"""

import json
import logging
import os
import signal
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging.handlers import RotatingFileHandler
from urllib.parse import parse_qs

# ---------------------------------------------------------------------------
# Defaults (overridden by environment variables)
# ---------------------------------------------------------------------------
DEFAULTS = {
    "MOCK_AUTH_HOST": "0.0.0.0",
    "MOCK_AUTH_PORT": "3000",
    "MOCK_AUTH_URL_RESOURCE": "",
    "MOCK_AUTH_LOG_DIR": "logs",
    "MOCK_AUTH_LOG_MAX_BYTES": "10485760",   # 10 MB
    "MOCK_AUTH_LOG_BACKUP_COUNT": "5",
    "MOCK_AUTH_LOG_LEVEL": "INFO",
    "MOCK_AUTH_PID_FILE": "",
}

MAX_BODY_SIZE = 1_048_576  # 1 MB

# ---------------------------------------------------------------------------
# HTML test page (embedded -- replaces the old index.html)
# ---------------------------------------------------------------------------
TEST_PAGE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Mock Authentication Backend</title>
  <style>
    body { font-family: sans-serif; margin: 2em; }
    fieldset { margin-bottom: 1em; max-width: 400px; }
    label { display: block; margin: .4em 0 .1em; }
    input[type=text] { width: 100%; box-sizing: border-box; }
    button { margin-top: .6em; }
    pre { background: #f4f4f4; padding: 1em; white-space: pre-wrap; }
  </style>
</head>
<body>
  <h1>Mock RTA Server</h1>

  <fieldset>
    <legend>Validate Credentials</legend>
    <form id="validateForm" method="POST" action="/validateCredentials">
      <label>Type
        <input type="text" name="type" value="publisher">
      </label>
      <label>Username
        <input type="text" name="username" value="">
      </label>
      <label>Password
        <input type="text" name="password" value="">
      </label>
      <label>Stream ID
        <input type="text" name="streamID" value="">
      </label>
      <button type="submit">Validate</button>
    </form>
  </fieldset>

  <fieldset>
    <legend>Invalidate Credentials</legend>
    <form id="invalidateForm" method="POST" action="/invalidateCredentials">
      <label>Username
        <input type="text" name="username" value="">
      </label>
      <label>Password
        <input type="text" name="password" value="">
      </label>
      <label>Stream ID
        <input type="text" name="streamID" value="">
      </label>
      <button type="submit">Invalidate</button>
    </form>
  </fieldset>

  <h3>Response</h3>
  <pre id="output">Submit a form to see the response.</pre>

  <script>
    document.querySelectorAll('form').forEach(function(form) {
      form.addEventListener('submit', function(e) {
        e.preventDefault();
        var data = new URLSearchParams(new FormData(form));
        fetch(form.action, {
          method: 'POST',
          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
          body: data
        })
        .then(function(r) { return r.text(); })
        .then(function(t) {
          document.getElementById('output').textContent = t;
        })
        .catch(function(err) {
          document.getElementById('output').textContent = 'Error: ' + err;
        });
      });
    });
  </script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Configuration helper
# ---------------------------------------------------------------------------

def _env(name):
    """Return the environment variable *name*, falling back to DEFAULTS."""
    return os.environ.get(name, DEFAULTS[name])


def configure_logging():
    """Set up root logger with rotating file handler and stdout handler."""
    log_dir = _env("MOCK_AUTH_LOG_DIR")
    max_bytes = int(_env("MOCK_AUTH_LOG_MAX_BYTES"))
    backup_count = int(_env("MOCK_AUTH_LOG_BACKUP_COUNT"))
    level_name = _env("MOCK_AUTH_LOG_LEVEL").upper()
    level = getattr(logging, level_name, logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    root = logging.getLogger()
    root.setLevel(level)

    # stdout -- also captured by systemd journal / Docker logs
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(fmt)
    root.addHandler(stdout_handler)

    # Rolling file
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "mock-auth.log"),
        maxBytes=max_bytes,
        backupCount=backup_count,
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    return root


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class RTAHandler(BaseHTTPRequestHandler):
    """HTTP request handler implementing the RTA mock endpoints."""

    server_version = "MockRTA/1.0"
    logger = logging.getLogger("rta")
    url_resource = ""  # set at startup from env

    # -- helpers ------------------------------------------------------------

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html, status=200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        """Read and parse the request body (JSON or form-urlencoded).

        Returns a dict (keys always map to single values, not lists).
        Returns None and sends 413 if body exceeds MAX_BODY_SIZE.
        """
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_BODY_SIZE:
            self.send_error(413, "Request body too large")
            return None
        raw = self.rfile.read(length) if length else b""
        content_type = (self.headers.get("Content-Type") or "").lower()

        if "application/json" in content_type:
            try:
                return json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return None
        else:
            # Treat everything else as form-urlencoded (matches Express
            # body-parser behaviour used by the original Node server).
            parsed = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
            # parse_qs returns lists; flatten to single values.
            return {k: v[0] for k, v in parsed.items()}

    # -- suppress default stderr access log ---------------------------------

    def log_message(self, format, *args):  # noqa: A002
        self.logger.info(
            "%s %s %s", self.client_address[0], self.command, self.path
        )

    # -- routing ------------------------------------------------------------

    def do_GET(self):  # noqa: N802
        if self.path == "/" or self.path == "/index.html":
            self._send_html(TEST_PAGE_HTML)
        else:
            self.send_error(404)

    def do_POST(self):  # noqa: N802
        routes = {
            "/logIn": self._handle_login,
            "/validateCredentials": self._handle_validate,
            "/invalidateCredentials": self._handle_invalidate,
            "/webhook": self._handle_webhook,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self.send_error(404)

    # -- endpoint handlers --------------------------------------------------

    def _handle_login(self):
        body = self._read_body()
        if body is None:
            return
        self.logger.info("logIn  username=%s password=%s",
                         body.get("username", ""), body.get("password", ""))
        self._send_json({
            "username": "streamUsername",
            "password": "streamPassword",
            "streamID": "streamID",
        })

    def _handle_validate(self):
        body = self._read_body()
        if body is None:
            return
        conn_type = body.get("type", "")
        username = body.get("username", "")
        password = body.get("password", "")
        stream_id = body.get("streamID", "")
        token = body.get("token", "")

        self.logger.info(
            "validateCredentials  type=%s username=%s password=%s "
            "streamID=%s token=%s",
            conn_type, username, password, stream_id, token,
        )

        if password != "pass":
            self.logger.info("validateCredentials  DENIED (bad password)")
            self._send_json({"result": False})
        elif conn_type == "publisher":
            self._send_json({"result": True, "url": self.url_resource})
        elif conn_type == "subscriber":
            self._send_json({"result": True})
        else:
            self._send_json({"result": False})

    def _handle_invalidate(self):
        body = self._read_body()
        if body is None:
            return
        username = body.get("username", "")
        password = body.get("password", "")
        stream_id = body.get("streamID", "")
        token = body.get("token", "")

        self.logger.info(
            "invalidateCredentials  username=%s password=%s "
            "streamID=%s token=%s",
            username, password, stream_id, token,
        )
        self._send_json({"result": True})

    def _handle_webhook(self):
        body = self._read_body()
        if body is None:
            return
        self.logger.info("webhook  body=%s", json.dumps(body))
        self._send_json({})


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def _write_pid_file(path):
    if path:
        with open(path, "w") as f:
            f.write(str(os.getpid()))


def _remove_pid_file(path):
    if path:
        try:
            os.remove(path)
        except OSError:
            pass


def main():
    configure_logging()
    logger = logging.getLogger("main")

    host = _env("MOCK_AUTH_HOST")
    port = int(_env("MOCK_AUTH_PORT"))
    pid_file = _env("MOCK_AUTH_PID_FILE")

    RTAHandler.url_resource = _env("MOCK_AUTH_URL_RESOURCE")

    server = ThreadingHTTPServer((host, port), RTAHandler)

    # Graceful shutdown on SIGTERM / SIGINT
    def _shutdown(signum, _frame):
        sig_name = signal.Signals(signum).name
        logger.info("Received %s -- shutting down", sig_name)
        # server.shutdown() must be called from a non-serving thread
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    _write_pid_file(pid_file)

    logger.info("Mock RTA server listening on %s:%d", host, port)
    try:
        server.serve_forever()
    finally:
        _remove_pid_file(pid_file)
        logger.info("Server stopped")


if __name__ == "__main__":
    main()
