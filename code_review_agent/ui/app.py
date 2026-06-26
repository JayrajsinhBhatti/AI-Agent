import json
import os
import sys
import pandas as pd
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to sys.path so we can import the agent
sys.path.append(str(Path(__file__).parent.parent.resolve()))

from agent.graph import review_graph

# Configure page settings
st.set_page_config(
    page_title="Autonomous Code Review Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium styling
st.markdown("""
<style>
    /* Sleek gradient header */
    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #6B7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Card borders and hover animations - Safe for Dark & Light modes */
    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 15px;
        border-radius: 10px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15), 0 2px 4px -2px rgba(0, 0, 0, 0.15);
        border-color: rgba(79, 70, 229, 0.4);
    }
    
    /* Step progress status indicator */
    .step-status {
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .status-pending { background-color: #F1F5F9; color: #64748B; border-left: 4px solid #94A3B8; }
    .status-running { background-color: #EFF6FF; color: #1D4ED8; border-left: 4px solid #3B82F6; }
    .status-completed { background-color: #ECFDF5; color: #047857; border-left: 4px solid #10B981; }
</style>
""", unsafe_allow_html=True)


HISTORY_FILE = Path(__file__).parent.parent / "report" / "history.json"

def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_to_history(repo_url, report, state):
    history = load_history()
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Check if this report is already in the history, remove duplicates
    history = [item for item in history if item.get("repo_url") != repo_url]
    
    # Add new item to the top
    new_item = {
        "repo_url": repo_url,
        "timestamp": timestamp,
        "report": report,
        "state": state
    }
    history.insert(0, new_item)
    
    # Limit history to top 5 items
    history = history[:5]
    
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"Error writing history file: {e}")

def clear_history():
    try:
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
    except Exception as e:
        print(f"Error clearing history: {e}")

