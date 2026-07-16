"""
Control case for test_bank_example_multifile_fileio: the same konton.txt
file I/O, but with all the code in a single main.py. This has always
worked and should keep working.
"""

from harness import run_snippet


def test(page, base_url):
    output = run_snippet(page, base_url, "prgh-mobius/lesson10/01-bank_example.json")
    assert "OSError" not in output, output
    assert "Vad vill du göra?" in output, output
