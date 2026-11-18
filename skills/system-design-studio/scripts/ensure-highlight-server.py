#!/usr/bin/env python3
"""
Ensure Highlight Server is Running
Silent, non-blocking utility that verifies port 7723 is listening.
If not, starts highlight-server.py as a detached background daemon process.
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_PORT = 7723

def is_port_listening(port=DEFAULT_PORT):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False

def ensure_server(port=DEFAULT_PORT):
    if is_port_listening(port):
        return True

    current_dir = Path(__file__).resolve().parent
    candidates = [
        current_dir / "highlight-server.py",
        Path.home() / ".system-design-studio" / "skills" / "system-design-studio" / "scripts" / "highlight-server.py",
        Path.home() / "Developer" / "system-design-studio" / "skills" / "system-design-studio" / "scripts" / "highlight-server.py",
    ]

    server_script = None
    for cand in candidates:
        if cand.is_file():
            server_script = cand
            break

    if not server_script:
        return False

    try:
        subprocess.Popen(
            [sys.executable, str(server_script), "--port", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True
        )
        time.sleep(0.15)
        return is_port_listening(port)
    except Exception:
        return False

if __name__ == "__main__":
    ensure_server()
