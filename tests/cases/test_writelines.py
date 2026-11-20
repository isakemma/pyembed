"""
Skulpt's file object has write() but no writelines(), so the lesson
example prgh-mobius/lesson07/04-write_to_file failed with "'file' object
has no attribute 'writelines'". embed.js adds it: any iterable of strings,
no newlines added, returns None, and a non-str is a TypeError as in Python 3.
"""

from harness import run_snippet


def test(page, base_url):
    out = run_snippet(page, base_url, "../tests/fixtures/writelines.json")
    assert "'Katt\\nHund\\nMarsvin\\n'" in out, out
    assert "None" in out, out
    assert "TypeError for non-str" in out, out
