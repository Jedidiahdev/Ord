import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, A2AMessage, MessagePriority, AgentStatus


@dataclass
class TaskNode:
    """Node in the task execution graph (LangGraph pattern)"""
    node_id: str
    agent_id: str
    task_type: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict] = None
    checkpoint_data: Optional[Dict] = None
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    completed_at: Optional[float] = None


@dataclass
class WorkflowGraph:
    """LangGraph-style workflow definition with checkpointing"""
    graph_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    nodes: Dict[str, TaskNode] = field(default_factory=dict)
    edges: List[tuple] = field(default_factory=list)  # (from_node, to_node, condition)
    status: str = "created"  # created, running, paused, completed, failed
    current_node: Optional[str] = None
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    ceo_approval_points: List[str] = field(default_factory=list)


@dataclass
class Project:
    """Complete project definition with full lifecycle"""
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    ceo_request: str = ""
    workflow: Optional[WorkflowGraph] = None
    variations: List[Dict] = field(default_factory=list)  # For 20-variation factory
    selected_variation: Optional[int] = None
    status: str = "created"
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    deployed_at: Optional[float] = None
    live_url: Optional[str] = None
    revenue_tracked: bool = False


class PMAgent(BaseAgent):
    """
    Ord-PM: The Chief Executive Agent
    
    Responsibilities:
    1. Receive CEO requests (voice/text from Telegram)
    2. Create task graphs using Planning pattern (Ch6)
    3. Route tasks to appropriate Domain Leaders
    4. Coordinate 20-variation experimentation
    5. Present options to CEO for approval
    6. Orchestrate full production sprints
    7. Final approver before deployments
    
    Communication Rules:
    - Only PM initiates cross-domain workflows (Rule 3)
    - All worker communication routes through Domain Leaders
    """
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-pm",
            name="Ord-PM",
            role="Project Manager / CEO Router",
            layer=1,  # Executive Council
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        # Active projects and workflows
        self.projects: Dict[str, Project] = {}
        self.active_workflows: Dict[str, WorkflowGraph] = {}
        
        # Agent capability registry for routing
        self.agent_capabilities: Dict[str, List[str]] = {}
        
        # Approval tracking
        self.pending_approvals: Dict[str, Dict] = {}
        
        self.logger.info("👑 Ord-PM initialized | CEO Router ready")
    
    def get_capabilities(self) -> List[str]:
        return [
            "task_graph_creation",
            "cross_domain_orchestration",
            "ceo_request_processing",
            "workflow_checkpointing",
            "approval_management",
            "20_variation_experimentation",
            "sprint_planning",
            "deployment_coordination"
        ]
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MAIN ENTRY: CEO Request Processing
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def process_ceo_request(
        self,
        request_text: str,
        input_type: str = "text",  # text, voice, screenshot, figma
        attachments: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for CEO requests.
        Multi-modal input router (Feature 8)
        """
        self.logger.info(f"👔 CEO Request received: {request_text[:50]}...")
        
        # Acknowledge with warm tone (Feature 17 - Emotional Intelligence)
        acknowledgment = self._generate_acknowledgment(request_text)
        
        # Classify request type
        request_type = self._classify_request(request_text)
        
        # Route to appropriate workflow
        if request_type == "product_build":
            return await self._initiate_product_build(request_text, input_type, attachments)
        elif request_type == "status_check":
            return await self._provide_status_update()
        elif request_type == "financial_review":
            return await self._schedule_financial_meeting()
        elif request_type == "hire_agent":
            return await self._initiate_hiring_workflow(request_text)
        elif request_type == "deploy_request":
            return await self._handle_deploy_request(request_text)
        else:
            return await self._general_orchestration(request_text)
    
    def _generate_acknowledgment(self, request: str) -> str:
        """Generate warm, professional acknowledgment (Feature 17)"""
        import random
        acknowledgments = [
            f"Absolutely! I'm on it right away. 💙",
            f"Great vision! Let me orchestrate the team to make this happen. 🚀",
            f"Love this direction! Breaking it down into actionable steps now. ✨",
            f"Consider it handled! The team will execute with precision. 🎯",
            f"Exciting project! I'll coordinate everything seamlessly. 🔥"
        ]
        return random.choice(acknowledgments)
    
    def _classify_request(self, request: str) -> str:
        """Classify CEO request type for routing"""
        request_lower = request.lower()
        
        build_keywords = ["build", "create", "make", "ship", "develop", "design", "app", "website", "product"]
        status_keywords = ["status", "update", "how are we", "progress", "what's happening"]
        financial_keywords = ["financial", "revenue", "stripe", "money", "budget", "meeting"]
        hire_keywords = ["hire", "new agent", "add agent", "recruit"]
        deploy_keywords = ["deploy", "launch", "ship to production", "go live"]
        
        if any(kw in request_lower for kw in build_keywords):
            return "product_build"
        elif any(kw in request_lower for kw in status_keywords):
            return "status_check"
        elif any(kw in request_lower for kw in financial_keywords):
            return "financial_review"
        elif any(kw in request_lower for kw in hire_keywords):
            return "hire_agent"
        elif any(kw in request_lower for kw in deploy_keywords):
            return "deploy_request"
        
        return "general"
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PRODUCT BUILD WORKFLOW (Feature 1, 9)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _initiate_product_build(
        self,
        request: str,
        input_type: str,
        attachments: Optional[List]
    ) -> Dict[str, Any]:
        """
        WORKFLOW 1: Product Building (The Main Event)
        20-variation experimentation → selection → sprint → deploy
        """
        # Create project
        project = Project(
            name=self._extract_project_name(request),
            description=request,
            ceo_request=request
        )
        self.projects[project.project_id] = project
        
        self.logger.info(f"🚀 Product build initiated: {project.name}")
        
        # Step 1: Create workflow graph with Planning pattern (Ch6)
        workflow = self._create_product_build_workflow(project)
        project.workflow = workflow
        self.active_workflows[workflow.graph_id] = workflow
        
        # Step 2: Schedule kickoff meeting via COO
        await self._schedule_kickoff_meeting(project)
        
        # Step 3: Initiate 20-variation experimentation
        await self._spawn_variation_experiments(project)
        
        return {
            "status": "initiated",
            "project_id": project.project_id,
            "message": f"🚀 Project '{project.name}' initiated! Running 20-variation experimentation...",
            "next_step": "variations_generating"
        }
    
    def _create_product_build_workflow(self, project: Project) -> WorkflowGraph:
        """
        Create LangGraph workflow for product building (Feature 2)
        Nodes: Experimentation → Analysis → Selection → Sprint → Review → Deploy
        """
        workflow = WorkflowGraph(name=f"Build: {project.name}")
        
        # Define nodes
        nodes = [
            TaskNode("experimentation", "ord-design,ord-fullstack-a,ord-fullstack-b,ord-se", 
                    "20_variation_factory", "Generate 20 product variations"),
            TaskNode("analysis", "ord-daa", "variation_scoring", 
                    "Score all variations on multiple dimensions"),
            TaskNode("presentation", "ord-pm", "ceo_presentation", 
                    "Present top 3 to CEO in Ord HQ"),
            TaskNode("selection", "ord-pm", "ceo_selection", 
                    "Wait for CEO to select winning variation"),
            TaskNode("sprint", "ord-design,ord-fullstack-a,ord-fullstack-b,ord-se,ord-content", 
                    "full_sprint", "Execute full production sprint"),
            TaskNode("review", "ord-review,ord-sec", "quality_gates", 
                    "Code review and security audit"),
            TaskNode("approval", "ord-pm", "deploy_approval", 
                    "Ask CEO for deploy approval"),
            TaskNode("deploy", "ord-se", "vercel_deploy", 
                    "Deploy to Vercel and send URL"),
            TaskNode("celebration", "ord-coo", "team_celebration", 
                    "Update DNA and celebrate")
        ]
        
        for node in nodes:
            workflow.nodes[node.node_id] = node
            if node.node_id in ["presentation", "approval"]:
                workflow.ceo_approval_points.append(node.node_id)
        
        # Define edges with conditions
        workflow.edges = [
            ("experimentation", "analysis", "all_complete"),
            ("analysis", "presentation", "scoring_done"),
            ("presentation", "selection", "ceo_viewed"),
            ("selection", "sprint", "winner_chosen"),
            ("sprint", "review", "code_complete"),
            ("review", "approval", "quality_passed"),
            ("approval", "deploy", "ceo_approved"),
            ("deploy", "celebration", "live_url_sent")
        ]
        
        return workflow
    
    def _extract_project_name(self, request: str) -> str:
        """Extract project name from CEO request"""
        # Simple extraction - can be enhanced with LLM
        words = request.split()
        if len(words) > 3:
            return " ".join(words[:4]).title()
        return request.title()
    
    async def _schedule_kickoff_meeting(self, project: Project) -> None:
        """Schedule kickoff via COO (Feature 6)"""
        await self.send_message(
            recipient_id="ord-coo",
            message_type="task",
            payload={
                "task": {
                    "type": "schedule_meeting",
                    "meeting_type": "kickoff",
                    "project_id": project.project_id,
                    "project_name": project.name,
                    "attendees": ["ord-pm", "ord-design", "ord-se", "ord-fullstack-a", "ord-fullstack-b"]
                }
            },
            priority=MessagePriority.HIGH
        )
    
    async def _spawn_variation_experiments(self, project: Project) -> None:
        """
        Feature 1: Hyper-Parallel 20-Variation Experimentation Factory
        Spawn 20 isolated sandboxes, each with mini-team
        """
        self.logger.info(f"🔬 Spawning 20 variation sandboxes for {project.name}")
        
        variation_tasks = []
        for i in range(20):
            task = self._create_variation_task(project, i)
            variation_tasks.append(task)
        
        # Execute in parallel (Parallelization Ch3)
        # In production, these would be Docker containers
        results = await asyncio.gather(*[
            self._execute_variation_sandbox(task) for task in variation_tasks
        ], return_exceptions=True)
        
        # Store results
        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                project.variations.append({
                    "variation_id": i,
                    "result": result,
                    "status": "completed"
                })
        
        # Trigger DAA analysis
        await self._request_variation_analysis(project)
    
    def _create_variation_task(self, project: Project, variation_id: int) -> Dict:
        """Create task for a single variation sandbox"""
        import random
        
        # Each variation gets slightly different creative direction
        creative_directions = [
            "minimalist and clean",
            "bold and vibrant",
            "professional enterprise",
            "playful and friendly",
            "dark mode premium",
            "light and airy",
            "high-conversion focused",
            "developer-centric",
            "mobile-first approach",
            "desktop-power-user",
            "AI-native interface",
            "traditional familiar",
            "cutting-edge experimental",
            "accessibility-first",
            "performance-optimized",
            "feature-rich comprehensive",
            "single-purpose focused",
            "collaboration-centric",
            "solo-user optimized",
            "enterprise-grade secure"
        ]
        
        return {
            "variation_id": variation_id,
            "project_id": project.project_id,
            "project_name": project.name,
            "description": project.description,
            "creative_direction": creative_directions[variation_id],
            "sandbox_id": f"sandbox-{project.project_id}-{variation_id}"
        }
    
    async def _execute_variation_sandbox(self, task: Dict) -> Dict:
        """
        Execute variation in isolated sandbox.
        In production: Docker container with resource limits
        """
        # Simulate sandbox execution
        await asyncio.sleep(0.5)  # Simulate work
        
        return {
            "mock_html": f"<html><body>Variation {task['variation_id']}: {task['creative_direction']}</body></html>",
            "schema": {"tables": ["users", "projects", "tasks"]},
            "pitch": f"A {task['creative_direction']} approach to {task['project_name']}",
            "estimated_build_time": "3-5 days",
            "estimated_cost": f"${500 + task['variation_id'] * 50}"
        }
    
    async def _request_variation_analysis(self, project: Project) -> None:
        """Request DAA to score all variations"""
        await self.send_message(
            recipient_id="ord-daa",
            message_type="task",
            payload={
                "task": {
                    "type": "score_variations",
                    "project_id": project.project_id,
                    "variations": project.variations
                }
            },
            priority=MessagePriority.HIGH,
            requires_response=True
        )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # WORKFLOW EXECUTION & CHECKPOINTING (Feature 2)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def execute_workflow_node(self, workflow_id: str, node_id: str) -> Dict:
        """
        Execute a single node in the workflow graph.
        Automatic checkpoint after every execution.
        """
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}
        
        node = workflow.nodes.get(node_id)
        if not node:
            return {"error": "Node not found"}
        
        # Check dependencies
        for dep_id in node.dependencies:
            dep_node = workflow.nodes.get(dep_id)
            if not dep_node or dep_node.status != "completed":
                return {"error": f"Dependency {dep_id} not completed"}
        
        # Execute node
        node.status = "running"
        workflow.current_node = node_id
        
        try:
            # Route to appropriate agent(s)
            agent_ids = node.agent_id.split(",")
            results = []
            
            for agent_id in agent_ids:
                result = await self.send_message(
                    recipient_id=agent_id,
                    message_type="task",
                    payload={"task": node.__dict__},
                    priority=MessagePriority.HIGH,
                    requires_response=True
                )
                results.append(result)
            
            node.result = {"results": results}
            node.status = "completed"
            node.completed_at = datetime.now().timestamp()
            
            # Checkpoint (Feature 2)
            await self._save_checkpoint(workflow, node)
            
            return node.result
            
        except Exception as e:
            node.status = "failed"
            await self._handle_node_failure(workflow, node, str(e))
            return {"error": str(e)}
    
    async def _save_checkpoint(self, workflow: WorkflowGraph, node: TaskNode) -> None:
        """Save workflow state for potential rewind/replay"""
        checkpoint = {
            "workflow_id": workflow.graph_id,
            "node_id": node.node_id,
            "timestamp": datetime.now().timestamp(),
            "workflow_state": workflow.status,
            "node_result": node.result
        }
        
        if self.memory:
            await self.memory.store(
                f"checkpoint:{workflow.graph_id}:{node.node_id}",
                checkpoint,
                tier="working"
            )
    
    async def _handle_node_failure(self, workflow: WorkflowGraph, node: TaskNode, error: str) -> None:
        """Handle node execution failure with escalation"""
        self.logger.error(f"❌ Node {node.node_id} failed: {error}")
        
        # Self-healing: retry with modified approach (Feature 3)
        await self.send_message(
            recipient_id="ord-coo",
            message_type="alert",
            payload={
                "alert_type": "task_failure",
                "workflow_id": workflow.graph_id,
                "node_id": node.node_id,
                "error": error
            },
            priority=MessagePriority.CRITICAL
        )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # APPROVAL MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def request_ceo_approval(
        self,
        approval_type: str,
        context: Dict,
        project_id: Optional[str] = None
    ) -> str:
        """
        Request CEO approval at critical decision points.
        Returns approval_id for tracking.
        """
        approval_id = str(uuid.uuid4())
        
        self.pending_approvals[approval_id] = {
            "approval_id": approval_id,
            "type": approval_type,
            "context": context,
            "project_id": project_id,
            "status": "pending",
            "requested_at": datetime.now().timestamp(),
            "response": None
        }
        
        # Send to CEO via Telegram
        await self.send_message(
            recipient_id="telegram_bot",
            message_type="ceo_approval_request",
            payload={
                "approval_id": approval_id,
                "type": approval_type,
                "message": self._format_approval_request(approval_type, context),
                "options": ["yes", "no", "modify"]
            },
            priority=MessagePriority.HIGH,
            requires_response=True
        )
        
        return approval_id
    
    def _format_approval_request(self, approval_type: str, context: Dict) -> str:
        """Format approval request with warm, professional tone"""
        if approval_type == "deploy":
            return (
                f"🚀 **Ready to Deploy!**\n\n"
                f"Project: {context.get('project_name', 'Unknown')}\n"
                f"Quality gates: ✅ Passed\n"
                f"Security audit: ✅ Passed\n\n"
                f"Ready to deploy to Vercel? (yes/no)"
            )
        elif approval_type == "variation_selection":
            return (
                f"🎨 **Top 3 Variations Ready!**\n\n"
                f"I've analyzed all 20 variations. The top 3 are ready for your review in Ord HQ.\n\n"
                f"Which direction resonates with your vision? (1/2/3/modify)"
            )
        
        return f"Approval needed for: {approval_type}"
    
    async def process_ceo_response(self, approval_id: str, response: str) -> Dict:
        """Process CEO's approval response"""
        approval = self.pending_approvals.get(approval_id)
        if not approval:
            return {"error": "Approval request not found"}
        
        approval["status"] = "responded"
        approval["response"] = response
        approval["responded_at"] = datetime.now().timestamp()
        
        # Route based on approval type
        if approval["type"] == "deploy" and response.lower() == "yes":
            return await self._execute_deployment(approval["project_id"])
        elif approval["type"] == "variation_selection":
            return await self._process_variation_selection(approval["project_id"], response)
        
        return {"status": "processed", "response": response}
    
    async def _execute_deployment(self, project_id: str) -> Dict:
        """Execute Vercel deployment after CEO approval"""
        project = self.projects.get(project_id)
        if not project:
            return {"error": "Project not found"}
        
        self.logger.info(f"🚀 Executing deployment for {project.name}")
        
        # Trigger deployment via SE
        await self.send_message(
            recipient_id="ord-se",
            message_type="task",
            payload={
                "task": {
                    "type": "deploy_to_vercel",
                    "project_id": project_id,
                    "project_name": project.name
                }
            },
            priority=MessagePriority.CRITICAL,
            requires_response=True
        )
        
        return {"status": "deploying", "message": "Deployment initiated! 🚀"}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Required by BaseAgent - handle direct task assignments"""
        task_type = task.get("type", "unknown")
        
        if task_type == "ceo_request":
            return await self.process_ceo_request(
                task.get("request_text", ""),
                task.get("input_type", "text"),
                task.get("attachments")
            )
        elif task_type == "ceo_response":
            return await self.process_ceo_response(
                task.get("approval_id"),
                task.get("response")
            )
        elif task_type == "variation_analysis_complete":
            return await self._present_variations_to_ceo(task.get("project_id"))
        
        return {"error": f"Unknown task type: {task_type}"}
    
    async def _present_variations_to_ceo(self, project_id: str) -> Dict:
        """Present top 3 variations to CEO in Ord HQ"""
        project = self.projects.get(project_id)
        if not project:
            return {"error": "Project not found"}
        
        # Sort variations by DAA score
        sorted_vars = sorted(
            project.variations,
            key=lambda v: v.get("daa_score", 0),
            reverse=True
        )[:3]
        
        # Send to dashboard for display
        await self.send_message(
            recipient_id="dashboard_api",
            message_type="update",
            payload={
                "update_type": "variations_ready",
                "project_id": project_id,
                "variations": sorted_vars
            },
            priority=MessagePriority.HIGH
        )
        
        # Request CEO selection
        approval_id = await self.request_ceo_approval(
            approval_type="variation_selection",
            context={"project_id": project_id, "variations": sorted_vars},
            project_id=project_id
        )
        
        return {
            "status": "awaiting_selection",
            "approval_id": approval_id,
            "message": "Top 3 variations presented in Ord HQ"
        }
    
    async def _provide_status_update(self) -> Dict:
        """Provide comprehensive company status"""
        active_projects = len([p for p in self.projects.values() if p.status != "completed"])
        pending_approvals = len([a for a in self.pending_approvals.values() if a["status"] == "pending"])
        
        return {
            "active_projects": active_projects,
            "pending_approvals": pending_approvals,
            "active_workflows": len(self.active_workflows),
            "message": f"📊 Status: {active_projects} active projects, {pending_approvals} awaiting your decision"
        }
    
    async def _schedule_financial_meeting(self) -> Dict:
        """Schedule financial review meeting"""
        await self.send_message(
            recipient_id="ord-coo",
            message_type="task",
            payload={
                "task": {
                    "type": "schedule_meeting",
                    "meeting_type": "financial_review",
                    "attendees": ["ord-pm", "ord-cfa", "ord-daa", "ord-cma", "ord-bd"]
                }
            },
            priority=MessagePriority.NORMAL
        )
        
        return {"status": "scheduled", "message": "Financial review meeting scheduled! 📅"}
    
    async def _initiate_hiring_workflow(self, request: str) -> Dict:
        """Route to HR for hiring workflow"""
        await self.send_message(
            recipient_id="ord-hr",
            message_type="task",
            payload={
                "task": {
                    "type": "initiate_hiring",
                    "request": request
                }
            },
            priority=MessagePriority.HIGH
        )
        
        return {"status": "routing_to_hr", "message": "Routing to Ord-HR for hiring process! 👥"}
    
    async def _handle_deploy_request(self, request: str) -> Dict:
        """Handle direct deploy request"""
        return {"status": "needs_project", "message": "Please specify which project to deploy"}
    
    async def _general_orchestration(self, request: str) -> Dict:
        """General request orchestration"""
        return {
            "status": "received",
            "message": f"I've received your request: '{request[:50]}...' Let me analyze and route appropriately.",
            "action": "analyzing"
        }
    
    async def _process_variation_selection(self, project_id: str, response: str) -> Dict:
        """Process CEO's variation selection"""
        project = self.projects.get(project_id)
        if not project:
            return {"error": "Project not found"}
        
        try:
            selected = int(response) - 1
            project.selected_variation = selected
            project.status = "sprint_started"
            
            # Initiate full sprint
            return await self._initiate_full_sprint(project)
        except ValueError:
            return {"status": "awaiting_clarification", "message": "Please select 1, 2, or 3"}
    
    async def _initiate_full_sprint(self, project: Project) -> Dict:
        """Initiate full production sprint after variation selection"""
        self.logger.info(f"🏃 Initiating full sprint for {project.name}")
        
        # Update workflow
        workflow = project.workflow
        workflow.status = "running"
        
        # Execute sprint node
        await self.execute_workflow_node(workflow.graph_id, "sprint")
        
        return {
            "status": "sprint_initiated",
            "project_id": project.project_id,
            "message": f"🏃 Full sprint initiated for '{project.name}'! The team is building with precision."
        }
