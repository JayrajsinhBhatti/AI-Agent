"""LLM-based unit test generation.

Identifies uncovered functions from coverage data and uses an LLM
to generate new pytest unit tests for them.
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
from typing import Any

from agent.prompts import TEST_GENERATION_PROMPT
from tools.test_runner import run_tests_in_sandbox


def identify_uncovered_functions(coverage_data: dict[str, Any], files: dict[str, str]) -> list[dict[str, Any]]:
    """Compare AST function line ranges with coverage.json missing lines to find untested functions."""
    
    uncovered_candidates = []
    cov_files = coverage_data.get("coverage", {}).get("files", {})
    if not cov_files:
        return []

    for rel_path, file_content in files.items():
        # Clean relative path format
        cov_key = rel_path
        # Match keys in coverage dict (which might be absolute path or relative)
        matching_key = None
        for k in cov_files.keys():
            k_norm = k.replace('\\', '/')
            rel_norm = rel_path.replace('\\', '/')
            if k_norm.endswith(rel_norm) or rel_norm.endswith(k_norm):
                matching_key = k
                break
                
        if not matching_key:
            continue
            
        file_cov = cov_files[matching_key]
        missing_lines = file_cov.get("missing_lines", [])
        if not missing_lines:
            continue
            
        # Parse AST to find functions
        try:
            tree = ast.parse(file_content)
            lines = file_content.splitlines()
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Skip private helper functions or dunder functions in general
                    if node.name.startswith("__") and node.name.endswith("__"):
                        continue
                    # Skip test functions
                    if node.name.startswith("test_"):
                        continue
                        
                    start_line = node.lineno
                    end_line = getattr(node, "end_lineno", start_line)
                    
                    # Check if any lines in this function range are in the missing lines list
                    func_lines = set(range(start_line, end_line + 1))
                    intersect = func_lines.intersection(missing_lines)
                    
                    if intersect:
                        uncovered_candidates.append({
                            "file_path": rel_path,
                            "name": node.name,
                            "start_line": start_line,
                            "end_line": end_line,
                            "content": "\n".join(lines[start_line - 1 : end_line])
                        })
        except Exception as e:
            print(f"[*] Warning: Failed to parse AST for {rel_path} to identify coverage: {e}")
            
    return uncovered_candidates


def generate_tests(function_info: dict[str, Any], source_code: str, llm) -> str:
    """Generate raw pytest unit test code for the function."""
    
    prompt = TEST_GENERATION_PROMPT.format(
        file_path=function_info["file_path"],
        symbol_name=function_info["name"],
        code_content=source_code
    )
    
    try:
        response = llm.invoke(prompt)
        cleaned = response.content.strip()
        # Remove markdown code block wrapping if present
        if cleaned.startswith("```python"):
            cleaned = cleaned[9:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()
    except Exception as e:
        print(f"[*] Warning: LLM failed to write test for {function_info['name']}: {e}")
        return ""


def generate_all_tests(
    coverage_data: dict[str, Any], 
    files: dict[str, str], 
    repo_path: str, 
    llm
) -> list[dict[str, Any]]:
    """Find untested functions, generate unit tests, and self-heal them in the sandbox."""
    
    candidates = identify_uncovered_functions(coverage_data, files)
    if not candidates:
        print("[*] No uncovered functions found to generate tests for.")
        return []
        
    print(f"[+] Found {len(candidates)} uncovered functions. Starting automated test writer...")
    generated_tests = []
    
    tests_dir = Path(repo_path) / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    for candidate in candidates:
        func_name = candidate["name"]
        file_path = candidate["file_path"]
        print(f"[*] Drafting unit test for '{func_name}' in {file_path}...")
        
        # 1. Draft the initial test code
        test_code = generate_tests(candidate, candidate["content"], llm)
        if not test_code:
            continue
            
        test_filename = f"test_generated_{func_name}.py"
        local_test_file = tests_dir / test_filename
        
        # 2. Iterative validation and self-healing loop
        max_attempts = 3
        success = False
        last_error = ""
        
        for attempt in range(1, max_attempts + 1):
            print(f"  Attempt {attempt}/{max_attempts}: Running sandboxed verification for {test_filename}...")
            local_test_file.write_text(test_code, encoding="utf-8")
            
            # Execute sandbox test run
            run_res = run_tests_in_sandbox(repo_path)
            
            status = run_res.get("status", "failed")
            exit_code = run_res.get("exit_code", 1)
            failed_count = run_res.get("failed", 0)
            errors_count = run_res.get("errors", 0)
            
            if status == "completed" and exit_code == 0 and failed_count == 0 and errors_count == 0:
                print(f"  [+] Success: New test {test_filename} passed sandbox validation!")
                success = True
                generated_tests.append({
                    "file_path": f"tests/{test_filename}",
                    "function_name": func_name,
                    "target_file": file_path,
                    "test_code": test_code,
                    "status": "validated_and_saved"
                })
                break
            else:
                last_error = run_res.get("stdout", "") + "\n" + run_res.get("stderr", "")
                print(f"  [-] Failed: Test execution failed in sandbox.")
                
                if attempt < max_attempts:
                    print(f"  [*] Requesting self-healing correction from LLM...")
                    # Ask LLM to correct the test code based on the execution error
                    correct_prompt = f"""You are a senior Python test engineer.
Your previously generated unit test for function '{func_name}' failed to run successfully in the test runner.

Target File Path: {file_path}
Function Source Code:
```python
{candidate["content"]}
```

Previously Generated Test Code:
```python
{test_code}
```

Pytest Run Failure Logs:
```text
{last_error[:4000]}
```

Analyze the failure logs, identify the issue (e.g. incorrect import path, missing mock, syntax error, or assertion mismatch), and return the complete corrected pytest unit test code.
Return ONLY raw Python test code. Do not include markdown code blocks or comments outside of code.
"""
                    try:
                        resp = llm.invoke(correct_prompt)
                        cleaned = resp.content.strip()
                        if cleaned.startswith("```python"):
                            cleaned = cleaned[9:]
                        elif cleaned.startswith("```"):
                            cleaned = cleaned[3:]
                        if cleaned.endswith("```"):
                            cleaned = cleaned[:-3]
                        test_code = cleaned.strip()
                    except Exception as e:
                        print(f"  [*] LLM self-healing call failed: {e}")
                        break
        
        # 3. Clean up if the test failed validation after all attempts
        if not success:
            print(f"  [!] Warning: Test {test_filename} could not be validated after {max_attempts} attempts. Deleting local file.")
            if local_test_file.exists():
                local_test_file.unlink()
                
    return generated_tests
