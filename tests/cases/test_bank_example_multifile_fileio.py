"""
Regression test for: a snippet whose file I/O call lives in an imported
module (not main.py) used to fail with "No such file or directory", even
though the exact same konton.txt works fine when opened directly from
main.py (see test_bank_example_singlefile_fileio).

Bug (fixed 2026-07-15): embed.js's virtual open() used to be defined as
a plain top-level name in the entry-point script's own globals, so it
only shadowed the real open() for __main__. bank.py here is imported as
a separate Skulpt module with its own globals, so its bare open() call
fell through to Skulpt's real open() and couldn't see snippet-declared
data files. Fixed by serving the VFS shim as a synthetic module
(`_pyembed_vfs`) that every project .py file imports via
`from _pyembed_vfs import *`, so they all share the same _vfs /
_vfs_written objects.
"""

from harness import run_snippet


def test(page, base_url):
    output = run_snippet(page, base_url, "prgh-mobius/lesson10/02-bank_example.json")
    assert "No such file or directory" not in output, (
        "bank.py's open('konton.txt') failed — imported-module file I/O is broken:\n"
        + output
    )
    assert "OSError" not in output, output
