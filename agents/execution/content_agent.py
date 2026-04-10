import time
from typing import Any, Dict, List
from dataclasses import dataclass

from agents.base_agent import BaseAgent


@dataclass
class ContentPiece:
    content_id: str
    project_id: str
    type: str
    title: str
    content: str
    tone: str
    status: str
    created_at: float


class ContentAgent(BaseAgent):
    """Ord-Content: messaging + launch collateral."""

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-content",
            name="Ord-Content",
            role="Content Designer",
            layer=3,
            orchestrator=orchestrator,
            memory_manager=memory_manager,
        )
        self.content_library: Dict[str, ContentPiece] = {}

    def get_capabilities(self) -> List[str]:
        return ["copywriting", "documentation", "launch_messaging", "variation_narratives"]

    async def create_variation_briefs(self, project_id: str, variations: List[Dict[str, Any]]) -> Dict[str, Any]:
        briefs = []
        for variation in variations:
            vid = variation.get("variation_id")
            direction = variation.get("creative_direction", "default")
            copy = f"Variation {vid} ({direction}) is optimized for rapid validation and executive clarity."
            briefs.append({"variation_id": vid, "brief": copy})
        return {"project_id": project_id, "briefs": briefs}

    async def process_task(self, task: Dict) -> Dict[str, Any]:
        if task.get("type") == "variation_briefs":
            return await self.create_variation_briefs(task.get("project_id", "proj"), task.get("variations", []))
        return {"error": f"Unknown task type: {task.get('type', 'unknown')}"}
