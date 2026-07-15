"""
Regression test for: writing to a filename chosen at runtime (e.g. via
input()) should surface the written file in the widget instead of
silently discarding it — the file panel gets a NEW entry, the output
panel gets a clickable link to it, and Reset removes it again.
"""

from harness import run_snippet, file_names, file_badges


def test(page, base_url):
    output = run_snippet(
        page, base_url, "../tests/fixtures/dynamic_file_io.json", inputs=["output.txt"]
    )
    assert "Wrote output.txt" in output, output

    names = file_names(page)
    assert "output.txt" in names, f"expected a new file panel entry, got {names}"

    badges = file_badges(page)
    # Badge text is lowercase "new" in the DOM; CSS applies text-transform: uppercase.
    assert badges.get("output.txt") == "new", f"expected 'new' badge, got {badges}"

    page.click(".pw-file-link")
    page.wait_for_timeout(150)
    content = page.eval_on_selector(".cm-content", "el => el.textContent")
    assert "hello from dynamic file" in content, content

    page.click(".pw-btn-reset")
    page.wait_for_timeout(150)
    assert "output.txt" not in file_names(page)