# Sidebar configuration
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/code.png", width=100)
    st.markdown("### 🤖 Setup & Run")
    
    repo_url = st.text_input(
        "GitHub Repository URL",
        value="https://github.com/pypa/sampleproject",
        help="Provide a link to a public GitHub repository to scan"
    )
    
    st.markdown("---")
    run_btn = st.button("🚀 Run Autonomous Review", use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📜 Scan History")
    
    history = load_history()
    if not history:
        st.info("No recent scans.")
    else:
        for idx, item in enumerate(history):
            repo_name = item.get("repo_url", "").split("/")[-1].replace(".git", "")
            label = f"📁 {repo_name}\n({item.get('timestamp')})"
            if st.button(label, key=f"hist_{idx}", use_container_width=True):
                st.session_state.review_report = item.get("report")
                st.session_state.current_state = item.get("state", {})
                st.rerun()
                
        st.markdown("")
        if st.button("🧹 Clear History", use_container_width=True):
            clear_history()
            st.rerun()


# Main View header
st.markdown('<div class="main-title">Autonomous Code Review & Debugging Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-driven linting, logic review, and sandboxed test validation for Python repositories.</div>', unsafe_allow_html=True)

# Graph node names and user-facing labels
NODE_LIST = [
    ("clone_repo", "📥 Cloning Repository"),
    ("read_files", "📂 Reading & Chunking Files"),
    ("run_static_analysis", "🔍 Static Security & Style Scan"),
    ("llm_bug_detection", "🧠 AI Bug Detection"),
    ("generate_fixes", "🔧 Proposing Code Corrections"),
    ("run_tests", "🧪 Running Sandbox Test Suite"),
    ("generate_tests", "✏️ Writing New Unit Tests"),
    ("validate_fixes", "🔄 Verifying Fixes in Sandbox"),
    ("build_report", "📋 Compiling Final Report")
]

# Initialize session state for workflow report
if "review_report" not in st.session_state:
    st.session_state.review_report = None
if "current_state" not in st.session_state:
    st.session_state.current_state = {}


if run_btn:
    if not repo_url.strip():
        st.error("Please enter a valid GitHub repository URL.")
    else:
        st.session_state.review_report = None
        st.session_state.current_state = {}
        
        # Display progress placeholders
        st.markdown("### 🔄 Agent Workflow Progress")
        progress_placeholders = {}
        
        for node_id, label in NODE_LIST:
            progress_placeholders[node_id] = st.empty()
            progress_placeholders[node_id].markdown(
                f'<div class="step-status status-pending">⏳ {label} - Pending</div>',
                unsafe_allow_html=True
            )
            
        # Run workflow via LangGraph stream
        inputs = {"repo_url": repo_url}
        config = {"recursion_limit": 50}
        
        try:
            active_node = None
            st.session_state.current_state = {"repo_url": repo_url}
            
            for event in review_graph.stream(inputs, config):
                for node_id, state_update in event.items():
                    # Update previous node to completed
                    if active_node and active_node in progress_placeholders:
                        prev_label = next(lbl for nid, lbl in NODE_LIST if nid == active_node)
                        progress_placeholders[active_node].markdown(
                            f'<div class="step-status status-completed">✅ {prev_label} - Done</div>',
                            unsafe_allow_html=True
                        )
                        
                    # Set current node to running
                    active_node = node_id
                    current_label = next(lbl for nid, lbl in NODE_LIST if nid == node_id)
                    progress_placeholders[node_id].markdown(
                        f'<div class="step-status status-running">🔄 {current_label} - Processing...</div>',
                        unsafe_allow_html=True
                    )
                    
                    # Accumulate states
                    st.session_state.current_state.update(state_update)
            
            # Set last node to completed
            if active_node and active_node in progress_placeholders:
                last_label = next(lbl for nid, lbl in NODE_LIST if nid == active_node)
                progress_placeholders[active_node].markdown(
                    f'<div class="step-status status-completed">✅ {last_label} - Done</div>',
                    unsafe_allow_html=True
                )
                
            st.session_state.review_report = st.session_state.current_state.get("report", {})
            save_to_history(repo_url, st.session_state.review_report, st.session_state.current_state)
            st.success("Review complete! Results are available below.")
            
        except Exception as e:
            st.error(f"Workflow failed: {e}")


# Display results if a report is generated
if st.session_state.review_report:
    report = st.session_state.review_report
    state = st.session_state.current_state
    
    st.markdown("---")
    st.markdown("### 📊 Code Review Results")
    
    # 1. Summary Metrics
    files_reviewed = report.get("files_reviewed", 0)
    chunks_reviewed = report.get("chunks_reviewed", 0)
    
    static_results = report.get("static_analysis", {})
    bandit_issues = static_results.get("bandit", [])
    pylint_issues = static_results.get("pylint", [])
    total_issues = len(bandit_issues) + len(pylint_issues)
    
    test_results = report.get("test_results", {})
    test_status = test_results.get("status", "not_run")
    passed = test_results.get("passed", 0)
    total_tests = test_results.get("total", 0)
    
    coverage_pct = 0.0
    if "coverage" in test_results and "totals" in test_results["coverage"]:
        coverage_pct = test_results["coverage"]["totals"].get("percent_covered", 0.0)
        
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Files Scanned", files_reviewed)
    m2.metric("AST Code Chunks", chunks_reviewed)
    m3.metric("Static Warnings", total_issues)
    
    if test_status == "no_tests_found":
        m4.metric("Unit Tests", "None Found")
        m5.metric("Coverage", "N/A")
    elif test_status == "completed":
        m4.metric("Unit Tests", f"{passed} / {total_tests} Pass")
        m5.metric("Coverage", f"{coverage_pct:.1f}%")
    else:
        m4.metric("Unit Tests", "Failed / Run Error")
        m5.metric("Coverage", "Error")
        
    # 2. Detail Tabs
    tab_static, tab_tests, tab_ai, tab_json = st.tabs([
        "🔎 Static Analysis Log", 
        "🧪 Sandbox Tests & Coverage", 
        "🧠 AI Findings & Code Fixes", 
        "📋 Export JSON Report"
    ])
    
    # -- Static Analysis Tab --
    with tab_static:
        st.markdown("#### 🔒 Bandit Security Issues")
        if not bandit_issues:
            st.info("No security issues found by Bandit.")
        else:
            bandit_df = pd.DataFrame([
                {
                    "File": issue.get("filename"),
                    "Line": issue.get("line_number"),
                    "Severity": issue.get("issue_severity"),
                    "Confidence": issue.get("issue_confidence"),
                    "Description": issue.get("issue_text")
                }
                for issue in bandit_issues
            ])
            st.dataframe(bandit_df, use_container_width=True)
            
        st.markdown("#### 📐 Pylint Code Quality Warnings")
        if not pylint_issues:
            st.info("No code quality warnings found by Pylint.")
        else:
            pylint_df = pd.DataFrame([
                {
                    "File": issue.get("path"),
                    "Line": issue.get("line"),
                    "Type": issue.get("type"),
                    "Symbol": issue.get("symbol"),
                    "Message": issue.get("message")
                }
                for issue in pylint_issues
            ])
            st.dataframe(pylint_df, use_container_width=True)
            
    # -- Sandbox Tests Tab --
    with tab_tests:
        if test_status == "no_tests_found":
            st.info("No test suite detected in this repository. Add tests under a `tests/` directory to run sandboxed checks.")
        elif test_status == "completed":
            st.markdown(f"**Sandboxed pytest Summary:** `{test_results.get('raw_summary', 'No summary generated')}`")
            
            st.markdown("#### 📂 Code Coverage Breakdown")
            cov_files = test_results.get("coverage", {}).get("files", {})
            if not cov_files:
                st.info("No coverage metrics found.")
            else:
                cov_df = pd.DataFrame([
                    {
                        "File": filepath,
                        "Covered Lines": info.get("summary", {}).get("covered_lines", 0),
                        "Missing Lines": info.get("summary", {}).get("missing_lines", 0),
                        "Coverage %": f"{info.get('summary', {}).get('percent_covered', 0.0):.2f}%"
                    }
                    for filepath, info in cov_files.items()
                ])
                st.dataframe(cov_df, use_container_width=True)
                
            st.markdown("#### 🖥️ Sandbox Execution Output Logs")
            with st.expander("Show Console Outputs (Stdout/Stderr)"):
                st.code(test_results.get("stdout", "") + "\n" + test_results.get("stderr", ""), language="text")
        else:
            st.error(f"Sandboxed runner encountered an error: {test_results.get('error', 'Unknown Error')}")
            
    # -- AI Findings Tab --
    with tab_ai:
        ai_findings = report.get("findings", [])
        suggested_fixes = report.get("suggested_fixes", [])
        
        if not ai_findings:
            st.info("No AI findings. Make sure LLM keys are configured.")
        else:
            st.markdown("#### 🧠 Identified AI Logic & Security Findings")
            for f in ai_findings:
                if f.get("status") == "identified":
                    severity_color = {
                        "critical": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🔵"
                    }.get(f.get("severity", "low").lower(), "⚪")
                    
                    with st.expander(f"{severity_color} {f.get('severity', 'low').upper()}: {f.get('symbol')} in {f.get('file_path')}"):
                        st.markdown(f"**Issue Description:** {f.get('issue_description')}")
                        st.markdown(f"**Suggested Fix:** {f.get('suggested_fix')}")
                        st.markdown("**Buggy Code snippet:**")
                        st.code(f.get("original_code"), language="python")
            
            st.markdown("#### 🔧 Proposed and Validated Fixes")
            validation_res = report.get("validation_results", {})
            st.markdown(f"**Sandbox Validation Status:** `{validation_res.get('status', 'N/A').upper()}`")
            
            if not suggested_fixes:
                st.info("No fixes generated (likely low severity or failed to compile).")
            else:
                for fix in suggested_fixes:
                    with st.expander(f"🔧 Fix for {fix.get('symbol')} in {fix.get('file_path')}"):
                        st.markdown(f"**Fix Explanation:** {fix.get('explanation')}")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Original Buggy Code:**")
                            st.code(fix.get("original_code"), language="python")
                        with col2:
                            st.markdown("**AI Corrected Code:**")
                            st.code(fix.get("fixed_code"), language="python")
            
    # -- JSON Report Export Tab --
    with tab_json:
        st.markdown("#### Final Report Document (JSON)")
        st.json(report)
        
        json_str = json.dumps(report, indent=4, ensure_ascii=False)
        st.download_button(
            label="Download JSON Report",
            data=json_str,
            file_name=f"review_report_{Path(report.get('repo_path', 'repo')).name}.json",
            mime="application/json",
            use_container_width=True
        )
