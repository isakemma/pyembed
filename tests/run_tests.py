#!/usr/bin/env python3
"""
Runs the widget regression tests in tests/cases/ against a real headless
browser. No pytest, no CI wiring — just `python3 tests/run_tests.py`
after the one-time setup in tests/README.md.
"""

import importlib.util
import sys
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

from harness import static_server

CASES_DIR = Path(__file__).parent / "cases"


def load_case(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    case_files = sorted(CASES_DIR.glob("test_*.py"))
    if not case_files:
        print("No test cases found in " + str(CASES_DIR))
        sys.exit(1)

    results = []
    with static_server() as base_url, sync_playwright() as pw:
        browser = pw.chromium.launch()
        for path in case_files:
            module = load_case(path)
            page = browser.new_page()
            errors = []
            page.on("console", lambda msg: errors.append(msg.text()) if msg.type == "error" else None)
            page.on("pageerror", lambda err: errors.append(str(err)))
            try:
                module.test(page, base_url)
                results.append((path.stem, True, None))
            except Exception as e:
                results.append((path.stem, False, "".join(traceback.format_exception_only(type(e), e)).strip()))
            finally:
                page.close()
        browser.close()

    print()
    failed = 0
    for name, ok, err in results:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}")
        if not ok:
            failed += 1
            print("       " + err.replace("\n", "\n       "))

    print(f"\n{len(results) - failed}/{len(results)} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
