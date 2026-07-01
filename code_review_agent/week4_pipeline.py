"""Standalone script demonstrating the Week 4 test coverage and self-healing test generation pipeline."""

import os
from dotenv import load_dotenv
from tools.coverage_analyzer import get_uncovered_functions
from tools.iterative_test_loop import iterative_test_loop

# Load environment keys
load_dotenv()

def run_week4_pipeline(file_path: str, test_dir: str, repo_path: str = "."):
    print(f"[*] Running Week 4 Pipeline for {file_path}...")
    print(f"[*] Analyzing test coverage to find uncovered functions...")
    
    uncovered = get_uncovered_functions(file_path, test_dir)
    print(f"[+] Found {len(uncovered)} uncovered functions: {[f['function_name'] for f in uncovered]}")
    
    generated_tests = []
    
    for func in uncovered:
        print(f"\n[*] Starting iterative self-healing test loop for '{func['function_name']}'...")
        res = iterative_test_loop(
            function_code=func["source"],
            function_name=func["function_name"],
            file_path=file_path,
            repo_path=repo_path
        )
        
        generated_tests.append({
            "function": func["function_name"],
            **res
        })
        
    print("\n[+] Week 4 Pipeline execution finished!")
    return generated_tests

if __name__ == "__main__":
    # Example target paths inside the repository
    target_file = "tools/vulnerable.py"
    target_test_dir = "tests"
    
    if os.path.exists(target_file):
        results = run_week4_pipeline(target_file, target_test_dir)
        print("\n--- Pipeline Results ---")
        for res in results:
            print(f"Function: {res['function']} | Attempts: {res['attempts']} | Passed E2B Validation: {res['passed']}")
    else:
        print(f"Error: Target file {target_file} not found. Please run the script from the code_review_agent directory.")