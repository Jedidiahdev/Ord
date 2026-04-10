import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, MessagePriority
from integrations.github import GitHubService
from integrations.vercel import VercelService


@dataclass
class CodeCommit:
    """Git commit record"""
    commit_id: str
    branch: str
    message: str
    files_changed: List[str]
    author: str
    timestamp: float
    project_id: str


@dataclass
class FeatureBranch:
    """Feature branch tracking"""
    branch_name: str
    project_id: str
    created_at: float
    commits: List[CodeCommit] = field(default_factory=list)
    status: str = "active"


class SEAgent(BaseAgent):
    """Ord-SE: Software Engineer with GitHub/Vercel ownership."""

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-se",
            name="Ord-SE",
            role="Software Engineer",
            layer=3,
            orchestrator=orchestrator,
            memory_manager=memory_manager,
        )

        self.branches: Dict[str, FeatureBranch] = {}
        self.commits: List[CodeCommit] = []
        self.github = GitHubService()
        self.vercel = VercelService()

        self.logger.info("💻 Ord-SE initialized | Code Craftsman")

    def get_capabilities(self) -> List[str]:
        return [
            "code_generation",
            "github_integration",
            "feature_development",
            "branching_and_commits",
            "pr_management",
            "testing",
            "pm_approved_deployment",
            "documentation",
        ]

    async def create_feature_branch(self, project_id: str, project_name: str) -> str:
        timestamp = int(time.time())
        branch_name = f"feature/{project_name.lower().replace(' ', '-')}-{timestamp}"
        self.branches[branch_name] = FeatureBranch(branch_name=branch_name, project_id=project_id, created_at=time.time())

        gh_result = self.github.create_branch(branch_name)
        if gh_result.get("status") == "error":
            self.logger.warning("GitHub branch creation failed: %s", gh_result.get("message"))

        return branch_name

    async def write_code(self, project_id: str, file_path: str, code: str, branch: str) -> Dict:
        commit = CodeCommit(
            commit_id=f"commit-{int(time.time())}",
            branch=branch,
            message=f"Ord-SE: update {file_path}",
            files_changed=[file_path],
            author=self.identity.agent_id,
            timestamp=time.time(),
            project_id=project_id,
        )

        self.commits.append(commit)
        if branch in self.branches:
            self.branches[branch].commits.append(commit)

        gh_result = self.github.commit_file(
            branch=branch,
            path=file_path,
            content=code,
            message=commit.message,
            author_name="Ord-SE",
        )

        return {
            "status": "committed",
            "commit_id": commit.commit_id,
            "branch": branch,
            "file": file_path,
            "github": gh_result,
        }

    async def create_pull_request(self, branch: str, title: str, description: str) -> Dict:
        pr_result = self.github.create_pull_request(branch=branch, title=title, body=description)
        pr_id = f"pr-{int(time.time())}" if pr_result.get("status") != "opened" else f"pr-{pr_result.get('pr_number')}"

        await self.send_message(
            recipient_id="ord-review",
            message_type="task",
            payload={
                "task": {
                    "type": "review_pr",
                    "pr_id": pr_id,
                    "branch": branch,
                    "title": title,
                    "description": description,
                }
            },
            priority=MessagePriority.HIGH,
        )

        return {
            "status": "pr_created",
            "pr_id": pr_id,
            "branch": branch,
            "github": pr_result,
            "message": f"PR created for {branch}; routed to Ord-Review.",
        }

    async def deploy_to_vercel(self, project_id: str, project_name: str, branch: str, approved_by_pm: bool) -> Dict:
        deployment = await self.vercel.create_deployment(
            name=project_name.lower().replace(" ", "-"),
            git_repo=f"{self.github.config.owner}/{self.github.config.repo}" if self.github.config.owner else project_name,
            branch=branch,
            approved_by_pm=approved_by_pm,
        )

        if deployment.get("status") in {"queued", "deployed"}:
            await self.send_message(
                recipient_id="ord-pm",
                message_type="event",
                payload={
                    "event_type": "deployment_complete",
                    "project_id": project_id,
                    "live_url": deployment.get("url"),
                },
                priority=MessagePriority.HIGH,
            )

        return deployment

    async def process_task(self, task: Dict) -> Dict[str, Any]:
        task_type = task.get("type", "unknown")

        if task_type == "create_branch":
            branch = await self.create_feature_branch(task.get("project_id", "proj"), task.get("project_name", "project"))
            return {"branch": branch}

        if task_type == "write_code":
            return await self.write_code(task.get("project_id", "proj"), task.get("file_path", "README.md"), task.get("code", ""), task.get("branch", "feature/ord"))

        if task_type == "create_pr":
            return await self.create_pull_request(task.get("branch", "feature/ord"), task.get("title", "Ord update"), task.get("description", ""))

        if task_type == "deploy_to_vercel":
            return await self.deploy_to_vercel(
                task.get("project_id", "proj"),
                task.get("project_name", "ord-app"),
                task.get("branch", "main"),
                bool(task.get("approved_by_pm", False)),
            )

        if task_type == "20_variation_code":
            return await self._generate_variation_code(task)

        return {"error": f"Unknown task type: {task_type}"}

    async def _generate_variation_code(self, task: Dict) -> Dict:
        variation_id = task.get("variation_id")
        project_name = task.get("project_name", "Project")

        code = f"""
// Variation {variation_id} for {project_name}
import React from 'react';

export default function App() {{
  return (
    <main className=\"min-h-screen bg-background text-foreground p-6\">
      <h1 className=\"text-3xl font-bold text-primary\">{project_name}</h1>
      <p className=\"mt-3 text-muted-foreground\">Variation {variation_id} implementation-ready scaffold.</p>
    </main>
  );
}}
"""

        return {"variation_id": variation_id, "code": code, "files": ["App.tsx", "index.css"]}
