"""
Regression test for: open() must accept Python 3's keyword arguments,
most importantly open(filename, encoding="utf-8"). Skulpt's own open()
is Python 2's positional-only open(name[, mode[, buffering]]) and fails
with "open() takes no keyword arguments"; embed.js wraps it.
"""

from harness import run_snippet


def test(page, base_url):
    output = run_snippet(page, base_url, "../tests/fixtures/open_keyword_args.json")
    expected = "räksmörgås\n\nett\ntvå\nräksmörgås\nappended\n\nTypeError\nmissing\n"
    assert expected in output, output
