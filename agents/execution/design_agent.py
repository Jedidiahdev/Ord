import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, MessagePriority


@dataclass
class DesignSpec:
    """Design specification document"""
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
    """Design variation for experimentation"""
    variation_id: int
    project_id: str
    name: str
    description: str
    mock_html: str
    schema: Dict
    pitch: str
    creative_direction: str


class DesignAgent(BaseAgent):
    """
    Ord-Design: UI/UX Designer Agent
    
    The visual storyteller who creates beautiful experiences.
    Design generates stunning UIs using shadcn/ui and ensures
    every pixel serves the user.
    """
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-design",
            name="Ord-Design",
            role="UI/UX Designer",
            layer=3,
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        self.design_specs: Dict[str, DesignSpec] = {}
        self.variations: List[DesignVariation] = []
        
        # shadcn/ui component library reference
        self.component_library = [
            "button", "card", "dialog", "dropdown-menu", "form",
            "input", "select", "table", "tabs", "toast",
            "avatar", "badge", "calendar", "chart", "checkbox",
            "collapsible", "command", "context-menu", "drawer",
            "hover-card", "label", "menubar", "navigation-menu",
            "popover", "progress", "radio-group", "resizable",
            "scroll-area", "separator", "sheet", "skeleton",
            "slider", "switch", "textarea", "toggle", "tooltip"
        ]
        
        # Ord brand colors
        self.brand_colors = {
            "background": "#0A0A0A",
            "foreground": "#FFFFFF",
            "primary": "#FD651E",
            "primary_foreground": "#FFFFFF",
            "secondary": "#1A1A1A",
            "muted": "#2A2A2A",
            "accent": "#FD651E",
            "border": "#333333"
        }
        
        self.logger.info("🎨 Ord-Design initialized | Visual Storyteller")
    
    def get_capabilities(self) -> List[str]:
        return [
            "ui_design",
            "ux_design",
            "design_specification",
            "shadcn_ui",
            "vision_analysis",
            "design_system",
            "prototyping",
            "design_variation_generation"
        ]
    
    async def create_design_spec(self, project_id: str, requirements: str) -> DesignSpec:
        """Create comprehensive design specification"""
        spec = DesignSpec(
            spec_id=f"spec-{int(time.time())}",
            project_id=project_id,
            title=f"Design Spec for {project_id}",
            color_palette=self.brand_colors,
            typography={
                "heading": "Inter",
                "body": "Inter",
                "mono": "JetBrains Mono"
            },
            components=self._select_components(requirements),
            layouts=self._design_layouts(requirements),
            interactions=self._design_interactions(requirements),
            created_at=time.time()
        )
        
        self.design_specs[spec.spec_id] = spec
        
        return spec
    
    def _select_components(self, requirements: str) -> List[str]:
        """Select appropriate shadcn/ui components"""
        # Simple keyword matching - in production, use LLM
        components = ["button", "card", "dialog", "input"]
        
        if "dashboard" in requirements.lower():
            components.extend(["table", "chart", "tabs"])
        if "form" in requirements.lower():
            components.extend(["form", "select", "checkbox", "textarea"])
        if "navigation" in requirements.lower():
            components.extend(["navigation-menu", "dropdown-menu", "sheet"])
        
        return components
    
    def _design_layouts(self, requirements: str) -> List[Dict]:
        """Design page layouts"""
        return [
            {"name": "header", "type": "fixed", "height": 64},
            {"name": "sidebar", "type": "collapsible", "width": 280},
            {"name": "main", "type": "flex", "direction": "column"},
            {"name": "footer", "type": "fixed", "height": 48}
        ]
    
    def _design_interactions(self, requirements: str) -> List[Dict]:
        """Design interaction patterns"""
        return [
            {"type": "hover", "target": "buttons", "effect": "scale"},
            {"type": "click", "target": "cards", "effect": "ripple"},
            {"type": "scroll", "target": "page", "effect": "parallax"}
        ]
    
    async def generate_variation(
        self,
        project_id: str,
        variation_id: int,
        creative_direction: str
    ) -> DesignVariation:
        """Generate a single design variation"""
        # Generate mock HTML based on creative direction
        colors = self._generate_color_variation(creative_direction)
        
        mock_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Variation {variation_id}</title>
    <style>
        :root {{
            --bg: {colors['bg']};
            --fg: {colors['fg']};
            --accent: {colors['accent']};
        }}
        body {{
            background: var(--bg);
            color: var(--fg);
            font-family: Inter, sans-serif;
        }}
        .accent {{ color: var(--accent); }}
    </style>
