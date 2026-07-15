# Python Snippet Widget

A lightweight, static, embeddable Python code runner styled after IDLE. Visitors can edit and run Python directly in the browser — no server required. Python executes via [Skulpt](https://skulpt.org) (Python compiled to JavaScript) and the editor is powered by [CodeMirror 6](https://codemirror.net).

---

## How embedding works

Embed a snippet on any page with a single `<iframe>`:

```html
<iframe
  src="https://USERNAME.github.io/REPO/viewer.html?src=basic-examples/hello.json"
  width="100%"
  height="540"
  style="border:none;border-radius:8px;"
  loading="lazy"
  allowfullscreen
></iframe>
```

- Replace `USERNAME` and `REPO` with your GitHub username and repository name
- The `src` parameter is relative to the `snippets/` folder
- Use the **</> Embed** button on any widget to get a ready-to-paste iframe

---

## Browsing snippets

Four pages are available for navigating snippets:

| URL | What it shows |
|-----|---------------|
| `gallery.html` | All courses and categories as clickable cards |
| `gallery.html?cat=basic-examples` | All snippets in a single category |
| `lecture.html?course=lectures&n=1` | All examples for a specific lesson inline |
| `viewer.html?src=basic-examples/hello.json` | A single snippet, full-page |

Change `n=1` to the lesson number you want.

---

## Categories and courses

All snippet-browsing metadata lives in `snippets/index.json`.

- **`categories`** — one entry per leaf folder under `snippets/`, e.g.:
  ```json
  { "id": "prgh-mobius-lesson01", "name": "Prgh Mobius – Lesson01", "folder": "prgh-mobius/lesson01", "snippets": [ ... ] }
  ```
  You normally don't hand-edit this — `create_index.py` rebuilds it from what's on disk (see [Utility scripts](#utility-scripts)).

- **`courses`** — groups a run of lesson categories (e.g. `prgh-mobius/lesson01` … `lesson12`) into one big card on `gallery.html`, and drives the lesson navigator on `lecture.html?course=<id>&n=<N>`:
  ```json
  { "id": "prgh-mobius", "label": "Prgh Möbius", "folderPrefix": "prgh-mobius/lesson" }
  ```
  **This is the one place to edit** when adding a new multi-lesson course. `folderPrefix` must match the start of each category's `folder` value (categories are matched with `folder.startsWith(folderPrefix)`, then the two-digit lesson number is read off the rest of the string).

Current courses:

| id | label | folderPrefix |
|----|-------|--------------|
| lectures | DD1310 – Lecture Examples | `lecture-examples/lecture` |
| mobius-dd100n | Möbius DD100N | `mobius-DD100N/lesson` |
| mobius-dd1310 | Möbius DD1310 | `mobius-DD1310/lektion` |
| tutorials-dd1310 | DD1310 Tutorials | `tutorials-DD1310/tutorial` |
| dd1320 | DD1320 – Automater | `DD1320/` |
| prgh-mobius | Prgh Möbius | `prgh-mobius/lesson` |

Categories that don't match any course's `folderPrefix` (e.g. `basic-examples`, `prgh`) show up as individual cards on `gallery.html` instead of being grouped.

---

## Snippet JSON format

Each snippet is a JSON file in the `snippets/` folder.

### Single file

```json
{
  "title": "Hello World",
  "description": "Optional subtitle shown below the title.",
  "files": [
    { "name": "main.py", "content": "print('Hello, world!')" }
  ]
}
```

### Multi-file project

```json
{
  "title": "My Project",
  "files": [
    { "name": "main.py",   "content": "from helper import greet\ngreet()" },
    { "name": "helper.py", "content": "def greet():\n    print('Hello!')" },
    { "name": "data.txt",  "content": "some data" }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `title` | No | Displayed as the widget heading |
| `description` | No | Displayed as a subtitle |
| `files` | Yes | Array of `{ name, content }` objects |

The first file named `main.py` is always the entry point executed when ▶ Run is clicked.

---

## Adding a new snippet

**Single snippet:**

1. Create a JSON file in the appropriate subfolder under `snippets/`
2. Run `create_index.py` to register it in `snippets/index.json`
3. Commit and push:

```bash
git add snippets/
git commit -m "Add new snippet"
git push
```

**Bulk import (a directory of source files, one snippet per leaf folder):**

1. Run `dir_to_snippets.py` to convert the directory tree into snippet JSON files (see [Utility scripts](#utility-scripts))
2. Run `create_index.py` to register the new/changed snippets in `index.json`
3. If it's a new multi-lesson course, add a `courses` entry (see [Categories and courses](#categories-and-courses))
4. Commit and push

---

## Utility scripts

### `create_index.py`

Rebuilds `snippets/index.json`'s `categories` list by scanning `snippets/` for every folder that directly contains `.json` files. Preserves existing category/snippet `id`s and titles, adds new categories/snippets it finds on disk, and flags (without deleting) index entries whose folder has disappeared. Leaves the `courses` list untouched.

```bash
python3 create_index.py
```

Run this any time you add, remove, or move snippet JSON files by hand, or after running `dir_to_snippets.py`.

### `dir_to_snippets.py`

Bulk-converts a directory tree of source files into snippet JSON files under `snippets/`. Each leaf directory (one with no subdirectories) becomes one snippet: every file inside it becomes a `files` entry, and the directory itself collapses into a same-named `.json` file at the mirrored path. Deletes any snippet JSON under the output folder that no longer has a matching leaf directory in the input, and prunes directories left empty by that cleanup.

```bash
python3 dir_to_snippets.py path/to/source-files prgh-mobius
# path/to/source-files/lesson01/{main.py,extra.py} → snippets/prgh-mobius/lesson01.json

python3 dir_to_snippets.py path/to/source-files prgh-mobius --dryrun
# preview writes/deletes without touching the filesystem
```

### `sync_index.py`

Reads the `title` field from each snippet JSON file and updates the matching entry in `index.json`. Run this after editing snippet titles directly in their JSON files.

```bash
python3 sync_index.py
```

### `py_to_json.py`

Converts a single `.py` file into a snippet JSON file ready to drop into the `snippets/` folder. For converting a whole directory of files at once, use `dir_to_snippets.py` instead.

```bash
python3 py_to_json.py myprogram.py
# → writes myprogram.json next to the input file

python3 py_to_json.py myprogram.py snippets/lecture-examples/lecture01/05.json
# → writes to a specific path
```

The output is a minimal single-file snippet with the filename as the title. Edit the `title` field in the JSON afterwards if needed, then run `sync_index.py` to update the index.

---

## File structure

```
/
├── index.html                  ← demo page (GitHub Pages homepage)
├── gallery.html                ← course/category browser
├── lecture.html                ← inline lesson viewer (all examples for one lesson)
├── viewer.html                 ← single-snippet full-page viewer
├── embed.js                    ← the widget script (self-contained)
├── create_index.py             ← rebuilds index.json's categories from snippets/ on disk
├── dir_to_snippets.py          ← bulk-converts a directory of source files into snippet JSON files
├── sync_index.py               ← syncs titles from JSON files into index.json
├── py_to_json.py               ← converts a single .py file into a snippet JSON file
├── snippets/
│   ├── index.json              ← categories + courses (see Categories and courses)
│   ├── basic-examples/
│   ├── lecture-examples/
│   │   └── lecture01/ … lecture16/
│   ├── mobius-DD100N/
│   │   └── lesson01/ … lesson08/
│   ├── mobius-DD1310/
│   │   └── lektion01/ … lektion12/
│   ├── tutorials-DD1310/
│   │   └── tutorial01/ … tutorial06/
│   ├── prgh-mobius/
│   │   └── lesson01/ … lesson12/
│   └── DD1320/
│       └── 01/ … 02/
├── .nojekyll                   ← disables Jekyll on GitHub Pages
└── README.md
```

---

## Widget features

| Feature | Details |
|---------|---------|
| **Editor** | CodeMirror 6 with IDLE-style syntax highlighting and Menlo font |
| **Syntax colours** | Keywords orange, strings green, comments red, built-ins purple, def/class names blue |
| **▶ Run** | Executes `main.py` via Skulpt; also triggered by **Ctrl+Enter** / **Cmd+Enter** |
| **⏹ Stop** | Interrupts a running program |
| **↺ Reset** | Restores all files to their original state and clears output |
| **↓ Download** | Saves the currently active file |
| **Fullscreen** | Browser fullscreen via the ⛶ button |
| **Output resize** | Drag the bar between editor and output to resize the output panel |
| **`input()`** | Rendered inline in the output panel — type and press Enter |
| **File I/O** | Virtual filesystem: `open()`, `read()`, `write()`, `readline()`, `for line in file` all work — see [File I/O in snippets](#file-io-in-snippets) below |
| **Multi-file** | Import across files; file panel on the left switches between them |
| **Turtle graphics** | `import turtle` opens a canvas overlay automatically |
| **`</> Embed`** | Generates an iframe embed code for the current snippet |

### File I/O in snippets

The virtual filesystem backing `open()` treats files two ways, depending on whether the name being written already exists in the snippet:

- **A file already in the snippet** (declared in its `files` array) — writing to it updates that file's content in the editor directly.
- **A name chosen at runtime** — e.g. `name = input("Filename: ")` followed by `open(name, "w")` — adds a new entry to the file panel, marked with a **NEW** badge, plus a clickable "📄 Wrote `<name>` — click to view" link in the output panel that jumps straight to it.

Either way, **↺ Reset** discards the changes: files revert to their original content, and any files created at runtime are removed from the panel.

---

## Deploying to GitHub Pages

### First-time setup

1. Create a new public repository on GitHub

2. Push this project to it:

```bash
cd py-snippet-widget
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/REPO.git
git branch -M main
git push -u origin main
```

3. Enable GitHub Pages:
   - Go to your repo → **Settings** → **Pages**
   - Under **Source**, select **Deploy from a branch**
   - Set branch to `main`, folder to `/ (root)`
   - Click **Save**

4. Visit `https://USERNAME.github.io/REPO/` after ~60 seconds

### Updating

Any `git push` to `main` automatically redeploys within 30–60 seconds.

---

## Browser support

Works in all modern browsers: Chrome, Firefox, Safari, Edge.
Requires ES modules support (universally available since 2019).

---

## Limitations

- Only standard Python built-ins and a subset of the standard library are available (no `numpy`, `pandas`, etc.) — see [Skulpt's supported modules](https://skulpt.org/docs/index.html)
- A running snippet can't be driven or scripted from the host page — `input()` always blocks until a person types a response in the output panel
- Only one snippet can run at a time per page
- Network access from Python code is not available
- `turtle` fill with `begin_fill()`/`end_fill()` only works reliably for one shape per run

---

## Open-source dependencies

### Skulpt
- **What it is**: Python 3 interpreter compiled to JavaScript
- **CDN**: `https://skulpt.org/js/skulpt.min.js`
- Unicode identifiers, strings, and filenames all work correctly (tested with Swedish `å`/`ä`/`ö` as well as Greek, Cyrillic, and CJK characters)
- **Licence**: MIT / Python Software Foundation License v2
- **Source**: https://github.com/skulpt/skulpt

### CodeMirror 6
- **What it is**: Code editor with syntax highlighting, line numbers, bracket matching
- **Version**: 6.0.1
- **CDN**: `https://esm.sh/codemirror@6.0.1`
- **Licence**: MIT
- **Source**: https://github.com/codemirror/codemirror.next

### esm.sh
- A CDN that serves npm packages as ES modules — used to load CodeMirror 6
- **Source**: https://github.com/esm-dev/esm.sh

---

## Licence

Released under the [MIT License](https://opensource.org/licenses/MIT).
