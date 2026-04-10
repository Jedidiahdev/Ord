from typing import Any, Dict, List

from agents.base_agent import BaseAgent


class BackendAgent(BaseAgent):
    """Ord-FullStack-B: schema/API generator for variation experiments."""

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-fullstack-b",
            name="Ord-FullStack-B",
            role="Backend Lead",
            layer=3,
            orchestrator=orchestrator,
            memory_manager=memory_manager,
        )
        self.logger.info("🔧 Ord-FullStack-B initialized | Infrastructure Architect")

    def get_capabilities(self) -> List[str]:
        return ["database_design", "api_design", "schema_migration", "deployment_config"]

    def _variation_schema(self, variation_id: int, direction: str) -> Dict[str, Any]:
        return {
            "variation_id": variation_id,
            "creative_direction": direction,
            "tables": [
                {"name": "users", "columns": ["id", "email", "created_at"]},
                {"name": "projects", "columns": ["id", "owner_id", "name", "status"]},
                {"name": "experiments", "columns": ["id", "project_id", "direction", "score"]},
                {"name": f"v{variation_id}_events", "columns": ["id", "experiment_id", "event_type", "timestamp"]},
            ],
            "relationships": [
                "projects.owner_id -> users.id",
                "experiments.project_id -> projects.id",
                f"v{variation_id}_events.experiment_id -> experiments.id",
            ],
        }

    async def generate_variation_backend(self, task: Dict) -> Dict:
        variation_id = int(task.get("variation_id", 1))
        direction = task.get("creative_direction", "dark")
        schema = self._variation_schema(variation_id, direction)
        api_code = f"""from fastapi import FastAPI

app = FastAPI(title=\"Variation {variation_id} API\")

@app.get(\"/api/variation/{variation_id}/summary\")
async def summary():
    return {{\"variation_id\": {variation_id}, \"direction\": \"{direction}\"}}
"""
        return {"variation_id": variation_id, "api_code": api_code, "schema": schema, "files": [f"api/variation_{variation_id}.py", "db/schema.sql"]}

    async def process_task(self, task: Dict) -> Dict[str, Any]:
        if task.get("type") == "20_variation_backend":
            return await self.generate_variation_backend(task)
        return {"error": f"Unknown task type: {task.get('type', 'unknown')}"}
