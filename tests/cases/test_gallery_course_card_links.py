"""
Regression test for: gallery.html used to hardcode `n=1` in every course
card's link, but not every course's lesson numbering starts at 1 (e.g.
tilproovn's lowest lesson was ovn02 — there was no ovn01). Clicking a
card like that landed on lecture.html with "Lesson 1 not found for
course X" instead of the course's first real lesson.

Uses a synthetic index.json (via request interception) rather than the
real one on disk, so this stays deterministic regardless of whether any
*real* course currently happens to start at a non-1 lesson number.
"""

import json

FAKE_INDEX = {
    "courses": [
        {"id": "fake-course", "label": "Fake Course", "folderPrefix": "fake-course/lesson"},
    ],
    "categories": [
        {"id": "fake-course-lesson03", "name": "Fake Course – Lesson 3", "folder": "fake-course/lesson03", "snippets": []},
        {"id": "fake-course-lesson04", "name": "Fake Course – Lesson 4", "folder": "fake-course/lesson04", "snippets": []},
        {"id": "fake-course-lesson05", "name": "Fake Course – Lesson 5", "folder": "fake-course/lesson05", "snippets": []},
    ],
}


def test(page, base_url):
    def fulfill_fake_index(route):
        route.fulfill(status=200, content_type="application/json", body=json.dumps(FAKE_INDEX))

    page.route("**/snippets/index.json", fulfill_fake_index)

    page.goto(f"{base_url}/gallery.html")
    page.wait_for_selector(".card", timeout=10000)
    page.wait_for_timeout(150)

    href = page.eval_on_selector_all(
        ".card",
        "els => els.find(e => e.querySelector('.card-title')?.textContent === 'Fake Course')?.getAttribute('href')",
    )
    assert href == "lecture.html?course=fake-course&n=3", (
        f"card linked to {href!r}, expected n=3 (the course's lowest real lesson, "
        "since lesson01/02 don't exist)"
    )

    # Confirm the link actually resolves, not just that the number looks right.
    page.goto(f"{base_url}/{href}")
    page.wait_for_selector("#hero-title", timeout=10000)
    page.wait_for_timeout(150)
    err_el = page.query_selector(".state-err")
    err = page.eval_on_selector(".state-err", "el => el.textContent") if err_el else None
    assert err is None, f"card link {href!r} failed to load: {err}"
    title = page.eval_on_selector("#hero-title", "el => el.textContent")
    assert title == "Fake Course – Lesson 3", f"unexpected title: {title!r}"

    page.unroute("**/snippets/index.json", fulfill_fake_index)
