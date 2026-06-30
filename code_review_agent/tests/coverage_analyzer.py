# tests/test_coverage_analyzer.py

from tools.coverage_analyzer import get_uncovered_functions

def test_finds_uncovered_functions():
    uncovered = get_uncovered_functions(
        file_path="tests/samples/coverage_sample.py",
        test_dir="tests/samples/"
    )
    
    uncovered_names = [f["function_name"] for f in uncovered]
    
    assert "divide" in uncovered_names
    assert "is_palindrome" in uncovered_names
    assert "add" not in uncovered_names  # this one IS covered

def test_uncovered_function_has_source():
    uncovered = get_uncovered_functions(
        file_path="tests/samples/coverage_sample.py",
        test_dir="tests/samples/"
    )
    
    for func in uncovered:
        assert func["source"]  # source code should not be empty
        assert func["start_line"] > 0
        assert func["end_line"] >= func["start_line"]