import statistics
import time
from dataclasses import dataclass
from typing import Any, Dict, List

from agents.base_agent import BaseAgent


@dataclass
class AnalysisReport:
    report_id: str
    title: str
    data_sources: List[str]
    findings: List[Dict[str, Any]]
    visualizations: List[str]
    confidence: float
    created_at: float


class DAAAgent(BaseAgent):
    """Ord-DAA: cross-executive analytics + dashboard configuration generator."""

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__("ord-daa", "Ord-DAA", "Data Analyst Agent", 2, orchestrator, memory_manager)
        self.reports: Dict[str, AnalysisReport] = {}
        self.dashboard_configs: Dict[str, Dict[str, Any]] = {}

    def get_capabilities(self) -> List[str]:
        return [
            "variation_scoring",
            "forecasting",
            "executive_data_analysis",
            "shadcn_dashboard_generation",
            "cross_domain_insights",
        ]

    async def score_variations(self, project_id: str, variations: List[Dict[str, Any]]) -> Dict[str, Any]:
        scored = []
        for v in variations:
            payload = v.get("result", {})
            build_time = 85 if "3-5" in str(payload.get("estimated_build_time", "")) else 70
            cost = 100 - min(80, float(str(payload.get("estimated_cost", "$1000")).replace("$", "")) / 20)
            market_fit = 75
            risk = 70
            score = round(build_time * 0.25 + cost * 0.25 + market_fit * 0.35 + risk * 0.15, 2)
            scored.append({"variation_id": v.get("variation_id"), "daa_score": score})
        scored.sort(key=lambda x: x["daa_score"], reverse=True)
        return {"project_id": project_id, "scored_variations": scored, "top_3": scored[:3]}

    async def analyze_executive_signals(self, cfa_data: Dict[str, Any], coo_data: Dict[str, Any]) -> Dict[str, Any]:
        revenue = float(cfa_data.get("revenue", 0))
        expense = float(cfa_data.get("expenses", 0))
        uptime = float(coo_data.get("fleet_health", {}).get("uptime_percent", 99.0))
        avg_tokens = float(coo_data.get("token_budget", {}).get("avg_tokens_per_response", 0))

        findings = [
            {"title": "Profitability", "value": revenue - expense, "status": "good" if revenue >= expense else "risk"},
            {"title": "Operations Uptime", "value": uptime, "status": "good" if uptime >= 98 else "watch"},
            {"title": "Token Efficiency", "value": avg_tokens, "status": "good" if avg_tokens <= 2000 else "risk"},
        ]

        report = AnalysisReport(
            report_id=f"report-{int(time.time())}",
            title="Executive Health & Finance Synthesis",
            data_sources=["ord-cfa", "ord-coo"],
            findings=findings,
            visualizations=["line:mrr", "bar:token_usage", "pie:treasury_mix"],
            confidence=0.83,
            created_at=time.time(),
        )
        self.reports[report.report_id] = report
        return {"report_id": report.report_id, "findings": findings, "confidence": report.confidence}

    async def create_shadcn_dashboard(self, title: str, report_id: str) -> Dict[str, Any]:
        report = self.reports.get(report_id)
        if not report:
            return {"error": "Report not found"}

        dashboard_id = f"dashboard-{int(time.time())}"
        # Config intended for shadcn/ui cards + charts + tables.
        config = {
            "id": dashboard_id,
            "title": title,
            "layout": "grid",
            "components": [
                {"type": "card", "title": "Net Profit", "metric": "profitability"},
                {"type": "chart", "variant": "line", "title": "MRR Trend", "metric": "mrr"},
                {"type": "chart", "variant": "bar", "title": "Token Usage", "metric": "token_usage"},
                {"type": "table", "title": "Key Findings", "rows": report.findings},
            ],
            "interactions": ["date_filter", "source_filter", "drilldown"],
        }
        self.dashboard_configs[dashboard_id] = config
        return {"dashboard_id": dashboard_id, "config": config}

    async def generate_insight(self, query: str) -> Dict[str, Any]:
        tokens = [len(w) for w in query.split()]
        mean = statistics.mean(tokens) if tokens else 0
        return {
            "query": query,
            "insight": "Higher detail requests correlate with cross-team execution complexity.",
            "confidence": 0.8,
            "signal_strength": round(mean, 2),
            "recommendation": "Use PM milestone gates + COO budget guardrails for this request.",
        }

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        t = task.get("type", "unknown")
        if t == "score_variations":
            return await self.score_variations(task.get("project_id", ""), task.get("variations", []))
        if t == "analyze_executive_signals":
            return await self.analyze_executive_signals(task.get("cfa_data", {}), task.get("coo_data", {}))
        if t == "create_dashboard":
            return await self.create_shadcn_dashboard(task.get("title", "Executive Dashboard"), task.get("report_id", ""))
        if t == "generate_insight":
            return await self.generate_insight(task.get("query", ""))
        return {"error": f"Unknown task type: {t}"}
