"""
Shared helpers for the widget regression tests. Not a test framework —
just enough to start the static server, drive one snippet through
Playwright, and hand back what happened.
"""

import contextlib
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def static_server():
    """Serves the repo root over HTTP for the duration of the `with` block."""
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://localhost:{port}"
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(f"{base_url}/embed.js", timeout=0.5)
                break
            except Exception:
                time.sleep(0.1)
        else:
            raise RuntimeError("static server did not come up")
        yield base_url
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def run_snippet(page, base_url, src, inputs=(), timeout=10000):
    """
    Loads viewer.html for `src` (a path relative to snippets/), clicks Run,
    answers any input() prompts in order with `inputs`, waits for the run
    to finish (or for the run to block on an unanswered input prompt), and
    returns the output panel's text content.
    """
    page.goto(f"{base_url}/viewer.html?src={src}")
    page.wait_for_selector(".pw-file", timeout=timeout)
    page.click(".pw-btn-run")

    for value in inputs:
        page.wait_for_selector(".pw-input-field", timeout=timeout)
        page.fill(".pw-input-field", value)
        page.press(".pw-input-field", "Enter")

    def finished_or_waiting(_):
        btn_done = page.eval_on_selector(
            ".pw-btn-run, .pw-btn-stop",
            "el => el.textContent.includes('Run') && !el.classList.contains('pw-btn-stop')",
        )
        waiting_for_input = page.query_selector(".pw-input-field") is not None
        return btn_done or waiting_for_input

    page.wait_for_function(
        """() => {
            const btn = document.querySelector('.pw-btn-run, .pw-btn-stop');
            const btnDone = btn && btn.textContent.includes('Run') && !btn.classList.contains('pw-btn-stop');
            const waitingForInput = !!document.querySelector('.pw-input-field');
            return btnDone || waitingForInput;
        }""",
        timeout=timeout,
    )
    page.wait_for_timeout(150)
    return page.eval_on_selector(".pw-output-pre", "el => el.textContent")


def file_names(page):
    """Names currently shown in the file sidebar."""
    return page.eval_on_selector_all(".pw-file .pw-file-name", "els => els.map(e => e.textContent)")


def file_badges(page):
    """Maps file name -> badge text (e.g. 'NEW'), for files that have one."""
    pairs = page.eval_on_selector_all(
        ".pw-file",
        "els => els.map(e => [e.querySelector('.pw-file-name')?.textContent, "
        "e.querySelector('.pw-file-badge')?.textContent || null])",
    )
    return dict(pairs)
