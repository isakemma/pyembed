"""
Regression test for: the editor area must never fully collapse (it used
to shrink to 0px in a small enough embed, leaving no code visible at
all), and short snippets should show some blank space below the code
rather than the editor tightly hugging just the actual content.

Fix: .pw-editor-area's min-height went from a bare 0 to
clamp(120px, 35%, 200px) in embed.js, so it always keeps a floor
(120px, ~7 lines) regardless of how small the embed is, and holds a
consistent size (up to 200px) for short snippets instead of shrinking
to fit their content.
"""

MIN_FLOOR_PX = 120


def test(page, base_url):
    # ── Long code in a very cramped iframe: editor must hold its floor,
    #    not shrink toward 0 the way it did before this fix. ──────────────
    page.set_viewport_size({"width": 900, "height": 200})
    page.goto(f"{base_url}/viewer.html?src=../tests/fixtures/long_code.json")
    page.wait_for_selector(".pw-file", timeout=10000)
    page.wait_for_timeout(200)

    editor_h = page.eval_on_selector(".pw-editor-area", "el => el.getBoundingClientRect().height")
    assert editor_h >= MIN_FLOOR_PX - 1, (
        f"editor area shrank to {editor_h:.1f}px in a cramped embed — "
        f"expected it to hold at least its {MIN_FLOOR_PX}px floor"
    )

    # ── Short snippet in a normal-sized iframe: editor area should stay
    #    at a comfortable size, not collapse to fit its one line of code —
    #    i.e. there should be visible blank space below the code. ───────
    page.set_viewport_size({"width": 900, "height": 540})
    page.goto(f"{base_url}/viewer.html?src=basic-examples/hello.json")
    page.wait_for_selector(".pw-file", timeout=10000)
    page.wait_for_timeout(200)

    editor_h = page.eval_on_selector(".pw-editor-area", "el => el.getBoundingClientRect().height")
    line_h = page.eval_on_selector(".cm-line", "el => el.getBoundingClientRect().height")
    assert editor_h > line_h * 3, (
        f"editor area ({editor_h:.1f}px) is barely taller than a single code line "
        f"({line_h:.1f}px) — short snippets should show blank space below the code, "
        "not hug the content tightly"
    )
