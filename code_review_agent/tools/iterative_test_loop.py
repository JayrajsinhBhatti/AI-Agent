"""From LLM generate test → Run in E2B Sandbox → if fails → send failure output back to LLM → Revise test → Repeat"""

import os
from pathlib import Path
from dotenv import load_dotenv
from tools.test_runner import run_tests_in_sandbox
from agent.prompts import TEST_GENERATION_PROMPT

# Load environment keys
load_dotenv()

def get_active_llm():
    """Resolves and returns the configured active LLM based on environment keys."""
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GOOGLE_API_KEY")

    if groq_key and not groq_key.startswith("your_"):
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_key, temperature=0.1)
        except ImportError:
            pass

    if gemini_key and not gemini_key.startswith("your_"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=gemini_key, temperature=0.1)
        except ImportError:
            pass

    # Generic fallback
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=gemini_key or "placeholder", temperature=0.1)

def iterative_test_loop(function_code: str, function_name: str, file_path: str, repo_path: str = ".", max_iterations: int = 3) -> dict:
    """Generates a pytest file, runs validation in E2B sandbox, and self-heals up to max_iterations."""
    
    llm = get_active_llm()
    
    # 1. Draft the initial test code using the standard prompt structure
    prompt = TEST_GENERATION_PROMPT.format(
        file_path=file_path,
        symbol_name=function_name,
        code_content=function_code
    )
    
    try:
        response = llm.invoke(prompt)
        test_code = response.content.strip()
        if test_code.startswith("```python"):
            test_code = test_code[9:]
        elif test_code.startswith("```"):
            test_code = test_code[3:]
        if test_code.endswith("```"):
            test_code = test_code[:-3]
        test_code = test_code.strip()
    except Exception as e:
        print(f"[*] Warning: Initial test drafting failed: {e}")
        return {"test_code": "", "attempts": 0, "passed": False}
        
    tests_dir = Path(repo_path) / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    test_filename = f"test_generated_{function_name}.py"
    local_test_file = tests_dir / test_filename
    
    success = False
    
    for attempt in range(1, max_iterations + 1):
        print(f"  Attempt {attempt}/{max_iterations}: Running sandboxed verification for {test_filename}...")
        local_test_file.write_text(test_code, encoding="utf-8")
        
        # Execute E2B sandbox test run
        result = run_tests_in_sandbox(repo_path)
        
        status = result.get("status", "failed")
        exit_code = result.get("exit_code", 1)
        failed_count = result.get("failed", 0)
        errors_count = result.get("errors", 0)
        
        if status == "completed" and exit_code == 0 and failed_count == 0 and errors_count == 0:
            print(f"  [+] Success: Test {test_filename} passed E2B sandbox validation!")
            success = True
            break
        else:
            last_error = result.get("stdout", "") + "\n" + result.get("stderr", "")
            print(f"  [-] Failed: Test execution failed in E2B sandbox.")
            
            if attempt < max_iterations:
                print(f"  [*] Requesting self-healing correction from LLM...")
                correct_prompt = f"""You are a senior Python test engineer.
Your previously generated unit test for function '{function_name}' failed to run successfully in the test runner.

Target File Path: {file_path}
Function Source Code:
```python
{function_code}
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

    # If verification failed after all attempts, clean up the file
    if not success:
        print(f"  [!] Warning: Test {test_filename} could not be validated. Deleting local file.")
        if local_test_file.exists():
            local_test_file.unlink()
        return {"test_code": test_code, "attempts": max_iterations, "passed": False}
        
    return {"test_code": test_code, "attempts": attempt, "passed": True}