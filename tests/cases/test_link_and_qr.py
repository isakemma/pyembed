"""
The 🔗 Link button opens the dialog on its "Link & QR" tab, with the
snippet's viewer.html address, a QR code for it, a working Copy link button
and a PNG download. </> Embed must still open on the iframe tab.

The QR generator is loaded from the jsDelivr CDN when the dialog opens, and
is the only thing the widget fetches from another host. This test uses the
real CDN (so it needs network access, and fails if the address in embed.js
stops working). If the CDN cannot be reached, the dialog must say so and
the link must still be there to copy.
"""

import re
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = "basic-examples/hello.json"


def test(page, base_url):
    embed_js = (REPO_ROOT / "embed.js").read_text(encoding="utf-8")
    cdn_url = re.search(r"QRCODE_CDN = '([^']+)'", embed_js).group(1)

    host = urlparse(base_url).netloc
    external = []
    page.on("request", lambda r: external.append(r.url)
            if urlparse(r.url).netloc not in (host, "") else None)
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])

    # ── Nothing external until the dialog is opened, then only the CDN ───
    page.goto(f"{base_url}/viewer.html?src={SRC}")
    page.wait_for_selector(".pw-file", timeout=10000)
    assert not external, external
    check_dialog(page, base_url)
    assert external == [cdn_url], external

    # ── CDN unreachable: a message instead of the code, link still there ─
    page.route(cdn_url, lambda route: route.abort())
    page.goto(f"{base_url}/viewer.html?src={SRC}")
    page.wait_for_selector(".pw-file", timeout=10000)
    page.click(".pw-btn-link")
    page.wait_for_function(
        "document.querySelector('.psw-modal-qr').textContent.includes('could not be loaded')",
        timeout=10000)
    assert page.locator(".psw-modal-qr svg").count() == 0
    assert page.is_disabled(".psw-modal-qr-dl")
    page.click(".psw-modal-copy-link")
    copied = page.evaluate("navigator.clipboard.readText()")
    assert copied == f"{base_url}/viewer.html?src=basic-examples%2Fhello.json", copied


def check_dialog(page, base_url):
    expected_url = f"{base_url}/viewer.html?src=basic-examples%2Fhello.json"

    # ── Link button → Link & QR tab ──────────────────────────────────────
    page.click(".pw-btn-link")
    panel = page.locator(".psw-modal-panel.active")
    assert panel.get_attribute("data-panel") == "link", panel.get_attribute("data-panel")
    url = page.input_value(".psw-modal-url")
    assert url == expected_url, url

    # The address works: it is the page we are on, apart from %2F for "/"
    assert page.url.replace("/hello", "%2Fhello") == url, (page.url, url)

    # A QR code: square, with its margin, and a 7×7 finder pattern whose top
    # row is the first thing in the path (7 dark modules from the corner).
    page.wait_for_selector(".psw-modal-qr svg", timeout=10000)
    view_box = page.get_attribute(".psw-modal-qr svg", "viewBox").split()
    size = int(view_box[2])
    assert view_box[2] == view_box[3] and (size - 8 - 17) % 4 == 0, view_box
    path = page.get_attribute(".psw-modal-qr svg path", "d")
    assert path.startswith("".join(f"M{c} 4h1v1h-1z" for c in range(4, 11)) + "M"), path[:120]

    # Copy link
    page.click(".psw-modal-copy-link")
    copied = page.evaluate("navigator.clipboard.readText()")
    assert copied == expected_url, copied

    # Download QR code: a PNG named after the snippet
    with page.expect_download() as dl:
        page.click(".psw-modal-qr-dl")
    assert dl.value.suggested_filename.endswith("_qr.png"), dl.value.suggested_filename
    with open(dl.value.path(), "rb") as f:
        assert f.read(8) == b"\x89PNG\r\n\x1a\n"

    # Escape closes the dialog
    page.keyboard.press("Escape")
    assert page.locator(".psw-modal-overlay").count() == 0

    # ── Embed button still opens on the iframe tab ───────────────────────
    page.click(".pw-btn-embed")
    panel = page.locator(".psw-modal-panel.active")
    assert panel.get_attribute("data-panel") == "iframe", panel.get_attribute("data-panel")
    assert expected_url in page.inner_text(".psw-modal-panel.active .psw-modal-code")
    page.click(".psw-modal-panel.active .psw-modal-close")
    assert page.locator(".psw-modal-overlay").count() == 0
