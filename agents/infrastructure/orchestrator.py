import asyncio
import importlib
import importlib.util
import logging
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

PYDANTIC_AVAILABLE = "pydantic" in sys.modules or importlib.util.find_spec("pydantic") is not None
pydantic_mod = importlib.import_module("pydantic") if PYDANTIC_AVAILABLE else None

if pydantic_mod is not None:
    BaseModel = pydantic_mod.BaseModel
    Field = pydantic_mod.Field
else:
    class BaseModel:
        def __init__(self, **kwargs: Any):
            for key, value in kwargs.items():
                setattr(self, key, value)

    def Field(default_factory=None):
        return default_factory() if default_factory is not None else None

from agents.base_agent import A2AMessage, BaseAgent
from core.feature_backbone import FeatureBackbone
from integrations.voice.briefing import VoiceBriefingService

logger = logging.getLogger("ord.orchestrator")


class OrchestratorState(BaseModel):
    task_id: str
    project_id: Optional[str] = None
    ceo_tone: str = "neutral"
    input_type: str = "text"
    current_agent: Optional[str] = None
    agent_queue: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    results: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class BusEnvelope:
    sender_id: str
    recipient_id: str
    payload: Dict[str, Any]
    created_at: float = field(default_factory=time.time)


class Orchestrator:
    """Ord-Orchestrator: execution router + message bus + experiment kickoff."""

    BANTER_LIBRARY = [
        "❤️ Ord-CFA just whispered 'we're profitable' — I'm blushing!",
        "🎉 Ord-Design's UI is so clean it made Ord-Sec cry happy tears",
        "✨ Team just leveled up — Ord-COO is doing a happy dance!",
    ]

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_bus: "asyncio.Queue[BusEnvelope]" = asyncio.Queue()
        self.banter_probability = 0.25
        self.feature_backbone = FeatureBackbone()
        self.voice_briefing = VoiceBriefingService()

    def register_agent(self, name_or_agent: Any, maybe_agent: Optional[BaseAgent] = None):
        if maybe_agent is None:
            agent = name_or_agent
            name = agent.identity.agent_id
        else:
            name = str(name_or_agent)
            agent = maybe_agent
        self.agents[name] = agent
        logger.info("Registered: %s", name)

    async def route(self, task: str, chat_id: Optional[int] = None, user_id: Optional[int] = None,
                    input_type: str = "text", ceo_tone: str = "neutral", agent_override: Optional[str] = None,
                    image_path: Optional[str] = None) -> Dict[str, Any]:
        state = OrchestratorState(
            task_id=f"task_{datetime.now(timezone.utc).timestamp()}",
            project_id=f"proj_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            ceo_tone=ceo_tone,
            input_type=input_type,
            context={"task": task, "chat_id": chat_id, "user_id": user_id, "image_path": image_path},
        )
        state.agent_queue = [agent_override] if agent_override else self._route_task(task)
        state.current_agent = state.agent_queue[0] if state.agent_queue else None

        for aid in state.agent_queue:
            agent = self.agents.get(aid)
            if not agent:
                continue
            payload = self._build_agent_payload(aid, state)
            msg = A2AMessage(sender_id="ord-orchestrator", recipient_id=aid, payload=payload)
            await self.message_bus.put(BusEnvelope(sender_id=msg.sender_id, recipient_id=aid, payload=payload))
            try:
                state.results[aid] = await agent.process_task(payload.get("task", payload))
            except Exception as exc:
                state.results[aid] = {"error": str(exc)}

        final_response = f"Execution completed for {task}"
        if random.random() < self.banter_probability:
            final_response = f"{final_response}\n\n{random.choice(self.BANTER_LIBRARY)}"

        return {
            "message": final_response,
            "project_id": state.project_id,
            "results": state.results,
            "agent_status": await self.get_agent_status(),
            "reflection": {
                "task_id": state.task_id,
                "wins": "Cross-functional execution completed.",
                "improvements": "Increase parallelization for repeated no-op steps.",
                "next_experiment": "Run governed experiment bundle with financial twin checks.",
            },
            "feature_backbone": self.feature_backbone.summary(),
        }

    async def voice_first_briefing(self, command: str, response_payload: Dict[str, Any]) -> Dict[str, Any]:
        briefing = self.voice_briefing.build_briefing(command, response_payload)
        return {"narration": briefing.narration, "daa_visuals": briefing.daa_visuals}

    def _route_task(self, task: str) -> List[str]:
        text = task.lower()
        if any(k in text for k in ["20", "variation", "experiment", "mock"]):
            return ["ord-design", "ord-fullstack-a", "ord-fullstack-b", "ord-content", "ord-review"]
        if any(k in text for k in ["deploy", "vercel"]):
            return ["ord-review", "ord-se"]
        if any(k in text for k in ["github", "branch", "pr", "commit"]):
            return ["ord-se", "ord-review"]
        if any(k in text for k in ["finance", "stripe"]):
            return ["ord-cfa"]
        return ["ord-pm"]

    def _build_agent_payload(self, agent_id: str, state: OrchestratorState) -> Dict[str, Any]:
        task_text = state.context.get("task", "")
        project_name = state.context.get("project_name", "Ord Project")
        if agent_id == "ord-design" and "variation" in task_text.lower():
            return {"task": {"type": "20_variation_experiment", "project_id": state.project_id, "project_name": project_name}}
        if agent_id == "ord-content":
            variations = state.results.get("ord-design", {}).get("variations", [])
            return {"task": {"type": "variation_briefs", "project_id": state.project_id, "variations": variations}}
        if agent_id == "ord-review":
            return {"task": {"type": "review_pr", "pr_id": "pr-simulated", "branch": "feature/simulated", "code": str(state.results)}}
        return {"task": {"type": "noop", "raw": task_text}}

    async def process_approval(self, approval_id: str, decision: str, chat_id: Optional[int] = None) -> Dict[str, Any]:
        _ = chat_id
        status = "approved" if decision == "yes" else "cancelled" if decision == "no" else "revising"
        return {"approval_id": approval_id, "status": status}

    async def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: {
                "name": agent.identity.role,
                "status": agent.status.value,
                "intelligence_score": agent.intelligence_score,
                "layer": agent.identity.layer,
            }
            for name, agent in self.agents.items()
        }

    async def process_messages(self) -> None:
        while True:
            envelope = await self.message_bus.get()
            logger.debug("A2A %s -> %s", envelope.sender_id, envelope.recipient_id)


orchestrator = Orchestrator()
