"""Bandit (security) and Pylint (style/errors) wrapper functions.

Runs static analysis tools and parses their JSON output.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _get_executable(name: str) -> str:
    """Dynamically locate the tool executable in the current virtual environment, falling back to global path."""
    exe_dir = Path(sys.executable).parent
    # Check common virtualenv directories for Windows (Scripts) and Unix (bin)
    for folder in [exe_dir, exe_dir.parent / "bin", exe_dir.parent / "Scripts"]:
        for ext in ["", ".exe"]:
            candidate = folder / f"{name}{ext}"
            if candidate.is_file():
                return str(candidate)
    return name


def run_bandit(repo_path: str) -> list[dict[str, Any]]:
    """Run Bandit security analysis on the repository."""
    
    path = Path(repo_path).expanduser().resolve()
    if not path.exists():
        return []
        
    try:
        bandit_exe = _get_executable("bandit")
        # Run bandit recursively on the directory and output json
        result = subprocess.run(
            [bandit_exe, "-r", str(path), "-f", "json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        # Bandit returns non-zero codes if issues are found, so we check stdout directly
        if result.stdout.strip():
            data = json.loads(result.stdout)
            return data.get("results", [])
    except Exception as e:
        print(f"Error running bandit: {e}")
        
    return []


def run_pylint(repo_path: str) -> list[dict[str, Any]]:
    """Run Pylint style/error analysis on the repository."""
    
    path = Path(repo_path).expanduser().resolve()
    if not path.exists():
        return []
        
    try:
        pylint_exe = _get_executable("pylint")
        # Pylint needs to run on python packages or files.
        # Let's run it directly on the directory path.
        result = subprocess.run(
            [pylint_exe, str(path), "--output-format=json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        # Pylint returns non-zero codes on errors/warnings, so parse output regardless of return code
        output = result.stdout.strip()
        if output:
            return json.loads(output)
    except Exception as e:
        print(f"Error running pylint: {e}")
        
    return []


def run_all_static_analysis(repo_path: str) -> dict[str, Any]:
    """Run both Bandit and Pylint and return combined results."""
    
    return {
        "status": "completed",
        "bandit": run_bandit(repo_path),
        "pylint": run_pylint(repo_path)
    }
