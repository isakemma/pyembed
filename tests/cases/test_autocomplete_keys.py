"""
Accepting an autocomplete suggestion: Tab and Enter both insert the
highlighted suggestion, and the list says so. Tab used to indent the line
instead (it is also the indent key), which left Enter as the only,
undiscoverable, way. With no list showing, Tab must still indent.
"""

SRC = "../tests/fixtures/long_code.json"
POPUP = ".cm-tooltip-autocomplete"


def last_line(page):
    return page.evaluate(
        "[...document.querySelectorAll('.cm-content .cm-line')].pop().textContent")


def type_on_new_last_line(page, text):
    page.click(".cm-content")
    page.keyboard.press("Control+End")
    page.keyboard.press("Enter")
    page.keyboard.press("Home")
    page.keyboard.press("Shift+End")      # drop any auto-indent
    page.keyboard.press("Delete")
    page.keyboard.type(text, delay=30)


def wait_for_list(page):
    page.wait_for_selector(POPUP, timeout=5000)
    # CodeMirror ignores accept keys for 75 ms after the list appears, so
    # that a key typed just as it pops up is not swallowed.
    page.wait_for_timeout(200)


def test(page, base_url):
    page.goto(f"{base_url}/viewer.html?src={SRC}")
    page.wait_for_selector(".cm-content", timeout=10000)

    # Tab accepts
    type_on_new_last_line(page, "isins")
    wait_for_list(page)
    hint = page.evaluate(f"getComputedStyle(document.querySelector('{POPUP}'), '::after').content")
    assert "Tab or Enter" in hint, hint
    page.keyboard.press("Tab")
    assert last_line(page) == "isinstance", repr(last_line(page))
    assert page.locator(POPUP).count() == 0

    # Enter accepts (and does not also add a line)
    type_on_new_last_line(page, "isins")
    wait_for_list(page)
    page.keyboard.press("Enter")
    assert last_line(page) == "isinstance", repr(last_line(page))

    # Escape closes the list; then Tab indents as before
    type_on_new_last_line(page, "isins")
    wait_for_list(page)
    page.keyboard.press("Escape")
    page.wait_for_selector(POPUP, state="detached", timeout=5000)
    page.keyboard.press("Tab")
    line = last_line(page)
    assert line.strip() == "isins" and line != "isins", repr(line)
