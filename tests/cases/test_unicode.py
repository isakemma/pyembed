"""
Regression tests for non-ASCII support: identifiers, filenames, and file
content should all work, not just the Latin-1 Swedish letters å/ä/ö.
"""

from harness import run_snippet, file_names


def test(page, base_url):
    out = run_snippet(page, base_url, "../tests/fixtures/unicode_latin1_ident.json")
    assert out.strip() == "True", out

    out = run_snippet(page, base_url, "../tests/fixtures/unicode_nonlatin1_ident.json")
    assert out.strip() == "52", out

    out = run_snippet(page, base_url, "../tests/fixtures/unicode_fileio.json")
    assert "Hej på dig, åäö! 变 λ п" in out, out
    assert "kafé.txt" in file_names(page), file_names(page)
