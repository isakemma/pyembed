# Python Snippet Widget

A lightweight, static, embeddable Python code runner styled after IDLE. Visitors can edit and run Python directly in the browser — no server required. Python executes via [Skulpt](https://skulpt.org) (Python compiled to JavaScript) and the editor is powered by [CodeMirror 6](https://codemirror.net).

---

## How embedding works

Embed a snippet on any page with a single `<iframe>`:

```html
<iframe
  src="https://USERNAME.github.io/REPO/viewer.html?basic-examples/hello"
  width="100%"
  height="540"
  style="border:none;border-radius:8px;"
  loading="lazy"
  allowfullscreen
></iframe>
```

- Replace `USERNAME` and `REPO` with your GitHub username and repository name
- What follows `viewer.html?` is the snippet's **address**: its folder under `snippets/`, then its name (see [Addresses](#addresses))
- Use the **</> Embed** button on any widget to get a ready-to-paste iframe
- Use the **🔗 Link** button to get the snippet's address (the `viewer.html` URL above) with a **Copy link** button, and a QR code for it that can be downloaded as a PNG for slides and handouts
- Links and iframes made before snippets had names, `viewer.html?src=basic-examples/hello.json` or `…?src=basic-examples%2Fhello.json`, keep working

---

## Browsing snippets

Four pages are available for navigating snippets:

| URL | What it shows |
|-----|---------------|
| `gallery.html` | All courses and categories as clickable cards |
| `gallery.html?cat=basic-examples` | All snippets in a single category |
| `lecture.html?course=lectures&n=1` | All examples for a specific lesson inline |
| `viewer.html?basic-examples/hello` | A single snippet, full-page |

Change `n=1` to the lesson number you want.

On `lecture.html` and `gallery.html?cat=…`, **↓ Files (.zip)** downloads all files of one example and **↓ Download all** those of the whole lesson. The zip unpacks to one directory per example, named after its address: `prgh-mobius/lesson01/count_up_down_example/main.py`.

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

## Addresses

A snippet's address is its folder under `snippets/` and its name:

```
https://USERNAME.github.io/REPO/viewer.html?prgh-lectures/frl07/sortering
```

The name comes from the snippet's file name, which `dir_to_snippets.py` takes from the name of the source directory:

| File (source directory) | Address handed out | Also works |
|---|---|---|
| `frl07/03-sortering.json` | `frl07/sortering` | `frl07/03-sortering` |
| `frl07/03-example.json` | `frl07/03-example` | |
| `lecture07/03.json` | `lecture07/03` | |
| `basic-examples/hello.json` | `basic-examples/hello` | |

- **The digits in front are the place in the lesson, not part of the name.** Two or more digits, optionally followed by one letter: `03-`, `03b-`, `10_`.
- **A name is optional.** `03.json` and `03-example.json` have none, and their address is the file name as it is. (Which words do not count as names is the `not_names` list in `snippets/addresses.json`; it starts out as `example`.)
- **A name must be the only one of its kind in the lesson.** If two files in a folder would get the same name (`01-lists`, `02-lists`), neither gets it; both keep the address with the number.
- Names are written in lower case with `a-z`, digits, `-` and `_`: `04-Köer och stackar` gets the address `koer-och-stackar`. A name must contain a letter.

**An address, once it exists, always leads to the same example.** `snippets/addresses.json` lists every address each snippet has ever had; `create_index.py` adds to it and never hands an address to another snippet. So:

| To… | do this | and then |
|---|---|---|
| add a directory of examples | nothing extra: run `dir_to_snippets.py` and `create_index.py` | every example has an address |
| give an example a name | rename its directory (or JSON file): `03-example` → `03-sortering` | the address `…/sortering` is handed out; `…/03-example` still leads to it |
| change the name later | rename again: `03-sortering` → `03-quicksort` | all three addresses lead to it |
| insert an example in the middle | give the new one a number that fits in between: `03b-binarsokning` | it is shown between 03 and 04; no other example is touched |
| renumber examples | only those that have a name: `03b-binarsokning` → `04-binarsokning` | the name is the address, so nothing changes for links |
| remove an example | delete it, then `python3 snippet_addresses.py retire ADDRESS` | the address says "This example has been removed" and is never reused |

Renaming is recognised when the files of the example are unchanged, or when the name is unchanged (so renumber *or* rename and edit in one go, as you like, but do not rename and edit at the same time). If `create_index.py` cannot tell where an example went, it says which addresses no longer lead anywhere, and how to say where they should lead (`snippet_addresses.py redirect`).

**Do not renumber examples that have no name** (`03-example` → `04-example`, `03.json` → `04.json`): their number *is* their address, so every existing link to 04 would show another example. `create_index.py` notices when a file has the content its neighbour had, warns, and keeps warning until it is undone or accepted.

`snippets/legacy-addresses.txt` is the list of the 505 addresses that existed before names (2026-11-13). It is never changed; `python3 snippet_addresses.py check` and the tests verify that each of them still leads to an example.

How a link is turned into a snippet is in one file, `site.js`, used by all the pages. The lists are data in `snippets/`, next to `index.json`.

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

▶ Run executes the `.py` file that is open in the editor, so every script in a multi-file snippet can be run on its own (and can still import the other files). The widget opens on `main.py`, so that is what runs by default; if the open file isn't a `.py` file, Run falls back to `main.py`.

---

## Adding a new snippet

**Single snippet:**

1. Create a JSON file in the appropriate subfolder under `snippets/`. Its file name decides its place in the lesson and its address: `03b-sortering.json` comes after `03…` and gets the address `…/sortering` (see [Addresses](#addresses))
2. Run `create_index.py` to register it in `snippets/index.json` and `snippets/addresses.json`
3. Commit and push:

```bash
git add snippets/
git commit -m "Add new snippet"
git push
```

**Bulk import (a directory of source files, one snippet per leaf folder):**

1. Run `dir_to_snippets.py` to convert the directory tree into snippet JSON files (see [Utility scripts](#utility-scripts))
2. Run `create_index.py` to register the new/changed snippets in `index.json` and give them addresses. No naming is needed; names can be given later by renaming directories (see [Addresses](#addresses))
3. If it's a new multi-lesson course, add a `courses` entry (see [Categories and courses](#categories-and-courses))
4. Commit and push

---

## Utility scripts

### `create_index.py`

Rebuilds `snippets/index.json`'s `categories` list by scanning `snippets/` for every folder that directly contains `.json` files. Preserves existing category/snippet `id`s and titles, adds new categories/snippets it finds on disk, removes snippets whose file is gone, and flags (without deleting) categories whose folder has disappeared. Within a category, snippets are ordered by the digits in front of their file names (`03`, `03b`, `04`); files without digits keep their order. Leaves the `courses` list untouched.

Then brings `snippets/addresses.json` up to date (see [Addresses](#addresses)) and reports what it found: renamed examples, new addresses, and anything it could not work out. In the last case it exits with status 1.

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

### `snippet_addresses.py`

For what `create_index.py` cannot work out by itself about [addresses](#addresses):

```bash
python3 snippet_addresses.py check
# every address, also those in legacy-addresses.txt, leads to an example that exists

python3 snippet_addresses.py redirect prgh-lectures/frl07/03-example prgh-lectures/frl07/sortering
# the first address (whose example is gone) now leads where the second one does

python3 snippet_addresses.py retire prgh-lectures/frl07/03-example
# the example was removed on purpose

python3 snippet_addresses.py accept
# after a warning about renumbered examples: yes, that is what I want
```

### `fix_indent.py`

Converts Python files whose indentation mixes tabs and spaces to spaces only. Python tolerates some such mixes, but they turn into errors as soon as a student adds a line in the editor. `dir_to_snippets.py` and `py_to_json.py` apply the same fix to what they read (the source files are left as they are), so this script is only needed for snippet JSON that was made or edited by hand.

```bash
python3 fix_indent.py --dryrun   # list the files that would be fixed
python3 fix_indent.py            # fix them, in the JSON files under snippets/
```

Files indented with only tabs, or only spaces of any width, are not touched: the editor follows each file's own indentation. A file is only rewritten if the result is provably the same program.

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
├── site.js                     ← shared by the pages: which snippet a link leads to, zip download
├── create_index.py             ← rebuilds index.json's categories from snippets/ on disk
├── snippet_addresses.py        ← keeps addresses.json; check / redirect / retire
├── dir_to_snippets.py          ← bulk-converts a directory of source files into snippet JSON files
├── sync_index.py               ← syncs titles from JSON files into index.json
├── py_to_json.py               ← converts a single .py file into a snippet JSON file
├── snippets/
│   ├── index.json              ← categories + courses (see Categories and courses)
│   ├── addresses.json          ← every address each snippet has had (see Addresses)
│   ├── legacy-addresses.txt    ← the addresses from before names; never changed
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
| **▶ Run** | Executes the open `.py` file (falling back to `main.py`) via Skulpt; also triggered by **Ctrl+Enter** / **Cmd+Enter** |
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

---

## Third-party code (Skulpt and CodeMirror)

The widget loads Skulpt and CodeMirror from `vendor/`, next to `embed.js`,
never from a CDN (esm.sh was down on 2026-10-30 and every snippet hung). The
files in `vendor/` are committed, so GitHub Pages still needs no build step.

- **CodeMirror** is an ordinary npm dependency: exact versions in
  `package.json`/`package-lock.json`, bundled into `vendor/codemirror.js` by
  `npm run vendor` (versions listed in `vendor/codemirror.json`). The names
  `embed.js` uses are listed in `scripts/codemirror-entry.js`.
  **Updates:** Dependabot opens one grouped pull request a month (security fixes
  at once). The tests workflow rebuilds the bundle on that branch and runs the
  widget tests; merge if they pass.
- **Skulpt** publishes no releases (npm 1.2.0 is from 2022), and skulpt.org
  serves builds of its main branch. `vendor/skulpt.min.js` and
  `vendor/skulpt-stdlib.js` are copies of skulpt.org's build, recorded with date
  and checksum in `vendor/skulpt.json`.
  **Updates:** `.github/workflows/skulpt-watch.yml` checks skulpt.org every
  Monday and opens an issue when the build has changed. Then run
  `npm run skulpt`, run the tests and commit `vendor/`.
- **The QR code generator** ([qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator),
  MIT) is the exception: nobody needs it to run code, so it is loaded from the
  jsDelivr CDN when the Link dialog is opened, and there is no copy in
  `vendor/`. If the CDN is down the dialog says so; the link still works, and
  any other QR code generator can make a code from it.
  **Updates:** the version is part of the address in `embed.js` (`QRCODE_CDN`);
  change it there by hand. Dependabot does not know about it.

By hand (Node 20+):

```bash
npm ci              # install the pinned versions
npm run vendor      # rebuild vendor/codemirror.js
npm run skulpt      # copy skulpt.org's current build into vendor/
```
