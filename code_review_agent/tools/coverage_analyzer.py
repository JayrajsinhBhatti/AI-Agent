"""Run coverage.py on repo to find uncovered functions"""

import subprocess
import json
import ast

def get_uncovered_functions(file_path: str, test_dir: str) -> list[dict]:
    """Runs coverage.py and returns functions with 0% coverage."""
    
    import sys
    
    # Run coverage
    subprocess.run(
        [sys.executable, "-m", "coverage", "run", "-m", "pytest", test_dir, "-q"],
        capture_output=True
    )
    
    # Get JSON report
    subprocess.run(
        [sys.executable, "-m", "coverage", "json", "-o", "coverage_report.json"],
        capture_output=True
    )
    
    with open("coverage_report.json") as f:
        coverage_data = json.load(f)
    
    uncovered = []
    file_data = {}
    for k, data in coverage_data["files"].items():
        k_norm = k.replace('\\', '/')
        file_path_norm = file_path.replace('\\', '/')
        if k_norm == file_path_norm or k_norm.endswith(file_path_norm) or file_path_norm.endswith(k_norm):
            file_data = data
            break
            
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