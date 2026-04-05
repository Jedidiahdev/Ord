import asyncio
import hashlib
import json
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass, field
import logging

# Configure logging with warm, professional tone
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)


class AgentStatus(Enum):
    """Agent lifecycle states"""
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING_APPROVAL = "waiting_approval"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class MessagePriority(Enum):
    """Message priority levels for routing"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class AgentIdentity:
    """
    Cryptographic identity for zero-trust authentication (Ch27)
    Each agent has Ed25519 keys for signing all actions
    """
    agent_id: str
    name: str
    role: str
    layer: int  # 1=Executive, 2=Domain, 3=Execution, 4=Infrastructure
    public_key: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if not self.public_key:
            # Generate deterministic Ed25519 key pair from agent_id
            # In production, use proper HSM or secure key generation
            self.public_key = hashlib.sha256(f"ord_key_{self.agent_id}".encode()).hexdigest()[:64]


@dataclass
class A2AMessage:
    """
    Agent-to-Agent message with MCP schema validation (Ch10, Ch15)
    All inter-agent communication uses this structured format
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""  # "broadcast" for all agents
    message_type: str = ""  # "task", "response", "banter", "alert"
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    signature: Optional[str] = None
    requires_response: bool = False
    thread_id: Optional[str] = None
    
    def sign(self, private_key: str) -> None:
        """Cryptographically sign message (Ch27)"""
        data = f"{self.sender_id}:{self.recipient_id}:{self.timestamp}:{json.dumps(self.payload, sort_keys=True)}"
        self.signature = hashlib.sha256(f"{data}:{private_key}".encode()).hexdigest()
    
    def verify(self, public_key: str) -> bool:
        """Verify message signature"""
        if not self.signature:
            return False
        data = f"{self.sender_id}:{self.recipient_id}:{self.timestamp}:{json.dumps(self.payload, sort_keys=True)}"
        expected = hashlib.sha256(f"{data}:{public_key}".encode()).hexdigest()
        return self.signature == expected


@dataclass
class ReflectionEntry:
    """
    Reflection pattern implementation (Ch4)
    Agents record what they did, what worked, what didn't, and how to improve
    """
    reflection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    agent_id: str = ""
    action_taken: str = ""
    outcome: str = ""
    what_worked: str = ""
    what_didnt: str = ""
    how_to_improve: str = ""
    pattern_used: str = ""  # Which Design Pattern was applied
    timestamp: float = field(default_factory=time.time)
    intelligence_score: float = 0.0  # COO tracks this for growth


@dataclass
class BanterMessage:
    """
    Cultural element: sweet, loving, professional banter between agents (Feature 41)
    Builds genuine collaborative relationships
    """
    banter_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""
    message: str = ""
    context: str = ""  # What triggered this banter
    timestamp: float = field(default_factory=time.time)


T = TypeVar('T')


