#!/usr/bin/env python3
import os
import threading
import subprocess
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, redirect, request, send_file, url_for

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = BASE_DIR / "outputs"
REPORT_PATH = OUTPUTS_DIR / "veille_ia_rapport.html"
LOG_PATH = OUTPUTS_DIR / "pipeline.log"

app = Flask(__name__)

_state_lock = threading.Lock()
_state = {
    "running": False,
    "last_start": None,
    "last_finish": None,
    "last_exit_code": None,
}


def _read_log_tail(max_bytes=8000):
    if not LOG_PATH.exists():
        return ""
    with open(LOG_PATH, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - max_bytes))
        data = f.read()
    return data.decode("utf-8", errors="replace")


def _run_pipeline():
    with _state_lock:
        _state["running"] = True
        _state["last_start"] = datetime.now()
        _state["last_finish"] = None
        _state["last_exit_code"] = None

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(f"\n=== Pipeline start {datetime.now().isoformat()} ===\n")
        log_file.flush()
        process = subprocess.Popen(
            ["bash", "start_pipeline.sh"],
            cwd=BASE_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
        exit_code = process.wait()
        log_file.write(f"=== Pipeline end {datetime.now().isoformat()} (exit {exit_code}) ===\n")

    with _state_lock:
        _state["running"] = False
        _state["last_finish"] = datetime.now()
        _state["last_exit_code"] = exit_code


@app.get("/")
def index():
    message = request.args.get("msg", "")
    with _state_lock:
        state = dict(_state)

    return render_template(
        "index.html",
        state=state,
        report_exists=REPORT_PATH.exists(),
        log_tail=_read_log_tail(),
        message=message,
    )


@app.post("/run")
def run_pipeline():
    with _state_lock:
        if _state["running"]:
            return redirect(url_for("index", msg="Pipeline deja en cours."), code=303)

    thread = threading.Thread(target=_run_pipeline, daemon=True)
    thread.start()
    return redirect(url_for("index", msg="Pipeline lance."), code=303)


@app.get("/report")
def report():
    if not REPORT_PATH.exists():
        return redirect(url_for("index", msg="Aucun rapport HTML trouve."), code=303)
    return send_file(REPORT_PATH, mimetype="text/html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
