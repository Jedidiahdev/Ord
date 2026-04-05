"""
Ord v3.0 - Software Engineer Agent (Ord-SE)
Production code, GitHub commits, feature development.

Patterns Implemented:
- Tool Use (Ch5): GitHub API, code generation
- Reflection (Ch4): Code quality improvement
- Exception Handling (Ch12): Build failure recovery

Constraint: Can only push to feature branches, never main
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, MessagePriority


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
    status: str = "active"  # active, merged, abandoned


class SEAgent(BaseAgent):
    """
    Ord-SE: Software Engineer Agent
    
    The code craftsman who brings designs to life.
    SE writes clean, production-ready code and manages
    the entire GitHub workflow.
    
    CONSTRAINT: Only pushes to feature branches, never main
    """
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-se",
            name="Ord-SE",
            role="Software Engineer",
            layer=3,
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        self.branches: Dict[str, FeatureBranch] = {}
        self.commits: List[CodeCommit] = []
        self.github_connected = False
        
        self.logger.info("💻 Ord-SE initialized | Code Craftsman")
    
    def get_capabilities(self) -> List[str]:
        return [
            "code_generation",
            "github_integration",
            "feature_development",
            "bug_fixing",
            "code_review_preparation",
            "testing",
            "deployment",
            "documentation"
        ]
    
    async def create_feature_branch(self, project_id: str, project_name: str) -> str:
        """Create feature branch for project (WORKFLOW 4)"""
        timestamp = int(time.time())
        branch_name = f"feature/{project_name.lower().replace(' ', '-')}-{timestamp}"
        
        branch = FeatureBranch(
            branch_name=branch_name,
            project_id=project_id,
            created_at=time.time()
        )
        
        self.branches[branch_name] = branch
        
        self.logger.info(f"🌿 Created feature branch: {branch_name}")
        
        return branch_name
    
    async def write_code(
        self,
        project_id: str,
        file_path: str,
        code: str,
        branch: str
    ) -> Dict:
        """Write code to file in feature branch"""
        # In production: use GitHub API
        commit = CodeCommit(
            commit_id=f"commit-{int(time.time())}",
            branch=branch,
            message=f"Add {file_path}",
            files_changed=[file_path],
            author=self.identity.agent_id,
            timestamp=time.time(),
            project_id=project_id
        )
        
        self.commits.append(commit)
        
        if branch in self.branches:
            self.branches[branch].commits.append(commit)
        
        return {
            "status": "committed",
            "commit_id": commit.commit_id,
            "branch": branch,
            "file": file_path
        }
    
    async def create_pull_request(
        self,
        branch: str,
        title: str,
        description: str
    ) -> Dict:
        """Create pull request (WORKFLOW 4 Step 4)"""
        pr_id = f"pr-{int(time.time())}"
        
        # Notify Review agent
        await self.send_message(
            recipient_id="ord-review",
            message_type="task",
            payload={
                "task": {
                    "type": "review_pr",
                    "pr_id": pr_id,
                    "branch": branch,
                    "title": title,
                    "description": description
                }
            },
            priority=MessagePriority.HIGH
        )
        
        return {
            "status": "pr_created",
            "pr_id": pr_id,
            "branch": branch,
            "message": f"PR created: {title}. Routing to Ord-Review for review."
        }
    
    async def deploy_to_vercel(self, project_id: str, project_name: str) -> Dict:
        """Deploy project to Vercel (WORKFLOW 4 Step 9)"""
        self.logger.info(f"🚀 Deploying {project_name} to Vercel...")
        
        # Simulate deployment
        await asyncio.sleep(2)
        
        live_url = f"https://{project_name.lower().replace(' ', '-')}-ord.vercel.app"
        
        # Notify PM of successful deployment
        await self.send_message(
            recipient_id="ord-pm",
            message_type="event",
            payload={
                "event_type": "deployment_complete",
                "project_id": project_id,
                "live_url": live_url
            },
            priority=MessagePriority.HIGH
        )
        
        return {
            "status": "deployed",
            "live_url": live_url,
            "project_id": project_id,
            "message": f"🎉 {project_name} is live at {live_url}"
        }
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Process SE-specific tasks"""
        task_type = task.get("type", "unknown")
        
        if task_type == "create_branch":
            branch = await self.create_feature_branch(
                task.get("project_id"),
                task.get("project_name")
            )
            return {"branch": branch}
        
        elif task_type == "write_code":
            return await self.write_code(
                task.get("project_id"),
                task.get("file_path"),
                task.get("code"),
                task.get("branch")
            )
        
        elif task_type == "create_pr":
            return await self.create_pull_request(
                task.get("branch"),
                task.get("title"),
                task.get("description")
            )
        
        elif task_type == "deploy_to_vercel":
            return await self.deploy_to_vercel(
                task.get("project_id"),
                task.get("project_name")
            )
        
        elif task_type == "20_variation_code":
            # Generate code for 20-variation experiment
            return await self._generate_variation_code(task)
        
        return {"error": f"Unknown task type: {task_type}"}
    
    async def _generate_variation_code(self, task: Dict) -> Dict:
        """Generate code for a single variation"""
        variation_id = task.get("variation_id")
        project_name = task.get("project_name")
        
        # Generate mock code for variation
        code = f"""
// Variation {variation_id} for {project_name}
// Creative direction: {task.get('creative_direction', 'default')}

import React from 'react';

export default function App() {{
  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white">
      <header className="p-6">
        <h1 className="text-3xl font-bold text-[#FD651E]">{project_name}</h1>
        <p>Variation {variation_id}</p>
      </header>
    </div>
  );
}}
"""
        
        return {
            "variation_id": variation_id,
            "code": code,
            "files": ["App.tsx", "index.css", "package.json"]
        }
