# ❗WEEK 3

"""
Apply fix to a temp copy of the file
Run pytest inside Docker
Check if tests pass
"""

import docker
import tempfile
import shutil
import os
from pathlib import Path

client = docker.from_env()

def apply_fix_to_file(original_file: str, fix: dict) -> str:
    """Creates a temp copy of the file with fix applied."""
    
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, Path(original_file).name)
    
    with open(original_file) as f:
        original_code = f.read()
    
    # Replace buggy snippet with fixed snippet
    patched_code = original_code.replace(
        fix["original_code"].strip(),
        fix["fixed_code"].strip()
    )
    
    with open(temp_file, "w") as f:
        f.write(patched_code)
    
    return temp_dir

def validate_fix_in_docker(repo_path: str, temp_dir: str) -> dict:
    """
    Copies fixed file into repo, runs pytest inside Docker container.
    Returns pass/fail result.
    """
    
    try:
        result = client.containers.run(
            image="code-review-sandbox",   # your built image name
            command="pytest --tb=short -q",
            volumes={
                temp_dir: {"bind": "/sandbox", "mode": "rw"},
            },
            working_dir="/sandbox",
            remove=True,                   # auto-remove container after run
            mem_limit="256m",              # resource limits
            cpu_quota=50000,
            stdout=True,
            stderr=True,
        )
        
        output = result.decode("utf-8")
        passed = "failed" not in output.lower() and "error" not in output.lower()
        
        return {
            "passed": passed,
            "output": output
        }
    
    except docker.errors.ContainerError as e:
        return {
            "passed": False,
            "output": str(e)
        }
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)