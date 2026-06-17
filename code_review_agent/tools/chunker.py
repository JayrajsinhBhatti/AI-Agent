"""Code chunking by Python function and class.

Implements:
  - chunk_python_file(file_path: str, content: str) -> list[CodeChunk]
  - chunk_python_files(files: dict[str, str]) -> list[CodeChunk]
"""

from __future__ import annotations

import ast
from typing import TypedDict


class CodeChunk(TypedDict):
    """A review-sized slice of a Python source file."""

    file_path: str
    name: str
    kind: str
    start_line: int
    end_line: int
    content: str


def chunk_python_files(files: dict[str, str]) -> list[CodeChunk]:
    """Chunk all Python files by top-level function and class definitions."""

    chunks: list[CodeChunk] = []
    for file_path, content in files.items():
        chunks.extend(chunk_python_file(file_path, content))
    return chunks


def chunk_python_file(file_path: str, content: str) -> list[CodeChunk]:
    """Chunk one Python file by module preamble, functions, and classes."""

    lines = content.splitlines()
    if not lines:
        return [_build_chunk(file_path, "<module>", "module", 1, 1, lines)]

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return [_build_chunk(file_path, "<module>", "module", 1, len(lines), lines)]

    definitions = [
        node
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    if not definitions:
        return [_build_chunk(file_path, "<module>", "module", 1, len(lines), lines)]

    definitions.sort(key=lambda node: node.lineno)
    chunks = _module_preamble_chunks(file_path, lines, definitions)

    for node in definitions:
        kind = "class" if isinstance(node, ast.ClassDef) else "function"
        end_line = getattr(node, "end_lineno", node.lineno)
        chunks.append(_build_chunk(file_path, node.name, kind, node.lineno, end_line, lines))

    return chunks


def _module_preamble_chunks(
    file_path: str, lines: list[str], definitions: list[ast.AST]
) -> list[CodeChunk]:
    first_definition_line = definitions[0].lineno
    if first_definition_line <= 1:
        return []

    preamble = lines[: first_definition_line - 1]
    if not any(line.strip() for line in preamble):
        return []

    return [_build_chunk(file_path, "<module>", "module", 1, first_definition_line - 1, lines)]


def _build_chunk(
    file_path: str,
    name: str,
    kind: str,
    start_line: int,
    end_line: int,
    lines: list[str],
) -> CodeChunk:
    return {
        "file_path": file_path,
        "name": name,
        "kind": kind,
        "start_line": start_line,
        "end_line": end_line,
        "content": "\n".join(lines[start_line - 1 : end_line]),
    }
