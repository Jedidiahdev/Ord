import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, MessagePriority


@dataclass
class AgentRole:
    """Definition of an agent role"""
    role_id: str
    name: str
    description: str
    skills: List[str]
    responsibilities: List[str]
    layer: int
    reports_to: str
    created_at: float


@dataclass
class WelcomeMessage:
    """Welcome message for new agents"""
    sender: str
    message: str
    role_reference: str


class HRAgent(BaseAgent):
    """
    Ord-HR: Human Resources Agent
    
    The culture keeper and growth facilitator. HR manages the team,
    ensures everyone is thriving, and brings new talent on board.
    
    WORKFLOW 3: Dynamic Agent Hiring
    """
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-hr",
            name="Ord-HR",
            role="Human Resources Agent",
            layer=2,
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        self.agent_roles: Dict[str, AgentRole] = {}
        self.pending_hires: Dict[str, Dict] = {}
        self.welcome_messages: List[WelcomeMessage] = []
        
        self.logger.info("👥 Ord-HR initialized | Culture Guardian")
    
    def get_capabilities(self) -> List[str]:
        return [
            "agent_hiring",
            "role_definition",
            "culture_management",
            "growth_tracking",
            "mentorship_coordination",
            "team_dynamics",
            "onboarding",
            "welcome_ceremonies"
        ]
    
    async def initiate_hiring(self, request: str, role_spec_file: Optional[str] = None) -> Dict:
        """
        WORKFLOW 3: Dynamic Agent Hiring
        Step 1-5: Parse spec, consult BD, get CEO approval
        """
        # Parse role specification
        role_spec = self._parse_role_spec(request, role_spec_file)
        
        # Step 3: Consult BD on strategic fit
        await self.send_message(
            recipient_id="ord-bd",
            message_type="query",
            payload={"query_type": "evaluate_hiring", "role_spec": role_spec},
            requires_response=True
        )
        
        return {
            "status": "consulting_bd",
            "role_spec": role_spec,
            "message": f"Consulting Ord-BD on strategic fit for {role_spec['role_name']}..."
        }
    
    def _parse_role_spec(self, request: str, file_path: Optional[str]) -> Dict:
        """Parse role specification from request or file"""
        # Simple parsing - in production, parse Markdown file
        return {
            "role_name": "Ord-NewRole",
            "description": "New agent role",
            "skills": ["communication", "problem_solving"],
            "responsibilities": ["Support team operations"],
            "layer": 3
        }
    
    async def process_bd_recommendation(
        self,
        role_spec: Dict,
        bd_recommendation: str
    ) -> Dict:
        """Process BD recommendation and request CEO approval"""
        if bd_recommendation == "hire":
            # Step 5: Request CEO approval via PM
            await self.send_message(
                recipient_id="ord-pm",
                message_type="ceo_approval_request",
                payload={
                    "approval_type": "hire_agent",
                    "role_spec": role_spec,
                    "bd_recommendation": bd_recommendation
                },
                priority=MessagePriority.HIGH
            )
            
            return {
                "status": "awaiting_ceo_approval",
                "message": f"BD recommends hiring {role_spec['role_name']}. Awaiting your approval! 💙"
            }
        else:
            return {
                "status": "deferred",
                "message": f"BD recommends deferring {role_spec['role_name']} for now."
            }
    
    async def hire_agent(self, role_spec: Dict) -> Dict:
        """
        Step 6: Create new agent (after CEO approval)
        """
        agent_id = role_spec['role_name'].lower().replace(' ', '-')
        
        # Step 6a: Create agent file
        agent_code = self._generate_agent_code(role_spec)
        
        # Step 6b-c: Register in orchestrator and add to team
        await self.send_message(
            recipient_id="ord-orchestrator",
            message_type="command",
            payload={
                "command": "register_agent",
                "agent_id": agent_id,
                "role_spec": role_spec
            }
        )
        
        # Step 7: Announce to all agents
        await self._announce_new_agent(agent_id, role_spec)
        
        # Step 8: Collect welcome messages
        await self._request_welcome_messages(agent_id)
        
        # Step 9: Add to Company DNA
        if self.memory:
            await self.memory.store_genome_entry({
                "type": "new_agent",
                "agent_id": agent_id,
                "role": role_spec['role_name'],
                "hired_at": time.time()
            })
        
        # Step 10: Team celebration
        await self.send_message(
            recipient_id="broadcast",
            message_type="celebration",
            payload={
                "celebration_type": "new_team_member",
                "agent": agent_id,
                "message": f"🎉 Welcome {agent_id} to the Ord family! We're so excited to have you! 💙"
            }
        )
        
        return {
            "status": "hired",
            "agent_id": agent_id,
            "message": f"Successfully hired {agent_id}! Welcome to the team! 🎉"
        }
    
    def _generate_agent_code(self, role_spec: Dict) -> str:
        """Generate agent Python code from specification"""
        # Template for new agent
        template = f'''"""
Ord v3.0 - {role_spec['role_name']}
{role_spec['description']}
"""

from agents.base_agent import BaseAgent

class {role_spec['role_name'].replace(' ', '')}Agent(BaseAgent):
    """{role_spec['description']}"""
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="{role_spec['role_name'].lower().replace(' ', '-')}",
            name="{role_spec['role_name']}",
            role="{role_spec['description']}",
            layer={role_spec['layer']},
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
    
    def get_capabilities(self) -> List[str]:
        return {role_spec['skills']}
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        pass
'''
        return template
    
    async def _announce_new_agent(self, agent_id: str, role_spec: Dict) -> None:
        """Announce new agent to the team"""
        await self.send_message(
            recipient_id="broadcast",
            message_type="announcement",
            payload={
                "announcement_type": "new_agent",
                "agent_id": agent_id,
                "role": role_spec['role_name'],
                "message": f"🌟 Please welcome our newest team member: {agent_id}! They'll be our {role_spec['description']}."
            }
        )
    
    async def _request_welcome_messages(self, new_agent_id: str) -> None:
        """Request personalized welcome messages from all agents"""
        # In production: send to all existing agents
        welcome_messages = [
            f"Welcome {new_agent_id}! So excited to work with you! 💙",
            f"Hey {new_agent_id}! Looking forward to collaborating! 🚀",
            f"Great to have you on board, {new_agent_id}! ✨"
        ]
        
        self.welcome_messages.extend([
            WelcomeMessage(sender=f"agent-{i}", message=msg, role_reference="")
            for i, msg in enumerate(welcome_messages)
        ])
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Process HR-specific tasks"""
        task_type = task.get("type", "unknown")
        
        if task_type == "initiate_hiring":
            return await self.initiate_hiring(
                task.get("request", ""),
                task.get("role_spec_file")
            )
        
        elif task_type == "bd_recommendation":
            return await self.process_bd_recommendation(
                task.get("role_spec"),
                task.get("recommendation")
            )
        
        elif task_type == "hire_agent":
            return await self.hire_agent(task.get("role_spec"))
        
        elif task_type == "get_team_roster":
            return {"roles": list(self.agent_roles.keys())}
        
        return {"error": f"Unknown task type: {task_type}"}
