from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ExecutiveBriefing:
    command: str
    narration: str
    daa_visuals: List[Dict[str, Any]]


class VoiceBriefingService:
    """Voice-first single-command executive briefing composer."""

    def build_briefing(self, command: str, orchestrator_snapshot: Dict[str, Any]) -> ExecutiveBriefing:
        agent_status = orchestrator_snapshot.get("agent_status", {})
        results = orchestrator_snapshot.get("results", {})

        narration = (
            "Sweet team update: mission momentum is strong. "
            f"We currently monitor {len(agent_status)} agents, with key outcomes from {len(results)} active streams. "
            "Thank you leadership — next moves are queued and ready."
        )

        visuals = [
            {"type": "kpi", "title": "Active Agents", "value": len(agent_status)},
            {"type": "kpi", "title": "Result Streams", "value": len(results)},
            {"type": "timeline", "title": "Executive Flow", "items": ["Signal", "Synthesis", "Decision", "Deployment"]},
        ]

        return ExecutiveBriefing(command=command, narration=narration, daa_visuals=visuals)
