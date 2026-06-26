"""Node functions for each step in the LangGraph agent pipeline."""

from __future__ import annotations

import tempfile
import os
import json
from pathlib import Path
from typing import Any

from agent.state import AgentState
from tools.chunker import chunk_python_files
from tools.file_reader import read_python_files
from tools.repo_cloner import clone_repo


def clone_repo_node(state: AgentState) -> dict[str, Any]:
    """Clone the requested GitHub repository."""

    repo_url = state.get("repo_url")
    if not repo_url:
        raise ValueError("Agent state must include repo_url")

    target_dir = state.get("clone_target_dir") or tempfile.mkdtemp(prefix="code-review-repo-")
    return {"repo_path": clone_repo(repo_url, target_dir)}


def read_files_node(state: AgentState) -> dict[str, Any]:
    """Read all Python files and split them into review chunks."""

    repo_path = state.get("repo_path")
    if not repo_path:
        raise ValueError("Agent state must include repo_path")

    files = read_python_files(repo_path)
    return {"files": files, "file_chunks": chunk_python_files(files)}


def static_analysis_node(state: AgentState) -> dict[str, Any]:
    """Run Bandit and Pylint recursive static analysis scans."""

    repo_path = state.get("repo_path")
    if not repo_path:
        raise ValueError("Agent state must include repo_path")

    try:
        from tools.static_analysis import run_all_static_analysis
    except ImportError:
        return {"static_analysis_results": {"status": "not_implemented"}}

    return {"static_analysis_results": run_all_static_analysis(repo_path)}


def _clean_json_response(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def llm_bug_detection_node(state: AgentState) -> dict[str, Any]:
    """Perform logic review and security scans on code chunks using LLM."""
    from agent.prompts import BUG_DETECTION_PROMPT

    # Find configuration key
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GOOGLE_API_KEY")

    llm = None
    if groq_key and not groq_key.startswith("your_"):
        try:
            from langchain_groq import ChatGroq
            # Use a slightly lower temperature for highly structured logical review
            llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_key, temperature=0.1)
        except ImportError:
            pass

    if not llm and gemini_key and not gemini_key.startswith("your_"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=gemini_key, temperature=0.1)
        except ImportError:
            pass

    # If no LLM is configured, return the fallback placeholders
    if not llm:
        print("[*] Warning: No active LLM key detected for BugDetector. Returning placeholders.")
        findings = [
            {
                "file_path": chunk["file_path"],
                "symbol": chunk["name"],
                "status": "pending_llm_review",
            }
            for chunk in state.get("file_chunks", [])
        ]
        return {"llm_findings": findings}

    findings = []
    static_results = state.get("static_analysis_results", {})
    
    # Analyze each AST code chunk
    for chunk in state.get("file_chunks", []):
        file_path = chunk["file_path"]
        # Skip unit test files to conserve API rate limits and avoid logical analysis on tests
        if "test_" in Path(file_path).name or "tests/" in file_path:
            continue
            
        print(f"[*] AI reviewing chunk {chunk['name']} in {chunk['file_path']}...")
        prompt = BUG_DETECTION_PROMPT.format(
            file_path=chunk["file_path"],
            symbol_name=chunk["name"],
            symbol_kind=chunk["kind"],
            code_content=chunk["content"],
            static_analysis=json.dumps(static_results, indent=2)
        )
        
        try:
            response = llm.invoke(prompt)
            cleaned_res = _clean_json_response(response.content)
            
            if cleaned_res:
                chunk_findings = json.loads(cleaned_res)
                if isinstance(chunk_findings, list):
                    for finding in chunk_findings:
                        # Append code context to findings to help the FixGenerator
                        finding["code_chunk_content"] = chunk["content"]
                        finding["status"] = "identified"
                        findings.append(finding)
        except Exception as e:
            print(f"[*] Warning: LLM review failed for chunk {chunk['name']}: {e}")

    # Fallback to placeholders if no issues found but we want code symbols tracked
    if not findings:
        findings = [
            {
                "file_path": chunk["file_path"],
                "symbol": chunk["name"],
                "status": "no_bugs_found",
            }
            for chunk in state.get("file_chunks", [])
        ]

    return {"llm_findings": findings}


def generate_fixes_node(state: AgentState) -> dict[str, Any]:
    """Generate proposed code corrections for identified issues using LLM."""
    from tools.fix_generator import generate_all_fixes

    repo_path = state.get("repo_path")
    if not repo_path:
        raise ValueError("Agent state must include repo_path")

    # Find configuration key
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GOOGLE_API_KEY")

    llm = None
    if groq_key and not groq_key.startswith("your_"):
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_key, temperature=0.1)
        except ImportError:
            pass

    if not llm and gemini_key and not gemini_key.startswith("your_"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=gemini_key, temperature=0.1)
        except ImportError:
            pass

    # If no LLM is configured, return empty fixes
    if not llm:
        print("[*] Warning: No active LLM key detected for FixGenerator. Returning empty suggested_fixes.")
        return {"suggested_fixes": []}

    findings = state.get("llm_findings", [])
    suggested_fixes = generate_all_fixes(findings, repo_path, llm)
    return {"suggested_fixes": suggested_fixes}


