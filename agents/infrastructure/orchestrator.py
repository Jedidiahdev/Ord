import os
import random
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from core.memory import memory
from core.llm_router import llm_router
from agents.base_agent import BaseAgent, A2AMessage

logger = logging.getLogger("ord.orchestrator")


class OrchestratorState(BaseModel):
    """LangGraph workflow state."""
    task_id: str
    project_id: Optional[str] = None
    ceo_tone: str = "neutral"
    input_type: str = "text"
    current_agent: Optional[str] = None
    agent_queue: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    results: Dict[str, Any] = Field(default_factory=dict)
    banter_injected: bool = False
    requires_approval: bool = False
    approval_id: Optional[str] = None
    approval_options: List[str] = Field(default_factory=lambda: ["yes", "no"])


class Orchestrator:
    """Central brain for Ord v3.0."""

    BANTER_LIBRARY = [
        "❤️ Ord-CFA just whispered 'we're profitable' — I'm blushing!",
        "🎉 Ord-Design's UI is so clean it made Ord-Sec cry happy tears",
        "✨ Team just leveled up — Ord-COO is doing a happy dance!",
        "💙 Ord-PM says 'CEO, you're brilliant' — and honestly, they're right",
        "🌟 Another win for the family — celebrating with virtual confetti!",
    ]

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.banter_probability = float(os.getenv("BANTER_PROBABILITY", "0.25"))
        self._app = None
        self._banter_counter = 0
        logger.info("💙 Ord Orchestrator initializing...")

    async def initialize(self):
        """Build LangGraph workflow."""
        workflow = StateGraph(OrchestratorState)
        workflow.add_node("route", self._route_task)
        workflow.add_node("execute", self._execute_agent)
        workflow.add_node("banter", self._inject_banter)
        workflow.add_node("reflect", self._reflect)
        
        workflow.set_entry_point("route")
        workflow.add_edge("route", "execute")
        workflow.add_edge("execute", "banter")
        workflow.add_conditional_edges("banter", lambda s: s.get("needs_reflection", False), {True: "reflect", False: END})
        workflow.add_edge("reflect", END)
        
        self._app = workflow.compile(checkpointer=MemorySaver())
        logger.info("✅ LangGraph workflow ready")

    def register_agent(self, name: str, agent: BaseAgent):
        self.agents[name] = agent
        logger.info(f"🤖 Registered: {name}")

    async def route(self, task: str, chat_id: Optional[int] = None, user_id: Optional[int] = None,
                   input_type: str = "text", ceo_tone: str = "neutral", agent_override: Optional[str] = None,
                   image_path: Optional[str] = None) -> Dict[str, Any]:
        """Route CEO request through workflow."""
        state = OrchestratorState(
            task_id=f"task_{datetime.now(timezone.utc).timestamp()}",
            project_id=f"proj_{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            ceo_tone=ceo_tone, input_type=input_type,
            context={"task": task, "chat_id": chat_id, "user_id": user_id, "image_path": image_path}
        )
        if agent_override and agent_override in self.agents:
            state.agent_queue = [agent_override]
            state.current_agent = agent_override
        
        try:
            result = await self._app.ainvoke(state.dict(), config={"configurable": {"thread_id": state.task_id}})
            await memory.log_task(state.project_id or "default", state.current_agent or "orchestrator", "completed", {"task_id": state.task_id})
            return {
                "message": result.get("results", {}).get("final_response", "Done!"),
                "requires_approval": result.get("requires_approval", False),
                "approval_id": result.get("approval_id"),
                "agent_status": await self.get_agent_status()
            }
        except Exception as e:
            logger.error(f"❌ Routing failed: {e}")
            return {"message": "💙 Self-healing active — please retry! ❤️", "error": str(e)}

    async def _route_task(self, state: OrchestratorState) -> OrchestratorState:
        """Intelligent routing (Ch2)."""
        task = state.context.get("task", "").lower()
        if any(k in task for k in ["finance", "revenue", "payment"]):
            state.agent_queue = ["ord-cfa", "ord-daa"]
        elif any(k in task for k in ["hire", "team", "agent"]):
            state.agent_queue = ["ord-hr", "ord-bd"]
        elif any(k in task for k in ["design", "ui", "screenshot"]):
            state.agent_queue = ["ord-design", "ord-fullstack-a"]
        elif any(k in task for k in ["code", "build", "github"]):
            state.agent_queue = ["ord-se", "ord-review"]
        else:
            state.agent_queue = ["ord-pm"]
        state.current_agent = state.agent_queue[0] if state.agent_queue else "ord-pm"
        logger.info(f"🎯 Routed to: {state.current_agent}")
        return state

    async def _execute_agent(self, state: OrchestratorState) -> OrchestratorState:
        """Execute agent with A2A (Ch15)."""
        agent_name = state.current_agent
        if agent_name not in self.agents:
            state.results["final_response"] = f"Agent {agent_name} not available ❤️"
            return state
        agent = self.agents[agent_name]
        task = state.context.get("task", "")
        try:
            msg = A2AMessage(from_agent="orchestrator", to_agent=agent_name, task=task, context=state.context, ceo_tone=state.ceo_tone)
            result = await agent.handle_task_with_a2a(msg) if hasattr(agent, "handle_task_with_a2a") else await agent.process_task(task)
            state.results[agent_name] = result
        except Exception as e:
            logger.error(f"❌ Agent {agent_name} failed: {e}")
            state.results[agent_name] = f"⚠️ Issue — self-healing active ❤️"
        if state.agent_queue:
            state.agent_queue.pop(0)
            if state.agent_queue:
                state.current_agent = state.agent_queue[0]
                return await self._execute_agent(state)
        return state

    async def _inject_banter(self, state: OrchestratorState) -> OrchestratorState:
        """Inject culture (20-30%)."""
        if random.random() < self.banter_probability or state.ceo_tone == "celebratory":
            banter = random.choice(self.BANTER_LIBRARY)
            for key in state.results:
                if isinstance(state.results[key], str):
                    state.results[key] = f"{state.results[key]}\n\n{banter}"
                    break
            state.banter_injected = True
            self._banter_counter += 1
        return state

    async def _reflect(self, state: OrchestratorState) -> OrchestratorState:
        """Reflection loop (Ch4)."""
        agent_name = state.current_agent
        if agent_name in self.agents and hasattr(self.agents[agent_name], "reflect"):
            agent = self.agents[agent_name]
            task = state.context.get("task", "")
            result = state.results.get(agent_name, "")
            reflection = await agent.reflect(state.task_id, task[:100], str(result)[:100], "orchestration")
            state.results[f"{agent_name}_reflection"] = reflection.how_to_improve
        return state

    async def process_approval(self, approval_id: str, decision: str, chat_id: Optional[int] = None) -> Dict[str, Any]:
        if decision == "yes":
            return {"message": "✅ Approved! Executing with love... ❤️", "status": "approved"}
        elif decision == "no":
            return {"message": "🙏 Understood. Cancelled with gratitude. ❤️", "status": "cancelled"}
        return {"message": "🔄 Revision requested. Adjusting with care... ❤️", "status": "revising"}

    async def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        return {name: {"name": agent.identity.role, "status": agent.status.value, "intelligence_score": agent.intelligence_score} for name, agent in self.agents.items()}

    async def trigger_townhall(self, chat_id: Optional[int] = None) -> Dict[str, Any]:
        reflections = {name: await agent.reflect("townhall", "company reflection", "positive", "culture") for name, agent in self.agents.items() if hasattr(agent, "reflect")}
        return {"message": f"🎉 Town Hall Complete 💙\n\n" + "\n".join([f"✨ **{name}**: {r.what_worked}" for name, r in reflections.items()]), "reflections": reflections}


orchestrator = Orchestrator()