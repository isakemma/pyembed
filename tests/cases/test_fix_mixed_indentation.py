"""
fix_indent.fix_mixed_indentation: Python files that mix tabs and spaces
are rewritten with spaces only, as the same program; everything else is
returned untouched. Also: no snippet in the repo may mix the two (run
`python3 fix_indent.py` if this fails after adding snippets by hand).

Not a browser test; it runs here so that CI covers it.
"""

import ast
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fix_indent import fix_mixed_indentation  # noqa: E402

MIXED = (
    "def f(x):\n"
    "  try:\n"
    "\t  y = int(x)   # a tab, then two spaces\n"
    "\t  return y\n"
    "  except ValueError: \t# tab inside the line stays\n"
    "\t  text = '''kept\n"
    "\t as it is'''\n"
    "\t  return [1,\n"
    "\t          2]\n"
    "\t\n"
    "print(f('1'))\n"
)
FIXED = (
    "def f(x):\n"
    "  try:\n"
    "    y = int(x)   # a tab, then two spaces\n"
    "    return y\n"
    "  except ValueError: \t# tab inside the line stays\n"
    "    text = '''kept\n"
    "\t as it is'''\n"
    "    return [1,\n"
    "            2]\n"
    "\n"
    "print(f('1'))\n"
)
UNTOUCHED = [
    "def f():\n\treturn 1\n",                     # tabs only
    "def f():\n    return 1\n",                   # spaces only
    "def f():\n  if 1:\n      return 1\n",        # odd widths, but spaces only
    "def f(:\n\t  return 1\n  x\n",               # not valid Python
    "x = '''\n\ttab\n  spaces\n'''\n",            # only inside a string
]


def test(page, base_url):
    fixed = fix_mixed_indentation(MIXED)
    assert fixed == FIXED, fixed
    assert ast.dump(ast.parse(fixed)) == ast.dump(ast.parse(MIXED))
    assert fix_mixed_indentation(fixed) == fixed

    for source in UNTOUCHED:
        assert fix_mixed_indentation(source) == source, source

    still_mixed = []
    for path in sorted((REPO_ROOT / "snippets").rglob("*.json")):
        if path.name == "index.json":
            continue
        snippet = json.loads(path.read_text(encoding="utf-8"))
        for entry in snippet.get("files", []) if isinstance(snippet, dict) else []:
            content = entry.get("content")
            if entry.get("name", "").endswith(".py") and isinstance(content, str):
                if fix_mixed_indentation(content) != content:
                    still_mixed.append(f"{path.relative_to(REPO_ROOT)}: {entry['name']}")
    assert not still_mixed, still_mixed
