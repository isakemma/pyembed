"""
py_to_json.py
Usage: python3 py_to_json.py input.py [output.json]

Converts a .py file into a snippet JSON file compatible with the widget format.
If no output path is given, the JSON is written next to the input file.
"""

import json
import os
import sys

from fix_indent import fix_mixed_indentation


def read_python_file(path):
    """
    Reads the content of a Python file.

    Arguments:
        path (str): Path to the .py file.

    Returns:
        str: The file content as a string.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_snippet(filename, content):
    """
    Builds a snippet dictionary in the widget JSON format.

    Arguments:
        filename (str): The name of the Python file (e.g. 'main.py').
        content (str): The Python source code as a string.

    Returns:
        dict: A snippet dictionary with 'title' and 'files' keys.
    """
    title = os.path.splitext(filename)[0]
    snippet = {
        "title": title,
        "files": [
            {
                "name": filename,
                "content": content
            }
        ]
    }
    return snippet


def write_json_file(path, data):
    """
    Writes a dictionary to a JSON file with pretty formatting.

    Arguments:
        path (str): Destination path for the .json file.
        data (dict): The data to serialize.

    Returns:
        None
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def derive_output_path(input_path):
    """
    Derives the output .json path from the input .py path.

    Arguments:
        input_path (str): Path to the input .py file.

    Returns:
        str: The output path with .json extension.
    """
    base = os.path.splitext(input_path)[0]
    return base + ".json"


def main():
    """
    Entry point. Reads arguments, converts the Python file, and writes the JSON.

    Arguments:
        None (reads from sys.argv)

    Returns:
        None
    """
    if len(sys.argv) < 2:
        print("Usage: python3 py_to_json.py input.py [output.json]")
        sys.exit(1)

    input_path = sys.argv[1]

    if not os.path.isfile(input_path):
        print("Error: file not found: " + input_path)
        sys.exit(1)

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        output_path = derive_output_path(input_path)

    filename = os.path.basename(input_path)
    content = read_python_file(input_path)
    fixed = fix_mixed_indentation(content)
    if fixed != content:
        print("Note: mixed tabs and spaces converted to spaces (see fix_indent.py).")
        content = fixed
    snippet = build_snippet(filename, content)
    write_json_file(output_path, snippet)

    print("Written to " + output_path)


main()
