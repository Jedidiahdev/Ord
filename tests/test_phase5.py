import asyncio
from pathlib import Path
import sys
import types

from core.feature_backbone import FeatureBackbone
from integrations.productization.exporter import ProductizationExporter
from integrations.voice.briefing import VoiceBriefingService

# lightweight stubs to avoid optional dependency imports in test env
mock_llm_router = types.ModuleType("core.llm_router")
mock_llm_router.llm_router = types.SimpleNamespace(route=lambda **_kwargs: "ok")
sys.modules.setdefault("core.llm_router", mock_llm_router)

mock_memory = types.ModuleType("core.memory")
mock_memory.memory = types.SimpleNamespace(
    update_agent_score=lambda *_args, **_kwargs: 51.0,
    store_genome_entry=lambda *_args, **_kwargs: "ok",
)
sys.modules.setdefault("core.memory", mock_memory)

from agents.base_agent import BaseAgent
from agents.executive.coo_agent import COOAgent


class _MemoryStub:
    async def update_agent_score(self, *_args, **_kwargs):
        return 51.0

    async def store_genome_entry(self, *_args, **_kwargs):
        return "ok"

    async def store(self, *_args, **_kwargs):
        return True

    async def retrieve(self, *_args, **_kwargs):
        return None


class DemoAgent(BaseAgent[str]):
    async def process_task(self, task: str):
        return {"message": f"handled {task}"}

    def get_capabilities(self):
        return ["demo"]


class _OrchestratorStub:
    def __init__(self):
        self.agents = {"a": type("Agent", (), {"intelligence_score": 60.0})(), "b": type("Agent", (), {"intelligence_score": 80.0})()}


def test_feature_backbone_summary():
    backbone = FeatureBackbone()
    summary = backbone.summary()
    assert summary["total_features"] == 50
    assert summary["priority_one_count"] == 15


def test_voice_briefing_shape():
    service = VoiceBriefingService()
    briefing = service.build_briefing("brief us", {"agent_status": {"a": {}}, "results": {"x": {}}})
    assert briefing.narration
    assert len(briefing.daa_visuals) >= 2


def test_productization_exporter(tmp_path: Path):
    exporter = ProductizationExporter()
    out = exporter.export(str(tmp_path), "test-app")
    assert (out / "README.md").exists()
    assert (out / ".env.example").exists()


def test_culture_and_reflection_payload():
    agent = DemoAgent("demo", "Demo", "Demo Agent", 1, memory_manager=_MemoryStub())
    result = asyncio.run(agent.process_task_with_culture("ship quickly", ceo_tone="celebratory"))
    assert "culture_closing" in result
    assert "reflection" in result
    assert result["reflection"]["agent_id"] == "demo"


def test_coo_compounding():
    coo = COOAgent(orchestrator=_OrchestratorStub(), memory_manager=_MemoryStub())
    snapshot = coo.compound_intelligence_scores()
    assert snapshot["fleet_average"] == 70.0
    assert snapshot["top_agent"] == "b"
