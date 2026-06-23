from langchain_core.tools import tool
import subprocess, tempfile, os

# check security errors
@tool
def run_bandit(filepath: str) -> str:
    """Run Bandit security analysis on a Python file."""
    result = subprocess.run(
        ["bandit", "-r", filepath, "-f", "json"],
        capture_output=True, text=True
    )
    
    return result.stdout or result.stderr


# check code queslity, style, common mistakes
@tool
def run_pylit(filepath: str) -> str:
    """Run Pylint style/error analysis on a Python file."""
    result = subprocess.run(
        ["pylint", filepath, "--output-format=json"],
        capture_output=True, text=True
    )
    
    return result.stdout