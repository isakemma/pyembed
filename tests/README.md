# Widget regression tests

Browser-driven regression tests for `embed.js`. These exist to catch
behavior regressions in the widget itself (file I/O, unicode handling,
etc.) — not part of the site, and not required by anyone just embedding
or editing snippets. Nothing here runs automatically; run it by hand
when you touch `embed.js` or want to check a suspected regression.

## One-time setup

```bash
cd tests
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Running

```bash
cd tests
source .venv/bin/activate
python3 run_tests.py
```

This starts a throwaway local static server for the repo root, runs each
`cases/test_*.py` against a headless Chromium, and prints a PASS/FAIL
line per case with the assertion failure underneath.

## Adding a new case

Add `cases/test_<name>.py` with a `test(page, base_url)` function that
raises an `AssertionError` (with a message containing the actual output)
on failure. Use `harness.run_snippet(page, base_url, src, inputs=[...])`
to run a snippet and get its output text, and `harness.file_names` /
`harness.file_badges` to inspect the file panel. `src` is the same path
you'd pass to `viewer.html?src=`; snippets outside `snippets/` (e.g. a
one-off fixture) can be reached with a `../` prefix, e.g.
`../tests/fixtures/my_case.json`.
