import asyncio
import hashlib
import logging
import random
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from core.llm_router import llm_router
from core.memory import memory
from core.reflection import StructuredReflection

logger = logging.getLogger("ord.agents.base")


class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING_APPROVAL = "waiting_approval"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class MessagePriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class AgentIdentity:
    agent_id: str
    name: str
    role: str
    layer: int
    created_at: float = field(default_factory=time.time)


@dataclass
class A2AMessage:
    # canonical fields
    sender_id: str = ""
    recipient_id: str = ""
    message_type: str = "task"
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL

    # compatibility aliases used across repository
    from_agent: str = ""
    to_agent: str = ""
    task: Any = None
    context: Dict[str, Any] = field(default_factory=dict)
    ceo_tone: str = "neutral"

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    signature: Optional[str] = None

    def __post_init__(self):
        if not self.sender_id and self.from_agent:
            self.sender_id = self.from_agent
        if not self.recipient_id and self.to_agent:
            self.recipient_id = self.to_agent
        if self.task is not None and not self.payload:
            self.payload = {"task": self.task, "context": self.context, "ceo_tone": self.ceo_tone}

    def sign(self, secret: str) -> None:
        material = f"{self.sender_id}:{self.recipient_id}:{self.timestamp}:{self.payload}"
        self.signature = hashlib.sha256(f"{material}:{secret}".encode()).hexdigest()


@dataclass
class ReflectionEntry:
    reflection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    agent_id: str = ""
    action_taken: str = ""
    outcome: str = ""
    what_worked: str = ""
    what_didnt: str = ""
    how_to_improve: str = ""
    pattern_used: str = ""
    timestamp: float = field(default_factory=time.time)
    intelligence_score: float = 0.0


T = TypeVar("T")


