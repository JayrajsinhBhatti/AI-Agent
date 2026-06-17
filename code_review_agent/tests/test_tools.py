"""Tests for the code review agent's tool modules."""

# TODO: Write tests for:
#   - tools.repo_loader (clone_repo, read_python_files)
#   - tools.static_analysis (run_bandit, run_pylint)
#   - tools.test_runner (run_tests_in_sandbox, parse_test_results)
#   - tools.fix_generator (generate_fix, apply_fix)
#   - tools.test_generator (identify_uncovered_functions, generate_tests)
#   - sandbox.e2b_client (create_sandbox, run_command_in_sandbox)
#   - report.report_builder (build_report, save_report_json)

from pathlib import Path

import pytest

from tools.chunker import chunk_python_file, chunk_python_files
from tools.file_reader import read_python_files
from tools.repo_cloner import clone_repo


def test_read_python_files_returns_relative_python_paths(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg" / "service.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# docs\n", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "ignored.py").write_text("x = 1\n", encoding="utf-8")

    files = read_python_files(str(tmp_path))

    assert files == {
        "pkg/__init__.py": "",
        "pkg/service.py": "def run():\n    return 1\n",
    }


def test_chunk_python_file_splits_module_function_and_class():
    content = '''"""Example module."""\n\nVALUE = 3\n\n\ndef helper():\n    return VALUE\n\n\nclass Worker:\n    def run(self):\n        return helper()\n'''

    chunks = chunk_python_file("pkg/service.py", content)

    assert [chunk["kind"] for chunk in chunks] == ["module", "function", "class"]
    assert [chunk["name"] for chunk in chunks] == ["<module>", "helper", "Worker"]
    assert chunks[1]["start_line"] == 6
    assert chunks[1]["end_line"] == 7
    assert "class Worker" in chunks[2]["content"]


def test_chunk_python_files_falls_back_to_module_for_syntax_errors():
    chunks = chunk_python_files({"broken.py": "def broken(:\n    pass\n"})

    assert chunks == [
        {
            "file_path": "broken.py",
            "name": "<module>",
            "kind": "module",
            "start_line": 1,
            "end_line": 2,
            "content": "def broken(:\n    pass",
        }
    ]


def test_clone_repo_validates_github_url(tmp_path):
    with pytest.raises(ValueError):
        clone_repo("https://example.com/org/repo", str(tmp_path / "repo"))


def test_clone_repo_uses_gitpython(monkeypatch, tmp_path):
    calls = {}

    def fake_clone_from(repo_url, destination):
        calls["repo_url"] = repo_url
        calls["destination"] = Path(destination)
        calls["destination"].mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("tools.repo_cloner.Repo.clone_from", fake_clone_from)

    destination = clone_repo("https://github.com/example/project", str(tmp_path / "project"))

    assert destination == str((tmp_path / "project").resolve())
    assert calls == {
        "repo_url": "https://github.com/example/project",
        "destination": (tmp_path / "project").resolve(),
    }
