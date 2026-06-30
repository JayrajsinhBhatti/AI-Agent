# tests/samples/test_coverage_sample.py
# Intentionally incomplete — only covers `add`, leaves divide/is_palindrome uncovered

from coverage_sample import add

def test_add():
    assert add(2, 3) == 5