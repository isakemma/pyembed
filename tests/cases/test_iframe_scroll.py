"""
Regression test for: in viewer.html (the iframe-embed page), long code
makes the whole page grow instead of scrolling inside the editor, so
mouse-wheel scrolling over the widget does nothing (the "scrollbar
works but the wheel doesn't" bug).

Root cause: viewer.html's host div starts as class="py-snippet", and
initWidget() adds "psw" to the same element, so embed.js's
`.psw { all: initial; ... }` reset (injected into the page after
viewer.html's own <style>, so it wins the equal-specificity tie) wipes
out viewer.html's `.py-snippet { flex: 1; }`. Without that flex:1, the
widget is no longer clipped to the iframe's height and instead grows to
fit its content — including the CodeMirror scroller, which ends up
exactly as tall as the code, leaving nothing to actually scroll.
"""

def test(page, base_url):
    page.set_viewport_size({"width": 900, "height": 400})
    page.goto(f"{base_url}/viewer.html?src=../tests/fixtures/long_code.json")
    page.wait_for_selector(".pw-file", timeout=10000)
    page.wait_for_timeout(300)

    # The page itself must never need to scroll — only panels inside the
    # widget should. If this is taller than the viewport, the widget broke
    # out of its iframe-filling layout.
    doc_scroll_height = page.evaluate("document.documentElement.scrollHeight")
    doc_client_height = page.evaluate("document.documentElement.clientHeight")
    assert doc_scroll_height <= doc_client_height + 1, (
        f"page grew to {doc_scroll_height}px in a {doc_client_height}px viewport "
        "instead of clipping content inside the widget"
    )

    # The editor's own scroller must actually have room to scroll.
    box = page.eval_on_selector(
        ".cm-scroller",
        "el => ({x: el.getBoundingClientRect().x, y: el.getBoundingClientRect().y,"
        " w: el.getBoundingClientRect().width, h: el.getBoundingClientRect().height})",
    )
    scroll_height = page.eval_on_selector(".cm-scroller", "el => el.scrollHeight")
    client_height = page.eval_on_selector(".cm-scroller", "el => el.clientHeight")
    assert scroll_height > client_height, (
        f"editor scroller isn't clipped (scrollHeight={scroll_height}, "
        f"clientHeight={client_height}) — nothing to scroll"
    )

    # And the mouse wheel must actually scroll it.
    before = page.eval_on_selector(".cm-scroller", "el => el.scrollTop")
    page.mouse.move(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)
    page.mouse.wheel(0, 300)
    page.wait_for_timeout(200)
    after = page.eval_on_selector(".cm-scroller", "el => el.scrollTop")
    assert after > before, f"mouse wheel did not scroll the editor (scrollTop stayed {before})"
