"""
Regression test for: math.gcd() must accept any number of arguments, as
it does since Python 3.9. Skulpt's math.gcd takes exactly two and fails
with "gcd() takes exactly 2 arguments (3 given)"; embed.js replaces it
when the math module is imported.
"""

from harness import run_snippet


def test(page, base_url):
    output = run_snippet(page, base_url, "../tests/fixtures/math_gcd_variadic.json")
    expected = "6\n6\n3\n0 7 0 2\nTrue\nTypeError\n"
    assert expected in output, output
