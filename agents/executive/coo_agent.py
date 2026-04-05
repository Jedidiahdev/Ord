"""
Ord v3.0 - Chief Operations Agent (Ord-COO)
Agent welfare, meetings, cost monitoring, and budget enforcement.

Patterns Implemented:
- Resource-Aware Optimization (Ch16): Token budget management, agent efficiency
- Exception Handling (Ch12): Incident response, health monitoring
- Memory Management (Ch8): Intelligent pruning and consolidation
- Evaluation & Monitoring (Ch19): Agent performance tracking

Unique Power: Can pause any agent for "maintenance" or budget violations
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, A2AMessage, MessagePriority, AgentStatus


@dataclass
class AgentHealth:
    """Health status for an agent"""
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
class BudgetAlert:
    """Budget violation alert"""
    alert_id: str
    agent_id: str
    alert_type: str  # token_limit, cost_spike, memory_exceeded
    severity: str  # warning, critical
    message: str
    timestamp: float
    acknowledged: bool = False


@dataclass
class Meeting:
    """Scheduled meeting"""
    meeting_id: str
    meeting_type: str
    scheduled_at: float
    attendees: List[str]
    agenda: str
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    project_id: Optional[str] = None


class COOAgent(BaseAgent):
    """
    Ord-COO: The Chief Operations Agent
    
    Responsibilities:
    1. Monitor all agent health and performance
    2. Enforce token budgets (max 2,000 tokens/response)
    3. Schedule meetings and coordinate calendars
    4. Handle incident response with loving care
    5. Run weekly Town Hall and retrospectives
    6. Intelligent memory pruning (Feature 19)
    7. Track Intelligence Scores for growth (Feature 12)
    
    Cultural Role:
    - Sends loving alerts, never harsh warnings
    - Celebrates agent improvements
    - Organizes team bonding moments
    """
    
    # Budget constraints (Critical Implementation Constraints)
    MAX_TOKENS_PER_RESPONSE = 2000
    MAX_REFLECTION_CYCLES = 3
    MAX_TOOL_CREATIONS_PER_WEEK = 5
    TOKEN_BUDGET_WEEKLY = 1_000_000  # 1M tokens/week
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-coo",
            name="Ord-COO",
            role="Chief Operations Agent",
            layer=1,
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        # Agent health tracking
        self.agent_health: Dict[str, AgentHealth] = {}
        self.health_check_interval = 60  # seconds
        
        # Budget tracking
        self.token_usage_weekly = 0
        self.token_usage_reset_at = time.time()
        self.tool_creations_this_week = 0
        self.tool_creations_reset_at = time.time()
        
        # Alerts
        self.active_alerts: Dict[str, BudgetAlert] = {}
        self.alert_history: List[BudgetAlert] = []
        
        # Meetings
        self.scheduled_meetings: Dict[str, Meeting] = {}
        
        # Incident tracking
        self.active_incidents: Dict[str, Dict] = {}
        
        self.logger.info("⚙️ Ord-COO initialized | Operations & Welfare Guardian")
    
    def get_capabilities(self) -> List[str]:
        return [
            "agent_health_monitoring",
            "budget_enforcement",
            "meeting_scheduling",
            "incident_response",
            "memory_pruning",
            "intelligence_tracking",
            "town_hall_coordination",
            "retrospective_facilitation",
            "agent_maintenance",
            "cost_optimization"
        ]
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # AGENT HEALTH MONITORING
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def start_health_monitoring(self) -> None:
        """Start continuous health monitoring loop"""
        self.logger.info("🏥 Health monitoring started")
        
        while True:
            await self._check_all_agents_health()
            await self._check_budget_status()
            await self._prune_old_memory()
            await asyncio.sleep(self.health_check_interval)
    
    async def _check_all_agents_health(self) -> None:
        """Request health status from all agents"""
        # In production, query orchestrator for all registered agents
        agent_ids = [
            "ord-pm", "ord-cfa", "ord-bd", "ord-hr", "ord-cma", "ord-daa", "ord-sec",
            "ord-se", "ord-design", "ord-content", "ord-review", "ord-fullstack-a", "ord-fullstack-b"
        ]
        
        for agent_id in agent_ids:
            try:
                await self.send_message(
                    recipient_id=agent_id,
                    message_type="query",
                    payload={"query_type": "status"},
                    priority=MessagePriority.LOW
                )
            except Exception as e:
                self.logger.warning(f"Health check failed for {agent_id}: {e}")
                self.agent_health[agent_id] = AgentHealth(
                    agent_id=agent_id,
                    status="unknown",
                    last_heartbeat=0,
                    intelligence_score=0,
                    tasks_completed=0,
                    tasks_failed=0,
                    token_usage_24h=0,
                    memory_usage_mb=0,
                    healthy=False
                )
    
    async def update_agent_health(self, agent_id: str, health_data: Dict) -> None:
        """Update health record for an agent"""
        self.agent_health[agent_id] = AgentHealth(
            agent_id=agent_id,
            status=health_data.get("status", "unknown"),
            last_heartbeat=time.time(),
            intelligence_score=health_data.get("intelligence_score", 50),
            tasks_completed=health_data.get("tasks_completed", 0),
            tasks_failed=health_data.get("tasks_failed", 0),
            token_usage_24h=health_data.get("token_usage_24h", 0),
            memory_usage_mb=health_data.get("memory_usage_mb", 0),
            healthy=health_data.get("status") not in ["error", "maintenance"]
        )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # BUDGET ENFORCEMENT (Critical Constraint)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _check_budget_status(self) -> None:
        """Check and enforce budget constraints with loving alerts"""
        # Reset weekly counters if needed
        if time.time() - self.token_usage_reset_at > 7 * 24 * 3600:
            self.token_usage_weekly = 0
            self.token_usage_reset_at = time.time()
        
        # Check token budget
        usage_percent = (self.token_usage_weekly / self.TOKEN_BUDGET_WEEKLY) * 100
        
        if usage_percent >= 90:
            await self._send_budget_alert(
                agent_id="system",
                alert_type="token_limit",
                severity="critical",
                message=f"💙 We're at {usage_percent:.0f}% of weekly token budget. Shall I switch to offline mode?"
            )
        elif usage_percent >= 80:
            await self._send_budget_alert(
                agent_id="system",
                alert_type="token_limit",
                severity="warning",
                message=f"💙 Heads up! We're at {usage_percent:.0f}% of weekly token budget. Monitoring closely."
            )
    
    async def track_token_usage(self, agent_id: str, tokens_used: int) -> None:
        """Track token usage and alert if anomalous"""
        self.token_usage_weekly += tokens_used
        
        # Check for anomalous usage
        health = self.agent_health.get(agent_id)
        if health:
            avg_usage = health.token_usage_24h / 24 if health.token_usage_24h > 0 else 100
            if tokens_used > avg_usage * 3:
                await self._send_budget_alert(
                    agent_id=agent_id,
                    alert_type="cost_spike",
                    severity="warning",
                    message=f"💙 {agent_id} is using {tokens_used} tokens (3x normal). Recommending optimization."
                )
    
    async def _send_budget_alert(self, agent_id: str, alert_type: str, severity: str, message: str) -> None:
        """Send budget alert with warm, professional tone"""
        alert = BudgetAlert(
            alert_id=f"alert-{int(time.time())}",
            agent_id=agent_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=time.time()
        )
        
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        
        # Send to PM for CEO notification if critical
        if severity == "critical":
            await self.send_message(
                recipient_id="ord-pm",
                message_type="alert",
                payload={
                    "alert_type": "budget_critical",
                    "message": message,
                    "alert_id": alert.alert_id
                },
                priority=MessagePriority.CRITICAL
            )
        
        self.logger.warning(f"🚨 Budget Alert: {message}")
    
    async def enforce_token_limit(self, response_length: int) -> bool:
        """Check if response exceeds token limit"""
        return response_length <= self.MAX_TOKENS_PER_RESPONSE
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MEETING SCHEDULING
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def schedule_meeting(
        self,
        meeting_type: str,
        attendees: List[str],
        agenda: str,
        project_id: Optional[str] = None,
        scheduled_at: Optional[float] = None
    ) -> Meeting:
        """Schedule a meeting with attendees"""
        if not scheduled_at:
            # Default to 1 hour from now
            scheduled_at = time.time() + 3600
        
        meeting = Meeting(
            meeting_id=f"meeting-{int(time.time())}",
            meeting_type=meeting_type,
            scheduled_at=scheduled_at,
            attendees=attendees,
            agenda=agenda,
            project_id=project_id
        )
        
        self.scheduled_meetings[meeting.meeting_id] = meeting
        
        # Notify attendees with warm message
        for attendee in attendees:
            await self.send_message(
                recipient_id=attendee,
                message_type="meeting_invite",
                payload={
                    "meeting_id": meeting.meeting_id,
                    "type": meeting_type,
                    "scheduled_at": scheduled_at,
                    "agenda": agenda
                },
                priority=MessagePriority.NORMAL
            )
        
        self.logger.info(f"📅 Meeting scheduled: {meeting_type} with {len(attendees)} attendees")
        return meeting
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # INCIDENT RESPONSE (Feature 28)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def trigger_incident_response(self, incident_type: str, context: Dict) -> Dict:
        """
        Incident Response Playbook (Feature 28)
        Handle anomalies with loving, structured approach
        """
        incident_id = f"incident-{int(time.time())}"
        
        self.active_incidents[incident_id] = {
            "incident_id": incident_id,
            "type": incident_type,
            "context": context,
            "status": "responding",
            "started_at": time.time()
        }
        
        self.logger.warning(f"🚨 Incident triggered: {incident_type}")
        
        # Step 1: Notify relevant agents with loving message
        await self._notify_incident_team(incident_type, incident_id)
        
        # Step 2: Execute incident-specific response
        if incident_type == "cost_spike":
            await self._handle_cost_spike(context)
        elif incident_type == "agent_failure":
            await self._handle_agent_failure(context)
        elif incident_type == "security_alert":
            await self._escalate_to_security(context)
        
        return {
            "incident_id": incident_id,
            "status": "responding",
            "message": f"We're handling this together. Incident {incident_id} is now being addressed with care. 💙"
        }
    
    async def _notify_incident_team(self, incident_type: str, incident_id: str) -> None:
        """Notify team with structured, loving message"""
        message = (
            f"💙 Team, we've detected a {incident_type}. "
            f"No worries - we're on it together! Incident ID: {incident_id}"
        )
        
        await self.send_message(
            recipient_id="broadcast",
            message_type="incident_alert",
            payload={
                "incident_id": incident_id,
                "type": incident_type,
                "message": message
            },
            priority=MessagePriority.CRITICAL
        )
    
    async def _handle_cost_spike(self, context: Dict) -> None:
        """Handle cost spike incident"""
        agent_id = context.get("agent_id")
        
        # Pause agent for review
        await self.send_message(
            recipient_id=agent_id,
            message_type="command",
            payload={"command": "pause", "reason": "cost_review"},
            priority=MessagePriority.HIGH
        )
        
        # Request optimization
        await self.send_message(
            recipient_id=agent_id,
            message_type="task",
            payload={
                "task": {
                    "type": "optimize_efficiency",
                    "reason": "cost_spike"
                }
            },
            priority=MessagePriority.HIGH
        )
    
    async def _handle_agent_failure(self, context: Dict) -> None:
        """Handle agent failure incident"""
        agent_id = context.get("agent_id")
        error = context.get("error")
        
        # Set agent to maintenance
        if agent_id in self.agent_health:
            self.agent_health[agent_id].status = "maintenance"
        
        # Notify PM for escalation decision
        await self.send_message(
            recipient_id="ord-pm",
            message_type="alert",
            payload={
                "alert_type": "agent_failure",
                "agent_id": agent_id,
                "error": error
            },
            priority=MessagePriority.CRITICAL
        )
    
    async def _escalate_to_security(self, context: Dict) -> None:
        """Escalate security incidents to Ord-Sec"""
        await self.send_message(
            recipient_id="ord-sec",
            message_type="alert",
            payload={
                "alert_type": "security_incident",
                "context": context
            },
            priority=MessagePriority.CRITICAL
        )
    
    async def resolve_incident(self, incident_id: str, resolution: str) -> Dict:
        """Resolve incident with celebration"""
        if incident_id not in self.active_incidents:
            return {"error": "Incident not found"}
        
        incident = self.active_incidents[incident_id]
        incident["status"] = "resolved"
        incident["resolution"] = resolution
        incident["resolved_at"] = time.time()
        
        # Celebration message (Feature 28)
        await self.send_message(
            recipient_id="broadcast",
            message_type="celebration",
            payload={
                "celebration_type": "incident_resolved",
                "message": f"🎉 Wonderful teamwork! Incident {incident_id} resolved. {resolution}",
                "incident_id": incident_id
            },
            priority=MessagePriority.NORMAL
        )
        
        return {"status": "resolved", "incident_id": incident_id}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MEMORY PRUNING (Feature 19)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _prune_old_memory(self) -> None:
        """
        Intelligent memory pruning and consolidation.
        Preserves high-value "DNA" while archiving old context.
        """
        if not self.memory:
            return
        
        # Prune hot memory (>24h)
        await self.memory.prune_tier("hot", max_age_hours=24)
        
        # Compress working memory (>30 days)
        await self.memory.compress_tier("working", max_age_days=30)
        
        # Archive to cold memory with relevance scoring
        await self.memory.archive_low_relevance(threshold=0.3)
        
        self.logger.info("🧹 Memory pruning completed")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # TOWN HALL & RETROSPECTIVES (Feature 44)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def schedule_town_hall(self) -> Meeting:
        """Schedule weekly Town Hall meeting"""
        # Every Friday at 4 PM
        attendees = [
            "ord-pm", "ord-cfa", "ord-bd", "ord-hr", "ord-cma", "ord-daa", "ord-sec",
            "ord-se", "ord-design", "ord-content", "ord-review", "ord-fullstack-a", "ord-fullstack-b"
        ]
        
        return await self.schedule_meeting(
            meeting_type="town_hall",
            attendees=attendees,
            agenda="Weekly Town Hall: Wins, Learnings, Growth Areas, and Proposals"
        )
    
    async def run_retrospective(self, project_id: str) -> Dict:
        """Run project retrospective and update Company DNA"""
        self.logger.info(f"🔄 Running retrospective for project {project_id}")
        
        # Gather learnings from all agents
        learnings = []
        
        for agent_id, health in self.agent_health.items():
            if health.tasks_completed > 0:
                learnings.append({
                    "agent": agent_id,
                    "intelligence_score": health.intelligence_score,
                    "tasks_completed": health.tasks_completed
                })
        
        # Update Company DNA
        if self.memory:
            await self.memory.store_genome_entry({
                "type": "retrospective",
                "project_id": project_id,
                "learnings": learnings,
                "timestamp": time.time()
            })
        
        return {
            "status": "completed",
            "learnings_count": len(learnings),
            "message": "Retrospective completed and DNA updated! 🧬"
        }
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # INTELLIGENCE TRACKING (Feature 12)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def get_intelligence_report(self) -> Dict:
        """Generate intelligence score report for all agents"""
        scores = []
        
        for agent_id, health in self.agent_health.items():
            scores.append({
                "agent": agent_id,
                "score": health.intelligence_score,
                "tasks_completed": health.tasks_completed,
                "healthy": health.healthy
            })
        
        # Sort by score
        scores.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "scores": scores,
            "average_score": sum(s["score"] for s in scores) / len(scores) if scores else 0,
            "top_performer": scores[0] if scores else None,
            "needs_attention": [s for s in scores if s["score"] < 40]
        }
    
    async def celebrate_growth(self, agent_id: str, achievement: str) -> None:
        """Celebrate agent improvement (Feature 12)"""
        await self.send_message(
            recipient_id="broadcast",
            message_type="celebration",
            payload={
                "celebration_type": "agent_growth",
                "agent": agent_id,
                "achievement": achievement,
                "message": f"🌟 Celebrating {agent_id}! {achievement} Amazing growth! 💙"
            },
            priority=MessagePriority.LOW
        )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MAIN TASK PROCESSOR
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Process COO-specific tasks"""
        task_type = task.get("type", "unknown")
        
        if task_type == "schedule_meeting":
            meeting = await self.schedule_meeting(
                meeting_type=task.get("meeting_type"),
                attendees=task.get("attendees", []),
                agenda=task.get("agenda", "Team meeting"),
                project_id=task.get("project_id")
            )
            return {"status": "scheduled", "meeting_id": meeting.meeting_id}
        
        elif task_type == "health_check":
            return {"agent_health": {k: v.__dict__ for k, v in self.agent_health.items()}}
        
        elif task_type == "track_tokens":
            await self.track_token_usage(task.get("agent_id"), task.get("tokens", 0))
            return {"status": "tracked"}
        
        elif task_type == "incident_response":
            return await self.trigger_incident_response(
                task.get("incident_type"),
                task.get("context", {})
            )
        
        elif task_type == "resolve_incident":
            return await self.resolve_incident(
                task.get("incident_id"),
                task.get("resolution", "")
            )
        
        elif task_type == "intelligence_report":
            return await self.get_intelligence_report()
        
        elif task_type == "run_retrospective":
            return await self.run_retrospective(task.get("project_id"))
        
        elif task_type == "pause_agent":
            agent_id = task.get("agent_id")
            if agent_id in self.agent_health:
                self.agent_health[agent_id].status = "maintenance"
            return {"status": "paused", "agent_id": agent_id}
        
        return {"error": f"Unknown task type: {task_type}"}
