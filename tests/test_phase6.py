import asyncio
import sys
import types

import pytest

mock_llm_router = types.ModuleType("core.llm_router")
mock_llm_router.llm_router = types.SimpleNamespace(route=lambda **_kwargs: "ok")
sys.modules.setdefault("core.llm_router", mock_llm_router)

mock_memory = types.ModuleType("core.memory")
mock_memory.memory = types.SimpleNamespace(
    update_agent_score=lambda *_args, **_kwargs: 51.0,
    store_genome_entry=lambda *_args, **_kwargs: "ok",
    log_task=lambda *_args, **_kwargs: None,
)
sys.modules.setdefault("core.memory", mock_memory)

mock_httpx = types.ModuleType("httpx")

class _AsyncClient:
    def __init__(self, *args, **kwargs):
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False
    async def post(self, *args, **kwargs):
        return types.SimpleNamespace(status_code=200, json=lambda: {"id": "dep_1", "url": "example.vercel.app", "inspectorUrl": "https://vercel.com"}, text="")

mock_httpx.AsyncClient = _AsyncClient
sys.modules.setdefault("httpx", mock_httpx)

mock_pydantic = types.ModuleType("pydantic")

class _BaseModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def _field(default_factory=None, default=None):
    if default_factory is not None:
        return default_factory()
    return default

mock_pydantic.BaseModel = _BaseModel
mock_pydantic.Field = _field
sys.modules.setdefault("pydantic", mock_pydantic)

from agents.execution.backend_agent import BackendAgent
from agents.execution.content_agent import ContentAgent
from agents.execution.design_agent import DesignAgent
from agents.execution.frontend_agent import FrontendAgent
from agents.execution.review_agent import ReviewAgent
from agents.execution.se_agent import SEAgent
from agents.executive.bd_agent import BDAgent
from agents.executive.cfa_agent import CFAAgent
from agents.executive.cma_agent import CMAAgent
from agents.executive.coo_agent import COOAgent
from agents.executive.daa_agent import DAAAgent
from agents.executive.hr_agent import HRAgent
from agents.executive.pm_agent import PMAgent
from agents.infrastructure.orchestrator import Orchestrator as InfraOrchestrator
from agents.infrastructure.ord_orchestrator_agent import OrdOrchestratorAgent
from agents.infrastructure.security_agent import SecurityAgent


class MemoryStub:
    async def update_agent_score(self, *_args, **_kwargs):
        return 51.0

    async def store_genome_entry(self, *_args, **_kwargs):
        return "ok"

    async def store(self, *_args, **_kwargs):
        return True

    async def retrieve(self, *_args, **_kwargs):
        return None


class OrchestratorStub:
    def __init__(self):
        self.agents = {}


@pytest.fixture()
def mem_stub():
    return MemoryStub()


@pytest.mark.parametrize(
    "agent_cls,task,expected_key",
    [
        (BDAgent, {"type": "evaluate_hiring", "role_spec": {"role_name": "Ord-Analyst", "description": "data"}}, "recommendation"),
        (CFAAgent, {"type": "process_webhook", "event": {"type": "invoice.paid", "data": {"object": {"id": "inv_1", "amount_paid": 2000, "currency": "usd"}}}}, "status"),
        (CMAAgent, {"type": "create_campaign", "spec": {"name": "Launch", "budget": 1000}}, "campaign_id"),
        (COOAgent, {"type": "schedule_meeting", "meeting_type": "standup", "attendees": ["ord-pm"], "agenda": "Daily sync"}, "status"),
        (DAAAgent, {"type": "generate_insight", "query": "stripe dashboard"}, "insight"),
        (HRAgent, {"type": "initiate_hiring", "request": "Need analytics specialist"}, "hire_id"),
        (ReviewAgent, {"type": "review_pr", "pr_id": "pr-1", "title": "feat", "description": "desc"}, "status"),
        (SEAgent, {"type": "20_variation_code", "variation_id": 2, "project_name": "Ord"}, "variation_id"),
        (FrontendAgent, {"type": "20_variation_frontend", "variation_id": 3, "project_name": "Ord", "creative_direction": "minimal"}, "variation_id"),
        (BackendAgent, {"type": "20_variation_backend", "variation_id": 4, "project_name": "Ord", "creative_direction": "bold"}, "variation_id"),
        (ContentAgent, {"type": "variation_briefs", "project_id": "p1", "variations": [{"variation_id": 1, "creative_direction": "clean"}]}, "briefs"),
        (SecurityAgent, {"type": "audit_code", "code": "const a = 1", "agent_id": "ord-se"}, "can_proceed"),
        (OrdOrchestratorAgent, {"type": "status"}, "status"),
    ],
)
def test_all_agents_smoke_paths(mem_stub, agent_cls, task, expected_key):
    orch = OrchestratorStub()
    if agent_cls is OrdOrchestratorAgent:
        orch.agents["ord-design"] = DesignAgent(orchestrator=orch, memory_manager=mem_stub)

    agent = agent_cls(orchestrator=orch, memory_manager=mem_stub)
    result = asyncio.run(agent.process_task(task))

    assert expected_key in result
    assert agent.get_capabilities()


def test_20_variation_engine_generates_full_set(mem_stub):
    orch = OrchestratorStub()
    orch.agents["ord-fullstack-a"] = FrontendAgent(orchestrator=orch, memory_manager=mem_stub)
    orch.agents["ord-fullstack-b"] = BackendAgent(orchestrator=orch, memory_manager=mem_stub)

    design = DesignAgent(orchestrator=orch, memory_manager=mem_stub)
    payload = asyncio.run(design.process_task({"type": "20_variation_experiment", "project_id": "proj-1", "project_name": "Orange SaaS"}))

    assert payload["status"] == "completed"
    assert payload["variation_count"] == 20
    assert len(payload["variations"]) == 20


def test_infra_orchestrator_voice_to_meeting_to_dashboard_flow(mem_stub):
    orch = InfraOrchestrator()
    orch.register_agent(DAAAgent(orchestrator=orch, memory_manager=mem_stub))
    orch.register_agent(CFAAgent(orchestrator=orch, memory_manager=mem_stub))

    routed = asyncio.run(orch.route("Run finance stripe dashboard review", ceo_tone="neutral"))
    assert "ord-cfa" in routed["results"]

    briefing = asyncio.run(orch.voice_first_briefing("show DAA dashboard", routed))
    assert briefing["narration"]
    assert len(briefing["daa_visuals"]) >= 2


def test_pm_workflow_creates_20_variations_and_graph(mem_stub):
    pm = PMAgent(orchestrator=OrchestratorStub(), memory_manager=mem_stub)

    async def fast_sandbox(task):
        return {"mock_html": "<div/>", "schema": {"tables": ["users"]}, "pitch": task["creative_direction"]}

    pm._execute_variation_sandbox = fast_sandbox  # type: ignore[method-assign]

    result = asyncio.run(pm.process_task({"type": "ceo_request", "request_text": "Build a simple SaaS landing page", "input_type": "text"}))

    assert result["status"] == "initiated"
    project = pm.projects[result["project_id"]]
    assert len(project.variations) == 20
    assert project.workflow is not None
    assert "deploy" in project.workflow.nodes
