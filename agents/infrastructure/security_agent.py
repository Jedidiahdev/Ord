import asyncio
import hashlib
import json
import re
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, A2AMessage, MessagePriority


@dataclass
class SecurityPolicy:
    """Security policy definition"""
    policy_id: str
    name: str
    category: str  # code, communication, financial, data
    rules: List[Dict]
    severity: str  # block, warn, log
    enabled: bool = True


@dataclass
class SecurityViolation:
    """Recorded security violation"""
    violation_id: str
    agent_id: str
    policy_id: str
    violation_type: str
    details: str
    timestamp: float
    action_taken: str
    resolved: bool = False


@dataclass
class AuditEntry:
    """Immutable audit log entry"""
    entry_id: str
    agent_id: str
    action: str
    resource: str
    outcome: str
    timestamp: float
    hash_chain: str


class SecurityAgent(BaseAgent):
    """
    Ord-Sec: Security Chief Agent
    
    The guardian of Ord's integrity. Sec enforces policies,
    audits all actions, and ensures compliance without
    getting in the way of progress.
    
    Policies:
    - No hardcoded secrets in code
    - All UI must be responsive
    - Tone must be professional
    - Financial writes require approval
    """
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-sec",
            name="Ord-Sec",
            role="Security Chief Agent",
            layer=2,
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        # Policy engine (Feature 22)
        self.policies: Dict[str, SecurityPolicy] = {}
        self.violations: List[SecurityViolation] = []
        self.audit_log: List[AuditEntry] = []
        self.last_hash = "0" * 64  # Genesis hash
        
        # Initialize default policies
        self._initialize_policies()
        
        self.logger.info("🔒 Ord-Sec initialized | Security Guardian")
    
    def get_capabilities(self) -> List[str]:
        return [
            "policy_enforcement",
            "code_security_audit",
            "compliance_monitoring",
            "violation_detection",
            "audit_logging",
            "message_verification",
            "incident_response",
            "rbac_management"
        ]
    
    def _initialize_policies(self) -> None:
        """Initialize default security policies (Feature 22)"""
        
        # Code security policy
        self.policies["code_no_secrets"] = SecurityPolicy(
            policy_id="code_no_secrets",
            name="No Hardcoded Secrets",
            category="code",
            rules=[
                {"pattern": r"(api[_-]?key|password|secret|token)\s*=\s*['\"][^'\"]+['\"]", "description": "Hardcoded credential detected"},
                {"pattern": r"sk-[a-zA-Z0-9]{24,}", "description": "Potential API key detected"}
            ],
            severity="block"
        )
        
        # UI policy
        self.policies["ui_responsive"] = SecurityPolicy(
            policy_id="ui_responsive",
            name="Responsive UI Required",
            category="code",
            rules=[
                {"pattern": r"width:\s*\d+px", "description": "Fixed width may not be responsive"}
            ],
            severity="warn"
        )
        
        # Communication policy
        self.policies["comm_professional"] = SecurityPolicy(
            policy_id="comm_professional",
            name="Professional Tone Required",
            category="communication",
            rules=[
                {"pattern": r"\b(stupid|idiot|dumb|hate)\b", "description": "Unprofessional language detected"}
            ],
            severity="block"
        )
        
        # Financial policy
        self.policies["fin_approval"] = SecurityPolicy(
            policy_id="fin_approval",
            name="Financial Writes Require Approval",
            category="financial",
            rules=[
                {"action": "stripe_write", "requires_approval": True},
                {"action": "crypto_transfer", "requires_approval": True}
            ],
            severity="block"
        )
    
    async def audit_code(self, code: str, agent_id: str) -> Dict:
        """Audit code for security violations"""
        violations = []
        
        for policy_id, policy in self.policies.items():
            if policy.category != "code" or not policy.enabled:
                continue
            
            for rule in policy.rules:
                if "pattern" in rule:
                    matches = re.finditer(rule["pattern"], code, re.IGNORECASE)
                    for match in matches:
                        violation = SecurityViolation(
                            violation_id=f"vio-{int(time.time())}",
                            agent_id=agent_id,
                            policy_id=policy_id,
                            violation_type=rule["description"],
                            details=f"Found at position {match.start()}: {match.group()[:30]}...",
                            timestamp=time.time(),
                            action_taken=policy.severity
                        )
                        violations.append(violation)
                        self.violations.append(violation)
        
        # Block if any blocking violations
        can_proceed = not any(v.action_taken == "block" for v in violations)
        
        return {
            "can_proceed": can_proceed,
            "violations": [v.__dict__ for v in violations],
            "summary": f"Found {len(violations)} issues" if violations else "No issues found"
        }
    
    async def verify_message(self, message: A2AMessage) -> bool:
        """Verify message authenticity and integrity"""
        # Verify signature
        sender_key = hashlib.sha256(f"ord_key_{message.sender_id}".encode()).hexdigest()[:64]
        return message.verify(sender_key)
    
    async def log_audit_event(
        self,
        agent_id: str,
        action: str,
        resource: str,
        outcome: str
    ) -> AuditEntry:
        """Create immutable audit log entry (Feature 21)"""
        entry_id = f"audit-{int(time.time())}-{len(self.audit_log)}"
        
        # Hash chain for tamper evidence
        data = f"{entry_id}:{agent_id}:{action}:{resource}:{outcome}:{time.time()}"
        current_hash = hashlib.sha256(f"{data}:{self.last_hash}".encode()).hexdigest()
        
        entry = AuditEntry(
            entry_id=entry_id,
            agent_id=agent_id,
            action=action,
            resource=resource,
            outcome=outcome,
            timestamp=time.time(),
            hash_chain=current_hash
        )
        
        self.audit_log.append(entry)
        self.last_hash = current_hash
        
        return entry
    
    async def check_financial_action(self, action_type: str, context: Dict) -> Dict:
        """Check if financial action is approved"""
        policy = self.policies.get("fin_approval")
        if not policy:
            return {"approved": True}
        
        for rule in policy.rules:
            if rule.get("action") == action_type:
                if rule.get("requires_approval"):
                    return {
                        "approved": False,
                        "requires_approval": True,
                        "message": f"Financial action '{action_type}' requires CEO approval via PM"
                    }
        
        return {"approved": True}
    
    async def generate_compliance_report(self) -> Dict:
        """Generate compliance status report (Feature 23)"""
        return {
            "policies_active": len([p for p in self.policies.values() if p.enabled]),
            "total_violations": len(self.violations),
            "unresolved_violations": len([v for v in self.violations if not v.resolved]),
            "audit_entries": len(self.audit_log),
            "compliance_score": max(0, 100 - len(self.violations) * 2),
            "recommendations": [
                "Continue monitoring code for hardcoded secrets",
                "Review UI responsiveness across all projects"
            ]
        }
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Process Sec-specific tasks"""
        task_type = task.get("type", "unknown")
        
        if task_type == "audit_code":
            return await self.audit_code(task.get("code", ""), task.get("agent_id"))
        
        elif task_type == "verify_message":
            message = task.get("message")
            if isinstance(message, dict):
                message = A2AMessage(**message)
            return {"verified": await self.verify_message(message)}
        
        elif task_type == "check_financial":
            return await self.check_financial_action(
                task.get("action_type"),
                task.get("context", {})
            )
        
        elif task_type == "compliance_report":
            return await self.generate_compliance_report()
        
        elif task_type == "log_audit":
            entry = await self.log_audit_event(
                task.get("agent_id"),
                task.get("action"),
                task.get("resource"),
                task.get("outcome")
            )
            return {"entry_id": entry.entry_id}
        
        return {"error": f"Unknown task type: {task_type}"}
