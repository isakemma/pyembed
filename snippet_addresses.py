#!/usr/bin/env python3
"""
snippet_addresses.py
Usage: python3 snippet_addresses.py check
       python3 snippet_addresses.py redirect OLD_ADDRESS CURRENT_ADDRESS
       python3 snippet_addresses.py retire ADDRESS
       python3 snippet_addresses.py accept

Keeps snippets/addresses.json, the list of every address a snippet has ever
had. An address is what stands after "viewer.html?" in a link, for example
prgh-lectures/frl07/sortering: the snippet's folder, then its name.

A snippet gets its addresses from its file name (which dir_to_snippets.py
takes from the source directory's name):

    frl07/03-sortering.json   ->  frl07/sortering      (the one handed out)
                                  frl07/03-sortering   (works too)
    frl07/03-example.json     ->  frl07/03-example     ("example" is no name)
    lecture07/03.json         ->  lecture07/03

The digits in front only decide the order within the lesson. An address that
has been in the list is never given to another snippet, so links keep
leading to the same example when it is renamed, renumbered or moved; the old
addresses follow it. create_index.py updates the list each time it runs.

The commands are for what create_index.py cannot work out by itself:

    check     Verify that every address (also those in legacy-addresses.txt)
              leads to a snippet that exists. Changes nothing.
    redirect  Make an address whose snippet is gone lead to the snippet that
              CURRENT_ADDRESS leads to (after a rename that was not detected).
    retire    Mark an address as removed on purpose: the viewer then says
              that the example has been removed.
    accept    Record the snippets' current content after create_index.py has
              warned that examples seem to have been renumbered.

Nothing here knows about particular courses: the list, and the words that do
not count as names, are data in the snippets folder.
"""

import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SNIPPETS_ROOT = os.path.join(SCRIPT_DIR, "snippets")

BOOK_NAME = "addresses.json"
FROZEN_NAME = "legacy-addresses.txt"
# JSON files in the snippets folder that are not snippets
NOT_SNIPPETS = ("index.json", BOOK_NAME)

ABOUT = (
    "Every address each snippet has ever had; the first one is handed out in "
    "links. Addresses are never reused, so old links keep working. Written by "
    "create_index.py and snippet_addresses.py: see Addresses in README.md."
)
# Two or more digits (and at most one letter, as in 03b) in front of a file
# name are its place in the lesson, not part of its name. One digit is not
# enough, so that "2d-lists" stays a name.
ORDER_PREFIX = re.compile(r"^(\d{2,})([a-z]?)(?:[-_]+(.*))?$")


def split_stem(stem):
    """
    Splits a snippet's file name (without .json) into its place in the
    lesson and the rest.

    Arguments:
        stem (str): File name without extension, e.g. '03b-sortering'.

    Returns:
        tuple: (order, rest). order is (number, letter), e.g. (3, 'b'), or
        None if the name does not start with digits; rest is what follows
        ('' for a name that is only a number).
    """
    match = ORDER_PREFIX.match(stem)
    if not match:
        return None, stem
    return (int(match.group(1)), match.group(2)), match.group(3) or ""


def order_key(stem):
    """
    Sort key that puts numbered snippets in number order (03, 03b, 04) and
    the ones without a number after them, without reordering those.

    Arguments:
        stem (str): File name without extension.

    Returns:
        tuple: Key for sorted() or list.sort().
    """
    order, _ = split_stem(stem)
    if order is None:
        return (1, 0, "")
    return (0, order[0], order[1])


