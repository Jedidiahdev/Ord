import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, MessagePriority


@dataclass
class MarketInsight:
    """Market intelligence insight"""
    insight_id: str
    category: str  # trend, competitor, opportunity, threat
    title: str
    description: str
    confidence: float
    source: str
    timestamp: float
    action_recommended: Optional[str] = None


@dataclass
class Competitor:
    """Competitor profile"""
    name: str
    website: str
    products: List[str]
    pricing: Dict
    strengths: List[str]
    weaknesses: List[str]
    last_updated: float


class BDAgent(BaseAgent):
    """
    Ord-BD: Business Development Agent
    
    The visionary who sees around corners. BD constantly scans the market,
    identifies opportunities, and ensures Ord stays ahead of the curve.
    """
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-bd",
            name="Ord-BD",
            role="Business Development Agent",
            layer=2,
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        self.insights: List[MarketInsight] = []
        self.competitors: Dict[str, Competitor] = {}
        self.market_reports: List[Dict] = []
        
        self.logger.info("📈 Ord-BD initialized | Market Intelligence Active")
    
    def get_capabilities(self) -> List[str]:
        return [
            "market_research",
            "competitor_analysis",
            "trend_identification",
            "opportunity_scoring",
            "growth_strategy",
            "product_market_fit",
            "pricing_intelligence",
            "partnership_evaluation"
        ]
    
    async def analyze_market(self, query: str) -> Dict:
        """Analyze market for specific query"""
        # In production: use web search tools
        insight = MarketInsight(
            insight_id=f"insight-{int(time.time())}",
            category="opportunity",
            title=f"Market analysis: {query}",
            description=f"Analysis of {query} market segment",
            confidence=0.75,
            source="market_research",
            timestamp=time.time()
        )
        
        self.insights.append(insight)
        
        return {
            "query": query,
            "insights": [insight.__dict__],
            "recommendation": "Consider entering this market segment"
        }
    
    async def evaluate_hiring_need(self, role_spec: Dict) -> Dict:
        """Evaluate if a new role aligns with growth strategy"""
        role_name = role_spec.get("role_name", "")
        skills = role_spec.get("skills", [])
        
        # Analyze strategic fit
        strategic_value = 0.7  # Default
        
        if "ai" in role_name.lower() or "ml" in role_name.lower():
            strategic_value = 0.95
        elif "security" in role_name.lower():
            strategic_value = 0.9
        elif "data" in role_name.lower():
            strategic_value = 0.85
        
        recommendation = "hire" if strategic_value > 0.7 else "defer"
        
        return {
            "role": role_name,
            "strategic_value": strategic_value,
            "recommendation": recommendation,
            "reasoning": f"This role aligns with our {strategic_value:.0%} strategic priorities"
        }
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Process BD-specific tasks"""
        task_type = task.get("type", "unknown")
        
        if task_type == "analyze_market":
            return await self.analyze_market(task.get("query", ""))
        
        elif task_type == "evaluate_hiring":
            return await self.evaluate_hiring_need(task.get("role_spec", {}))
        
        elif task_type == "competitor_analysis":
            return {"competitors": list(self.competitors.keys())}
        
        return {"error": f"Unknown task type: {task_type}"}
