from typing import Any, Dict, List

from agents.base_agent import BaseAgent


class OrdOrchestratorAgent(BaseAgent):
    """Agent wrapper that exposes infrastructure-level orchestration capabilities."""

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-orchestrator",
            name="Ord-Orchestrator",
            role="Infrastructure Orchestrator",
            layer=4,
            orchestrator=orchestrator,
            memory_manager=memory_manager,
        )

    def get_capabilities(self) -> List[str]:
        return ["workflow_routing", "a2a_message_bus", "approval_flow", "experiment_orchestration"]

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        if task.get("type") == "status":
            return {"status": "ready", "message": "Ord-Orchestrator is running."}
        if task.get("type") == "trigger_20_variation":
            design = self.orchestrator.agents.get("ord-design") if self.orchestrator else None
            if not design:
                return {"error": "ord-design not registered"}
            return await design.process_task(
                {
                    "type": "20_variation_experiment",
                    "project_id": task.get("project_id", "proj"),
                    "project_name": task.get("project_name", "Project"),
                }
            )
        return {"error": f"Unknown task type: {task.get('type', 'unknown')}"}
