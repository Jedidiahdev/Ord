import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent


@dataclass
class MarketInsight:
    insight_id: str
    category: str
    title: str
    description: str
    confidence: float
    source: str
    timestamp: float
    action_recommended: Optional[str] = None


@dataclass
class Competitor:
    name: str
    website: str
    products: List[str]
    pricing: Dict[str, Any]
    strengths: List[str]
    weaknesses: List[str]
    last_updated: float


class BDAgent(BaseAgent):
    """Ord-BD: Market intelligence + opportunity scoring engine."""

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__("ord-bd", "Ord-BD", "Business Development Agent", 2, orchestrator, memory_manager)
        self.insights: List[MarketInsight] = []
        self.competitors: Dict[str, Competitor] = {}
        self.pipeline_opportunities: List[Dict[str, Any]] = []

    def get_capabilities(self) -> List[str]:
        return [
            "market_research",
            "competitor_analysis",
            "trend_identification",
            "opportunity_scoring",
            "growth_strategy",
            "partnership_evaluation",
            "hiring_strategy_alignment",
        ]

    async def analyze_market(self, query: str) -> Dict[str, Any]:
        confidence = 0.78 if any(k in query.lower() for k in ["ai", "automation", "agent"]) else 0.68
        insight = MarketInsight(
            insight_id=f"insight-{int(time.time())}",
            category="opportunity",
            title=f"Market signal for {query}",
            description=f"Demand and willingness-to-pay appear favorable for {query}.",
            confidence=confidence,
            source="bd_engine",
            timestamp=time.time(),
            action_recommended="run_2_week_validation_sprint",
        )
        self.insights.append(insight)
        return {"query": query, "insight": insight.__dict__, "next_actions": ["pricing_test", "customer_interviews"]}

    async def update_competitor(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        competitor = Competitor(
            name=profile.get("name", "unknown"),
            website=profile.get("website", ""),
            products=profile.get("products", []),
            pricing=profile.get("pricing", {}),
            strengths=profile.get("strengths", []),
            weaknesses=profile.get("weaknesses", []),
            last_updated=time.time(),
        )
        self.competitors[competitor.name.lower()] = competitor
        return {"status": "updated", "competitor": competitor.name}

    async def score_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        market_size = float(opportunity.get("market_size", 0))
        urgency = float(opportunity.get("urgency", 0.5))
        differentiation = float(opportunity.get("differentiation", 0.5))
        score = min(100.0, (market_size * 0.00001 * 45) + (urgency * 30) + (differentiation * 25))
        record = {"opportunity": opportunity.get("name", "unknown"), "score": round(score, 2), "timestamp": time.time()}
        self.pipeline_opportunities.append(record)
        return {"status": "scored", **record, "recommendation": "pursue" if score >= 65 else "watch"}

    async def evaluate_hiring_need(self, role_spec: Dict[str, Any]) -> Dict[str, Any]:
        role_name = role_spec.get("role_name", "")
        must_hire_keywords = ["security", "data", "revenue", "ml", "ai"]
        strategic_value = 0.95 if any(k in role_name.lower() for k in must_hire_keywords) else 0.72
        return {
            "role": role_name,
            "strategic_value": strategic_value,
            "recommendation": "hire" if strategic_value >= 0.75 else "defer",
            "reasoning": "Role supports near-term strategic objectives and execution velocity.",
        }

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        t = task.get("type", "unknown")
        if t == "analyze_market":
            return await self.analyze_market(task.get("query", ""))
        if t == "update_competitor":
            return await self.update_competitor(task.get("profile", {}))
        if t == "score_opportunity":
            return await self.score_opportunity(task.get("opportunity", {}))
        if t == "evaluate_hiring":
            return await self.evaluate_hiring_need(task.get("role_spec", {}))
        if t == "market_brief":
            return {"insights": [i.__dict__ for i in self.insights[-10:]], "competitors": list(self.competitors.keys())}
        return {"error": f"Unknown task type: {t}"}
