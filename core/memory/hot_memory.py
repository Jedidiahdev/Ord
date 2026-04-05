import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class HotMemoryEntry:
    """Single hot memory entry"""
    key: str
    value: Any
    agent_id: str
    created_at: float
    expires_at: float
    access_count: int = 0


class HotMemory:
    """
    Hot Memory Layer (Redis simulation)
    
    Fast in-memory storage for active context.
    Automatically expires entries after 24 hours.
    """
    
    DEFAULT_TTL = 24 * 3600  # 24 hours
    MAX_SIZE_MB = 100
    
    def __init__(self):
        self.store: Dict[str, HotMemoryEntry] = {}
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        import logging
        return logging.getLogger("Ord.Memory.Hot")
    
    async def store(
        self,
        key: str,
        value: Any,
        agent_id: str,
        ttl: Optional[int] = None
    ) -> bool:
        """Store value in hot memory"""
        ttl = ttl or self.DEFAULT_TTL
        
        entry = HotMemoryEntry(
            key=key,
            value=value,
            agent_id=agent_id,
            created_at=time.time(),
            expires_at=time.time() + ttl,
            access_count=0
        )
        
        self.store[key] = entry
        self.logger.debug(f"Stored {key} for agent {agent_id}")
        
        return True
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from hot memory"""
        entry = self.store.get(key)
        
        if not entry:
            return None
        
        # Check expiration
        if time.time() > entry.expires_at:
            del self.store[key]
            return None
        
        # Update access count
        entry.access_count += 1
        
        return entry.value
    
    async def retrieve_for_agent(
        self,
        agent_id: str,
        pattern: Optional[str] = None
    ) -> List[Dict]:
        """Retrieve all entries for an agent"""
        results = []
        
        for key, entry in self.store.items():
            if entry.agent_id == agent_id:
                if pattern is None or pattern in key:
                    if time.time() <= entry.expires_at:
                        results.append({
                            "key": key,
                            "value": entry.value,
                            "created_at": entry.created_at,
                            "access_count": entry.access_count
                        })
        
        return results
    
    async def delete(self, key: str) -> bool:
        """Delete entry from hot memory"""
        if key in self.store:
            del self.store[key]
            return True
        return False
    
    async def prune_expired(self) -> int:
        """Remove expired entries"""
        now = time.time()
        expired = [k for k, v in self.store.items() if now > v.expires_at]
        
        for key in expired:
            del self.store[key]
        
        if expired:
            self.logger.info(f"Pruned {len(expired)} expired entries")
        
        return len(expired)
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        total_size = sum(len(str(v.value)) for v in self.store.values())
        
        return {
            "entries": len(self.store),
            "size_bytes": total_size,
            "size_mb": total_size / (1024 * 1024),
            "max_mb": self.MAX_SIZE_MB
        }
