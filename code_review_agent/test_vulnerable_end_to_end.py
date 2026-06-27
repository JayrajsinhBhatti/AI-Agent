import os
import shutil
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load API keys and sandbox variables
load_dotenv()

# Mock the repo cloner before importing the graph
import tools.repo_cloner

# Setup a temporary repository folder
temp_repo_dir = tempfile.mkdtemp(prefix="local-vulnerable-repo-")

# Mock clone_repo to return the temp folder path
tools.repo_cloner.clone_repo = lambda url, dest: temp_repo_dir

class MockLLM:
    def invoke(self, prompt: str):
        class Response:
            def __init__(self, content):
                self.content = content
        
        # Determine if it's bug detection or fix generation
        if "BUG_DETECTION_PROMPT" in prompt or "Analyze the following Python code chunk" in prompt:
            if "Symbol Name: factorial" in prompt:
                content = """[
                    {
                        "file_path": "tools/vulnerable.py",
                        "symbol": "factorial",
                        "severity": "high",
                        "issue_description": "Infinite recursion for negative input values due to missing boundary check.",
                        "original_code": "if n == 0:\\n        return 1\\n    return n * factorial(n - 1)",
                        "suggested_fix": "Add a check to raise ValueError if n < 0."
                    }
                ]"""
            else:
                content = "[]"
            return Response(content)
            
        elif "FIX_GENERATION_PROMPT" in prompt or "Resolve the following issue in the provided Python code chunk" in prompt:
            if "Symbol: factorial" in prompt:
                content = """{
                    "fixed_code": "def factorial(n: int) -> int:\\n    \\\"\\\"\\\"Calculate the factorial of n (vulnerable to Infinite Recursion).\\\"\\\"\\\"\\n    if n < 0:\\n        raise ValueError(\\\"n must be non-negative\\\")\\n    if n == 0:\\n        return 1\\n    return n * factorial(n - 1)",
                    "explanation": "Added a guard clause to raise ValueError for negative numbers to prevent infinite recursion."
                }"""
            else:
                content = '{"fixed_code": "", "explanation": "Not mocked"}'
            return Response(content)

        elif "TEST_GENERATION_PROMPT" in prompt or "Generate a comprehensive pytest unit test" in prompt:
            content = """import pytest
from tools.vulnerable import factorial

def test_factorial_valid():
    assert factorial(5) == 120

def test_factorial_negative():
    with pytest.raises(ValueError):
        factorial(-1)
"""
            return Response(content)

        elif "CODE_REVIEW_SUMMARY_PROMPT" in prompt or "Summarize the overall findings of the code review" in prompt:
            content = "Mock Lead Architect Summary: The codebase was successfully scanned. Handled 1 critical bug in factorial function. Test validation succeeded inside sandbox environment."
            return Response(content)

        elif "BOOTSTRAP_TEST_PROMPT" in prompt or "Generate a basic pytest unit test file" in prompt:
            content = """import pytest
from tools.vulnerable import factorial

def test_factorial_smoke():
    assert factorial(0) == 1
"""
            return Response(content)
            
        return Response("[]")

import langchain_groq
langchain_groq.ChatGroq = lambda *args, **kwargs: MockLLM()

try:
    import langchain_google_genai
    langchain_google_genai.ChatGoogleGenerativeAI = lambda *args, **kwargs: MockLLM()
except ImportError:
    pass

from agent.graph import review_graph

def main():
    print("[*] Starting Local End-to-End Vulnerability Test...\n")
    print(f"[*] Created simulation folder at: {temp_repo_dir}")
    
    # Copy files to temp folder to simulate repository layout
    src_dir = Path(__file__).parent
    
    tools_dir = Path(temp_repo_dir) / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = Path(temp_repo_dir) / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy vulnerable scripts and tests
    shutil.copy(src_dir / "tools" / "vulnerable.py", tools_dir / "vulnerable.py")
    shutil.copy(src_dir / "tests" / "test_vulnerable.py", tests_dir / "test_vulnerable.py")
    
    # Create empty __init__.py files to make them modules
    (tools_dir / "__init__.py").touch()
    (tests_dir / "__init__.py").touch()
    
    # Run the compiled LangGraph workflow
    inputs = {
        "repo_url": "https://github.com/example/vulnerable-test-mock"
    }
    
    config = {"recursion_limit": 50}
    try:
        final_state = review_graph.invoke(inputs, config)
        print("\n[+] End-to-End Workflow Execution Completed successfully!")
        
        report = final_state.get("report", {})
        
        # Print results
        print("\n--- AI Bug Detection Findings ---")
        findings = report.get("findings", [])
        for f in findings:
            print(f"- {f.get('severity', 'low').upper()}: {f.get('symbol')} in {f.get('file_path')} -> {f.get('issue_description')}")
            
        print("\n--- AI Suggested Fixes ---")
        fixes = report.get("suggested_fixes", [])
        for fix in fixes:
            print(f"- Fix for {fix.get('symbol')} in {fix.get('file_path')}: {fix.get('explanation')}")
            
        print("\n--- E2B Sandbox Baseline Test Results ---")
        test_res = report.get("test_results", {})
        print(f"Status: {test_res.get('status')}")
        if test_res.get("error"):
            print(f"Error: {test_res.get('error')}")
            
        print("\n--- E2B Sandbox Fix Validation Results ---")
        validation = report.get("validation_results", {})
        print(f"Validation Status: {validation.get('status')}")
        print(f"Pytest summary: {validation.get('passed')} passed, {validation.get('failed')} failed, {validation.get('errors')} errors")
        
    except Exception as e:
        print(f"[-] Pipeline execution failed: {e}")
    finally:
        # Clean up simulation folder
        shutil.rmtree(temp_repo_dir)
        print("\n[*] Cleaned up simulation directory.")

if __name__ == "__main__":
    main()
