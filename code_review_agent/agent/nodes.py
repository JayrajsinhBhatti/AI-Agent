"""Node functions for each step in the LangGraph agent pipeline."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from agent.state import AgentState
from tools.chunker import chunk_python_files
from tools.file_reader import read_python_files
from tools.repo_cloner import clone_repo


# TODO: Implements one function per graph node:
#   - clone_repo_node(state)
#   - read_files_node(state)
#   - static_analysis_node(state)
#   - llm_bug_detection_node(state)
#   - generate_fixes_node(state)
#   - run_tests_node(state)
#   - generate_tests_node(state)
#   - validate_fixes_node(state)
#   - build_report_node(state)


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
    """Run static analysis when the static analysis module is implemented."""

    repo_path = state.get("repo_path")
    if not repo_path:
        raise ValueError("Agent state must include repo_path")

    try:
        from tools.static_analysis import run_all_static_analysis
    except ImportError:
        return {"static_analysis_results": {"status": "not_implemented"}}

    return {"static_analysis_results": run_all_static_analysis(repo_path)}


def llm_bug_detection_node(state: AgentState) -> dict[str, Any]:
    """Prepare chunk-level placeholders for later LLM review."""

    findings = [
        {
            "file_path": chunk["file_path"],
            "symbol": chunk["name"],
            "status": "pending_llm_review",
        }
        for chunk in state.get("file_chunks", [])
    ]
    return {"llm_findings": findings}


def generate_fixes_node(state: AgentState) -> dict[str, Any]:
    """Create the suggested fixes field for later LLM fix generation."""

    return {"suggested_fixes": []}


def run_tests_node(state: AgentState) -> dict[str, Any]:
    """Detect whether tests are present before sandbox execution is added."""

    repo_path = state.get("repo_path")
    has_tests = False
    if repo_path:
        root = Path(repo_path)
        has_tests = any(root.glob("test*.py")) or any(root.glob("tests/test*.py"))
    return {"test_results": {"status": "not_run", "has_tests": has_tests}}


def generate_tests_node(state: AgentState) -> dict[str, Any]:
    """Create the generated tests field for later test generation."""

    return {"generated_tests": []}


def validate_fixes_node(state: AgentState) -> dict[str, Any]:
    """Create the validation field for later fix validation."""

    return {"validation_results": {"status": "not_run"}}


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
