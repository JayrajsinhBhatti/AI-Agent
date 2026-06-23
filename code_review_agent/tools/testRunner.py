"""Create safe environment where repo can be executed sucessfully,
    upload repository.
    install dependencies.
    run the tests: python -m pytest tests/
    read & extract results.
"""

from langchain_core.tools import tool
import subprocess

@tool
def run_tests(repo_path: str) -> str:
    """Run pytest inside Docker."""

    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{repo_path}:/app",
        "python:3.11",
        "sh",
        "-c",
        "pip install -r /app/requirements.txt && pytest /app/tests"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return result.stdout + result.stderr