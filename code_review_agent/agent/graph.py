"""LangGraph StateGraph definition for the code review agent pipeline."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from agent.nodes import (
    build_report_node,
    clone_repo_node,
    generate_fixes_node,
    generate_tests_node,
    llm_bug_detection_node,
    read_files_node,
    run_tests_node,
    static_analysis_node,
    validate_fixes_node,
)
from agent.state import AgentState


# TODO: Defines the StateGraph with nodes for:
#   1. clone_repo
#   2. read_files
#   3. run_static_analysis
#   4. llm_bug_detection
#   5. generate_fixes
#   6. run_tests
#   7. generate_tests
#   8. validate_fixes
#   9. build_report


def build_review_graph():
    """Build the complete review workflow graph."""

    graph = StateGraph(AgentState)
    graph.add_node("clone_repo", clone_repo_node)
    graph.add_node("read_files", read_files_node)
    graph.add_node("run_static_analysis", static_analysis_node)
    graph.add_node("llm_bug_detection", llm_bug_detection_node)
    graph.add_node("generate_fixes", generate_fixes_node)
    graph.add_node("run_tests", run_tests_node)
    graph.add_node("generate_tests", generate_tests_node)
    graph.add_node("validate_fixes", validate_fixes_node)
    graph.add_node("build_report", build_report_node)

    graph.set_entry_point("clone_repo")
    graph.add_edge("clone_repo", "read_files")
    graph.add_edge("read_files", "run_static_analysis")
    graph.add_edge("run_static_analysis", "llm_bug_detection")
    graph.add_edge("llm_bug_detection", "generate_fixes")
    graph.add_edge("generate_fixes", "run_tests")
    graph.add_edge("run_tests", "generate_tests")
    graph.add_edge("generate_tests", "validate_fixes")
    graph.add_edge("validate_fixes", "build_report")
    graph.add_edge("build_report", END)
    return graph.compile()


review_graph = build_review_graph()
