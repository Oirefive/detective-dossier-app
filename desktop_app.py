from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

import uvicorn


HOST = "127.0.0.1"
PORT = 8000


def bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent


def data_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "app_data"
    return bundle_root() / "app_data"


def write_log(message: str) -> None:
    target = data_root()
    target.mkdir(parents=True, exist_ok=True)
    (target / "launcher.log").open("a", encoding="utf-8").write(message + "\n")


def run_server() -> None:
    try:
        os.environ["ARCHIVE_BUNDLE_ROOT"] = str(bundle_root())
        os.environ["ARCHIVE_DATA_ROOT"] = str(data_root())
        write_log(f"bundle_root={bundle_root()}")
        write_log(f"data_root={data_root()}")

        from backend.app import app

        config = uvicorn.Config(
            app,
            host=HOST,
            port=PORT,
            reload=False,
            log_level="warning",
            log_config=None,
            access_log=False,
        )
        server = uvicorn.Server(config)
        server.run()
    except Exception:
        write_log(traceback.format_exc())
        raise


def wait_for_server(timeout_seconds: float = 20.0) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((HOST, PORT)) == 0:
                return True
        time.sleep(0.25)
    return False


def find_edge() -> str:
    candidates = [
        shutil.which("msedge"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    raise SystemExit("Microsoft Edge was not found")


def main() -> None:
    try:
        write_log("launcher started")
        write_log(f"frozen={getattr(sys, 'frozen', False)}")
        write_log(f"sys.executable={sys.executable}")
        write_log(f"sys._MEIPASS={getattr(sys, '_MEIPASS', '')}")

        dist = bundle_root() / "dist" / "index.html"
        write_log(f"dist_path={dist}")
        if not dist.exists():
            write_log("frontend build was not found")
            raise SystemExit("Frontend build was not found")

        data = data_root()
        (data / "exports").mkdir(parents=True, exist_ok=True)
        (data / "uploads").mkdir(parents=True, exist_ok=True)
        write_log("data directories prepared")

        thread = threading.Thread(target=run_server, daemon=False)
        thread.start()
        write_log("server thread started")

        if not wait_for_server():
            write_log("server did not start in time")
            raise SystemExit(f"Local server did not start on http://{HOST}:{PORT}")

        edge = find_edge()
        write_log(f"edge={edge}")
        subprocess.Popen(
            [
                edge,
                f"--app=http://{HOST}:{PORT}",
                "--window-size=1600,980",
                "--disable-features=msHubApps",
            ]
        )
        write_log("edge launched")
        thread.join()
    except Exception:
        write_log(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
