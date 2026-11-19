#!/usr/bin/env python3
"""
Artifact Highlight Sync Server
Runs locally to bridge the HTML artifact's highlighter with the filesystem.
Reads/writes .highlights.json sidecar files next to artifact HTML files.

Usage:
  python3 highlight_server.py [--port 7723]
"""

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PORT = 7723
SIDECAR_SUFFIX = ".highlights.json"

# Fallback store: when the artifact path is not writable (e.g. a URL path like
# "/brain/.../file.html" that the server received from a sandboxed iframe), we
# keep sidecars in a central directory keyed by a sanitised version of the path.
STORE_DIR = Path.home() / ".gemini" / "antigravity" / "highlights"
STORE_DIR.mkdir(parents=True, exist_ok=True)


def _sanitise(artifact_path: str) -> str:
    """Turn an arbitrary path string into a safe flat filename."""
    return artifact_path.replace("/", "_").replace("\\", "_").strip("_") or "default"


def sidecar_path(artifact_path: str) -> Path:
    p = Path(artifact_path)
    # Try the natural sidecar location (next to the artifact) first
    candidate = p.parent / (p.name + SIDECAR_SUFFIX)
    # If the parent directory exists and is writable, use it
    if p.parent.exists() and os.access(p.parent, os.W_OK):
        return candidate
    # Otherwise fall back to the central store
    return STORE_DIR / (_sanitise(artifact_path) + SIDECAR_SUFFIX)


def load_highlights(artifact_path: str) -> list:
    # Check both locations so old data is found even after directory moves
    for sp in [sidecar_path(artifact_path),
               STORE_DIR / (_sanitise(artifact_path) + SIDECAR_SUFFIX)]:
        if sp.exists():
            try:
                return json.loads(sp.read_text())
            except Exception:
                continue
    return []


def save_highlights(artifact_path: str, highlights: list) -> None:
    sp = sidecar_path(artifact_path)
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(highlights, indent=2))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stderr.write(f"[highlight-server] {format % args}\n")
        sys.stderr.flush()

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path == "/highlights":
            artifact = qs.get("artifact", [None])[0]
            if not artifact:
                self._respond(400, {"error": "missing ?artifact= param"})
                return
            highlights = load_highlights(artifact)
            self._respond(200, highlights)

        elif parsed.path == "/ping":
            self._respond(200, {"status": "ok", "port": PORT})

        else:
            self._respond(404, {"error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path == "/highlights":
            artifact = qs.get("artifact", [None])[0]
            if not artifact:
                self._respond(400, {"error": "missing ?artifact= param"})
                return
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                highlights = json.loads(body)
                if not isinstance(highlights, list):
                    raise ValueError("expected array")
            except Exception as e:
                self._respond(400, {"error": str(e)})
                return
            save_highlights(artifact, highlights)
            self._respond(200, {"saved": len(highlights)})

        else:
            self._respond(404, {"error": "not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        artifact = qs.get("artifact", [None])[0]
        if not artifact:
            self._respond(400, {"error": "missing ?artifact= param"})
            return
        sp = sidecar_path(artifact)
        if sp.exists():
            sp.unlink()
        self._respond(200, {"cleared": True})

    def _respond(self, status: int, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description="Artifact Highlight Sync Server")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"[highlight-server] Listening on http://127.0.0.1:{args.port}")
    print(f"[highlight-server] Sidecar files written as <artifact>.highlights.json")
    print(f"[highlight-server] Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[highlight-server] Stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
