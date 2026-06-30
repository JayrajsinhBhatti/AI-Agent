"""Run coverage.py on repo to find uncovered functions"""

import subprocess
import json
import ast

def get_uncovered_functions(file_path: str, test_dir: str) -> list[dict]:
    """Runs coverage.py and returns functions with 0% coverage."""
    
    # Run coverage
    subprocess.run(
        ["python", "-m", "coverage", "run", "-m", "pytest", test_dir, "-q"],
        capture_output=True
    )
    
    # Get JSON report
    subprocess.run(
        ["python", "-m", "coverage", "json", "-o", "coverage_report.json"],
        capture_output=True
    )
    
    with open("coverage_report.json") as f:
        coverage_data = json.load(f)
    
    uncovered = []
    file_data = coverage_data["files"].get(file_path, {})
    missing_lines = set(file_data.get("missing_lines", []))
    
    # Parse AST to find which functions fall on missing lines
    with open(file_path) as f:
        source = f.read()
    
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_lines = set(range(node.lineno, node.end_lineno + 1))
            if func_lines & missing_lines:  # overlap = uncovered
                uncovered.append({
                    "function_name": node.name,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                    "source": ast.get_source_segment(source, node)
                })
    
    return uncovered