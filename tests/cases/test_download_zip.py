"""
The "↓ Files (.zip)" and "↓ Download all" buttons on lecture.html and
gallery.html?cat= download a snippet's files, or a whole lesson's, as a zip
made in the browser (site.js). Inside the zip each example is a directory
named after its address, so it unpacks the way the examples are organised:

    fake/lesson01/sortering/main.py
    fake/lesson01/sortering/räkna.py
    fake/lesson01/01/main.py          (an example without a name)

Python's zipfile must be able to read the file, check its checksums, and
get file names and content with å/ä/ö back unchanged.

Uses a synthetic index, address list and snippets (request interception).
"""

import json
import zipfile

BOOK = {
    "snippets": {
        "fake/lesson01/03-sortering.json": {"addresses": [
            "fake/lesson01/sortering", "fake/lesson01/03-sortering", "fake/lesson01/03-example"]},
        "fake/lesson01/01.json": {"addresses": ["fake/lesson01/01"]},
    },
    "retired": [],
}
INDEX = {
    "courses": [{"id": "fake", "label": "Fake", "folderPrefix": "fake/lesson"}],
    "categories": [{"id": "fake", "name": "Fake 1", "folder": "fake/lesson01", "snippets": [
        {"id": "a", "file": "fake/lesson01/01.json", "title": "First"},
        {"id": "b", "file": "fake/lesson01/03-sortering.json", "title": "Sortering"},
    ]}],
}
FIRST = "print('första')\n"
MAIN = "from räkna import antal\nprint(antal('åäö ÅÄÖ – 日本'))\n"
HELPER = "def antal(text):\n\treturn len(text)\n"
DATA = ""
SNIPPETS = {
    "fake/lesson01/01.json": {"title": "First", "files": [{"name": "main.py", "content": FIRST}]},
    "fake/lesson01/03-sortering.json": {"title": "Sortering", "files": [
        {"name": "main.py", "content": MAIN},
        {"name": "räkna.py", "content": HELPER},
        {"name": "tom.txt", "content": DATA},
        {"name": "../../outside.txt", "content": "must stay inside\n"},
    ]},
}
SORTERING = {
    "fake/lesson01/sortering/main.py": MAIN,
    "fake/lesson01/sortering/räkna.py": HELPER,
    "fake/lesson01/sortering/tom.txt": DATA,
    "fake/lesson01/sortering/outside.txt": "must stay inside\n",
}
EVERYTHING = {"fake/lesson01/01/main.py": FIRST, **SORTERING}


def read_zip(download):
    with zipfile.ZipFile(download.path()) as z:
        assert z.testzip() is None, z.testzip()
        for info in z.infolist():
            assert info.compress_type == zipfile.ZIP_STORED and info.flag_bits & 0x800, info
        return {name: z.read(name).decode("utf-8") for name in z.namelist()}


def click_and_read(page, selector):
    with page.expect_download() as dl:
        page.click(selector)
    return dl.value.suggested_filename, read_zip(dl.value)


def test(page, base_url):
    def fulfill(route):
        path = route.request.url.split("/snippets/", 1)[1]
        body = {"addresses.json": BOOK, "index.json": INDEX}.get(path) or SNIPPETS[path]
        route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    for pattern in ("**/snippets/fake/**", "**/snippets/index.json", "**/snippets/addresses.json"):
        page.route(pattern, fulfill)

    # ── lecture.html: one example, and the whole lesson ──────────────────
    page.goto(f"{base_url}/lecture.html?course=fake&n=1")
    page.wait_for_function("document.querySelectorAll('.snippet-group .dl-btn').length === 2")
    name, files = click_and_read(page, ".snippet-group:nth-of-type(2) .dl-btn")
    assert name == "sortering.zip" and files == SORTERING, (name, files)
    name, files = click_and_read(page, ".snippet-group:nth-of-type(1) .dl-btn")
    assert name == "01.zip" and files == {"fake/lesson01/01/main.py": FIRST}, (name, files)
    name, files = click_and_read(page, ".hero .dl-btn")
    assert name == "fake-lesson01.zip" and files == EVERYTHING, (name, files)
    # Each example also links to its own page, by its address
    links = page.eval_on_selector_all(".snippet-open", "els => els.map(e => e.getAttribute('href'))")
    assert links == ["viewer.html?fake/lesson01/01", "viewer.html?fake/lesson01/sortering"], links

    # ── gallery.html?cat=: the same, from the cards ──────────────────────
    page.goto(f"{base_url}/gallery.html?cat=fake/lesson01")
    page.wait_for_function("document.querySelectorAll('.card .card-title').length === 2")
    name, files = click_and_read(page, ".card-cell:nth-child(2) .dl-btn")
    assert name == "sortering.zip" and files == SORTERING, (name, files)
    name, files = click_and_read(page, ".hero .dl-btn")
    assert name == "fake-lesson01.zip" and files == EVERYTHING, (name, files)

    # ── A file that cannot be fetched: said on the button, no download ───
    page.unroute("**/snippets/fake/**")
    page.route("**/snippets/fake/**", lambda route: route.fulfill(status=404, body=""))
    page.click(".hero .dl-btn")
    page.wait_for_function("document.querySelector('.hero .dl-btn').textContent.includes('Download failed')")