def slug(text):
    """
    Turns a name into something that survives in a URL, a QR code and on
    paper: lower case, a-z, digits, '-' and '_' only. å, ä, ö and other
    accented letters lose their accents; anything else becomes '-'.

    Arguments:
        text (str): The name as written in a file or directory name.

    Returns:
        str: The name for the address, '' if nothing is left.
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9_]+", "-", text.lower())
    return text.strip("-_")


def short_name(stem, not_names):
    """
    The name a snippet's file name gives it, if it gives one.

    Arguments:
        stem (str): File name without extension, e.g. '03-sortering'.
        not_names (list[str]): Words that do not count as names (the
            "not_names" list in addresses.json, e.g. 'example').

    Returns:
        str or None: 'sortering' for '03-sortering'; None for '03',
        '03-example' and '03-2' (a name must contain a letter, so that it
        cannot be mistaken for a number).
    """
    _, rest = split_stem(stem)
    name = slug(rest)
    if not name or not re.search(r"[a-z]", name) or name in not_names:
        return None
    return name


def fingerprint(path):
    """
    A short checksum of a snippet's files (names and content, not its
    title), used to recognise a snippet that has been renamed or moved.

    Arguments:
        path (str): Path to the snippet JSON file.

    Returns:
        str: 12 hex digits, '' if the file cannot be read as a snippet.
    """
    try:
        with open(path, encoding="utf-8") as f:
            snippet = json.load(f)
        files = [[entry.get("name", ""), entry.get("content", "")]
                 for entry in snippet.get("files", [])]
    except (OSError, ValueError, AttributeError):
        return ""
    text = json.dumps(files, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def list_snippet_files(root):
    """
    Lists the snippet JSON files under root.

    Arguments:
        root (str): The snippets folder.

    Returns:
        list[str]: Paths relative to root with '/' separators, sorted.
    """
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in filenames:
            if not name.endswith(".json"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/")
            if rel in NOT_SNIPPETS:
                continue
            found.append(rel)
    return sorted(found)


def load_book(root):
    """
    Reads addresses.json.

    Arguments:
        root (str): The snippets folder.

    Returns:
        dict: {'not_names': [...], 'snippets': {file: {'addresses': [...],
        'content': fingerprint}}, 'retired': [...]}; an empty one if the
        file does not exist yet.
    """
    path = os.path.join(root, BOOK_NAME)
    book = {}
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            book = json.load(f)
    book.setdefault("not_names", ["example"])
    book.setdefault("snippets", {})
    book.setdefault("retired", [])
    return book


def save_book(root, book):
    """
    Writes addresses.json with one snippet per line, sorted, so that a
    change shows up in `git diff` as the lines of the snippets concerned.

    Arguments:
        root (str): The snippets folder.
        book (dict): As returned by load_book().

    Returns:
        None
    """
    def dump(value):
        return json.dumps(value, ensure_ascii=False)

    lines = ["{", '  "about": ' + dump(ABOUT) + ",",
             '  "not_names": ' + dump(book["not_names"]) + ",",
             '  "snippets": {']
    entries = sorted(book["snippets"].items())
    for i, (file, entry) in enumerate(entries):
        comma = "," if i < len(entries) - 1 else ""
        lines.append("    " + dump(file) + ": " + dump(entry) + comma)
    lines += ["  },", '  "retired": ' + dump(sorted(book["retired"])), "}"]
    with open(os.path.join(root, BOOK_NAME), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def normalize(address):
    """
    Brings what can stand in a link to the form used in addresses.json:
    no '.json' at the end, no '/' at either end.

    Arguments:
        address (str): E.g. 'lecture-examples/lecture07/03.json'.

    Returns:
        str: E.g. 'lecture-examples/lecture07/03'.
    """
    address = address.strip().strip("/")
    if address.endswith(".json"):
        address = address[:-len(".json")]
    return address


def owners(book):
    """
    Arguments:
        book (dict): As returned by load_book().

    Returns:
        dict: Maps each address in the book to the snippet file it leads to.
    """
    return {address: file
            for file, entry in book["snippets"].items()
            for address in entry["addresses"]}


def resolve(book, address):
    """
    Looks an address up the way the viewer does (site.js): exactly as
    written first, then without regard to upper and lower case.

    Arguments:
        book (dict): As returned by load_book().
        address (str): An address, with or without '.json'.

    Returns:
        str or None: The snippet file, '' if the address is retired, None
        if the book does not know it.
    """
    address = normalize(address)
    owner = owners(book)
    if address in owner:
        return owner[address]
    if address in book["retired"]:
        return ""
    lowered = address.lower()
    for known, file in owner.items():
        if known.lower() == lowered:
            return file
    return None


def update_book(root, accept=False):
    """
    Brings addresses.json up to date with the snippet files under root.

    A new file gets its addresses. A file that is gone, while a new file has
    the same content or claims one of its addresses, has been renamed or
    moved: the new file takes over all its addresses. Addresses are only
    ever added, never moved from one existing snippet to another.

    Arguments:
        root (str): The snippets folder.
        accept (bool): Record the current content also of snippets that
            look renumbered (see below).

    Returns:
        dict: What happened, each a list:
            'new'        files that got their first addresses
            'renamed'    (old file, new file)
            'named'      (file, address) for addresses added to known files
            'renumbered' (file, other file): file now has the content that
                         other file had, so links to it show another example
            'conflicts'  (file, address, owner): file cannot have address
                         because it belongs to owner
            'gone'       files in the book that no longer exist
    """
    book = load_book(root)
    entries = book["snippets"]
    files = list_snippet_files(root)
    prints = {file: fingerprint(os.path.join(root, *file.split("/"))) for file in files}
    report = {key: [] for key in
              ("new", "renamed", "named", "renumbered", "conflicts", "gone")}

    def folder(file):
        return file.rsplit("/", 1)[0] if "/" in file else ""

    def stem_address(file):
        return file[:-len(".json")]

    def name_address(file):
        name = short_name(os.path.basename(stem_address(file)), book["not_names"])
        if name is None:
            return None
        return (folder(file) + "/" if folder(file) else "") + name

    before = {file: entry.get("content", "") for file, entry in entries.items()}
    known = [file for file in files if file in entries]
    new = [file for file in files if file not in entries]
    gone = [file for file in entries if file not in prints]

    # ── Renamed or moved: a file is gone and a new one continues it ──────
    def adopt(old, file):
        entries[file] = entries.pop(old)
        gone.remove(old)
        new.remove(file)
        report["renamed"].append((old, file))

    for old in list(gone):
        same = [file for file in new if prints[file] and prints[file] == before[old]]
        near = [file for file in same if folder(file) == folder(old)]
        candidates = near or same
        if len(candidates) == 1:
            adopt(old, candidates[0])
    for file in list(new):
        if not gone:
            break
        owner = owners(book)
        for address in (name_address(file), stem_address(file)):
            if owner.get(address) in gone:
                adopt(owner[address], file)
                break

    for file in new:
        entries[file] = {"addresses": [], "content": prints[file]}
        report["new"].append(file)

    # ── Renumbered: a known file now has what its neighbour had ──────────
    # Its links have silently started to show another example. That cannot
    # be repaired from here (two examples would need the same address), so
    # it is reported, again on every run, until it is undone or accepted.
    changed = [file for file in known if prints[file] != before[file]]
    for file in changed:
        donors = [other for other, content in before.items()
                  if other != file and content and content == prints[file]
                  and folder(other) == folder(file)
                  and prints.get(other) != content]
        if donors and not accept:
            report["renumbered"].append((file, donors[0]))
    # What the book remembers of the files involved is left as it was, so
    # that the next run sees the same thing.
    keep = {file for pair in report["renumbered"] for file in pair}
    for file in changed:
        if file not in keep:
            entries[file]["content"] = prints[file]

    # ── Addresses from the file names ────────────────────────────────────
    # First each file's own name without .json (what old links contain),
    # then the short names; a short name that several files in a folder
    # would get is given to none of them.
    owner = owners(book)
    retired = set(book["retired"])

    fresh = set(report["new"]) | {file for _, file in report["renamed"]}

    def claim(file, address, alone=True):
        if owner.get(address) == file:
            return True
        if address in owner or address in retired:
            # Said once, when the file is first seen, except when the file
            # is left with no address at all (check() reports that).
            if file in fresh:
                report["conflicts"].append(
                    (file, address, owner.get(address, "an example that was removed")))
            return False
        if not alone:
            return False
        owner[address] = file
        if file not in report["new"]:
            report["named"].append((file, address))
        return True

    own = defaultdict(list)
    for file in files:
        if claim(file, stem_address(file)):
            own[file].append(stem_address(file))
    wanted = defaultdict(list)
    for file in files:
        if name_address(file) and name_address(file) != stem_address(file):
            wanted[name_address(file)].append(file)
    for address, claimants in wanted.items():
        for file in claimants:
            if claim(file, address, alone=len(claimants) == 1):
                own[file].insert(0, address)

    for file in files:
        rest = [a for a in entries[file]["addresses"] if a not in own[file]]
        entries[file]["addresses"] = own[file] + rest

    report["gone"] = sorted(gone)
    save_book(root, book)
    return report


def read_frozen(root):
    """
    Reads legacy-addresses.txt, the addresses that existed before snippets
    got names.

    Arguments:
        root (str): The snippets folder.

    Returns:
        list[str]: The addresses as written in the file ([] if no file).
    """
    path = os.path.join(root, FROZEN_NAME)
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f
                if line.strip() and not line.startswith("#")]


def check(root):
    """
    Verifies that every address leads somewhere.

    Arguments:
        root (str): The snippets folder.

    Returns:
        list[str]: One line per problem; empty if all is well.
    """
    book = load_book(root)
    files = set(list_snippet_files(root))
    problems = []
    for file, entry in sorted(book["snippets"].items()):
        if file not in files:
            problems.append(
                "No longer leads anywhere: " + ", ".join(entry["addresses"])
                + "\n    (" + file + " is gone. Renamed? Then: python3 snippet_addresses.py"
                + " redirect " + (entry["addresses"] or ["OLD"])[0] + " ITS_NEW_ADDRESS"
                + "\n     Removed on purpose? Then: python3 snippet_addresses.py retire "
                + (entry["addresses"] or ["OLD"])[0] + ")")
        elif not entry["addresses"]:
            problems.append("Has no address: " + file
                            + "\n    (its file name is the address of an earlier example;"
                            + " give it another name)")
    for file in sorted(files - set(book["snippets"])):
        problems.append("Not in " + BOOK_NAME + " yet: " + file
                        + "\n    (run python3 create_index.py)")
    for address in read_frozen(root):
        target = resolve(book, address)
        if target is None:
            problems.append("In " + FROZEN_NAME + " but not in " + BOOK_NAME + ": " + address)
    return problems


def redirect(root, old, current):
    """
    Makes the address old lead to the snippet that current leads to.
    Refuses if old still leads to a snippet that exists.

    Arguments:
        root (str): The snippets folder.
        old (str): Address whose snippet file is gone.
        current (str): Address of the snippet it should lead to.

    Returns:
        str: Message saying what was done or why not.
    """
    book = load_book(root)
    files = set(list_snippet_files(root))
    old, owner = normalize(old), owners(book)
    target = resolve(book, current)
    if not target or target not in files:
        return "Error: " + current + " does not lead to a snippet that exists."
    source = owner.get(old)
    if source in files:
        return ("Error: " + old + " leads to " + source + ", which exists. "
                "An address is never moved away from a snippet that is still there.")
    moved = [old]
    if source is not None:
        # The other addresses of the snippet that is gone come along
        moved = book["snippets"].pop(source)["addresses"]
    if old in book["retired"]:
        book["retired"].remove(old)
    book["snippets"][target]["addresses"] += moved
    save_book(root, book)
    return "Now leading to " + target + ": " + ", ".join(moved)


def retire(root, address):
    """
    Marks an address as removed on purpose. Only possible when its snippet
    file is gone.

    Arguments:
        root (str): The snippets folder.
        address (str): The address to retire.

    Returns:
        str: Message saying what was done or why not.
    """
    book = load_book(root)
    files = set(list_snippet_files(root))
    address = normalize(address)
    source = owners(book).get(address)
    if source is None:
        return "Error: " + address + " is not in " + BOOK_NAME + "."
    if source in files:
        return "Error: " + address + " leads to " + source + ", which exists."
    retired = book["snippets"].pop(source)["addresses"]
    book["retired"] += retired
    save_book(root, book)
    return "Retired: " + ", ".join(retired)


def print_report(report):
    """
    Prints what update_book() did, and what the user has to decide.

    Arguments:
        report (dict): As returned by update_book().

    Returns:
        bool: True if something needs attention.
    """
    for old, file in report["renamed"]:
        print("  Renamed: " + old + " -> " + file + " (its old addresses still work)")
    for file, address in report["named"]:
        print("  New address: " + address + " -> " + file)
    for file, address, owner in report["conflicts"]:
        print("  NOTE: " + file + " does not get the address " + address
              + ": it belongs to " + owner + ".")
    for file, other in report["renumbered"]:
        print("  WARNING: " + file + " now has the content that " + other + " had.")
    if report["renumbered"]:
        print(
            "  Renumbering makes existing links and QR codes show another example.\n"
            "  To insert an example, give the new one a number that fits in between\n"
            "  (03b-name) and leave the others alone. Undo the renumbering, or run\n"
            "  `python3 snippet_addresses.py accept` if this is what you want.")
    return bool(report["renumbered"])


def main():
    """
    Entry point: runs the command given on the command line (see the top
    of this file).

    Arguments:
        None (reads from sys.argv)

    Returns:
        int: Exit status, 0 if all is well.
    """
    args = sys.argv[1:]
    if args == ["check"]:
        problems = check(SNIPPETS_ROOT)
        for problem in problems:
            print(problem)
        count = len(owners(load_book(SNIPPETS_ROOT)))
        print(str(count) + " addresses, " + str(len(problems)) + " problem(s).")
        return 1 if problems else 0
    if len(args) == 3 and args[0] == "redirect":
        message = redirect(SNIPPETS_ROOT, args[1], args[2])
    elif len(args) == 2 and args[0] == "retire":
        message = retire(SNIPPETS_ROOT, args[1])
    elif args == ["accept"]:
        update_book(SNIPPETS_ROOT, accept=True)
        message = "Recorded the current content of every snippet."
    else:
        print(__doc__.strip().split("\n\n")[0])
        return 1
    print(message)
    return 1 if message.startswith("Error") else 0


if __name__ == "__main__":
    sys.exit(main())
