"""Python code file reader.

Implements:
  - read_python_files(repo_path: str) -> dict[str, str]
"""

from __future__ import annotations

from pathlib import Path


IGNORED_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".tox",
    ".venv",
    "venv",
    "env",
    "node_modules",
}


def read_python_files(repo_path: str) -> dict[str, str]:
    """Read every .py file from a repository into memory."""

    root = Path(repo_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

    files: dict[str, str] = {}
    for path in sorted(root.rglob("*.py")):
        if _is_ignored(path, root):
            continue
        relative_path = path.relative_to(root).as_posix()
        files[relative_path] = path.read_text(encoding="utf-8", errors="replace")
    return files


def _is_ignored(path: Path, root: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.relative_to(root).parts)
