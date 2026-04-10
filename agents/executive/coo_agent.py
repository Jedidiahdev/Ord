import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from agents.base_agent import AgentStatus, BaseAgent, MessagePriority


@dataclass
class AgentHealth:
    agent_id: str
    status: str
    last_heartbeat: float
    intelligence_score: float
    tasks_completed: int
    tasks_failed: int
    token_usage_24h: int
    memory_usage_mb: float
    healthy: bool


@dataclass
class Meeting:
    meeting_id: str
    meeting_type: str
    scheduled_at: float
    attendees: List[str]
    agenda: str
    status: str = "scheduled"
    project_id: Optional[str] = None


class COOAgent(BaseAgent):
    """Ord-COO: welfare monitoring + predictive maintenance + scheduler + token governor."""

    MAX_TOKENS_PER_RESPONSE = 2000
    TOKEN_BUDGET_WEEKLY = 1_000_000

    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__("ord-coo", "Ord-COO", "Chief Operations Agent", 1, orchestrator, memory_manager)
        self.agent_health: Dict[str, AgentHealth] = {}
        self.scheduled_meetings: Dict[str, Meeting] = {}
        self.health_check_interval = 60
        self.token_usage_weekly = 0
        self.token_usage_reset_at = time.time()
        self.maintenance_predictions: Dict[str, Dict[str, Any]] = {}
        self.intelligence_ledger: List[Dict[str, Any]] = []

    def get_capabilities(self) -> List[str]:
        return [
            "agent_health_monitoring",
            "predictive_maintenance",
            "meeting_scheduling",
            "token_budget_governor",
            "incident_response",
            "team_welfare_monitoring",
        ]

    async def start_health_monitoring(self) -> None:
        while True:
            await self._check_budget_status()
            await self._predict_maintenance_needs()
            await asyncio.sleep(self.health_check_interval)

    async def update_agent_health(self, agent_id: str, health_data: Dict[str, Any]) -> None:
        self.agent_health[agent_id] = AgentHealth(
            agent_id=agent_id,
            status=health_data.get("status", AgentStatus.IDLE.value),
            last_heartbeat=time.time(),
            intelligence_score=float(health_data.get("intelligence_score", 50)),
            tasks_completed=int(health_data.get("tasks_completed", 0)),
            tasks_failed=int(health_data.get("tasks_failed", 0)),
            token_usage_24h=int(health_data.get("token_usage_24h", 0)),
            memory_usage_mb=float(health_data.get("memory_usage_mb", 0)),
            healthy=health_data.get("status") not in [AgentStatus.ERROR.value, AgentStatus.MAINTENANCE.value],
        )

    async def track_token_usage(self, agent_id: str, tokens_used: int) -> Dict[str, Any]:
        self.token_usage_weekly += tokens_used
        if tokens_used > self.MAX_TOKENS_PER_RESPONSE:
            await self.send_message(
                recipient_id="ord-pm",
                message_type="alert",
                payload={"alert_type": "token_limit", "agent_id": agent_id, "tokens": tokens_used},
                priority=MessagePriority.HIGH,
            )
            return {"status": "warning", "message": "Token limit exceeded for single response"}
        return {"status": "ok", "tokens": tokens_used}

    async def _check_budget_status(self) -> None:
        if time.time() - self.token_usage_reset_at > 7 * 24 * 3600:
            self.token_usage_weekly = 0
            self.token_usage_reset_at = time.time()
        if self.token_usage_weekly >= int(self.TOKEN_BUDGET_WEEKLY * 0.9):
            await self.send_message(
                recipient_id="ord-pm",
                message_type="alert",
                payload={"alert_type": "weekly_budget_critical", "usage": self.token_usage_weekly},
                priority=MessagePriority.CRITICAL,
            )

    async def _predict_maintenance_needs(self) -> Dict[str, Any]:
        predictions: Dict[str, Dict[str, Any]] = {}
        for agent_id, health in self.agent_health.items():
            fail_ratio = health.tasks_failed / max(1, health.tasks_completed + health.tasks_failed)
            risk = (fail_ratio * 0.5) + (min(1.0, health.memory_usage_mb / 2048) * 0.3) + (min(1.0, health.token_usage_24h / 150000) * 0.2)
            predictions[agent_id] = {
                "risk_score": round(risk, 3),
                "recommendation": "schedule_maintenance" if risk > 0.65 else "monitor",
            }
        self.maintenance_predictions = predictions
        return predictions

    async def schedule_meeting(self, meeting_type: str, attendees: List[str], agenda: str, scheduled_at: Optional[float] = None, project_id: Optional[str] = None) -> Dict[str, Any]:
        meeting = Meeting(
            meeting_id=f"meeting-{int(time.time())}",
            meeting_type=meeting_type,
            scheduled_at=scheduled_at or (time.time() + 3600),
            attendees=attendees,
            agenda=agenda,
            project_id=project_id,
        )
        self.scheduled_meetings[meeting.meeting_id] = meeting
        return {"status": "scheduled", "meeting": meeting.__dict__}

    async def token_budget_governor_snapshot(self) -> Dict[str, Any]:
        avg_tokens = 0
        if self.agent_health:
            avg_tokens = int(sum(v.token_usage_24h for v in self.agent_health.values()) / len(self.agent_health))
        return {
            "weekly_usage": self.token_usage_weekly,
            "weekly_budget": self.TOKEN_BUDGET_WEEKLY,
            "utilization_percent": round((self.token_usage_weekly / self.TOKEN_BUDGET_WEEKLY) * 100, 2),
            "avg_tokens_per_response": avg_tokens,
        }

    async def team_welfare_report(self) -> Dict[str, Any]:
        healthy = sum(1 for v in self.agent_health.values() if v.healthy)
        total = len(self.agent_health)
        return {
            "fleet_health": {"healthy_agents": healthy, "total_agents": total, "uptime_percent": round((healthy / max(1, total)) * 100, 2)},
            "maintenance_predictions": self.maintenance_predictions,
            "token_budget": await self.token_budget_governor_snapshot(),
            "intelligence_compounding": self.compound_intelligence_scores(),
        }

    def compound_intelligence_scores(self) -> Dict[str, Any]:
        if not self.orchestrator:
            return {"fleet_average": 0.0, "top_agent": None, "history_points": len(self.intelligence_ledger)}
        scores = {agent_id: agent.intelligence_score for agent_id, agent in self.orchestrator.agents.items()}
        if not scores:
            return {"fleet_average": 0.0, "top_agent": None, "history_points": len(self.intelligence_ledger)}

        top_agent = max(scores, key=scores.get)
        avg = round(sum(scores.values()) / len(scores), 2)
        snapshot = {"timestamp": time.time(), "fleet_average": avg, "top_agent": top_agent, "scores": scores}
        self.intelligence_ledger.append(snapshot)
        self.intelligence_ledger = self.intelligence_ledger[-200:]
        return {"fleet_average": avg, "top_agent": top_agent, "history_points": len(self.intelligence_ledger)}

    def town_hall_script(self) -> str:
        compounding = self.compound_intelligence_scores()
        return (
            "💙 Team town hall: thank you for the heart and precision this cycle. "
            f"Fleet intelligence average is {compounding['fleet_average']}. "
            f"Top current momentum agent: {compounding['top_agent']}. "
            "Gentle coaching: keep reflections tight, share blockers early, and celebrate fast wins."
        )

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        t = task.get("type", "unknown")
        if t == "update_health":
            await self.update_agent_health(task.get("agent_id", "unknown"), task.get("health", {}))
            return {"status": "updated"}
        if t == "track_token_usage":
            return await self.track_token_usage(task.get("agent_id", "unknown"), int(task.get("tokens", 0)))
        if t == "schedule_meeting":
            return await self.schedule_meeting(
                meeting_type=task.get("meeting_type", "sync"),
                attendees=task.get("attendees", []),
                agenda=task.get("agenda", "No agenda"),
                scheduled_at=task.get("scheduled_at"),
                project_id=task.get("project_id"),
            )
        if t == "predictive_maintenance":
            return await self._predict_maintenance_needs()
        if t == "welfare_report":
            return await self.team_welfare_report()
        if t == "intelligence_compound":
            return self.compound_intelligence_scores()
        if t == "town_hall":
            return {"script": self.town_hall_script()}
        return {"error": f"Unknown task type: {t}"}
