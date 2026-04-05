import asyncio
from typing import Any, Dict, List, Optional

from core.memory.hot_memory import HotMemory
from core.memory.working_memory import WorkingMemory
from core.memory.cold_memory import ColdMemory
from core.memory.genome import CompanyGenome


class MemoryManager:
    """
    Unified Memory Manager
    
    Coordinates all memory tiers:
    - Hot (Redis): Last 24h, <100MB/agent
    - Working (SQLite): Last 30 days, compressed summaries
    - Cold (Chroma): Archived, semantic search only
    - Genome: Company DNA, permanent learnings
    """
    
    def __init__(self):
        self.hot = HotMemory()
        self.working = WorkingMemory()
        self.cold = ColdMemory()
        self.genome = CompanyGenome()
        
        self.logger = self._setup_logging()
        self.logger.info("🧠 Memory Manager initialized")
    
    def _setup_logging(self):
        import logging
        return logging.getLogger("Ord.Memory")
    
    async def store(
        self,
        key: str,
        value: Any,
        tier: str = "working",
        agent_id: str = "system"
    ) -> bool:
        """
        Store value in appropriate memory tier.
        
        Tiers:
        - hot: Fast access, 24h TTL
        - working: Medium-term, 30 days
        - cold: Archive with semantic search
        - genome: Permanent Company DNA
        """
        if tier == "hot":
            return await self.hot.store(key, value, agent_id)
        
        elif tier == "working":
            return await self.working.store(key, value, agent_id)
        
        elif tier == "cold":
            text_content = str(value)
            return await self.cold.store(key, value, text_content)
        
        elif tier == "genome":
            return bool(await self.genome.store_entry(
                entry_type="memory",
                agent_id=agent_id,
                content={"key": key, "value": value}
            ))
        
        return False
    
    async def retrieve(
        self,
        key: str,
        tier: Optional[str] = None
    ) -> Optional[Any]:
        """
        Retrieve value from memory.
        If tier not specified, searches all tiers.
        """
        if tier:
            if tier == "hot":
                return await self.hot.retrieve(key)
            elif tier == "working":
                return await self.working.retrieve(key)
            elif tier == "cold":
                results = await self.cold.semantic_search(key, limit=1)
                return results[0]["value"] if results else None
        
        # Search all tiers
        for t in ["hot", "working"]:
            result = await self.retrieve(key, t)
            if result is not None:
                return result
        
        return None
    
    async def semantic_search(
        self,
        query: str,
        context: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """Search cold memory using semantic similarity"""
        return await self.cold.semantic_search(query, limit)
    
    async def store_genome_entry(
        self,
        entry_type: str,
        agent_id: str,
        content: Dict,
        tags: Optional[List[str]] = None
    ) -> str:
        """Store entry in Company Genome"""
        return await self.genome.store_entry(
            entry_type=entry_type,
            agent_id=agent_id,
            content=content,
            tags=tags,
            importance=content.get("importance", 0.5)
        )
    
    async def query_genome(
        self,
        query: str,
        entry_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """Query Company Genome"""
        return await self.genome.query(query, entry_type, limit)
    
    async def inherit_wisdom(self, project_type: str) -> Dict:
        """Inherit wisdom for new project"""
        return await self.genome.inherit_wisdom(project_type)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Maintenance Operations (Feature 19)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def prune_tier(self, tier: str, **kwargs) -> int:
        """Prune old entries from a tier"""
        if tier == "hot":
            return await self.hot.prune_expired()
        elif tier == "working":
            max_age = kwargs.get("max_age_days", 30)
            return await self.working.prune_old(max_age)
        elif tier == "cold":
            threshold = kwargs.get("threshold", 0.3)
            return await self.cold.archive_low_relevance(threshold)
        return 0
    
    async def compress_tier(self, tier: str, **kwargs) -> int:
        """Compress entries in a tier"""
        if tier == "working":
            max_age = kwargs.get("max_age_days", 30)
            return await self.working.compress_tier(max_age)
        return 0
    
    async def archive_low_relevance(self, threshold: float = 0.3) -> int:
        """Archive low-relevance entries"""
        return await self.cold.archive_low_relevance(threshold)
    
    def get_stats(self) -> Dict:
        """Get memory statistics for all tiers"""
        return {
            "hot": self.hot.get_stats(),
            "working": self.working.get_stats(),
            "cold": self.cold.get_stats(),
            "genome": self.genome.get_stats()
        }
