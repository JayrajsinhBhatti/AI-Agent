"""E2B sandbox wrapper for isolated code execution.

Provides a high-level interface to the E2B SDK for running
code, tests, and installing dependencies in a sandboxed environment.

"""

# TODO: Implement:
#   - create_sandbox() -> Sandbox
#   - upload_repo_to_sandbox(sandbox, repo_path: str) -> None
#   - run_command_in_sandbox(sandbox, command: str) -> dict
#   - install_dependencies(sandbox, requirements_path: str) -> None
#   - cleanup_sandbox(sandbox) -> None

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from e2b import Sandbox


def create_sandbox() -> Sandbox:
    """Create and return a new E2B Sandbox instance."""
    # Note: Requires E2B_API_KEY environment variable to be set.
    return Sandbox.create()


def upload_repo_to_sandbox(sandbox: Sandbox, repo_path: str) -> None:
    """Upload a local directory to the sandbox."""
    root = Path(repo_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

    # Ensure the remote workspace directory exists
    sandbox.commands.run("mkdir -p /home/user/workspace")

    for path in root.rglob("*"):
        if path.is_file() and not _is_ignored(path, root):
            relative_path = path.relative_to(root).as_posix()
            try:
                content = path.read_text(encoding="utf-8")
                # Write file directly to the sandbox
                sandbox.files.write(f"/home/user/workspace/{relative_path}", content)
            except Exception as e:
                print(f"Skipping binary/unreadable file {relative_path}: {e}")


def _is_ignored(path: Path, root: Path) -> bool:
    IGNORED = {
        ".git",
        "__pycache__",
        "venv",
        ".venv",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache"
    }
    return any(part in IGNORED for part in path.relative_to(root).parts)


def install_dependencies(sandbox: Sandbox, requirements_path: str) -> None:
    """Install dependencies from a requirements file inside the sandbox."""
    try:
        # Ensure pip is up to date
        sandbox.commands.run("pip install --upgrade pip", cwd="/home/user/workspace")
    except Exception as e:
        print(f"Warning: pip upgrade failed: {e}")
    
    try:
        # Run the installation
        result = sandbox.commands.run(f"pip install -r {requirements_path}", cwd="/home/user/workspace")
        if result.exit_code != 0:
            print(f"Warning: Dependency installation may have failed. stderr: {result.stderr}")
    except Exception as e:
        print(f"Warning: Dependency installation failed. stderr: {getattr(e, 'stderr', e)}")


def run_command_in_sandbox(sandbox: Sandbox, command: str) -> dict[str, Any]:
    """Run a shell command in the sandbox and return the result."""
    try:
        result = sandbox.commands.run(command, cwd="/home/user/workspace")
        stdout = getattr(result, "stdout", "")
        stderr = getattr(result, "stderr", "")
        exit_code = getattr(result, "exit_code", 0)
    except Exception as e:
        stdout = getattr(e, "stdout", "")
        stderr = getattr(e, "stderr", "")
        exit_code = getattr(e, "exit_code", 1)
        
    return {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code
    }


def cleanup_sandbox(sandbox: Sandbox) -> None:
    """Close and terminate the sandbox."""
    sandbox.kill()
