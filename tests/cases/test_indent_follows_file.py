"""
Enter and Tab must indent the way the file already does: 2 spaces, 4
spaces, tabs or whatever step its blocks use. The editor used to insert 2
spaces everywhere, so in a 4-space file Enter after a line at 8 spaces
went to 6 (IndentationError), and in a tab-indented file it mixed spaces
with the tabs (TabError). Files with no block yet get 4 spaces.

Each file ends in "def f(x): / if x: / return 1". The test types, at the
end: Enter (stays in the block), a statement, Enter, a `while`, Enter
(indents one level), `pass`, Enter, Tab (one more level).
"""

EXPECTED_UNIT = {
    "four.py": "    ",
    "two.py": "  ",
    "tabs.py": "\t",
    "three.py": "   ",
    "mostly_two.py": "  ",
    "flat.py": "    ",
    "empty.py": "    ",
}


def editor_lines(page):
    return page.evaluate(
        "[...document.querySelectorAll('.cm-content .cm-line')].map(l => l.textContent)")


def test(page, base_url):
    page.goto(f"{base_url}/viewer.html?src=../tests/fixtures/indent_styles.json")
    page.wait_for_selector(".pw-file", timeout=10000)

    for name, unit in EXPECTED_UNIT.items():
        page.click(f".pw-file[title='{name}']")
        page.click(".cm-content")
        page.keyboard.press("Control+End")
        if name in ("flat.py", "empty.py"):
            if name == "flat.py":
                page.keyboard.press("Enter")
            page.keyboard.type("while x:")
            expected = ["while x:", unit + "pass", unit * 2 + "y"]
        else:
            page.keyboard.press("Enter")
            page.keyboard.type("x = 2")
            page.keyboard.press("Enter")
            page.keyboard.type("while x:")
            expected = [unit * 2 + "return 1", unit * 2 + "x = 2", unit * 2 + "while x:",
                        unit * 3 + "pass", unit * 4 + "y"]
        page.keyboard.press("Enter")
        page.keyboard.type("pass")
        page.keyboard.press("Enter")
        page.keyboard.press("Tab")
        page.keyboard.type("y")

        actual = editor_lines(page)[-len(expected):]
        assert actual == expected, (name, actual)
