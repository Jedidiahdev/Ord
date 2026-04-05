import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, MessagePriority


@dataclass
class CodeReview:
    """Code review record"""
    review_id: str
    pr_id: str
    branch: str
    reviewer: str
    status: str  # pending, approved, changes_requested
    comments: List[Dict]
    issues_found: List[Dict]
    security_passed: bool
    quality_score: float
    reviewed_at: float


class ReviewAgent(BaseAgent):
    """
    Ord-Review: Code Reviewer Agent
    
    The quality guardian who ensures every line of code
    meets Ord's high standards. Review is thorough,
    constructive, and never harsh.
    
    CONSTRAINT: Must approve before PM can approve deployment
    """
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-review",
            name="Ord-Review",
            role="Code Reviewer",
            layer=3,
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        self.reviews: Dict[str, CodeReview] = {}
        
        # Review criteria
        self.criteria = {
            "code_quality": {
                "readability": 0.25,
                "maintainability": 0.25,
                "efficiency": 0.20,
                "testing": 0.15,
                "documentation": 0.15
            },
            "security_checks": [
                "no_hardcoded_secrets",
                "input_validation",
                "sql_injection_prevention",
                "xss_protection"
            ]
        }
        
        self.logger.info("🔍 Ord-Review initialized | Quality Guardian")
    
    def get_capabilities(self) -> List[str]:
        return [
            "code_review",
            "quality_gates",
            "security_review",
            "pr_approval",
            "issue_tracking",
            "constructive_feedback",
            "standards_enforcement"
        ]
    
    async def review_pr(self, pr_id: str, branch: str, code: str) -> CodeReview:
        """
        Review pull request (WORKFLOW 4 Step 5)
        Comprehensive review with constructive feedback
        """
        self.logger.info(f"🔍 Reviewing PR {pr_id} from {branch}")
        
        # Run security audit via Sec
        security_result = await self._run_security_audit(code)
        
        # Analyze code quality
        quality_issues = self._analyze_code_quality(code)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(code, quality_issues)
        
        # Generate constructive comments
        comments = self._generate_comments(quality_issues)
        
        # Determine status
        status = "approved" if (quality_score >= 80 and security_result["passed"]) else "changes_requested"
        
        review = CodeReview(
            review_id=f"review-{int(time.time())}",
            pr_id=pr_id,
            branch=branch,
            reviewer=self.identity.agent_id,
            status=status,
            comments=comments,
            issues_found=quality_issues,
            security_passed=security_result["passed"],
            quality_score=quality_score,
            reviewed_at=time.time()
        )
        
        self.reviews[review.review_id] = review
        
        # Notify PM of review completion
        await self.send_message(
            recipient_id="ord-pm",
            message_type="event",
            payload={
                "event_type": "review_complete",
                "pr_id": pr_id,
                "status": status,
                "quality_score": quality_score,
                "security_passed": security_result["passed"]
            },
            priority=MessagePriority.HIGH
        )
        
        return review
    
    async def _run_security_audit(self, code: str) -> Dict:
        """Request security audit from Ord-Sec"""
        # In production: send message to Sec
        # For now, simulate
        return {
            "passed": True,
            "violations": [],
            "message": "Security audit passed"
        }
    
    def _analyze_code_quality(self, code: str) -> List[Dict]:
        """Analyze code for quality issues"""
        issues = []
        
        # Check for common issues
        if "console.log" in code:
            issues.append({
                "type": "maintainability",
                "severity": "warning",
                "message": "Remove console.log statements before merging",
                "line": None
            })
        
        if len(code.split('\n')) > 300:
            issues.append({
                "type": "maintainability",
                "severity": "suggestion",
                "message": "Consider breaking this into smaller modules",
                "line": None
            })
        
        if "TODO" in code or "FIXME" in code:
            issues.append({
                "type": "documentation",
                "severity": "warning",
                "message": "Address TODO/FIXME comments or create tickets",
                "line": None
            })
        
        return issues
    
    def _calculate_quality_score(self, code: str, issues: List[Dict]) -> float:
        """Calculate overall quality score"""
        base_score = 100.0
        
        for issue in issues:
            if issue["severity"] == "error":
                base_score -= 15
            elif issue["severity"] == "warning":
                base_score -= 8
            elif issue["severity"] == "suggestion":
                base_score -= 3
        
        return max(0, base_score)
    
    def _generate_comments(self, issues: List[Dict]) -> List[Dict]:
        """Generate constructive, loving comments"""
        comments = []
        
        loving_prefixes = [
            "Great work! 💙 ",
            "Nice approach! ✨ ",
            "Looking good! 🌟 ",
            "Well done! 🚀 "
        ]
        
        import random
        
        for issue in issues:
            prefix = random.choice(loving_prefixes)
            comments.append({
                "type": issue["type"],
                "message": f"{prefix}{issue['message']}",
                "severity": issue["severity"]
            })
        
        if not issues:
            comments.append({
                "type": "praise",
                "message": "🎉 Fantastic work! This code is clean, well-structured, and ready to ship!",
                "severity": "positive"
            })
        
        return comments
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Process Review-specific tasks"""
        task_type = task.get("type", "unknown")
        
        if task_type == "review_pr":
            review = await self.review_pr(
                task.get("pr_id"),
                task.get("branch"),
                task.get("code", "")
            )
            return {
                "review_id": review.review_id,
                "status": review.status,
                "quality_score": review.quality_score,
                "security_passed": review.security_passed,
                "comments": review.comments
            }
        
        elif task_type == "get_review_criteria":
            return self.criteria
        
        return {"error": f"Unknown task type: {task_type}"}
