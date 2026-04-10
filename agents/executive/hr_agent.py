import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent, MessagePriority


@dataclass
class AgentRole:
    role_id: str
    name: str
    description: str
    skills: List[str]
    responsibilities: List[str]
    layer: int
    reports_to: str
    created_at: float


@dataclass
class WelcomeMessage:
    sender: str
    message: str
    role_reference: str


class HRAgent(BaseAgent):
    """Ord-HR: hiring pipeline + onboarding with loving welcomes."""

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__("ord-hr", "Ord-HR", "Human Resources Agent", 2, orchestrator, memory_manager)
        self.agent_roles: Dict[str, AgentRole] = {}
        self.pending_hires: Dict[str, Dict[str, Any]] = {}
        self.welcome_messages: List[WelcomeMessage] = []

    def get_capabilities(self) -> List[str]:
        return [
            "agent_hiring",
            "role_definition",
            "culture_management",
            "onboarding",
            "welcome_ceremonies",
            "growth_tracking",
        ]

    def _parse_role_spec(self, request: str, file_path: Optional[str]) -> Dict[str, Any]:
        role_name = "Ord-NewRole"
        if "security" in request.lower():
            role_name = "Ord-SecOps"
        elif "analytics" in request.lower() or "data" in request.lower():
            role_name = "Ord-Analyst"
        return {
            "role_name": role_name,
            "description": request or "New agent role",
            "skills": ["communication", "problem_solving", "execution"],
            "responsibilities": ["Support executive roadmap", "Ship reliable deliverables"],
            "layer": 3,
            "spec_file": file_path,
        }

    async def initiate_hiring(self, request: str, role_spec_file: Optional[str] = None) -> Dict[str, Any]:
        role_spec = self._parse_role_spec(request, role_spec_file)
        hire_id = f"hire-{int(time.time())}"
        self.pending_hires[hire_id] = {"status": "bd_review", "role_spec": role_spec, "created_at": time.time()}
        await self.send_message(
            recipient_id="ord-bd",
            message_type="query",
            payload={"query_type": "evaluate_hiring", "role_spec": role_spec, "hire_id": hire_id},
            priority=MessagePriority.HIGH,
            requires_response=True,
        )
        return {"status": "consulting_bd", "hire_id": hire_id, "role_spec": role_spec}

    async def process_bd_recommendation(self, hire_id: str, bd_recommendation: str) -> Dict[str, Any]:
        hire = self.pending_hires.get(hire_id)
        if not hire:
            return {"error": "Unknown hire_id"}
        hire["bd_recommendation"] = bd_recommendation
        if bd_recommendation != "hire":
            hire["status"] = "deferred"
            return {"status": "deferred", "message": "BD recommends deferring this hire."}

        hire["status"] = "awaiting_ceo_approval"
        await self.send_message(
            recipient_id="ord-pm",
            message_type="ceo_approval_request",
            payload={"approval_type": "hire_agent", "hire_id": hire_id, "role_spec": hire["role_spec"]},
            priority=MessagePriority.HIGH,
        )
        return {"status": "awaiting_ceo_approval", "hire_id": hire_id}

    async def hire_agent(self, hire_id: str) -> Dict[str, Any]:
        hire = self.pending_hires.get(hire_id)
        if not hire:
            return {"error": "Unknown hire_id"}
        role_spec = hire["role_spec"]
        agent_id = role_spec["role_name"].lower().replace(" ", "-")
        role = AgentRole(
            role_id=agent_id,
            name=role_spec["role_name"],
            description=role_spec["description"],
            skills=role_spec["skills"],
            responsibilities=role_spec["responsibilities"],
            layer=role_spec["layer"],
            reports_to="ord-pm",
            created_at=time.time(),
        )
        self.agent_roles[agent_id] = role
        hire["status"] = "hired"

        await self._announce_new_agent(agent_id, role_spec)
        await self._request_welcome_messages(agent_id)

        return {
            "status": "hired",
            "agent_id": agent_id,
            "role": role.__dict__,
            "welcome_bundle": [m.__dict__ for m in self.welcome_messages[-3:]],
        }

    async def _announce_new_agent(self, agent_id: str, role_spec: Dict[str, Any]) -> None:
        await self.send_message(
            recipient_id="broadcast",
            message_type="announcement",
            payload={
                "announcement_type": "new_agent",
                "agent_id": agent_id,
                "message": f"🌟 Please welcome {agent_id}! We're grateful to have you. 💙",
                "role": role_spec.get("description", ""),
            },
        )

    async def _request_welcome_messages(self, new_agent_id: str) -> None:
        msgs = [
            f"Welcome, {new_agent_id}! You belong here. 💙",
            f"So happy you're joining us, {new_agent_id}! 🚀",
            f"Let's build beautiful things together, {new_agent_id}. ✨",
        ]
        self.welcome_messages.extend([WelcomeMessage(sender=f"agent-{i}", message=m, role_reference=new_agent_id) for i, m in enumerate(msgs)])

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        t = task.get("type", "unknown")
        if t == "initiate_hiring":
            return await self.initiate_hiring(task.get("request", ""), task.get("role_spec_file"))
        if t == "bd_recommendation":
            return await self.process_bd_recommendation(task.get("hire_id", ""), task.get("recommendation", "defer"))
        if t == "hire_agent":
            return await self.hire_agent(task.get("hire_id", ""))
        if t == "get_team_roster":
            return {"roles": {k: v.__dict__ for k, v in self.agent_roles.items()}}
        return {"error": f"Unknown task type: {t}"}
