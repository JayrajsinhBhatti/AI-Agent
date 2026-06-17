"""GitHub repository cloning and Python file reader.

Uses GitPython to clone a repo and reads all .py files into memory.
"""

# TODO: Implemented through focused modules:
#   - clone_repo(repo_url: str, target_dir: str) -> str
#   - read_python_files(repo_path: str) -> dict[str, str]

from __future__ import annotations

from tools.chunker import CodeChunk, chunk_python_file, chunk_python_files
from tools.file_reader import read_python_files
from tools.repo_cloner import clone_repo

__all__ = [
    "CodeChunk",
    "chunk_python_file",
    "chunk_python_files",
    "clone_repo",
    "read_python_files",
]