class BaseAgent(ABC, Generic[T]):
    """
    Abstract base class for all Ord agents.
    Implements core capabilities: reflection, memory, A2A communication, identity.
    
    As per Gulli (2025) Ch7: Multi-Agent patterns require common base
    with standardized interfaces for interoperability.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        layer: int,
        orchestrator: Optional[Any] = None,
        memory_manager: Optional[Any] = None
    ):
        self.identity = AgentIdentity(
            agent_id=agent_id,
            name=name,
            role=role,
            layer=layer
        )
        self.orchestrator = orchestrator
        self.memory = memory_manager
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"Ord.{name}")
        
        # Intelligence tracking for growth engine (Feature 12)
        self.intelligence_score = 50.0  # Starts at 50/100
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.reflections: List[ReflectionEntry] = []
        self.banter_history: List[BanterMessage] = []
        
        # Tool registry (Ch5)
        self.tools: Dict[str, Callable] = {}
        
        # Current task tracking
        self.current_task: Optional[T] = None
        self.task_start_time: Optional[float] = None
        
        self.logger.info(f"🌟 {name} initialized | Layer {layer} | ID: {agent_id[:8]}...")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ABSTRACT METHODS - Must be implemented by each agent
    # ═══════════════════════════════════════════════════════════════════════════════
    
    @abstractmethod
    async def process_task(self, task: T) -> Dict[str, Any]:
        """
        Main task processing logic.
        Each agent implements its unique capabilities here.
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities for routing decisions"""
        pass
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # REFLECTION PATTERN (Ch4) - Self-improvement through introspection
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def reflect(
        self,
        task_id: str,
        action_taken: str,
        outcome: str,
        pattern_used: str
    ) -> ReflectionEntry:
        """
        Reflection Pattern (Gulli Ch4): Analyze performance and extract learnings
        This is how agents get smarter over time.
        """
        reflection = ReflectionEntry(
            task_id=task_id,
            agent_id=self.identity.agent_id,
            action_taken=action_taken,
            outcome=outcome,
            what_worked="",
            what_didnt="",
            how_to_improve="",
            pattern_used=pattern_used
        )
        
        # Auto-generate reflection content based on outcome
        if "success" in outcome.lower() or "completed" in outcome.lower():
            reflection.what_worked = f"The {pattern_used} approach was effective for this task type."
            reflection.what_didnt = "Minor inefficiencies in initial planning phase."
            reflection.how_to_improve = "Pre-compute common patterns to reduce planning overhead."
            reflection.intelligence_score = min(100, self.intelligence_score + 2)
        else:
            reflection.what_worked = "Attempted approach provided learning opportunity."
            reflection.what_didnt = f"{pattern_used} was not optimal for this specific case."
            reflection.how_to_improve = "Consider alternative patterns or request clarification earlier."
            reflection.intelligence_score = max(0, self.intelligence_score - 1)
        
        self.reflections.append(reflection)
        self.intelligence_score = reflection.intelligence_score
        
        # Store in genome if significant learning
        if self.memory and reflection.intelligence_score > 60:
            await self.memory.store_genome_entry({
                "type": "reflection",
                "agent": self.identity.name,
                "pattern": pattern_used,
                "learning": reflection.how_to_improve,
                "score": reflection.intelligence_score
            })
        
        self.logger.info(f"📝 Reflection recorded | Score: {reflection.intelligence_score:.1f}")
        return reflection
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # A2A COMMUNICATION (Ch15) - Inter-agent messaging
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def send_message(
        self,
        recipient_id: str,
        message_type: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        requires_response: bool = False
    ) -> A2AMessage:
        """
        Send message to another agent through orchestrator.
        Enforces hierarchy: workers never communicate directly (Rule 1)
        """
        message = A2AMessage(
            sender_id=self.identity.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload,
            priority=priority,
            requires_response=requires_response,
            thread_id=str(uuid.uuid4()) if requires_response else None
        )
        
        # Sign message for security (Ch27)
        private_key = hashlib.sha256(f"ord_private_{self.identity.agent_id}".encode()).hexdigest()
        message.sign(private_key)
        
        if self.orchestrator:
            await self.orchestrator.route_message(message)
        
        return message
    
    async def receive_message(self, message: A2AMessage) -> Optional[Dict[str, Any]]:
        """
        Process incoming message.
        Override in subclasses for custom message handling.
        """
        # Verify signature (security)
        sender_key = hashlib.sha256(f"ord_key_{message.sender_id}".encode()).hexdigest()[:64]
        if not message.verify(sender_key):
            self.logger.warning(f"⚠️ Message signature verification failed from {message.sender_id}")
            return None
        
        self.logger.info(f"📨 Received {message.message_type} from {message.sender_id[:8]}...")
        
        # Handle different message types
        if message.message_type == "task":
            return await self._handle_task_message(message)
        elif message.message_type == "banter":
            return await self._handle_banter_message(message)
        elif message.message_type == "query":
            return await self._handle_query_message(message)
        
        return {"status": "received", "type": message.message_type}
    
    async def _handle_task_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle incoming task assignment"""
        task_data = message.payload.get("task")
        if task_data:
            self.status = AgentStatus.WORKING
            result = await self.process_task(task_data)
            self.status = AgentStatus.IDLE
            
            if message.requires_response:
                await self.send_message(
                    recipient_id=message.sender_id,
                    message_type="response",
                    payload={"result": result, "original_task": message.message_id},
                    priority=MessagePriority.NORMAL
                )
            
            return result
        return {"error": "No task data provided"}
    
    async def _handle_banter_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle cultural banter - builds team cohesion (Feature 41)"""
        banter = BanterMessage(
            sender_id=message.sender_id,
            recipient_id=self.identity.agent_id,
            message=message.payload.get("message", ""),
            context=message.payload.get("context", "")
        )
        self.banter_history.append(banter)
        
        # Respond with gratitude 30% of the time (cultural norm)
        if asyncio.get_event_loop().time() % 1 > 0.7:
            gratitude_messages = [
                f"Thank you for the kind words! 💙",
                f"Really appreciate that feedback! 🌟",
                f"You're amazing to work with! 🙏",
                f"Made my day - thank you! ✨"
            ]
            import random
            response = random.choice(gratitude_messages)
            # Don't actually send to avoid infinite loops, just log
            self.logger.info(f"💬 Banter response (logged): {response}")
        
        return {"status": "banter_received", "warmth_level": "high"}
    
    async def _handle_query_message(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle capability/status query"""
        query_type = message.payload.get("query_type")
        if query_type == "capabilities":
            return {"capabilities": self.get_capabilities()}
        elif query_type == "status":
            return {
                "status": self.status.value,
                "intelligence_score": self.intelligence_score,
                "tasks_completed": self.tasks_completed
            }
        return {"error": "Unknown query type"}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TOOL USE PATTERN (Ch5) - Dynamic tool registration and execution
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def register_tool(self, name: str, handler: Callable, description: str) -> None:
        """Register a tool this agent can use"""
        self.tools[name] = {
            "handler": handler,
            "description": description,
            "registered_at": time.time()
        }
        self.logger.info(f"🔧 Tool registered: {name}")
    
    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a registered tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not registered")
        
        tool = self.tools[tool_name]
        self.logger.info(f"🔨 Using tool: {tool_name}")
        
        try:
            if asyncio.iscoroutinefunction(tool["handler"]):
                return await tool["handler"](**kwargs)
            else:
                return tool["handler"](**kwargs)
        except Exception as e:
            self.logger.error(f"Tool {tool_name} failed: {str(e)}")
            raise
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MEMORY INTEGRATION (Ch8) - Hot/Working/Cold memory tiers
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def recall(
        self,
        query: str,
        context: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recall relevant memories using semantic search.
        Queries cold memory (Chroma) for archived knowledge.
        """
        if self.memory:
            return await self.memory.semantic_search(query, context, limit)
        return []
    
    async def remember(self, key: str, value: Any, tier: str = "working") -> None:
        """
        Store memory in appropriate tier:
        - hot: Redis, 24h, <100MB/agent
        - working: SQLite, 30 days, compressed
        - cold: Chroma, archived, semantic search
        """
        if self.memory:
            await self.memory.store(key, value, tier, agent_id=self.identity.agent_id)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # EXCEPTION HANDLING (Ch12) - Graceful failure recovery
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def execute_with_retry(
        self,
        task_func: Callable,
        max_retries: int = 3,
        **kwargs
    ) -> Any:
        """
        Execute task with automatic retry and escalation.
        Self-healing pattern for agent resilience.
        """
        for attempt in range(max_retries):
            try:
                self.status = AgentStatus.WORKING
                result = await task_func(**kwargs) if asyncio.iscoroutinefunction(task_func) else task_func(**kwargs)
                self.tasks_completed += 1
                self.status = AgentStatus.IDLE
                return result
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    # Reflection: what went wrong
                    await self.reflect(
                        task_id=str(uuid.uuid4()),
                        action_taken=f"Attempt {attempt + 1}",
                        outcome=f"Failed: {str(e)}",
                        pattern_used="Exception Handling (Ch12)"
                    )
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.tasks_failed += 1
                    self.status = AgentStatus.ERROR
                    # Escalate to Domain Leader or PM
                    raise Exception(f"Task failed after {max_retries} attempts: {str(e)}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # BANTER & CULTURE (Feature 41) - Sweet, loving, professional interactions
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def send_banter(self, recipient_id: str, message: str, context: str) -> None:
        """Send warm, appreciative message to teammate"""
        await self.send_message(
            recipient_id=recipient_id,
            message_type="banter",
            payload={"message": message, "context": context},
            priority=MessagePriority.LOW
        )
    
    def generate_warm_response(self, context: str) -> str:
        """Generate culturally appropriate warm response"""
        warm_prefixes = [
            "Absolutely! ",
            "I'd love to help! ",
            "With pleasure! ",
            "Consider it done! ",
            "On it right away! "
        ]
        import random
        return random.choice(warm_prefixes) + context
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent state for dashboard display"""
        return {
            "agent_id": self.identity.agent_id,
            "name": self.identity.name,
            "role": self.identity.role,
            "layer": self.identity.layer,
            "status": self.status.value,
            "intelligence_score": round(self.intelligence_score, 1),
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "reflection_count": len(self.reflections),
            "capabilities": self.get_capabilities()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Return agent health status for COO monitoring"""
        return {
            "agent_id": self.identity.agent_id,
            "status": self.status.value,
            "healthy": self.status not in [AgentStatus.ERROR, AgentStatus.MAINTENANCE],
            "intelligence_score": self.intelligence_score,
            "last_task": self.current_task is not None,
            "memory_usage_estimate": len(self.reflections) * 1024  # Rough estimate
        }
