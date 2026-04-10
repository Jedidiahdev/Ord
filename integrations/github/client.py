import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class GitHubConfig:
    token: str
    owner: str
    repo: str
    default_base_branch: str = "main"

    @classmethod
    def from_env(cls) -> "GitHubConfig":
        return cls(
            token=os.getenv("GITHUB_TOKEN", ""),
            owner=os.getenv("GITHUB_OWNER", ""),
            repo=os.getenv("GITHUB_REPO", ""),
            default_base_branch=os.getenv("GITHUB_BASE_BRANCH", "main"),
        )


class GitHubService:
    """Thin adapter over PyGithub for Ord-SE owned branching/commit/PR workflows."""

    def __init__(self, config: Optional[GitHubConfig] = None):
        self.config = config or GitHubConfig.from_env()
        self._client = None
        self._repo = None

    @property
    def enabled(self) -> bool:
        return bool(self.config.token and self.config.owner and self.config.repo)

    def connect(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"status": "disabled", "message": "Missing GitHub env configuration"}

        try:
            from github import Github  # type: ignore

            self._client = Github(self.config.token)
            self._repo = self._client.get_repo(f"{self.config.owner}/{self.config.repo}")
            return {"status": "connected", "repo": self._repo.full_name}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def create_branch(self, branch_name: str, source_branch: Optional[str] = None) -> Dict[str, Any]:
        if not self._repo:
            conn = self.connect()
            if conn.get("status") != "connected":
                return conn

        source_branch = source_branch or self.config.default_base_branch
        try:
            source_ref = self._repo.get_git_ref(f"heads/{source_branch}")
            self._repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source_ref.object.sha)
            return {"status": "created", "branch": branch_name, "base": source_branch}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def commit_file(self, branch: str, path: str, content: str, message: str, author_name: str = "Ord-SE") -> Dict[str, Any]:
        if not self._repo:
            conn = self.connect()
            if conn.get("status") != "connected":
                return conn

        try:
            try:
                existing = self._repo.get_contents(path, ref=branch)
                result = self._repo.update_file(
                    path=path,
                    message=message,
                    content=content,
                    sha=existing.sha,
                    branch=branch,
                    author={"name": author_name, "email": "ord-se@ord.ai"},
                )
            except Exception:
                result = self._repo.create_file(
                    path=path,
                    message=message,
                    content=content,
                    branch=branch,
                    author={"name": author_name, "email": "ord-se@ord.ai"},
                )

            return {
                "status": "committed",
                "branch": branch,
                "path": path,
                "commit_sha": result["commit"].sha,
                "timestamp": time.time(),
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    def create_pull_request(self, branch: str, title: str, body: str, base: Optional[str] = None) -> Dict[str, Any]:
        if not self._repo:
            conn = self.connect()
            if conn.get("status") != "connected":
                return conn

        base = base or self.config.default_base_branch
        try:
            pr = self._repo.create_pull(title=title, body=body, head=branch, base=base)
            return {
                "status": "opened",
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "base": base,
                "head": branch,
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}
