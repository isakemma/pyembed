#!/usr/bin/env python3
"""
create_index.py

Scans the snippets/ directory tree and rebuilds snippets/index.json:
  - Creates a category for every directory that directly contains .json files
  - Adds entries for every .json file found
  - Preserves existing category names, IDs, and per-snippet IDs from the current index
  - Updates titles from the snippet files themselves

Run from the py-snippet-widget directory:
    python3 create_index.py
"""

import json
import os
import re

INDEX_PATH   = os.path.join(os.path.dirname(__file__), 'snippets', 'index.json')
SNIPPET_ROOT = os.path.join(os.path.dirname(__file__), 'snippets')


def slug(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


def folder_to_name(folder):
    """Turn a folder path like 'lecture-examples/lecture01' into a display name."""
    parts = folder.split('/')
    formatted = []
    for part in parts:
        words = re.split(r'[-_]+', part)
        formatted.append(' '.join(w.capitalize() for w in words if w))
    return ' – '.join(formatted)


def folder_to_id(folder):
    return slug(folder.replace('/', '-'))


def read_title(snippet_path):
    try:
        with open(snippet_path, encoding='utf-8') as f:
            data = json.load(f)
        return data.get('title', '').strip()
    except (json.JSONDecodeError, OSError):
        return ''


def scan_snippets(root):
    """
    Walk root and return an ordered list of (rel_folder, [sorted json filenames])
    for every directory that directly contains at least one .json file.
    rel_folder is relative to root and uses forward slashes.
    """
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        json_files = sorted(f for f in filenames if f.endswith('.json') and f != 'index.json')
        if not json_files:
            continue
        rel = os.path.relpath(dirpath, root).replace(os.sep, '/')
        if rel == '.':
            rel = ''
        result.append((rel, json_files))
    return result


def update_snippets(cat, folder, json_files):
    """Add missing snippet entries to cat and sync titles from disk."""
    by_file = {e['file']: e for e in cat.get('snippets', [])}
    entries = list(cat.get('snippets', []))
    cat_id = cat.get('id', folder_to_id(folder) if folder else 'root')

    added = 0
    updated = 0

    for fname in json_files:
        rel_file = (folder + '/' + fname) if folder else fname
        path = os.path.join(SNIPPET_ROOT, rel_file)
        title = read_title(path)

        if rel_file in by_file:
            entry = by_file[rel_file]
            if title and title != entry.get('title', ''):
                print('  Updated title: ' + rel_file)
                print('    old: ' + entry.get('title', ''))
                print('    new: ' + title)
                entry['title'] = title
                updated += 1
        else:
            stem = os.path.splitext(fname)[0]
            entry = {
                'id': cat_id + '-' + slug(stem),
                'file': rel_file,
                'title': title or stem,
            }
            entries.append(entry)
            by_file[rel_file] = entry
            print('  New snippet:  ' + rel_file)
            added += 1

    cat['snippets'] = entries
    return added, updated


def main():
    if os.path.isfile(INDEX_PATH):
        with open(INDEX_PATH, encoding='utf-8') as f:
            index = json.load(f)
    else:
        index = {'categories': []}

    existing_by_folder = {cat.get('folder', ''): cat for cat in index['categories']}

    fs_entries = scan_snippets(SNIPPET_ROOT)
    fs_folders = dict(fs_entries)

    total_added_cats = 0
    total_added_snippets = 0
    total_updated_titles = 0

    # Update categories that already exist in the index
    for cat in index['categories']:
        folder = cat.get('folder', '')
        if folder not in fs_folders:
            print('  MISSING folder: ' + (folder or '(root)'))
            continue
        a, u = update_snippets(cat, folder, fs_folders[folder])
        total_added_snippets += a
        total_updated_titles += u

    # Add new categories for directories not yet in the index
    known_folders = set(existing_by_folder.keys())
    for folder, json_files in fs_entries:
        if folder in known_folders:
            continue
        cat = {
            'id': folder_to_id(folder) if folder else 'root',
            'name': folder_to_name(folder) if folder else 'Snippets',
            'folder': folder,
            'snippets': [],
        }
        print('  New category: ' + (folder or '(root)'))
        a, u = update_snippets(cat, folder, json_files)
        total_added_cats += 1
        total_added_snippets += a
        total_updated_titles += u
        index['categories'].append(cat)

    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print()
    print(f'{total_added_cats} categories added, '
          f'{total_added_snippets} snippets added, '
          f'{total_updated_titles} titles updated.')
    print('index.json saved.')


if __name__ == '__main__':
    main()
