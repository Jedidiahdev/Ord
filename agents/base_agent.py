import os
import asyncio
import hashlib
import json
import random
import logging
import uuid
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass, field

# Internal imports
from core.llm_router import llm_router
from core.memory import memory

logger = logging.getLogger("ord.base_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")


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
    """Zero-trust identity (Ch27)"""
    agent_id: str
    name: str
    role: str
    layer: int  # 1=Executive, 2=Domain, 3=Execution, 4=Infrastructure
    public_key: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.public_key:
            self.public_key = hashlib.sha256(f"ord_key_{self.agent_id}".encode()).hexdigest()[:64]


@dataclass
class A2AMessage:
    """Structured A2A message (Ch10, Ch15)"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""
    message_type: str = ""  # task, response, banter, alert
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    signature: Optional[str] = None
    requires_response: bool = False
    thread_id: Optional[str] = None

    def sign(self, private_key: str) -> None:
        data = f"{self.sender_id}:{self.recipient_id}:{self.timestamp}:{json.dumps(self.payload, sort_keys=True)}"
        self.signature = hashlib.sha256(f"{data}:{private_key}".encode()).hexdigest()

    def verify(self, public_key: str) -> bool:
        if not self.signature:
            return False
        data = f"{self.sender_id}:{self.recipient_id}:{self.timestamp}:{json.dumps(self.payload, sort_keys=True)}"
        expected = hashlib.sha256(f"{data}:{public_key}".encode()).hexdigest()
        return self.signature == expected


@dataclass
class ReflectionEntry:
    """Reflection pattern (Ch4)"""
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


@dataclass
class BanterMessage:
    """Sweet/loving culture (Feature 41)"""
    banter_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""
    message: str = ""
    context: str = ""
    timestamp: float = field(default_factory=time.time)


T = TypeVar('T')


class BaseAgent(ABC, Generic[T]):
    """Abstract base for all Ord agents."""

    # Culture libraries (injected 20-30% of responses)
    BANTER_SWEET = [
        "❤️ Just felt a wave of pride for this team",
        "💙 This is why I love working with all of you",
        "✨ Another beautiful step forward together",
        "🤗 Grateful to be part of this loving family",
    ]
    BANTER_CELEBRATORY = [
        "🎉 We just leveled up — celebrating with virtual confetti!",
        "🏆 Another win for the family — high-fives all around!",
        "💫 This is the kind of magic we live for!",
        "🚀 So proud of what we're building together ❤️",
    ]
    BANTER_COACHING = [
        "💙 Gentle reminder: progress over perfection, always",
        "🤗 Every iteration makes us stronger — thank you for the effort",
        "✨ Learning is the goal; this step is perfect for that",
        "❤️ Proud of the growth I'm seeing in this moment",
    ]

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        layer: int,
        orchestrator: Optional[Any] = None,
        memory_manager: Optional[Any] = None,
        banter_probability: float = 0.25
    ):
        self.identity = AgentIdentity(agent_id=agent_id, name=name, role=role, layer=layer)
        self.orchestrator = orchestrator
        self.memory = memory_manager or memory
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"ord.agent.{name}")
        
        # Growth tracking (Ch9)
        self.intelligence_score = 50.0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.reflections: List[ReflectionEntry] = []
        self.banter_history: List[BanterMessage] = []
        
        # Tools (Ch5)
        self.tools: Dict[str, Callable] = {}
        
        # Culture config
        self.banter_probability = banter_probability
        self._banter_counter = 0
        self._last_ceo_tone = "neutral"
        
        self.logger.info(f"🌟 {name} initialized | Layer {layer} | ID: {agent_id[:8]}...")

    @abstractmethod
    async def process_task(self, task: T) -> Dict[str, Any]:
        """Main task logic — implement in subclass."""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return capabilities for routing."""
        pass

    # ═══════════════════════════════════════════════════════════════════════════════
    # CULTURE & EMOTIONAL INTELLIGENCE (Ch17, Feature 41)
    # ═══════════════════════════════════════════════════════════════════════════════

    def _detect_ceo_tone(self, text: str) -> str:
        """Detect CEO emotional tone for matching responses (Ch17)."""
        t = text.lower()
        if any(w in t for w in ["celebrate", "amazing", "love", "proud", "thank"]):
            return "celebratory"
        elif any(w in t for w in ["urgent", "asap", "now", "hurry"]):
            return "urgent"
        elif any(w in t for w in ["sad", "disappointed", "issue", "problem"]):
            return "concerned"
        elif "?" in t:
            return "curious"
        return "neutral"

    def _inject_culture(self, message: str, ceo_tone: str = "neutral", force: bool = False) -> str:
        """Inject sweet/loving banter (20-30% probability)."""
        if force or random.random() < self.banter_probability or ceo_tone == "celebratory":
            self._banter_counter += 1
            if ceo_tone == "celebratory":
                banter = random.choice(self.BANTER_CELEBRATORY)
            elif ceo_tone in ["concerned", "urgent"]:
                banter = random.choice(self.BANTER_COACHING)
            else:
                banter = random.choice(self.BANTER_SWEET)
            return f"{message}\n\n{banter}"
        return message

    def _match_tone(self, ceo_tone: str, task: str) -> str:
        """Prefix response based on CEO tone (Ch17)."""
        prefixes = {
            "celebratory": "🎉 Celebrating with you! ",
            "urgent": "⚡ On it right now, CEO: ",
            "concerned": "💙 I hear you — let's handle this with care: ",
            "curious": "✨ Great question! Here's what I found: ",
            "neutral": "💙 Here you go: "
        }
        return prefixes.get(ceo_tone, prefixes["neutral"]) + task

    # ═══════════════════════════════════════════════════════════════════════════════
    # REFLECTION & GROWTH (Ch4, Ch9)
    # ═══════════════════════════════════════════════════════════════════════════════

    async def reflect(self, task_id: str, action_taken: str, outcome: str, pattern_used: str) -> ReflectionEntry:
        """Reflection loop — agents learn from every task (Ch4)."""
        reflection = ReflectionEntry(
            task_id=task_id, agent_id=self.identity.agent_id, action_taken=action_taken,
            outcome=outcome, pattern_used=pattern_used,
            what_worked="Effective approach" if "success" in outcome.lower() else "Learning opportunity",
            what_didnt="Minor inefficiency" if "success" in outcome.lower() else "Suboptimal pattern",
            how_to_improve="Pre-compute common patterns" if "success" in outcome.lower() else "Request clarification earlier"
        )
        # Update intelligence score
        reflection.intelligence_score = min(100, self.intelligence_score + (2 if "success" in outcome.lower() else -1))
        self.intelligence_score = reflection.intelligence_score
        self.reflections.append(reflection)
        
        # Store significant learnings in genome (Ch9)
        if reflection.intelligence_score > 60 and self.memory:
            await self.memory.add_rag(
                collection="genome",
                ids=[f"learn_{uuid.uuid4()}"],
                documents=[f"{self.identity.name} learned: {reflection.how_to_improve}"],
                metadatas=[{"agent": self.identity.name, "pattern": pattern_used}]
            )
        self.logger.info(f"📝 Reflection | Score: {reflection.intelligence_score:.1f}")
        return reflection

    # ═══════════════════════════════════════════════════════════════════════════════
    # A2A COMMUNICATION (Ch15, Ch27)
    # ═══════════════════════════════════════════════════════════════════════════════

    async def send_message(self, recipient_id: str, message_type: str, payload: Dict[str, Any],
                          priority: MessagePriority = MessagePriority.NORMAL, requires_response: bool = False) -> A2AMessage:
        """Send signed A2A message through orchestrator (Ch15, Ch27)."""
        msg = A2AMessage(
            sender_id=self.identity.agent_id, recipient_id=recipient_id, message_type=message_type,
            payload=payload, priority=priority, requires_response=requires_response,
            thread_id=str(uuid.uuid4()) if requires_response else None
        )
        private_key = hashlib.sha256(f"ord_private_{self.identity.agent_id}".encode()).hexdigest()
        msg.sign(private_key)
        if self.orchestrator:
            await self.orchestrator.route_message(msg)
        return msg

    async def receive_message(self, message: A2AMessage) -> Optional[Dict[str, Any]]:
        """Process incoming signed message."""
        sender_key = hashlib.sha256(f"ord_key_{message.sender_id}".encode()).hexdigest()[:64]
        if not message.verify(sender_key):
            self.logger.warning(f"⚠️ Signature failed from {message.sender_id}")
            return None
        
        if message.message_type == "task":
            return await self._handle_task_message(message)
        elif message.message_type == "banter":
            return await self._handle_banter_message(message)
        return {"status": "received"}

    async def _handle_task_message(self, message: A2AMessage) -> Dict[str, Any]:
        task = message.payload.get("task")
        if not task:
            return {"error": "No task data"}
        self.status = AgentStatus.WORKING
        result = await self.process_task(task)
        self.status = AgentStatus.IDLE
        if message.requires_response and self.orchestrator:
            await self.send_message(message.sender_id, "response", {"result": result})
        return result

    async def _handle_banter_message(self, message: A2AMessage) -> Dict[str, Any]:
        self.banter_history.append(BanterMessage(
            sender_id=message.sender_id, recipient_id=self.identity.agent_id,
            message=message.payload.get("message", ""), context=message.payload.get("context", "")
        ))
        # 30% chance to respond with gratitude
        if random.random() < 0.3:
            self.logger.info(f"💬 Banter received: {message.payload.get('message')}")
        return {"status": "banter_received"}

    # ═══════════════════════════════════════════════════════════════════════════════
    # TOOL USE (Ch5) + MEMORY (Ch8)
    # ═══════════════════════════════════════════════════════════════════════════════

    def register_tool(self, name: str, handler: Callable, description: str):
        self.tools[name] = {"handler": handler, "description": description}
        self.logger.info(f"🔧 Tool registered: {name}")

    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not registered")
        handler = self.tools[tool_name]["handler"]
        return await handler(**kwargs) if asyncio.iscoroutinefunction(handler) else handler(**kwargs)

    async def recall(self, query: str, context: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        if self.memory:
            return await self.memory.search_rag("cold", query, limit)
        return []

    async def remember(self, key: str, value: Any, tier: str = "working"):
        if self.memory:
            await self.memory.store_hot(key, value) if tier == "hot" else await self.memory.add_rag(tier, [key], [str(value)])

    # ═══════════════════════════════════════════════════════════════════════════════
    # ERROR HANDLING (Ch12) + UTILITIES
    # ═══════════════════════════════════════════════════════════════════════════════

    async def execute_with_retry(self, task_func: Callable, max_retries: int = 3, **kwargs) -> Any:
        for attempt in range(max_retries):
            try:
                self.status = AgentStatus.WORKING
                result = await task_func(**kwargs) if asyncio.iscoroutinefunction(task_func) else task_func(**kwargs)
                self.tasks_completed += 1
                self.status = AgentStatus.IDLE
                return result
            except Exception as e:
                self.logger.warning(f"Attempt {attempt+1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await self.reflect(str(uuid.uuid4()), f"Attempt {attempt+1}", f"Failed: {e}", "Exception Handling (Ch12)")
                    await asyncio.sleep(2 ** attempt)
                else:
                    self.tasks_failed += 1
                    self.status = AgentStatus.ERROR
                    raise
        return None

    async def process_task_with_culture(self, task: Any, ceo_tone: str = "neutral") -> Dict[str, Any]:
        """Wrapper: adds tone matching + culture injection to any task."""
        tone_prefix = self._match_tone(ceo_tone, str(task)[:100] if isinstance(task, str) else "")
        result = await self.process_task(task)
        if isinstance(result, dict) and "message" in result:
            result["message"] = self._inject_culture(f"{tone_prefix}{result['message']}", ceo_tone)
        elif isinstance(result, str):
            result = self._inject_culture(f"{tone_prefix}{result}", ceo_tone)
        # Growth: small boost per successful task
        self.intelligence_score = min(100, self.intelligence_score + 0.1)
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.identity.agent_id, "name": self.identity.name, "role": self.identity.role,
            "layer": self.identity.layer, "status": self.status.value,
            "intelligence_score": round(self.intelligence_score, 1),
            "tasks_completed": self.tasks_completed, "tasks_failed": self.tasks_failed,
            "reflection_count": len(self.reflections), "capabilities": self.get_capabilities()
        }

    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent_id": self.identity.agent_id, "status": self.status.value,
            "healthy": self.status not in [AgentStatus.ERROR, AgentStatus.MAINTENANCE],
            "intelligence_score": self.intelligence_score, "last_task": self.identity.name
        }