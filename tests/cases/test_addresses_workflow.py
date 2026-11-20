"""
The whole life of an example's address, with dir_to_snippets.py and
create_index.py run for real against a copy of tests/fixtures/example_tree
in a temporary directory (nothing under snippets/ is touched):

  - bulk-adding a directory needs no naming: every example gets an address
  - renaming a directory gives the example a name; the old address follows
  - renaming again, renumbering and moving keep every earlier address
  - an example inserted in the middle (03b-...) lands in the right place
    and disturbs no address
  - two examples that would get the same name both stay without it
  - å/ä/ö and spaces are taken out of names; a name cannot be a number
  - shifting unnamed examples up is noticed and reported, not followed
  - an address is never handed to another example, even after its own
    example was removed

Not a browser test; it runs here so that CI covers it.
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import create_index  # noqa: E402
import dir_to_snippets  # noqa: E402
import snippet_addresses as sa  # noqa: E402

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "example_tree"


class Site:
    """A source tree and a snippets folder in a temporary directory."""

    def __init__(self, tmp):
        self.source = Path(tmp) / "source"
        self.root = Path(tmp) / "snippets"
        shutil.copytree(FIXTURE, self.source)
        self.root.mkdir()

    def convert(self):
        """Runs dir_to_snippets.py and create_index.py; returns (output, exit status)."""
        saved = (dir_to_snippets.SNIPPETS_ROOT, create_index.INDEX_PATH,
                 create_index.SNIPPET_ROOT, sys.argv)
        dir_to_snippets.SNIPPETS_ROOT = str(self.root)
        create_index.SNIPPET_ROOT = str(self.root)
        create_index.INDEX_PATH = str(self.root / "index.json")
        sys.argv = ["dir_to_snippets.py", str(self.source), "course"]
        out, status = io.StringIO(), 0
        try:
            with contextlib.redirect_stdout(out):
                dir_to_snippets.main()
                try:
                    create_index.main()
                except SystemExit as e:
                    status = e.code
        finally:
            (dir_to_snippets.SNIPPETS_ROOT, create_index.INDEX_PATH,
             create_index.SNIPPET_ROOT, sys.argv) = saved
        return out.getvalue(), status

    def leads_to(self, address):
        return sa.resolve(sa.load_book(str(self.root)), address)

    def handed_out(self, file):
        return sa.load_book(str(self.root))["snippets"][file]["addresses"][0]

    def order(self, folder):
        index = json.loads((self.root / "index.json").read_text(encoding="utf-8"))
        cat = next(c for c in index["categories"] if c["folder"] == folder)
        return [os.path.basename(s["file"]) for s in cat["snippets"]]

    def rename(self, old, new):
        (self.source / old).rename(self.source / new)

    def write(self, rel, text):
        path = self.source / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def test(page, base_url):
    assert sa.split_stem("03b-sortering") == ((3, "b"), "sortering")
    assert sa.split_stem("03") == ((3, ""), "")
    assert sa.split_stem("2d-lists") == (None, "2d-lists")
    assert sa.slug("Köer och  stackar (Åäö)") == "koer-och-stackar-aao"
    assert sa.short_name("03-example", ["example"]) is None
    assert sa.short_name("03-2", []) is None

    with tempfile.TemporaryDirectory() as tmp:
        site = Site(tmp)

        # ── Bulk add: no naming work, everything has an address ──────────
        out, status = site.convert()
        assert status == 0, out
        assert site.leads_to("course/ovn01/02-example") == "course/ovn01/02-example.json"
        assert site.handed_out("course/ovn01/02-example.json") == "course/ovn01/02-example"
        # A name that only one example in the lesson has becomes its address
        assert site.handed_out("course/ovn02/03-for_loops.json") == "course/ovn02/for_loops"
        assert site.leads_to("course/ovn02/03-for_loops.json") == "course/ovn02/03-for_loops.json"
        # ... but not one that two would get
        assert site.leads_to("course/ovn02/lists") is None
        assert site.handed_out("course/ovn02/01-lists.json") == "course/ovn02/01-lists"

        # From here on, these are the addresses that must never break
        first = sorted(sa.owners(sa.load_book(str(site.root))))
        (site.root / sa.FROZEN_NAME).write_text(
            "# frozen\n" + "".join(a + ".json\n" for a in first), encoding="utf-8")

        # ── Give an example a name: rename its directory ─────────────────
        site.rename("ovn01/02-example", "ovn01/02-sortering")
        out, status = site.convert()
        assert status == 0, out
        assert "Renamed: course/ovn01/02-example.json -> course/ovn01/02-sortering.json" in out, out
        assert site.handed_out("course/ovn01/02-sortering.json") == "course/ovn01/sortering"
        for address in ("course/ovn01/sortering", "course/ovn01/02-sortering",
                        "course/ovn01/02-example", "course/ovn01/02-example.json"):
            assert site.leads_to(address) == "course/ovn01/02-sortering.json", address
        assert site.order("course/ovn01") == ["01-example.json", "02-sortering.json", "03-example.json"]

        # ── Rename it again, and give it another number at the same time ─
        site.rename("ovn01/02-sortering", "ovn01/07-quicksort")
        out, status = site.convert()
        assert status == 0, out
        assert site.handed_out("course/ovn01/07-quicksort.json") == "course/ovn01/quicksort"
        for address in ("course/ovn01/sortering", "course/ovn01/02-example", "course/ovn01/quicksort"):
            assert site.leads_to(address) == "course/ovn01/07-quicksort.json", address

        # A named example can be renumbered and edited in one go: its name
        # is what identifies it
        site.rename("ovn01/07-quicksort", "ovn01/02-quicksort")
        site.write("ovn01/02-quicksort/main.py", "print('edited')\n")
        out, status = site.convert()
        assert status == 0, out
        assert site.leads_to("course/ovn01/02-example") == "course/ovn01/02-quicksort.json"

        # ── Insert an example in the middle of the lesson ────────────────
        site.write("ovn01/02b-binarsokning/main.py", "print('new')\n")
        out, status = site.convert()
        assert status == 0, out
        assert site.order("course/ovn01") == [
            "01-example.json", "02-quicksort.json", "02b-binarsokning.json", "03-example.json"]
        assert site.handed_out("course/ovn01/02b-binarsokning.json") == "course/ovn01/binarsokning"
        assert site.leads_to("course/ovn01/03-example") == "course/ovn01/03-example.json"

        # ── Names: å/ä/ö and spaces, numbers, collisions ─────────────────
        site.write("ovn02/04-Köer och stackar/main.py", "print('queue')\n")
        site.write("ovn02/05-02/main.py", "print('a number is no name')\n")
        site.write("ovn02/06-for_loops/main.py", "print('same name as 03')\n")
        site.write("ovn02/07-01-lists/main.py", "print('looks like an old address')\n")
        out, status = site.convert()
        assert status == 0, out
        assert site.handed_out("course/ovn02/04-Köer och stackar.json") == "course/ovn02/koer-och-stackar"
        assert site.leads_to("course/ovn02/04-Köer och stackar") == "course/ovn02/04-Köer och stackar.json"
        assert site.handed_out("course/ovn02/05-02.json") == "course/ovn02/05-02"
        # for_loops stays with the example that had it first
        assert site.leads_to("course/ovn02/for_loops") == "course/ovn02/03-for_loops.json"
        assert site.handed_out("course/ovn02/06-for_loops.json") == "course/ovn02/06-for_loops"
        # "01-lists" is the address of 01-lists.json and stays so
        assert site.leads_to("course/ovn02/01-lists") == "course/ovn02/01-lists.json"
        assert site.handed_out("course/ovn02/07-01-lists.json") == "course/ovn02/07-01-lists"
        assert "does not get the address course/ovn02/01-lists" in out, out

        # ── A rename that cannot be recognised is reported, then fixed ───
        site.rename("ovn01/03-example", "ovn01/03-moduler")
        site.write("ovn01/03-moduler/main.py", "print('renamed and rewritten')\n")
        out, status = site.convert()
        assert status == 1 and "No longer leads anywhere: course/ovn01/03-example" in out, out
        message = sa.redirect(str(site.root), "course/ovn01/03-example", "course/ovn01/moduler")
        assert not message.startswith("Error"), message
        assert site.leads_to("course/ovn01/03-example.json") == "course/ovn01/03-moduler.json"
        assert sa.check(str(site.root)) == []
        # An address cannot be taken from an example that still exists
        message = sa.redirect(str(site.root), "course/ovn01/quicksort", "course/ovn01/moduler")
        assert message.startswith("Error"), message

        # ── Shifting unnamed examples up is noticed ──────────────────────
        # ovn02: what was in 01-lists goes to 02-lists, and 01-lists gets
        # new content: the old address of 02-lists now shows another example.
        old_first = (site.source / "ovn02/01-lists/main.py").read_text(encoding="utf-8")
        site.write("ovn02/02-lists/main.py", old_first)
        site.write("ovn02/01-lists/main.py", "print('a new first example')\n")
        out, status = site.convert()
        assert status == 1, out
        assert "course/ovn02/02-lists.json now has the content that course/ovn02/01-lists.json had" in out, out
        out, status = site.convert()
        assert status == 1, "the warning must stay until it is dealt with:\n" + out
        sa.update_book(str(site.root), accept=True)
        out, status = site.convert()
        assert status == 0, out

        # ── Removed on purpose; its address is not reused ────────────────
        shutil.rmtree(site.source / "ovn01/01-example")
        out, status = site.convert()
        assert status == 1 and "No longer leads anywhere: course/ovn01/01-example" in out, out
        message = sa.retire(str(site.root), "course/ovn01/01-example")
        assert not message.startswith("Error"), message
        assert site.leads_to("course/ovn01/01-example") == ""
        site.write("ovn01/01-example/main.py", "print('another example, same directory name')\n")
        out, status = site.convert()
        assert status == 1 and "Has no address: course/ovn01/01-example.json" in out, out
        assert site.leads_to("course/ovn01/01-example") == ""
        site.rename("ovn01/01-example", "ovn01/01-valkommen")
        out, status = site.convert()
        assert status == 0, out
        assert site.handed_out("course/ovn01/01-valkommen.json") == "course/ovn01/valkommen"

        # ── Every address from the first day still leads to its example ──
        book = sa.load_book(str(site.root))
        files = set(sa.list_snippet_files(str(site.root)))
        for address in first:
            target = sa.resolve(book, address)
            assert target == "" or target in files, (address, target)
        assert site.leads_to("course/ovn01/02-example") == "course/ovn01/02-quicksort.json"
        assert site.leads_to("course/ovn01/03-example") == "course/ovn01/03-moduler.json"

    # ── The real content: the book is complete and the frozen list holds ─
    root = str(REPO_ROOT / "snippets")
    assert sa.check(root) == [], sa.check(root)
    frozen = sa.read_frozen(root)
    assert len(frozen) >= 505, len(frozen)
    book, files = sa.load_book(root), set(sa.list_snippet_files(root))
    for address in frozen:
        target = sa.resolve(book, address)
        assert target == "" or target in files, (address, target)
