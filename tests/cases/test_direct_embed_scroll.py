"""
Regression test for the non-iframe embed path: a widget placed directly
on a normal page (as on index.html/gallery.html/lecture.html), via
<div class="py-snippet" data-src="...">, rather than through viewer.html.

Unlike viewer.html, this path doesn't rely on any host-page CSS to size
the widget — .pw-widget has its own fixed height (520px) regardless of
the page around it — so this checks that path independently: the
widget itself must clip long code and actually respond to mouse-wheel
scrolling inside it, regardless of whether the surrounding page scrolls.
"""


def test(page, base_url):
    page.set_viewport_size({"width": 900, "height": 700})
    page.goto(f"{base_url}/tests/fixtures/direct_embed.html")
    page.wait_for_selector(".pw-file", timeout=10000)
    page.wait_for_timeout(300)

    widget_height = page.eval_on_selector(".pw-widget", "el => el.getBoundingClientRect().height")
    assert 500 <= widget_height <= 540, f"expected the widget's own fixed ~520px height, got {widget_height}"

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

    before = page.eval_on_selector(".cm-scroller", "el => el.scrollTop")
    page.mouse.move(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)
    page.mouse.wheel(0, 300)
    page.wait_for_timeout(200)
    after = page.eval_on_selector(".cm-scroller", "el => el.scrollTop")
    assert after > before, f"mouse wheel did not scroll the editor (scrollTop stayed {before})"
