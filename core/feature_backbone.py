from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class BackboneFeature:
    id: str
    name: str
    category: str
    priority: int
    status: str = "planned"


class FeatureBackbone:
    """Tracks the 50-feature production backbone with explicit top-priority focus."""

    def __init__(self) -> None:
        self.features: List[BackboneFeature] = self._seed_features()

    def _seed_features(self) -> List[BackboneFeature]:
        # Top 15 prioritized first (requested for Phase 5)
        prioritized = [
            ("F01", "Variation Factory", "product", 1),
            ("F02", "Financial Twin", "finance", 1),
            ("F03", "Governance Ledger", "governance", 1),
            ("F04", "Structured Reflection Loop", "learning", 1),
            ("F05", "COO Intelligence Compounding", "operations", 1),
            ("F06", "Self-Healing Runtime", "resilience", 1),
            ("F07", "Unified A2A Event Logging", "observability", 1),
            ("F08", "Voice-First Executive Briefing", "interface", 1),
            ("F09", "One-Click Productization", "product", 1),
            ("F10", "Agent Skill Registry", "agents", 1),
            ("F11", "Experiment Scoring Matrix", "analytics", 1),
            ("F12", "Town Hall Narrative Generator", "culture", 1),
            ("F13", "Deployment Guardrails", "governance", 1),
            ("F14", "Memory Tier Health Monitor", "memory", 1),
            ("F15", "API Contract Validation", "platform", 1),
        ]

        remaining = [
            ("F16", "Prompt Budget Optimizer", "operations"),
            ("F17", "Market Signal Harvester", "analytics"),
            ("F18", "Hiring Workflow Assistant", "hr"),
            ("F19", "Legal Policy Linter", "governance"),
            ("F20", "Incident Response Drillbook", "resilience"),
            ("F21", "Release Notes Autopilot", "delivery"),
            ("F22", "Integration Health Dashboard", "integrations"),
            ("F23", "Scenario Planning Simulator", "analytics"),
            ("F24", "Customer Insight Summarizer", "growth"),
            ("F25", "Partner Outreach Sequencer", "bd"),
            ("F26", "Security Posture Assessor", "security"),
            ("F27", "Realtime Unit Economics Feed", "finance"),
            ("F28", "Agent Performance Heatmap", "operations"),
            ("F29", "Experiment Replay Recorder", "learning"),
            ("F30", "Changelog Knowledge Graph", "memory"),
            ("F31", "A/B Launch Gate", "delivery"),
            ("F32", "Narrated Demo Builder", "interface"),
            ("F33", "Cross-Team SLA Tracker", "operations"),
            ("F34", "Design System Consistency Scanner", "design"),
            ("F35", "Token Usage Forecaster", "operations"),
            ("F36", "Failover Mode Switch", "resilience"),
            ("F37", "Sandbox Cost Meter", "finance"),
            ("F38", "Compliance Audit Trail", "governance"),
            ("F39", "KPI Storyboard", "analytics"),
            ("F40", "Launch Retrospective Engine", "learning"),
            ("F41", "Team Wellbeing Pulse", "culture"),
            ("F42", "Content Variant Composer", "content"),
            ("F43", "API Usage Metering", "platform"),
            ("F44", "Queue Backpressure Control", "platform"),
            ("F45", "Memory Drift Detector", "memory"),
            ("F46", "Live Objectives Board", "operations"),
            ("F47", "Executive Approval Workflow", "governance"),
            ("F48", "Recovery Checkpoint Browser", "resilience"),
            ("F49", "Cost-to-Serve Calculator", "finance"),
            ("F50", "Platform Onboarding Wizard", "platform"),
        ]

        items = [BackboneFeature(fid, name, category, priority) for fid, name, category, priority in prioritized]
        items.extend(BackboneFeature(fid, name, category, 2) for fid, name, category in remaining)
        return items

    def top_priorities(self) -> List[BackboneFeature]:
        return [feature for feature in self.features if feature.priority == 1]

    def summary(self) -> dict:
        return {
            "total_features": len(self.features),
            "priority_one_count": len(self.top_priorities()),
            "priority_one_ids": [feature.id for feature in self.top_priorities()],
        }
