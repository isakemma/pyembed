#!/usr/bin/env python3
"""
dir_to_snippets.py
Usage: python3 dir_to_snippets.py INPUT_DIR OUTPUT_SUBDIR [--dryrun]

Walks INPUT_DIR looking for leaf directories (directories that contain no
subdirectories). Every leaf directory becomes one snippet JSON file
(same format as snippets/prgh/l6-7_random.json), with one "files" entry
per file found in that leaf directory.

The directory structure of INPUT_DIR is replicated under
snippets/OUTPUT_SUBDIR, with each leaf directory turned into a sibling
.json file instead of a directory, e.g.:

    INPUT_DIR/DD1320/01/  (task1.py, task2.py)
        -> snippets/OUTPUT_SUBDIR/DD1320/01.json

Any .json files already present under snippets/OUTPUT_SUBDIR that no
longer correspond to a leaf directory in INPUT_DIR are deleted, and any
directories left empty by those deletions are removed as well.

Pass --dryrun to print what would be written/deleted without touching
the filesystem.
"""

import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SNIPPETS_ROOT = os.path.join(SCRIPT_DIR, "snippets")


def read_file(path):
    """
    Reads the content of a file as text.

    Arguments:
        path (str): Path to the file.

    Returns:
        str: The file content as a string.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_snippet(title, filenames, leaf_dir):
    """
    Builds a snippet dictionary in the widget JSON format.

    Arguments:
        title (str): The snippet title.
        filenames (list[str]): Sorted file names found in the leaf directory.
        leaf_dir (str): Path to the leaf directory the files live in.

    Returns:
        dict: A snippet dictionary with 'title' and 'files' keys.
    """
    return {
        "title": title,
        "files": [
            {"name": name, "content": read_file(os.path.join(leaf_dir, name))}
            for name in filenames
        ],
    }


def find_leaves(input_dir):
    """
    Walks input_dir and finds every leaf directory (a directory with no
    subdirectories) that contains at least one file.

    Arguments:
        input_dir (str): Root directory to scan.

    Returns:
        list[tuple[str, str]]: Pairs of (relative_path, absolute_path) for
        each leaf directory, relative_path using '/' separators.
    """
    leaves = []
    for dirpath, dirnames, filenames in os.walk(input_dir):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        filenames = sorted(f for f in filenames if not f.startswith("."))

        if dirnames:
            if filenames:
                print(
                    "Warning: ignoring loose file(s) in non-leaf directory: "
                    + dirpath
                )
            continue

        if not filenames:
            continue

        rel = os.path.relpath(dirpath, input_dir).replace(os.sep, "/")
        leaves.append((rel, dirpath, filenames))

    leaves.sort(key=lambda item: item[0])
    return leaves


def existing_json_files(output_root):
    """
    Lists all .json files currently present under output_root.

    Arguments:
        output_root (str): Directory to scan.

    Returns:
        set[str]: Paths relative to output_root, using '/' separators.
    """
    found = set()
    if not os.path.isdir(output_root):
        return found

    for dirpath, dirnames, filenames in os.walk(output_root):
        for name in filenames:
            if name.endswith(".json"):
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, output_root).replace(os.sep, "/")
                found.add(rel)
    return found


def remove_empty_dirs(root, dryrun):
    """
    Removes directories under root (and root itself) that are empty,
    walking bottom-up.

    Arguments:
        root (str): Directory tree to clean up.
        dryrun (bool): If True, only print what would be removed.

    Returns:
        None
    """
    if not os.path.isdir(root):
        return

    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        if not dirnames and not filenames:
            if dryrun:
                print("Would remove empty directory: " + dirpath)
            else:
                os.rmdir(dirpath)
                print("Removed empty directory: " + dirpath)


def main():
    """
    Entry point. Reads arguments, scans INPUT_DIR, writes/updates snippet
    JSON files under snippets/OUTPUT_SUBDIR, and deletes stale ones.

    Arguments:
        None (reads from sys.argv)

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description="Convert a directory tree of source files into snippet JSON files."
    )
    parser.add_argument("input_dir", help="Directory to scan for leaf directories.")
    parser.add_argument(
        "output_subdir", help="Subdirectory under snippets/ to write the JSON files to."
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Print what would be done without writing or deleting anything.",
    )
    args = parser.parse_args()

    input_dir = args.input_dir
    if not os.path.isdir(input_dir):
        print("Error: input directory not found: " + input_dir)
        sys.exit(1)

    output_root = os.path.join(SNIPPETS_ROOT, args.output_subdir)

    leaves = find_leaves(input_dir)
    if not leaves:
        print("No leaf directories with files found under " + input_dir)

    expected = set()
    for rel, leaf_dir, filenames in leaves:
        rel_json = rel + ".json"
        expected.add(rel_json)
        title = os.path.basename(rel)
        out_path = os.path.join(output_root, *rel_json.split("/"))

        if args.dryrun:
            print(
                "Would write "
                + out_path
                + " (title="
                + title
                + ", files="
                + ", ".join(filenames)
                + ")"
            )
            continue

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        snippet = build_snippet(title, filenames, leaf_dir)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(snippet, f, ensure_ascii=False, indent=2)
        print("Written " + out_path)

    existing = existing_json_files(output_root)
    stale = sorted(existing - expected)
    for rel_json in stale:
        full = os.path.join(output_root, *rel_json.split("/"))
        if args.dryrun:
            print("Would delete " + full)
        else:
            os.remove(full)
            print("Deleted " + full)

    remove_empty_dirs(output_root, args.dryrun)


if __name__ == "__main__":
    main()
