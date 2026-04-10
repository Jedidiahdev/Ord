import asyncio
import logging
import os
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from core.llm_router import llm_router
from core.memory import memory

logger = logging.getLogger("ord.core.orchestrator")


@dataclass
class BusMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""
    message_type: str = "task"
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class OrchestratorState:
    task_id: str
    input_text: str
    ceo_tone: str = "neutral"
    context: Dict[str, Any] = field(default_factory=dict)
    execution_plan: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    needs_reflection: bool = True
    banter_ratio: float = 0.25
    done: bool = False


class Orchestrator:
    """Central brain built on LangGraph with dynamic planning + memory checkpoints."""

    BANTER = [
        "💙 Proud of this team — we're doing beautiful work together.",
        "✨ Tiny win, big momentum. Love this pace.",
        "🤗 Thank you team — this collaboration is everything.",
    ]

    def __init__(self) -> None:
        self.agents: Dict[str, Any] = {}
        self.message_bus: "asyncio.Queue[BusMessage]" = asyncio.Queue()
        self.checkpointer = MemorySaver()
        self._graph = self._build_graph()
        self.banter_probability = float(os.getenv("BANTER_PROBABILITY", "0.25"))

    def register_agent(self, agent: Any) -> None:
        self.agents[agent.identity.agent_id] = agent
        logger.info("Registered agent: %s", agent.identity.agent_id)

    def _build_graph(self):
        graph = StateGraph(dict)
        graph.add_node("plan", self._dynamic_plan)
        graph.add_node("execute", self._execute_plan)
        graph.add_node("banter", self._inject_banter)
        graph.add_node("reflect", self._reflection_loop)
        graph.add_node("finish", self._finish)

        graph.set_entry_point("plan")
        graph.add_edge("plan", "execute")
        graph.add_edge("execute", "banter")
        graph.add_conditional_edges("banter", self._needs_reflection, {True: "reflect", False: "finish"})
        graph.add_edge("reflect", "finish")
        graph.add_edge("finish", END)

        return graph.compile(checkpointer=self.checkpointer)

    async def route(self, task: str, ceo_tone: str = "neutral", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        state = OrchestratorState(
            task_id=f"task-{int(time.time())}-{uuid.uuid4().hex[:8]}",
            input_text=task,
            ceo_tone=ceo_tone,
            context=context or {},
            banter_ratio=self.banter_probability,
        )
        result = await self._graph.ainvoke(state.__dict__, config={"configurable": {"thread_id": state.task_id}})
        return result

    async def _dynamic_plan(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Build dynamic graph execution queue from task intent + registered capabilities."""
        text = state.get("input_text", "").lower()
        plan: List[str] = []

        if any(k in text for k in ["design", "ui", "figma"]):
            plan += [aid for aid in self.agents if "design" in aid]
        if any(k in text for k in ["code", "api", "build", "backend", "frontend"]):
            plan += [aid for aid in self.agents if any(k in aid for k in ["se", "frontend", "backend", "review"])]
        if any(k in text for k in ["finance", "revenue", "pricing"]):
            plan += [aid for aid in self.agents if any(k in aid for k in ["cfa", "daa"])]
        if not plan:
            plan = [next(iter(self.agents), "ord-pm")]

        # preserve order and uniqueness
        deduped = []
        for agent_id in plan:
            if agent_id not in deduped and agent_id in self.agents:
                deduped.append(agent_id)

        state["execution_plan"] = deduped
        await memory.log_task("dynamic", "orchestrator", "plan", {"agents": deduped})
        return state

    async def _execute_plan(self, state: Dict[str, Any]) -> Dict[str, Any]:
        plan: List[str] = state.get("execution_plan", [])
        results: Dict[str, Any] = state.get("results", {})

        for agent_id in plan:
            agent = self.agents.get(agent_id)
            if not agent:
                continue
            bus_msg = BusMessage(sender_id="orchestrator", recipient_id=agent_id, payload={"task": state.get("input_text", ""), "tone": state.get("ceo_tone", "neutral")})
            await self.message_bus.put(bus_msg)

            try:
                agent_result = await agent.process_task_with_culture(state.get("input_text", ""), ceo_tone=state.get("ceo_tone", "neutral"))
                results[agent_id] = agent_result
                await memory.log_task("dynamic", agent_id, "execute_success", {"task_id": state.get("task_id")})
            except Exception as exc:
                results[agent_id] = {"error": str(exc)}
                await memory.log_task("dynamic", agent_id, "execute_error", {"error": str(exc)})

        state["results"] = results
        return state

    async def _inject_banter(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Inject loving banter around 20-30% target frequency."""
        if random.random() <= float(state.get("banter_ratio", self.banter_probability)):
            state.setdefault("results", {})["banter"] = random.choice(self.BANTER)
        return state

    def _needs_reflection(self, state: Dict[str, Any]) -> bool:
        return bool(state.get("needs_reflection", True))

    async def _reflection_loop(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Reflection loop: ask each participating agent to reflect and update score."""
        summary: Dict[str, Any] = {}
        for agent_id in state.get("execution_plan", []):
            agent = self.agents.get(agent_id)
            if not agent:
                continue
            reflection = await agent.reflect(
                task_id=state.get("task_id", "unknown"),
                action_taken=state.get("input_text", "")[:120],
                outcome="success" if "error" not in str(state.get("results", {}).get(agent_id, "")) else "failure",
                pattern_used="langgraph-reflection",
            )
            summary[agent_id] = reflection.how_to_improve
        state.setdefault("results", {})["reflection"] = summary
        return state

    async def _finish(self, state: Dict[str, Any]) -> Dict[str, Any]:
        tone = state.get("ceo_tone", "neutral")
        body = f"Execution completed for: {state.get('input_text', '')}"
        if tone == "urgent":
            body = f"⚡ {body}"
        elif tone == "celebratory":
            body = f"🎉 {body}"
        state.setdefault("results", {})["final_response"] = body
        state["done"] = True
        return state

    async def process_messages(self) -> None:
        while True:
            message = await self.message_bus.get()
            logger.debug("A2A bus delivered %s -> %s (%s)", message.sender_id, message.recipient_id, message.message_type)


orchestrator = Orchestrator()
