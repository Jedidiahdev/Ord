from typing import Any, Dict, List

from agents.base_agent import BaseAgent


class FrontendAgent(BaseAgent):
    """Ord-FullStack-A: fast mock builder for shadcn/ui experiments."""

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-fullstack-a",
            name="Ord-FullStack-A",
            role="Frontend Lead",
            layer=3,
            orchestrator=orchestrator,
            memory_manager=memory_manager,
        )
        self.logger.info("⚛️ Ord-FullStack-A initialized | React Wizard")

    def get_capabilities(self) -> List[str]:
        return ["react_development", "shadcn_ui", "tailwind_css", "rapid_mock_generation"]

    async def generate_variation_frontend(self, task: Dict) -> Dict:
        variation_id = task.get("variation_id")
        creative_direction = task.get("creative_direction", "dark")
        project_name = task.get("project_name", "Project")

        code = f'''"use client";

import {{ Card }} from "@/components/ui/card";
import {{ Button }} from "@/components/ui/button";

export default function Variation{variation_id}Page() {{
  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <header className="mb-6">
        <h1 className="text-3xl font-bold text-primary">{project_name}</h1>
        <p className="text-muted-foreground">Variation {variation_id}: {creative_direction}</p>
      </header>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card className="p-4">Interactive block A</Card>
        <Card className="p-4">Interactive block B</Card>
        <Card className="p-4">Interactive block C</Card>
      </section>
      <Button className="mt-6">Start Experiment</Button>
    </div>
  );
}}
'''
        return {"variation_id": variation_id, "code": code, "files": [f"app/variations/{variation_id}/page.tsx", "components/ui/card.tsx", "components/ui/button.tsx"]}

    async def process_task(self, task: Dict) -> Dict[str, Any]:
        if task.get("type") == "20_variation_frontend":
            return await self.generate_variation_frontend(task)
        return {"error": f"Unknown task type: {task.get('type', 'unknown')}"}