</head>
<body>
    <div class="min-h-screen p-8">
        <h1 class="accent text-4xl font-bold">Variation {variation_id}</h1>
        <p class="mt-4 opacity-80">{creative_direction.title()} design approach</p>
        <div class="mt-8 grid grid-cols-3 gap-4">
            <div class="p-4 rounded-lg border border-gray-700">Feature 1</div>
            <div class="p-4 rounded-lg border border-gray-700">Feature 2</div>
            <div class="p-4 rounded-lg border border-gray-700">Feature 3</div>
        </div>
    </div>
</body>
</html>
"""
        
        variation = DesignVariation(
            variation_id=variation_id,
            project_id=project_id,
            name=f"Variation {variation_id}",
            description=f"{creative_direction.title()} design approach",
            mock_html=mock_html,
            schema={"tables": ["users", "projects", "tasks"]},
            pitch=f"A {creative_direction} approach to the project",
            creative_direction=creative_direction
        )
        
        self.variations.append(variation)
        return variation
    
    def _generate_color_variation(self, direction: str) -> Dict:
        """Generate color palette based on creative direction"""
        variations = {
            "minimalist": {"bg": "#FFFFFF", "fg": "#000000", "accent": "#333333"},
            "bold": {"bg": "#0A0A0A", "fg": "#FFFFFF", "accent": "#FF0066"},
            "professional": {"bg": "#F5F5F5", "fg": "#1A1A1A", "accent": "#0066CC"},
            "playful": {"bg": "#FFF5F5", "fg": "#333333", "accent": "#FF6B6B"},
            "dark": {"bg": "#0A0A0A", "fg": "#E0E0E0", "accent": "#FD651E"}
        }
        
        for key in variations:
            if key in direction.lower():
                return variations[key]
        
        return variations["dark"]  # Default to Ord dark theme
    
    async def analyze_screenshot(self, image_data: str) -> Dict:
        """Analyze screenshot for design insights"""
        # In production: use vision model
        return {
            "detected_elements": ["header", "navigation", "cards", "buttons"],
            "color_scheme": "dark",
            "layout_type": "dashboard",
            "recommendations": [
                "Consider increasing contrast for accessibility",
                "Add more whitespace between sections"
            ]
        }
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Process Design-specific tasks"""
        task_type = task.get("type", "unknown")
        
        if task_type == "create_spec":
            spec = await self.create_design_spec(
                task.get("project_id"),
                task.get("requirements", "")
            )
            return {"spec_id": spec.spec_id, "components": spec.components}
        
        elif task_type == "generate_variation":
            variation = await self.generate_variation(
                task.get("project_id"),
                task.get("variation_id"),
                task.get("creative_direction", "default")
            )
            return {
                "variation_id": variation.variation_id,
                "mock_html": variation.mock_html,
                "pitch": variation.pitch
            }
        
        elif task_type == "analyze_screenshot":
            return await self.analyze_screenshot(task.get("image_data", ""))
        
        elif task_type == "20_variation_design":
            # Part of 20-variation factory
            return await self._generate_variation_for_factory(task)
        
        return {"error": f"Unknown task type: {task_type}"}
    
    async def _generate_variation_for_factory(self, task: Dict) -> Dict:
        """Generate design for 20-variation experimentation"""
        variation = await self.generate_variation(
            task.get("project_id"),
            task.get("variation_id"),
            task.get("creative_direction", "default")
        )
        
        return {
            "variation_id": variation.variation_id,
            "mock_html": variation.mock_html,
            "schema": variation.schema,
            "pitch": variation.pitch,
            "estimated_build_time": "3-5 days",
            "estimated_cost": f"${500 + variation.variation_id * 50}"
        }
