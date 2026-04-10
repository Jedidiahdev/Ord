import asyncio
import time
from typing import Any, Dict, List
from dataclasses import dataclass

from agents.base_agent import BaseAgent


@dataclass
class DesignSpec:
    spec_id: str
    project_id: str
    title: str
    color_palette: Dict[str, str]
    typography: Dict
    components: List[str]
    layouts: List[Dict]
    interactions: List[Dict]
    created_at: float


@dataclass
class DesignVariation:
    variation_id: int
    project_id: str
    name: str
    description: str
    mock_html: str
    schema: Dict
    pitch: str
    creative_direction: str


class DesignAgent(BaseAgent):
    """Ord-Design: Design system + 20-variation experimentation lead."""

    CREATIVE_DIRECTIONS = [
        "minimalist", "bold", "professional", "playful", "dark", "data-rich", "editorial", "neo-brutalist", "glassmorphism", "ai-copilot",
        "kanban", "calendar-first", "chat-centric", "analytics-heavy", "founder-dashboard", "mobile-first", "enterprise", "startup", "fintech", "developer-tooling",
    ]

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-design",
            name="Ord-Design",
            role="UI/UX Designer",
            layer=3,
            orchestrator=orchestrator,
            memory_manager=memory_manager,
        )
        self.design_specs: Dict[str, DesignSpec] = {}
        self.variations: List[DesignVariation] = []
        self.logger.info("🎨 Ord-Design initialized | Visual Storyteller")

    def get_capabilities(self) -> List[str]:
        return ["ui_design", "ux_design", "shadcn_ui", "rapid_prototyping", "20_variation_experimentation"]

    async def generate_variation(self, project_id: str, variation_id: int, creative_direction: str) -> DesignVariation:
        mock_html = f"""
<div class=\"min-h-screen bg-background text-foreground p-8\">
  <header class=\"mb-6\">
    <h1 class=\"text-3xl font-bold text-primary\">Variation {variation_id}</h1>
    <p class=\"text-muted-foreground\">{creative_direction} shadcn/ui direction</p>
  </header>
  <section class=\"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4\">
    <article class=\"rounded-lg border p-4\">Card A</article>
    <article class=\"rounded-lg border p-4\">Card B</article>
    <article class=\"rounded-lg border p-4\">Card C</article>
  </section>
</div>
"""
        schema = {
            "tables": ["users", "projects", "experiments", f"variation_{variation_id}_events"],
            "indexes": ["projects.owner_id", "experiments.project_id", f"variation_{variation_id}_events.timestamp"],
        }
        return DesignVariation(
            variation_id=variation_id,
            project_id=project_id,
            name=f"Variation {variation_id}",
            description=f"{creative_direction.title()} UI concept",
            mock_html=mock_html,
            schema=schema,
            pitch=f"{creative_direction.title()} concept optimized for validation speed.",
            creative_direction=creative_direction,
        )

    async def run_20_variation_experiment(self, project_id: str, project_name: str) -> Dict[str, Any]:
        frontend = self.orchestrator.agents.get("ord-fullstack-a") if self.orchestrator else None
        backend = self.orchestrator.agents.get("ord-fullstack-b") if self.orchestrator else None

        async def build_one(variation_id: int, direction: str) -> Dict[str, Any]:
            design = await self.generate_variation(project_id, variation_id, direction)
            self.variations.append(design)
            front_task = {"type": "20_variation_frontend", "variation_id": variation_id, "creative_direction": direction, "project_name": project_name}
            back_task = {"type": "20_variation_backend", "variation_id": variation_id, "creative_direction": direction, "project_name": project_name}
            frontend_result = await frontend.process_task(front_task) if frontend else {}
            backend_result = await backend.process_task(back_task) if backend else {}
            return {"design": design, "frontend": frontend_result, "backend": backend_result}

        tasks = [build_one(i + 1, d) for i, d in enumerate(self.CREATIVE_DIRECTIONS)]
        results = await asyncio.gather(*tasks)
        return {
            "status": "completed",
            "project_id": project_id,
            "project_name": project_name,
            "variation_count": len(results),
            "variations": [
                {
                    "variation_id": row["design"].variation_id,
                    "creative_direction": row["design"].creative_direction,
                    "mock_html": row["design"].mock_html,
                    "db_schema": row["backend"].get("schema", {}),
                    "frontend_files": row["frontend"].get("files", []),
                }
                for row in results
            ],
            "message": "20 interactive shadcn/ui mocks + schema drafts generated.",
        }

    async def process_task(self, task: Dict) -> Dict[str, Any]:
        task_type = task.get("type", "unknown")
        if task_type == "20_variation_experiment":
            return await self.run_20_variation_experiment(task.get("project_id", "proj"), task.get("project_name", "project"))
        return {"error": f"Unknown task type: {task_type}"}
