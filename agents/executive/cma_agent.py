import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent


@dataclass
class Campaign:
    campaign_id: str
    name: str
    type: str
    status: str
    budget: float
    spent: float
    start_date: float
    end_date: Optional[float]
    metrics: Dict[str, Any] = field(default_factory=dict)
    content_pieces: List[str] = field(default_factory=list)


@dataclass
class ContentPiece:
    content_id: str
    type: str
    title: str
    content: str
    status: str
    campaign_id: Optional[str]
    created_at: float
    published_at: Optional[float]
    performance: Dict[str, Any] = field(default_factory=dict)


class CMAAgent(BaseAgent):
    """Ord-CMA: campaign planning + attribution and ROI tracking."""

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__("ord-cma", "Ord-CMA", "Chief Marketing Agent", 2, orchestrator, memory_manager)
        self.campaigns: Dict[str, Campaign] = {}
        self.content_library: Dict[str, ContentPiece] = {}

    def get_capabilities(self) -> List[str]:
        return [
            "campaign_management",
            "content_strategy",
            "roi_tracking",
            "attribution_modeling",
            "brand_management",
            "marketing_automation",
        ]

    async def create_campaign(self, campaign_spec: Dict[str, Any]) -> Dict[str, Any]:
        campaign = Campaign(
            campaign_id=f"campaign-{int(time.time())}",
            name=campaign_spec.get("name", "New Campaign"),
            type=campaign_spec.get("type", "content"),
            status="planned",
            budget=float(campaign_spec.get("budget", 0)),
            spent=0.0,
            start_date=campaign_spec.get("start_date", time.time()),
            end_date=campaign_spec.get("end_date"),
            metrics={"leads": 0, "conversions": 0, "revenue": 0.0},
        )
        self.campaigns[campaign.campaign_id] = campaign
        return {"status": "created", "campaign_id": campaign.campaign_id, "campaign": campaign.__dict__}

    async def generate_content(self, content_spec: Dict[str, Any]) -> Dict[str, Any]:
        content = ContentPiece(
            content_id=f"content-{int(time.time())}",
            type=content_spec.get("type", "blog"),
            title=content_spec.get("title", "New Content"),
            content=content_spec.get("content", ""),
            status="draft",
            campaign_id=content_spec.get("campaign_id"),
            created_at=time.time(),
            published_at=None,
        )
        self.content_library[content.content_id] = content
        if content.campaign_id and content.campaign_id in self.campaigns:
            self.campaigns[content.campaign_id].content_pieces.append(content.content_id)
        return {"status": "created", "content_id": content.content_id}

    async def update_campaign_metrics(self, campaign_id: str, metrics_delta: Dict[str, Any]) -> Dict[str, Any]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}
        campaign.spent += float(metrics_delta.get("spent", 0))
        campaign.metrics["leads"] = campaign.metrics.get("leads", 0) + int(metrics_delta.get("leads", 0))
        campaign.metrics["conversions"] = campaign.metrics.get("conversions", 0) + int(metrics_delta.get("conversions", 0))
        campaign.metrics["revenue"] = campaign.metrics.get("revenue", 0.0) + float(metrics_delta.get("revenue", 0.0))
        return {"status": "updated", "campaign_id": campaign_id, "metrics": campaign.metrics}

    async def track_campaign_roi(self, campaign_id: str) -> Dict[str, Any]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}

        revenue = float(campaign.metrics.get("revenue", 0.0))
        spent = campaign.spent
        roi = ((revenue - spent) / spent * 100) if spent > 0 else 0.0
        cpl = spent / max(campaign.metrics.get("leads", 0), 1)
        cpa = spent / max(campaign.metrics.get("conversions", 0), 1)

        return {
            "campaign": campaign.name,
            "revenue": revenue,
            "spent": spent,
            "roi_percent": round(roi, 2),
            "cost_per_lead": round(cpl, 2),
            "cost_per_acquisition": round(cpa, 2),
            "status": campaign.status,
        }

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        t = task.get("type", "unknown")
        if t == "create_campaign":
            return await self.create_campaign(task.get("spec", {}))
        if t == "generate_content":
            return await self.generate_content(task.get("spec", {}))
        if t == "update_metrics":
            return await self.update_campaign_metrics(task.get("campaign_id", ""), task.get("delta", {}))
        if t == "track_roi":
            return await self.track_campaign_roi(task.get("campaign_id", ""))
        return {"error": f"Unknown task type: {t}"}
