"""
▶ Run executes the .py file that is open, not always main.py, so every
script in a multi-file example can be run on its own (e.g. djur_0.py and
djur_1.py next to main.py). The open file can still import its siblings.
When a non-.py file is open, Run falls back to main.py.
"""

from harness import run_snippet


def _open_and_run(page, name):
    page.click(f".pw-file[title='{name}']")
    page.click(".pw-btn-run")
    page.wait_for_function(
        """() => {
            const btn = document.querySelector('.pw-btn-run, .pw-btn-stop');
            return btn && btn.textContent.includes('Run') && !btn.classList.contains('pw-btn-stop');
        }"""
    )
    page.wait_for_timeout(150)
    return page.eval_on_selector(".pw-output-pre", "el => el.textContent")


def test(page, base_url):
    # Opens on main.py, so the default run is unchanged.
    out = run_snippet(page, base_url, "../tests/fixtures/run_active_file.json")
    assert "ran main.py" in out, out
    assert page.get_attribute(".pw-btn-run", "title").startswith("Run main.py"), \
        page.get_attribute(".pw-btn-run", "title")

    out = _open_and_run(page, "other.py")
    assert "ran other.py: hello from helper" in out, out
    assert "ran main.py" not in out, out
    assert page.get_attribute(".pw-btn-run", "title").startswith("Run other.py")

    out = _open_and_run(page, "notes.txt")
    assert "ran main.py" in out, out
