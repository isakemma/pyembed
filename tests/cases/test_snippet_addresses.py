"""
How a link leads to a snippet (site.js, used by viewer.html, gallery.html
and the widget's Link dialog):

  - viewer.html?folder/name shows the snippet with that name
  - so does every address the snippet had before, and links from before
    names existed: viewer.html?src=folder/03-example.json, with "/" or %2F,
    even though that file no longer exists
  - upper/lower case and things added to the link (&fbclid=...) do no harm
  - the Link dialog and the gallery hand out the name, whichever address
    the page was opened with
  - an address that was retired says so
  - without an address list everything works as before names
  - all of it works when the site lives under a sub-path (/REPO/)

Uses a synthetic addresses.json, index.json and snippets (via request
interception), so it does not depend on the real content. That every real
address still leads somewhere is checked in test_addresses_workflow.py.
"""

import json

BOOK = {
    "snippets": {
        # Was 03-example.json, then renamed
        "fake/lesson01/03-sortering.json": {"addresses": [
            "fake/lesson01/sortering", "fake/lesson01/03-sortering", "fake/lesson01/03-example"]},
        "fake/lesson01/01.json": {"addresses": ["fake/lesson01/01"]},
    },
    "retired": ["fake/lesson01/02"],
}
INDEX = {
    "courses": [],
    "categories": [{"id": "fake", "name": "Fake", "folder": "fake/lesson01", "snippets": [
        {"id": "a", "file": "fake/lesson01/01.json", "title": "First"},
        {"id": "b", "file": "fake/lesson01/03-sortering.json", "title": "Sortering"},
    ]}],
}
SNIPPETS = {
    "fake/lesson01/01.json": {"title": "First", "files": [{"name": "main.py", "content": "print(1)\n"}]},
    "fake/lesson01/03-sortering.json": {"title": "Sortering", "files": [{"name": "main.py", "content": "print(3)\n"}]},
}


def install_fakes(page, with_book=True):
    def fulfill(route):
        path = route.request.url.split("/snippets/", 1)[1]
        if path == "addresses.json" and with_book:
            body = BOOK
        elif path == "index.json":
            body = INDEX
        elif path in SNIPPETS:
            body = SNIPPETS[path]
        else:
            # Also fake/lesson01/03-example.json: that file is gone
            route.fulfill(status=404, body="not found")
            return
        route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    page.unroute("**/snippets/fake/**")
    page.unroute("**/snippets/addresses.json")
    page.unroute("**/snippets/index.json")
    page.route("**/snippets/fake/**", fulfill)
    page.route("**/snippets/index.json", fulfill)
    if with_book:
        page.route("**/snippets/addresses.json", fulfill)
    else:
        page.route("**/snippets/addresses.json", lambda route: route.fulfill(status=404, body=""))


def title_at(page, url):
    page.goto(url)
    page.wait_for_selector(".pw-file", timeout=10000)
    return page.inner_text(".pw-title")


def link_in_dialog(page):
    page.click(".pw-btn-link")
    link = page.input_value(".psw-modal-url")
    page.keyboard.press("Escape")
    page.click(".pw-btn-embed")
    code = page.inner_text(".psw-modal-panel.active .psw-modal-code")
    page.keyboard.press("Escape")
    assert f'src="{link}"' in code, (link, code)
    return link


def check_site(page, site):
    """Everything that must work, for a site whose pages are at `site`."""
    install_fakes(page)

    # ── Every address of a snippet leads to it ───────────────────────────
    for query in (
        "fake/lesson01/sortering",
        "fake/lesson01/03-sortering",
        "fake/lesson01/03-example",                # the name it had before
        "src=fake/lesson01/03-example.json",       # links from before names
        "src=fake%2Flesson01%2F03-example.json",
        "fake%2Flesson01%2Fsortering",
        "FAKE/Lesson01/Sortering",
        "fake/lesson01/sortering&fbclid=abc123",
        "utm_source=x&fake/lesson01/sortering",
    ):
        title = title_at(page, f"{site}/viewer.html?{query}")
        assert title == "Sortering", (query, title)
        # ... and whichever was used, the dialog hands out the name
        link = link_in_dialog(page)
        assert link == f"{site}/viewer.html?fake/lesson01/sortering", (query, link)

    # A snippet without a name: its number, in the short form
    assert title_at(page, f"{site}/viewer.html?src=fake%2Flesson01%2F01.json") == "First"
    assert link_in_dialog(page) == f"{site}/viewer.html?fake/lesson01/01"
    assert title_at(page, f"{site}/viewer.html?fake/lesson01/01") == "First"

    # ── Retired, and unknown ─────────────────────────────────────────────
    page.goto(f"{site}/viewer.html?fake/lesson01/02")
    page.wait_for_function("document.getElementById('widget').textContent.includes('has been removed')")
    page.goto(f"{site}/viewer.html?fake/lesson01/no-such-example")
    page.wait_for_selector(".pw-state-err", timeout=10000)
    page.goto(f"{site}/viewer.html")
    page.wait_for_function("document.getElementById('widget').textContent.includes('No snippet specified')")

    # ── The gallery links with the names, in the lesson's order ──────────
    page.goto(f"{site}/gallery.html?cat=fake/lesson01")
    page.wait_for_function("document.querySelectorAll('.card .card-title').length === 2")
    cards = page.eval_on_selector_all(
        ".card", "els => els.map(e => [e.querySelector('.card-title').textContent, e.getAttribute('href')])")
    assert cards == [["First", "viewer.html?fake/lesson01/01"],
                     ["Sortering", "viewer.html?fake/lesson01/sortering"]], cards
    page.click(".card-cell:nth-child(2) .card")
    page.wait_for_selector(".pw-file", timeout=10000)
    assert page.inner_text(".pw-title") == "Sortering"

    # ── A snippet outside the snippets folder has no address ─────────────
    title_at(page, f"{site}/viewer.html?src=../tests/fixtures/long_code.json")
    assert link_in_dialog(page) == f"{site}/viewer.html?src=..%2Ftests%2Ffixtures%2Flong_code.json"

    # ── No address list: file paths, as before names ─────────────────────
    install_fakes(page, with_book=False)
    assert title_at(page, f"{site}/viewer.html?src=fake%2Flesson01%2F01.json") == "First"
    assert link_in_dialog(page) == f"{site}/viewer.html?src=fake%2Flesson01%2F01.json"
    assert title_at(page, f"{site}/viewer.html?fake/lesson01/03-sortering") == "Sortering"


def test(page, base_url):
    check_site(page, base_url)

    # ── A widget embedded directly in another page (no viewer, no site.js
    #    on the page): the dialog fetches site.js itself ───────────────────
    install_fakes(page)
    page.goto(f"{base_url}/tests/fixtures/direct_embed_named.html")
    page.wait_for_selector(".pw-file", timeout=10000)
    assert page.evaluate("typeof window.PySnippets") == "undefined"
    assert link_in_dialog(page) == f"{base_url}/viewer.html?fake/lesson01/sortering"

    # ── The same site under https://USER.github.io/REPO/ ─────────────────
    # (requests to a made-up host are answered from the local server)
    site = "http://pages.test/REPO"

    def from_local_server(route):
        route.fulfill(response=route.fetch(url=route.request.url.replace(site, base_url)))

    page.route(site + "/**", from_local_server)
    check_site(page, site)
