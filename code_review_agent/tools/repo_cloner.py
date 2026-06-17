"""GitHub repository cloner.

Implements:
  - clone_repo(repo_url: str, target_dir: str) -> str
"""

from __future__ import annotations

import shutil
from pathlib import Path
from urllib.parse import urlparse

try:
    from git import Repo
except ImportError:
    class Repo:  # type: ignore[no-redef]
        """Lazy GitPython error so non-clone tools remain importable."""

        @staticmethod
        def clone_from(repo_url: str, destination: Path) -> None:
            raise ImportError(
                "GitPython is required for clone_repo. Install dependencies with "
                "`pip install -r requirements.txt`."
            )


def clone_repo(repo_url: str, target_dir: str) -> str:
    """Clone a public GitHub repository and return its local path."""

    _validate_public_github_url(repo_url)
    destination = Path(target_dir).expanduser().resolve()

    if destination.exists() and any(destination.iterdir()):
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    Repo.clone_from(repo_url, destination)
    return str(destination)


def _validate_public_github_url(repo_url: str) -> None:
    parsed = urlparse(repo_url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "github.com":
        raise ValueError("repo_url must be an HTTP(S) GitHub repository URL")
    if len(parsed.path.strip("/").split("/")) < 2:
        raise ValueError("repo_url must include an owner and repository name")
