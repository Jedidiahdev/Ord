"""
Ord v3.0 - Content Designer Agent (Ord-Content)
Copy, branding, marketing assets, and messaging.

Patterns Implemented:
- Learning & Adaptation (Ch9): Tone and style improvement
- Memory Management (Ch8): Brand voice consistency
- Tool Use (Ch5): Content generation tools

Responsibilities:
1. Copywriting for all products
2. Brand voice consistency
3. Marketing asset creation
4. Documentation writing
5. Messaging strategy
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, MessagePriority


@dataclass
class ContentPiece:
    """Content asset"""
    content_id: str
    project_id: str
    type: str  # copy, marketing, documentation, branding
    title: str
    content: str
    tone: str
    status: str
    created_at: float


class ContentAgent(BaseAgent):
    """
    Ord-Content: Content Designer Agent
    
    The wordsmith who gives Ord its voice.
    Content creates compelling copy that converts,
    documents that clarify, and messaging that resonates.
    """
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-content",
            name="Ord-Content",
            role="Content Designer",
            layer=3,
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        self.content_library: Dict[str, ContentPiece] = {}
        
        # Brand voice guidelines
        self.brand_voice = {
            "tone": "sweet, loving, professional, encouraging",
            "style": "clear, concise, warm",
            "avoid": ["harsh", "critical", "cold", "corporate-speak"],
            "emojis": ["💙", "✨", "🚀", "🎉", "🌟"],
            "signature_phrases": [
                "We've got this",
                "Together we can",
                "With love and precision"
            ]
        }
        
        self.logger.info("✍️ Ord-Content initialized | Wordsmith")
    
    def get_capabilities(self) -> List[str]:
        return [
            "copywriting",
            "brand_messaging",
            "marketing_content",
            "documentation",
            "tone_consistency",
            "content_strategy",
            "landing_page_copy",
            "email_campaigns"
        ]
    
    async def write_copy(
        self,
        project_id: str,
        context: str,
        content_type: str = "product_copy"
    ) -> ContentPiece:
        """Write product copy with brand voice"""
        content = ContentPiece(
            content_id=f"content-{int(time.time())}",
            project_id=project_id,
            type=content_type,
            title=f"{context} Copy",
            content=self._generate_copy(context, content_type),
            tone=self.brand_voice["tone"],
            status="draft",
            created_at=time.time()
        )
        
        self.content_library[content.content_id] = content
        
        return content
    
    def _generate_copy(self, context: str, content_type: str) -> str:
        """Generate copy based on context and type"""
        templates = {
            "hero": f"""
# Welcome to {context} 💙

Experience the future of AI-native companies.
Built with love. Designed for excellence.

**Get Started Today** ✨
""",
            "feature": f"""
## {context}

Unlock new possibilities with our cutting-edge {context.lower()} features.
Designed to help you achieve more with less effort.

- Intuitive interface
- Powerful automation
- Seamless integration
""",
            "cta": f"""
Ready to transform your workflow? 🚀

Join thousands of teams already using {context}.
Start your journey today.

[Get Started] [Learn More]
""",
            "product_copy": f"""
{context} - The AI-native solution you've been waiting for.

We believe technology should work *for* you, not against you.
That's why we built {context} with love, precision, and a deep
understanding of what teams actually need.

**What makes us different?** 💙
✨ Sweet, loving automation
🚀 Ruthlessly professional execution  
🌟 Exponentially self-improving systems

Let's build something amazing together.
"""
        }
        
        return templates.get(content_type, templates["product_copy"])
    
    async def create_landing_page(self, project_id: str, project_name: str) -> Dict:
        """Create complete landing page copy"""
        sections = {
            "hero": await self.write_copy(project_id, project_name, "hero"),
            "features": await self.write_copy(project_id, "Key Features", "feature"),
            "cta": await self.write_copy(project_id, project_name, "cta")
        }
        
        return {
            "project_id": project_id,
            "sections": {k: v.content for k, v in sections.items()},
            "meta_description": f"{project_name} - The AI-native solution built with love and precision."
        }
    
    async def write_documentation(self, project_id: str, topic: str) -> ContentPiece:
        """Write technical documentation"""
        doc = ContentPiece(
            content_id=f"doc-{int(time.time())}",
            project_id=project_id,
            type="documentation",
            title=f"{topic} Documentation",
            content=f"""
# {topic}

## Overview

This documentation covers everything you need to know about {topic}.

## Getting Started

1. Install the package
2. Configure your environment
3. Start building

## API Reference

### Methods

- `initialize()` - Set up the component
- `process()` - Execute the main logic
- `cleanup()` - Release resources

## Examples

```javascript
import {{ Component }} from '{project_id}';

const app = new Component();
app.initialize();
```

## Support

Need help? We're here for you! 💙
""",
            tone="professional",
            status="published",
            created_at=time.time()
        )
        
        self.content_library[doc.content_id] = doc
        return doc
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Process Content-specific tasks"""
        task_type = task.get("type", "unknown")
        
        if task_type == "write_copy":
            content = await self.write_copy(
                task.get("project_id"),
                task.get("context", ""),
                task.get("content_type", "product_copy")
            )
            return {"content_id": content.content_id, "content": content.content}
        
        elif task_type == "create_landing_page":
            return await self.create_landing_page(
                task.get("project_id"),
                task.get("project_name")
            )
        
        elif task_type == "write_documentation":
            doc = await self.write_documentation(
                task.get("project_id"),
                task.get("topic", "")
            )
            return {"doc_id": doc.content_id, "content": doc.content}
        
        elif task_type == "get_brand_voice":
            return self.brand_voice
        
        return {"error": f"Unknown task type: {task_type}"}
