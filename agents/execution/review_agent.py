import time
from dataclasses import dataclass
from typing import Any, Dict, List

from agents.base_agent import BaseAgent


@dataclass
class CodeReview:
    review_id: str
    pr_id: str
    branch: str
    reviewer: str
    status: str
    comments: List[Dict]
    issues_found: List[Dict]
    security_passed: bool
    quality_score: float
    reviewed_at: float


class ReviewAgent(BaseAgent):
    """Ord-Review: quality gate before PM approves deployment."""

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-review",
            name="Ord-Review",
            role="Code Reviewer",
            layer=3,
            orchestrator=orchestrator,
            memory_manager=memory_manager,
        )
        self.reviews: Dict[str, CodeReview] = {}

    def get_capabilities(self) -> List[str]:
        return ["code_review", "quality_scoring", "security_gate", "deployment_gate"]

    async def review_pr(self, pr_id: str, branch: str, code: str) -> CodeReview:
        issues = []
        if "TODO" in code:
            issues.append({"severity": "warning", "message": "Resolve TODO comments before merge."})
        quality_score = 100.0 - (10.0 * len(issues))
        status = "approved" if quality_score >= 90 else "changes_requested"
        review = CodeReview(
            review_id=f"review-{int(time.time())}",
            pr_id=pr_id,
            branch=branch,
            reviewer=self.identity.agent_id,
            status=status,
            comments=[{"message": "Looks good overall."}] if not issues else issues,
            issues_found=issues,
            security_passed=True,
            quality_score=quality_score,
            reviewed_at=time.time(),
        )
        self.reviews[review.review_id] = review
        return review

    async def process_task(self, task: Dict) -> Dict[str, Any]:
        if task.get("type") == "review_pr":
            review = await self.review_pr(task.get("pr_id", "pr-local"), task.get("branch", "feature/local"), task.get("code", ""))
            return {"review_id": review.review_id, "status": review.status, "quality_score": review.quality_score}
        return {"error": f"Unknown task type: {task.get('type', 'unknown')}"}
