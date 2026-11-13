#!/usr/bin/env python3
"""
fix_indent.py
Usage: python3 fix_indent.py [--dryrun]

Rewrites Python files whose indentation mixes tabs and spaces so that they
use spaces only. Python accepts some such mixes, but they break as soon as
somebody edits the file: the widget's editor indents new lines in one style,
and a block whose lines are indented differently is an error.

Run as a script, it fixes every .py file inside the snippet JSON files under
snippets/. dir_to_snippets.py and py_to_json.py call fix_mixed_indentation()
on what they read, so newly generated snippets are fixed on the way in and
the source files are left as they are.

Only mixed files are touched. Files indented with tabs only, or spaces only
(of any width), are left alone: the editor follows either.
"""

import argparse
import ast
import io
import json
import os
import re
import sys
import tokenize
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SNIPPETS_ROOT = os.path.join(SCRIPT_DIR, "snippets")

LEADING = re.compile(r"[ \t]*")
SKIPPED = (tokenize.COMMENT, tokenize.NL, tokenize.INDENT, tokenize.DEDENT,
           tokenize.NEWLINE, tokenize.ENDMARKER)


def space_unit(lines, skip):
    """
    Finds how many spaces one indentation level is in the parts of the file
    that are indented with spaces: the most common step in from a line ending
    in ':' to the line after it (the same rule as detectIndent in embed.js).

    Arguments:
        lines (list[str]): The file's lines.
        skip (set[int]): Indices of lines inside multi-line strings.

    Returns:
        int: Spaces per level, 4 if the file has no space-indented block.
    """
    steps = Counter()
    opener = None
    for i, line in enumerate(lines):
        if i in skip:
            opener = None
            continue
        code = re.sub(r"#.*$", "", line).rstrip()
        if not code.strip():
            continue
        lead = LEADING.match(code).group(0)
        if opener is not None and "\t" not in lead and "\t" not in opener:
            if len(lead) > len(opener):
                steps[len(lead) - len(opener)] += 1
        opener = lead if code.endswith(":") else None
    return steps.most_common(1)[0][0] if steps else 4


def fix_mixed_indentation(source):
    """
    Returns source with every line indented by spaces, one fixed number of
    spaces per block level, if its indentation mixes tabs and spaces.

    The result is only used if it is the same program: the syntax tree must
    be unchanged. Text inside multi-line strings is never touched.

    Arguments:
        source (str): Python source code.

    Returns:
        str: The rewritten source, or source itself if it does not mix tabs
        and spaces, cannot be parsed, or could not be rewritten safely.
    """
    lines = source.split("\n")
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        tree_before = ast.dump(ast.parse(source))
    except (SyntaxError, tokenize.TokenError, ValueError):
        return source

    # Lines that continue a multi-line string: their text is data, not layout.
    in_string = set()
    for tok in tokens:
        if tok.type == tokenize.STRING and tok.end[0] > tok.start[0]:
            in_string.update(range(tok.start[0], tok.end[0]))   # 0-based: start+1 .. end

    leads = [LEADING.match(line).group(0) for i, line in enumerate(lines)
             if line.strip() and i not in in_string]
    if not (any("\t" in lead for lead in leads) and any(" " in lead for lead in leads)):
        return source

    # Block depth of each line that starts a statement, and of each line that
    # only holds a comment (the depth of the statement that follows it).
    depth = 0
    statement_depth = {}
    comment_lines = []
    at_line_start = True
    for tok in tokens:
        if tok.type == tokenize.INDENT:
            depth += 1
        elif tok.type == tokenize.DEDENT:
            depth -= 1
        elif tok.type == tokenize.NEWLINE:
            at_line_start = True
        elif tok.type == tokenize.COMMENT:
            if not lines[tok.start[0] - 1][:tok.start[1]].strip():
                comment_lines.append(tok.start[0] - 1)
        elif tok.type not in SKIPPED and at_line_start:
            statement_depth[tok.start[0] - 1] = depth
            at_line_start = False
    statement_rows = sorted(statement_depth)
    for row in comment_lines:
        if row in statement_depth:
            continue
        following = [r for r in statement_rows if r > row]
        statement_depth[row] = statement_depth[following[0]] if following else 0

    unit = space_unit(lines, in_string)
    fixed = []
    for i, line in enumerate(lines):
        if i in in_string:
            fixed.append(line)
        elif not line.strip():
            fixed.append("")
        elif i in statement_depth:
            fixed.append(" " * (unit * statement_depth[i]) + line.lstrip(" \t"))
        else:
            # A continuation line inside brackets: keep its alignment.
            lead = LEADING.match(line).group(0)
            fixed.append(lead.expandtabs(unit) + line[len(lead):])
    result = "\n".join(fixed)

    try:
        if ast.dump(ast.parse(result)) != tree_before:
            return source
    except SyntaxError:
        return source
    return result


def fix_snippet_file(path, dryrun):
    """
    Fixes the .py files inside one snippet JSON file, rewriting it if any
    of them changed.

    Arguments:
        path (str): Path to the snippet JSON file.
        dryrun (bool): If True, report but do not write.

    Returns:
        list[str]: Names of the files inside the snippet that were fixed.
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        snippet = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(snippet, dict):
        return []

    changed = []
    for entry in snippet.get("files", []):
        name = entry.get("name", "")
        content = entry.get("content")
        if not name.endswith(".py") or not isinstance(content, str):
            continue
        fixed = fix_mixed_indentation(content)
        if fixed != content:
            entry["content"] = fixed
            changed.append(name)

    if changed and not dryrun:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snippet, f, ensure_ascii=False, indent=2)
            if text.endswith("\n"):
                f.write("\n")
    return changed


def main():
    parser = argparse.ArgumentParser(
        description="Replace mixed tab/space indentation in the snippets with spaces.")
    parser.add_argument("--dryrun", action="store_true",
                        help="print what would be fixed without writing")
    args = parser.parse_args()

    count = 0
    for dirpath, dirnames, filenames in os.walk(SNIPPETS_ROOT):
        dirnames.sort()
        for filename in sorted(filenames):
            if not filename.endswith(".json") or filename == "index.json":
                continue
            path = os.path.join(dirpath, filename)
            for name in fix_snippet_file(path, args.dryrun):
                count += 1
                print(("Would fix " if args.dryrun else "Fixed ")
                      + os.path.relpath(path, SCRIPT_DIR) + ": " + name)
    print(str(count) + " file(s) with mixed indentation"
          + (" found." if args.dryrun else " fixed."))


if __name__ == "__main__":
    sys.exit(main())
