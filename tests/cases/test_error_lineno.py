"""
Regression test for error line-number reporting. embed.js injects exactly
one line (`from _pyembed_vfs import *`) at the top of every project .py
file and subtracts that offset when formatting a traceback's line number.
This checks that offset is still correct for an error raised directly in
main.py, and for one raised inside a module main.py imports.
"""

from harness import run_snippet


def test(page, base_url):
    out = run_snippet(page, base_url, "../tests/fixtures/error_lineno_mainfile.json")
    assert "ValueError: boom on line 3 (line 3)" in out, out

    out = run_snippet(page, base_url, "../tests/fixtures/error_lineno_imported.json")
    assert "ValueError: boom on line 3 of helper (line 3)" in out, out
