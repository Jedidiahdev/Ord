"""
Ord v3.0 - Orchestrator (Ord-Orchestrator)
Lightweight message bus and A2A communication fabric.

Patterns Implemented:
- A2A Communication (Ch15): Inter-agent messaging
- Routing (Ch2): Intelligent message routing
- Model Context Protocol (Ch10): Schema validation

Function: Message bus ONLY - no business logic, just routing
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict

from agents.base_agent import A2AMessage, MessagePriority, AgentStatus


@dataclass
class RouteRule:
    """Message routing rule"""
    from_layer: Optional[int]
    to_layer: Optional[int]
    allowed: bool
    description: str


class Orchestrator:
    """
    Ord-Orchestrator: The Message Bus
    
    The orchestrator is a lightweight message router.
    It has NO business logic - it only routes messages
    between agents according to the hierarchy rules.
    
    RULE 1: Workers NEVER communicate directly with each other
    RULE 2: Domain Leaders coordinate their domains
    RULE 3: Only PM initiates cross-domain workflows
    """
    
    def __init__(self):
        # Agent registry
        self.agents: Dict[str, Any] = {}
        
        # Message queues per agent
        self.message_queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        
        # Message history for audit
        self.message_history: List[A2AMessage] = []
        
        # Routing rules (enforces hierarchy)
        self.routing_rules = self._initialize_routing_rules()
        
        # Subscribers for broadcast messages
        self.broadcast_subscribers: List[str] = []
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        self.logger = self._setup_logging()
        self.logger.info("🔄 Ord-Orchestrator initialized | Message Bus Ready")
    
    def _setup_logging(self):
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        )
        return logging.getLogger("Ord.Orchestrator")
    
    def _initialize_routing_rules(self) -> List[RouteRule]:
        """Initialize routing rules that enforce hierarchy"""
        return [
            # Executive Council (Layer 1) can communicate with everyone
            RouteRule(1, 1, True, "Executive Council internal communication"),
            RouteRule(1, 2, True, "Executive to Domain Leaders"),
            RouteRule(1, 3, True, "Executive to Execution Team (via Domain Leaders preferred)"),
            RouteRule(1, 4, True, "Executive to Infrastructure"),
            
            # Domain Leaders (Layer 2) coordinate their domains
            RouteRule(2, 1, True, "Domain Leaders report to Executive"),
            RouteRule(2, 2, True, "Domain Leaders can communicate"),
            RouteRule(2, 3, True, "Domain Leaders assign to Execution Team"),
            RouteRule(2, 4, True, "Domain Leaders use Infrastructure"),
            
            # Execution Team (Layer 3) - Workers NEVER communicate directly (Rule 1)
            RouteRule(3, 1, True, "Execution Team reports to Executive"),
            RouteRule(3, 2, True, "Execution Team reports to Domain Leaders"),
            RouteRule(3, 3, False, "WORKERS NEVER COMMUNICATE DIRECTLY - Route through PM"),
            RouteRule(3, 4, True, "Execution Team uses Infrastructure"),
            
            # Infrastructure (Layer 4) supports everyone
            RouteRule(4, 1, True, "Infrastructure supports Executive"),
            RouteRule(4, 2, True, "Infrastructure supports Domain Leaders"),
            RouteRule(4, 3, True, "Infrastructure supports Execution Team"),
            RouteRule(4, 4, True, "Infrastructure internal communication"),
        ]
    
    def register_agent(self, agent: Any) -> None:
        """Register an agent with the orchestrator"""
        agent_id = agent.identity.agent_id
        self.agents[agent_id] = agent
        
        # Set orchestrator reference on agent
        agent.orchestrator = self
        
        self.logger.info(f"✅ Agent registered: {agent_id} (Layer {agent.identity.layer})")
    
    async def route_message(self, message: A2AMessage) -> bool:
        """
        Route message to recipient(s).
        Enforces hierarchy rules.
        """
        # Validate message
        if not self._validate_message(message):
            self.logger.warning(f"❌ Invalid message from {message.sender_id}")
            return False
        
        # Check routing rules
        sender = self.agents.get(message.sender_id)
        recipient_id = message.recipient_id
        
        if not sender:
            self.logger.warning(f"❌ Unknown sender: {message.sender_id}")
            return False
        
        # Handle broadcast
        if recipient_id == "broadcast":
            return await self._broadcast_message(message)
        
        # Check hierarchy
        recipient = self.agents.get(recipient_id)
        if not recipient:
            self.logger.warning(f"❌ Unknown recipient: {recipient_id}")
            return False
        
        # Enforce Rule 1: Workers never communicate directly
        if sender.identity.layer == 3 and recipient.identity.layer == 3:
            if sender.identity.agent_id != recipient.identity.agent_id:
                self.logger.error(
                    f"🚫 HIERARCHY VIOLATION: {sender.identity.agent_id} "
                    f"tried to communicate directly with {recipient_id}. "
                    f"Route through PM instead."
                )
                return False
        
        # Route message
        await self._deliver_message(message)
        
        # Store in history
        self.message_history.append(message)
        
        return True
    
    def _validate_message(self, message: A2AMessage) -> bool:
        """Validate message structure (MCP Ch10)"""
        return (
            message.sender_id and
            message.recipient_id and
            message.message_type and
            isinstance(message.payload, dict)
        )
    
    async def _deliver_message(self, message: A2AMessage) -> None:
        """Deliver message to recipient"""
        recipient_id = message.recipient_id
        
        # Add to recipient's queue
        await self.message_queues[recipient_id].put(message)
        
        self.logger.info(
            f"📨 Message delivered: {message.sender_id[:8]}... -> {recipient_id[:8]}... "
            f"({message.message_type})"
        )
        
        # Trigger event handlers
        for handler in self.event_handlers.get(message.message_type, []):
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(f"Event handler error: {e}")
    
    async def _broadcast_message(self, message: A2AMessage) -> bool:
        """Broadcast message to all agents"""
        self.logger.info(f"📢 Broadcasting {message.message_type} from {message.sender_id}")
        
        for agent_id, agent in self.agents.items():
            if agent_id != message.sender_id:  # Don't send to self
                # Create copy for each recipient
                msg_copy = A2AMessage(
                    sender_id=message.sender_id,
                    recipient_id=agent_id,
                    message_type=message.message_type,
                    payload=message.payload,
                    priority=message.priority,
                    timestamp=message.timestamp,
                    signature=message.signature
                )
                await self._deliver_message(msg_copy)
        
        return True
    
    async def process_messages(self) -> None:
        """Main message processing loop"""
        self.logger.info("🔄 Message processing started")
        
        while True:
            for agent_id, queue in self.message_queues.items():
                if not queue.empty():
                    message = await queue.get()
                    agent = self.agents.get(agent_id)
                    
                    if agent:
                        try:
                            await agent.receive_message(message)
                        except Exception as e:
                            self.logger.error(f"Error processing message for {agent_id}: {e}")
            
            await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning
    
    def subscribe_to_event(self, event_type: str, handler: Callable) -> None:
        """Subscribe to event type"""
        self.event_handlers[event_type].append(handler)
    
    def get_agent_status(self) -> Dict[str, Dict]:
        """Get status of all registered agents"""
        return {
            agent_id: {
                "name": agent.identity.name,
                "layer": agent.identity.layer,
                "status": agent.status.value,
                "intelligence_score": agent.intelligence_score
            }
            for agent_id, agent in self.agents.items()
        }
    
    def get_message_stats(self) -> Dict:
        """Get message routing statistics"""
        return {
            "total_messages": len(self.message_history),
            "agents_registered": len(self.agents),
            "messages_by_type": self._count_messages_by_type()
        }
    
    def _count_messages_by_type(self) -> Dict[str, int]:
        """Count messages by type"""
        counts = defaultdict(int)
        for msg in self.message_history:
            counts[msg.message_type] += 1
        return dict(counts)
