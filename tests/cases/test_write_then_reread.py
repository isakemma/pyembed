"""
Regression test for: writing to a file and then re-opening it for
reading later in the same run should see the freshly written content,
not stale/missing content. This matters because the file-I/O
implementation backs reads with a DOM element's textContent, which has
to be kept in sync on every write for a later re-open to see it.
"""

from harness import run_snippet


def test(page, base_url):
    output = run_snippet(page, base_url, "../tests/fixtures/write_then_reread.json")
    assert "first\nsecond\n" in output, output