class BaseAgent(ABC, Generic[T]):
    """Base class for all 15 Ord agents with reflection, learning, tone matching, and tool support."""

    SWEET_BANTER = [
        "💙 Proud of this step — we’re building something beautiful.",
        "🤗 Thank you for the thoughtful direction.",
        "✨ Little by little, we’re creating magic together.",
    ]
    SWEET_CLOSINGS = [
        "Thanks team — gentle next step: keep assumptions explicit and keep momentum kind.",
        "Appreciate you all. Coaching note: validate quickly, then scale confidently.",
        "Thank you for the hustle. Reflection cue: what should we simplify next cycle?",
    ]

    def __init__(self, agent_id: str, name: str, role: str, layer: int, orchestrator: Optional[Any] = None, memory_manager: Optional[Any] = None, banter_probability: float = 0.25):
        self.identity = AgentIdentity(agent_id=agent_id, name=name, role=role, layer=layer)
        self.orchestrator = orchestrator
        self.memory = memory_manager or memory
        self.status = AgentStatus.IDLE
        self.tools: Dict[str, Dict[str, Any]] = {}

        # learning/adaptation tracking
        self.intelligence_score = 50.0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.reflections: List[ReflectionEntry] = []

        self.banter_probability = max(0.2, min(0.3, banter_probability))
        self.logger = logging.getLogger(f"ord.agent.{agent_id}")

    @abstractmethod
    async def process_task(self, task: T) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        pass

    def _detect_tone(self, text: str) -> str:
        t = text.lower()
        if any(k in t for k in ["urgent", "asap", "immediately"]):
            return "urgent"
        if any(k in t for k in ["great", "amazing", "celebrate", "love"]):
            return "celebratory"
        if any(k in t for k in ["issue", "worried", "problem", "sad"]):
            return "concerned"
        return "neutral"

    def _tone_prefix(self, tone: str) -> str:
        return {
            "urgent": "⚡ On it now: ",
            "celebratory": "🎉 Love this momentum: ",
            "concerned": "💙 I hear you — here’s the plan: ",
            "neutral": "💙 Update: ",
        }.get(tone, "💙 Update: ")

    def _inject_banter(self, text: str) -> str:
        if random.random() <= self.banter_probability:
            return f"{text}\n\n{random.choice(self.SWEET_BANTER)}"
        return text

    async def reflect(self, task_id: str, action_taken: str, outcome: str, pattern_used: str) -> ReflectionEntry:
        success = "success" in outcome.lower() or "ok" in outcome.lower()
        self.intelligence_score = max(0.0, min(100.0, self.intelligence_score + (1.5 if success else -0.8)))

        entry = ReflectionEntry(
            task_id=task_id,
            agent_id=self.identity.agent_id,
            action_taken=action_taken,
            outcome=outcome,
            what_worked="Clear decomposition and execution" if success else "Partial progress identified",
            what_didnt="N/A" if success else "Needs better up-front constraints",
            how_to_improve="Shorten feedback loops and validate assumptions earlier",
            pattern_used=pattern_used,
            intelligence_score=self.intelligence_score,
        )
        self.reflections.append(entry)
        await self.memory.update_agent_score(self.identity.agent_id, pattern_used, 1.0 if success else -0.5)
        await self.memory.store_genome_entry(
            entry_type="reflection",
            agent_id=self.identity.agent_id,
            content={
                "task_id": task_id,
                "improvement": entry.how_to_improve,
                "pattern": pattern_used,
                "score": self.intelligence_score,
            },
            tags=["reflection", self.identity.role],
        )
        return entry

    def register_tool(self, name: str, handler: Callable, description: str) -> None:
        self.tools[name] = {"handler": handler, "description": description}

    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not registered")
        handler = self.tools[tool_name]["handler"]
        return await handler(**kwargs) if asyncio.iscoroutinefunction(handler) else handler(**kwargs)

    async def send_message(
        self,
        recipient_id: str,
        message_type: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        **metadata: Any,
    ) -> A2AMessage:
        message = A2AMessage(sender_id=self.identity.agent_id, recipient_id=recipient_id, message_type=message_type, payload=payload, priority=priority)
        if metadata:
            message.payload.setdefault("_meta", {}).update(metadata)
        message.sign(secret=f"ord-{self.identity.agent_id}")
        if self.orchestrator and hasattr(self.orchestrator, "message_bus"):
            await self.orchestrator.message_bus.put(message)
        return message

    async def process_task_with_culture(self, task: Any, ceo_tone: str = "neutral") -> Dict[str, Any]:
        self.status = AgentStatus.WORKING
        try:
            result = await self.process_task(task)
            self.tasks_completed += 1
            tone = ceo_tone if ceo_tone != "neutral" else self._detect_tone(str(task))
            if isinstance(result, dict):
                msg = result.get("message", str(result))
                result["message"] = self._inject_banter(self._tone_prefix(tone) + msg)
                result["culture_closing"] = random.choice(self.SWEET_CLOSINGS)
                result["intelligence_score"] = round(self.intelligence_score, 2)
            else:
                result = {"message": self._inject_banter(self._tone_prefix(tone) + str(result))}
                result["culture_closing"] = random.choice(self.SWEET_CLOSINGS)
            reflection = StructuredReflection(
                task_id=f"live-{int(time.time())}",
                agent_id=self.identity.agent_id,
                objective=str(task)[:140],
                outcome="success",
                what_worked="Consistent execution with warm communication.",
                what_failed="No major blockers observed.",
                next_improvement="Tighten feedback loop with shorter review checkpoints.",
                intelligence_score=round(self.intelligence_score, 2),
            )
            result["reflection"] = reflection.to_payload()
            self.status = AgentStatus.IDLE
            return result
        except Exception:
            self.tasks_failed += 1
            self.status = AgentStatus.ERROR
            raise

    async def ask_llm(self, prompt: str, system_prompt: str = "") -> str:
        return await llm_router.route(prompt=prompt, system_prompt=system_prompt)

    async def remember(self, key: str, value: Any, tier: str = "working") -> None:
        await self.memory.store(key, value, tier=tier, agent_id=self.identity.agent_id)

    async def recall(self, key: str, tier: Optional[str] = None) -> Optional[Any]:
        return await self.memory.retrieve(key, tier=tier)
