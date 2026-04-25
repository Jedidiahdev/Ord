import asyncio

from core.memory import FourTierMemorySystem


def test_four_tier_memory_local_chroma_fallback_roundtrip():
    memory = FourTierMemorySystem()

    async def run_flow():
        await memory.add_rag("default", ["doc-1"], ["Revenue forecast for stripe workflow"], [{"source": "unit"}])
        hits = await memory.search_rag("default", "stripe workflow", 1)
        assert hits
        assert "stripe" in hits[0].lower()

    asyncio.run(run_flow())
