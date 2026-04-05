"""
Ord v3.0 - Frontend Lead Agent (Ord-FullStack-A)
React + Tailwind + shadcn/ui expert, client-side specialist.

Patterns Implemented:
- Parallelization (Ch3): Component development in parallel
- Tool Use (Ch5): Frontend build tools, component libraries
- Reflection (Ch4): UI/UX improvement

Responsibilities:
1. React application architecture
2. Tailwind CSS styling
3. shadcn/ui component implementation
4. Client-side state management
5. Responsive design implementation
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, MessagePriority


@dataclass
class ComponentSpec:
    """React component specification"""
    component_id: str
    name: str
    props: List[Dict]
    styling: Dict
    interactions: List[str]
    accessibility: Dict
    code: str


class FrontendAgent(BaseAgent):
    """
    Ord-FullStack-A: Frontend Lead Agent
    
    The React wizard who crafts beautiful user interfaces.
    FullStack-A specializes in client-side excellence with
    shadcn/ui and Tailwind CSS.
    """
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-fullstack-a",
            name="Ord-FullStack-A",
            role="Frontend Lead",
            layer=3,
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        self.components: Dict[str, ComponentSpec] = {}
        
        # Tech stack
        self.tech_stack = {
            "framework": "React 18",
            "styling": "Tailwind CSS 3.4",
            "components": "shadcn/ui",
            "state": "Zustand / React Query",
            "build": "Vite",
            "type_check": "TypeScript"
        }
        
        self.logger.info("⚛️ Ord-FullStack-A initialized | React Wizard")
    
    def get_capabilities(self) -> List[str]:
        return [
            "react_development",
            "tailwind_css",
            "shadcn_ui",
            "component_architecture",
            "responsive_design",
            "state_management",
            "frontend_optimization",
            "accessibility"
        ]
    
    async def create_component(self, spec: Dict) -> ComponentSpec:
        """Create React component from specification"""
        component_id = f"comp-{int(time.time())}"
        
        name = spec.get("name", "Component")
        props = spec.get("props", [])
        
        # Generate component code
        code = self._generate_component_code(name, props, spec)
        
        component = ComponentSpec(
            component_id=component_id,
            name=name,
            props=props,
            styling=spec.get("styling", {}),
            interactions=spec.get("interactions", []),
            accessibility=spec.get("accessibility", {}),
            code=code
        )
        
        self.components[component_id] = component
        
        return component
    
    def _generate_component_code(self, name: str, props: List[Dict], spec: Dict) -> str:
        """Generate React component code"""
        props_interface = "\n".join([
            f"  {p['name']}{'' if p.get('required') else '?'}: {p['type']};"
            for p in props
        ])
        
        props_destructure = ", ".join([p['name'] for p in props])
        props_destructure = f"{{ {props_destructure} }}" if props_destructure else ""
        
        code = f'''"use client";

import React from "react";
import {{ cn }} from "@/lib/utils";

interface {name}Props {{
{props_interface}
}}

export function {name}({props_destructure}: {name}Props) {{
  return (
    <div className={{cn(
      "rounded-lg border border-border bg-card p-6",
      spec.get("styling", {{}}).get("className", "")
    )}}>
      {/* Component content */}
    </div>
  );
}}
'''
        return code
    
    async def implement_page(self, page_spec: Dict) -> Dict:
        """Implement complete page with multiple components"""
        page_name = page_spec.get("name", "Page")
        sections = page_spec.get("sections", [])
        
        components_code = []
        
        for section in sections:
            component = await self.create_component({
                "name": section.get("component_name", "Section"),
                "props": section.get("props", []),
                "styling": section.get("styling", {})
            })
            components_code.append(component.code)
        
        page_code = f'''"use client";

import React from "react";
import {{ cn }} from "@/lib/utils";

{chr(10).join(components_code)}

export default function {page_name}Page() {{
  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Page sections */}
      </div>
    </main>
  );
}}
'''
        
        return {
            "page_name": page_name,
            "code": page_code,
            "components": len(components_code)
        }
    
    async def generate_variation_frontend(self, task: Dict) -> Dict:
        """Generate frontend code for 20-variation experiment"""
        variation_id = task.get("variation_id")
        creative_direction = task.get("creative_direction", "default")
        
        # Adjust styling based on creative direction
        theme = self._get_theme_for_direction(creative_direction)
        
        code = f'''"use client";

import React from "react";
import {{ Button }} from "@/components/ui/button";
import {{ Card }} from "@/components/ui/card";

// Variation {variation_id} - {creative_direction}
export default function App() {{
  return (
    <div className="min-h-screen" style={{ background: theme.bg, color: theme.fg }}>
      <header className="p-6 border-b" style={{ borderColor: theme.border }}>
        <h1 className="text-3xl font-bold" style={{ color: theme.accent }}>
          {task.get("project_name", "Project")}
        </h1>
        <p className="mt-2 opacity-80">{creative_direction}</p>
      </header>
      
      <main className="p-6">
        <div className="grid grid-cols-3 gap-4">
          <Card className="p-4">Feature 1</Card>
          <Card className="p-4">Feature 2</Card>
          <Card className="p-4">Feature 3</Card>
        </div>
        
        <Button className="mt-6" style={{ background: theme.accent }}>
          Get Started
        </Button>
      </main>
    </div>
  );
}}
'''
        
        return {
            "variation_id": variation_id,
            "code": code,
            "theme": theme,
            "files": ["page.tsx", "layout.tsx", "globals.css"]
        }
    
    def _get_theme_for_direction(self, direction: str) -> Dict:
        """Get color theme based on creative direction"""
        themes = {
            "minimalist": {"bg": "#FFFFFF", "fg": "#000000", "accent": "#333333", "border": "#E5E5E5"},
            "bold": {"bg": "#0A0A0A", "fg": "#FFFFFF", "accent": "#FF0066", "border": "#333333"},
            "professional": {"bg": "#F5F5F5", "fg": "#1A1A1A", "accent": "#0066CC", "border": "#D1D1D1"},
            "dark": {"bg": "#0A0A0A", "fg": "#E0E0E0", "accent": "#FD651E", "border": "#333333"}
        }
        
        for key in themes:
            if key in direction.lower():
                return themes[key]
        
        return themes["dark"]
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Process Frontend-specific tasks"""
        task_type = task.get("type", "unknown")
        
        if task_type == "create_component":
            component = await self.create_component(task.get("spec", {}))
            return {"component_id": component.component_id, "code": component.code}
        
        elif task_type == "implement_page":
            return await self.implement_page(task.get("page_spec", {}))
        
        elif task_type == "20_variation_frontend":
            return await self.generate_variation_frontend(task)
        
        elif task_type == "get_tech_stack":
            return self.tech_stack
        
        return {"error": f"Unknown task type: {task_type}"}
