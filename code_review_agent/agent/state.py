"""State schema (TypedDict) for the code review agent graph."""

from __future__ import annotations

from typing import Any, TypedDict

from tools.chunker import CodeChunk


# TODO: Defines AgentState TypedDict with fields for:
#   - repo_url: str
#   - repo_path: str
#   - files: dict[str, str]
#   - static_analysis_results: dict
#   - llm_findings: list
#   - suggested_fixes: list
#   - test_results: dict
#   - generated_tests: list
#   - validation_results: dict
#   - report: dict


class AgentState(TypedDict, total=False):
    """Shared state passed between review workflow nodes."""

    repo_url: str
    repo_path: str
    clone_target_dir: str
    files: dict[str, str]
    file_chunks: list[CodeChunk]
    static_analysis_results: dict[str, Any]
    llm_findings: list[dict[str, Any]]
    suggested_fixes: list[dict[str, Any]]
    test_results: dict[str, Any]
    generated_tests: list[dict[str, Any]]
    validation_results: dict[str, Any]
    report: dict[str, Any]
    errors: list[str]
