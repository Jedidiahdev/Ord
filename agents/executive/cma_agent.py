"""
Ord v3.0 - Chief Marketing Agent (Ord-CMA)
Campaigns, content strategy, ROI tracking, and brand management.

Patterns Implemented:
- Prioritization (Ch20): Campaign prioritization and resource allocation
- Reflection (Ch4): Campaign performance analysis
- Tool Use (Ch5): Content generation, social media integration

Responsibilities:
1. Marketing campaign management
2. Content strategy and calendar
3. ROI tracking and optimization
4. Brand voice consistency
5. Customer feedback analysis
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, MessagePriority


@dataclass
class Campaign:
    """Marketing campaign"""
    campaign_id: str
    name: str
    type: str  # email, social, content, paid
    status: str  # planned, active, completed, paused
    budget: float
    spent: float
    start_date: float
    end_date: Optional[float]
    metrics: Dict = field(default_factory=dict)
    content_pieces: List[str] = field(default_factory=list)


@dataclass
class ContentPiece:
    """Individual content piece"""
    content_id: str
    type: str  # blog, social, email, video
    title: str
    content: str
    status: str
    campaign_id: Optional[str]
    created_at: float
    published_at: Optional[float]
    performance: Dict = field(default_factory=dict)


class CMAAgent(BaseAgent):
    """
    Ord-CMA: Chief Marketing Agent
    
    The voice of Ord to the world. CMA manages campaigns,
    creates compelling content, and tracks every dollar's ROI.
    """
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-cma",
            name="Ord-CMA",
            role="Chief Marketing Agent",
            layer=2,
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        self.campaigns: Dict[str, Campaign] = {}
        self.content_library: Dict[str, ContentPiece] = {}
        self.brand_guidelines = {
            "voice": "sweet, loving, professional, encouraging",
            "colors": ["#FD651E", "#0A0A0A", "#FFFFFF"],
            "tone": "warm and approachable yet ruthlessly professional"
        }
        
        self.logger.info("📣 Ord-CMA initialized | Brand Guardian")
    
    def get_capabilities(self) -> List[str]:
        return [
            "campaign_management",
            "content_strategy",
            "roi_tracking",
            "brand_management",
            "social_media",
            "email_marketing",
            "copywriting",
            "customer_feedback_analysis",
            "marketing_automation"
        ]
    
    async def create_campaign(self, campaign_spec: Dict) -> Dict:
        """Create new marketing campaign"""
        campaign = Campaign(
            campaign_id=f"campaign-{int(time.time())}",
            name=campaign_spec.get("name", "New Campaign"),
            type=campaign_spec.get("type", "content"),
            status="planned",
            budget=campaign_spec.get("budget", 0),
            spent=0,
            start_date=campaign_spec.get("start_date", time.time()),
            end_date=campaign_spec.get("end_date")
        )
        
        self.campaigns[campaign.campaign_id] = campaign
        
        return {
            "status": "created",
            "campaign_id": campaign.campaign_id,
            "message": f"Campaign '{campaign.name}' created and ready to launch! 🚀"
        }
    
    async def generate_content(self, content_spec: Dict) -> Dict:
        """Generate marketing content"""
        content = ContentPiece(
            content_id=f"content-{int(time.time())}",
            type=content_spec.get("type", "blog"),
            title=content_spec.get("title", "New Content"),
            content=content_spec.get("content", ""),
            status="draft",
            campaign_id=content_spec.get("campaign_id"),
            created_at=time.time()
        )
        
        self.content_library[content.content_id] = content
        
        return {
            "status": "created",
            "content_id": content.content_id,
            "preview": content.content[:200] + "..."
        }
    
    async def track_campaign_roi(self, campaign_id: str) -> Dict:
        """Track and analyze campaign ROI"""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}
        
        revenue = campaign.metrics.get("revenue", 0)
        spent = campaign.spent
        roi = ((revenue - spent) / spent * 100) if spent > 0 else 0
        
        return {
            "campaign": campaign.name,
            "revenue": revenue,
            "spent": spent,
            "roi_percent": roi,
            "status": campaign.status
        }
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Process CMA-specific tasks"""
        task_type = task.get("type", "unknown")
        
        if task_type == "create_campaign":
            return await self.create_campaign(task.get("spec", {}))
        
        elif task_type == "generate_content":
            return await self.generate_content(task.get("spec", {}))
        
        elif task_type == "track_roi":
            return await self.track_campaign_roi(task.get("campaign_id"))
        
        elif task_type == "get_brand_guidelines":
            return self.brand_guidelines
        
        return {"error": f"Unknown task type: {task_type}"}
