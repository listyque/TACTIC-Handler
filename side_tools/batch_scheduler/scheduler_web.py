"""Token-protected local web control for the batch scheduler."""

from __future__ import annotations

import hmac
import json
import mimetypes
import shutil
import socket
import threading
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit
from urllib.request import urlopen


from .scheduler_web_ui import ACCESS_REQUIRED_HTML, WEB_HTML


def _local_ipv4() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.connect(("192.0.2.1", 80))
            return connection.getsockname()[0]
    except OSError:
        pass
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        }
        return next(
            address
            for address in sorted(addresses)
            if not address.startswith(("127.", "169.254."))
        )
    except (OSError, StopIteration):
        return "127.0.0.1"


class _BatchWebHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        request = urlsplit(self.path)
        if request.path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        if request.path in {"/", "/index.html"} and not self._authorized(request):
            self._send(self.server.access_html, "text/html; charset=utf-8")
            return
        if not self._authorized(request):
            self._json({"error": "Invalid access token"}, HTTPStatus.FORBIDDEN)
            return
        try:
            if request.path in {"/", "/index.html"}:
                self._send(self.server.web_html, "text/html; charset=utf-8")
            elif request.path in self.server.icon_fonts:
                self._file(self.server.icon_fonts[request.path])
            elif request.path == "/api/state":
                query = parse_qs(request.query)
                selected = (query.get("selected") or [""])[0]
                self._json(self.server.dispatch({"type": "state", "selected": selected}))
            elif request.path == "/api/preview":
                query = parse_qs(request.query)
                path = self.server.dispatch(
                    {
                        "type": "preview",
                        "job": (query.get("job") or [""])[0],
                        "index": int((query.get("index") or ["-1"])[0]),
                    }
                )
                self._file(Path(path))
            elif request.path == "/api/thumb":
                query = parse_qs(request.query)
                source = self.server.dispatch(
                    {
                        "type": "thumb",
                        "identity": (query.get("identity") or [""])[0],
                    }
                )
                self._preview(source)
            else:
                self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except (OSError, TypeError, ValueError) as error:
            self._json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception as error:
            self._json({"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self):
        request = urlsplit(self.path)
        if not self._authorized(request):
            self._json({"error": "Invalid access token"}, HTTPStatus.FORBIDDEN)
            return
        if request.path != "/api/action":
            self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 2 or length > 65536:
                raise ValueError("Invalid request size")
            payload = json.loads(self.rfile.read(length))
            self._json(self.server.dispatch({"type": "action", **payload}))
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            self._json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception as error:
            self._json({"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def _authorized(self, request) -> bool:
        if request.path in {
            "/assets/icons-solid.ttf",
            "/assets/icons-regular.ttf",
            "/assets/icons-material.ttf",
        }:
            return True
        if not self.server.require_token:
            return True
        query_token = (parse_qs(request.query).get("token") or [""])[0]
        supplied = self.headers.get("X-Batch-Token", "") or query_token
        return hmac.compare_digest(supplied, self.server.token)

    def _json(self, value, status=HTTPStatus.OK):
        self._send(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode(),
            "application/json; charset=utf-8",
            status,
        )

    def _send(self, value, content_type, status=HTTPStatus.OK):
        body = value.encode() if isinstance(value, str) else value
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        if content_type.startswith("text/html"):
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data: http: https:",
            )
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path):
        if not path.is_file():
            raise FileNotFoundError("Preview is no longer available")
        self.send_response(HTTPStatus.OK)
        self.send_header(
            "Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        )
        self.send_header("Content-Length", str(path.stat().st_size))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        with path.open("rb") as source:
            shutil.copyfileobj(source, self.wfile, 1024 * 1024)

    def _preview(self, source):
        url = str(source)
        if not url.startswith(("http://", "https://")):
            self._file(Path(url))
            return
        safe_url = quote(url, safe=":/?#[]@!$&'()*+,;=%")
        with urlopen(safe_url, timeout=15) as response:
            content_type = response.headers.get("Content-Type") or (
                mimetypes.guess_type(urlsplit(url).path)[0]
                or "application/octet-stream"
            )
            self._send(response.read(), content_type)

    def log_message(self, _format, *_args):
        pass


class BatchWebServer:
    def __init__(self, dispatch, host="0.0.0.0", port=0, require_token=False):
        self.dispatch = dispatch
        self.host = host
        self.port = int(port)
        self.require_token = bool(require_token)
        self.token = uuid.uuid4().hex if self.require_token else ""
        fonts = Path(__file__).resolve().parents[2] / "thlib/ui/assets/fonts"
        self.icon_fonts = {
            "/assets/icons-solid.ttf": fonts / "fontawesome5-solid-webfont.ttf",
            "/assets/icons-regular.ttf": fonts / "fontawesome5-regular-webfont.ttf",
            "/assets/icons-material.ttf": fonts / "materialdesignicons-webfont.ttf",
        }
        self._server = None
        self._thread = None

    @property
    def url(self) -> str:
        host = _local_ipv4() if self.host == "0.0.0.0" else self.host
        url = f"http://{host}:{self.port}/"
        return url + f"?token={self.token}" if self.require_token else url

    def start(self) -> str:
        if self._server is not None:
            return self.url
        server = ThreadingHTTPServer((self.host, self.port), _BatchWebHandler)
        server.daemon_threads = True
        server.block_on_close = False
        server.dispatch = self.dispatch
        server.require_token = self.require_token
        server.token = self.token
        server.access_html = ACCESS_REQUIRED_HTML.encode("utf-8")
        server.web_html = WEB_HTML.encode("utf-8")
        server.icon_fonts = self.icon_fonts
        self._server = server
        self.port = server.server_port
        self._thread = threading.Thread(
            target=server.serve_forever,
            kwargs={"poll_interval": 0.2},
            name="batch-web",
            daemon=True,
        )
        self._thread.start()
        return self.url

    def stop(self) -> None:
        server, self._server = self._server, None
        if server is None:
            return
        server.shutdown()
        server.server_close()
        if self._thread is not threading.current_thread():
            self._thread.join(timeout=2)
        self._thread = None