def run_tests_node(state: AgentState) -> dict[str, Any]:
    """Run tests in the E2B sandbox if tests are present."""

    repo_path = state.get("repo_path")
    if not repo_path:
        raise ValueError("Agent state must include repo_path")

    # Check if there are any test files
    root = Path(repo_path)
    test_files = (
        list(root.glob("test*.py")) +
        list(root.glob("tests/test*.py")) +
        list(root.glob("**/test_*.py"))
    )
    has_tests = len(test_files) > 0

    if not has_tests:
        return {"test_results": {"status": "no_tests_found", "has_tests": False}}

    try:
        from tools.test_runner import run_tests_in_sandbox
        results = run_tests_in_sandbox(repo_path)
        results["has_tests"] = True
        return {"test_results": results}
    except Exception as e:
        return {
            "test_results": {
                "status": "failed",
                "error": str(e),
                "has_tests": True
            }
        }


def generate_tests_node(state: AgentState) -> dict[str, Any]:
    """Create the generated tests field for later test generation."""

    return {"generated_tests": []}


def validate_fixes_node(state: AgentState) -> dict[str, Any]:
    """Test applied fixes inside the sandbox environment to ensure correctness."""
    from tools.fix_generator import apply_fix
    from tools.test_runner import run_tests_in_sandbox

    repo_path = state.get("repo_path")
    if not repo_path:
        raise ValueError("Agent state must include repo_path")

    suggested_fixes = state.get("suggested_fixes", [])
    if not suggested_fixes:
        return {"validation_results": {"status": "no_fixes_to_validate"}}

    test_results = state.get("test_results", {})
    # Check if a test suite is present
    if not test_results.get("has_tests", False):
        return {"validation_results": {"status": "no_tests_found_to_validate"}}

    # 1. Apply fixes locally and keep backups
    original_contents = {}
    applied_count = 0
    
    for fix in suggested_fixes:
        file_path = fix["file_path"]
        full_path = Path(repo_path) / file_path
        
        # Backup original content
        if full_path.exists() and file_path not in original_contents:
            try:
                original_contents[file_path] = full_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"[*] Warning: Could not backup {file_path}: {e}")
                continue

        # Apply fix on local file
        success = apply_fix(
            repo_path,
            file_path,
            fix["original_code"],
            fix["fixed_code"],
            symbol=fix.get("symbol"),
            original_chunk_content=fix.get("original_chunk_content")
        )
        if success:
            applied_count += 1

    if applied_count == 0:
        return {"validation_results": {"status": "failed_to_apply_fixes_locally"}}

    # 2. Upload and run pytest inside E2B sandbox
    print(f"[*] Validating {applied_count} applied fixes in E2B sandbox...")
    validation_res = run_tests_in_sandbox(repo_path)

    # 3. Restore original files locally to keep codebase clean
    for file_path, content in original_contents.items():
        try:
            full_path = Path(repo_path) / file_path
            full_path.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"[*] Error restoring original content for {file_path}: {e}")
            
    print("[*] Local repository code restored to original state.")

    # 4. Evaluate validation results
    passed = validation_res.get("passed", 0)
    failed = validation_res.get("failed", 0)
    errors = validation_res.get("errors", 0)
    exit_code = validation_res.get("exit_code", 1)

    status = "failed"
    if exit_code == 0 and failed == 0 and errors == 0 and passed > 0:
        status = "passed"

    return {
        "validation_results": {
            "status": status,
            "exit_code": exit_code,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "stdout": validation_res.get("stdout", ""),
            "stderr": validation_res.get("stderr", "")
        }
    }


def build_report_node(state: AgentState) -> dict[str, Any]:
    """Build a basic structured report from the current workflow state."""

    return {
        "report": {
            "repo_url": state.get("repo_url"),
            "repo_path": state.get("repo_path"),
            "files_reviewed": len(state.get("files", {})),
            "chunks_reviewed": len(state.get("file_chunks", [])),
            "static_analysis": state.get("static_analysis_results", {}),
            "findings": state.get("llm_findings", []),
            "suggested_fixes": state.get("suggested_fixes", []),
            "test_results": state.get("test_results", {}),
            "generated_tests": state.get("generated_tests", []),
            "validation_results": state.get("validation_results", {}),
        }
    }
