import json
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ColdMemoryEntry:
    """Cold memory entry with embeddings"""
    key: str
    value: Any
    text_content: str  # For embedding
    embedding: Optional[List[float]]
    metadata: Dict
    created_at: float
    relevance_score: float


class ColdMemory:
    """
    Cold Memory Layer (ChromaDB simulation)
    
    Permanent archive with semantic search capabilities.
    Stores Company DNA, historical projects, and learnings.
    """
    
    def __init__(self, storage_path: str = "memory/cold_memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.entries: Dict[str, ColdMemoryEntry] = {}
        self._load_entries()
        
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        import logging
        return logging.getLogger("Ord.Memory.Cold")
    
    def _load_entries(self):
        """Load entries from disk"""
        index_file = self.storage_path / "index.json"
        if index_file.exists():
            with open(index_file, 'r') as f:
                data = json.load(f)
                for key, entry_data in data.items():
                    self.entries[key] = ColdMemoryEntry(**entry_data)
    
    def _save_entries(self):
        """Save entries to disk"""
        index_file = self.storage_path / "index.json"
        with open(index_file, 'w') as f:
            data = {
                k: {
                    "key": v.key,
                    "value": v.value,
                    "text_content": v.text_content,
                    "embedding": v.embedding,
                    "metadata": v.metadata,
                    "created_at": v.created_at,
                    "relevance_score": v.relevance_score
                }
                for k, v in self.entries.items()
            }
            json.dump(data, f)
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate simple embedding (simulation).
        In production: use sentence-transformers or OpenAI embeddings.
        """
        # Simple bag-of-words embedding simulation
        words = text.lower().split()
        # Create a simple 128-dim embedding
        embedding = [0.0] * 128
        
        for i, word in enumerate(words[:128]):
            # Use hash of word for deterministic embedding
            hash_val = hash(word) % 1000 / 1000.0
            embedding[i] = hash_val
        
        # Normalize
        import math
        magnitude = math.sqrt(sum(x**2 for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        dot = sum(x * y for x, y in zip(a, b))
        return dot  # Already normalized
    
    async def store(
        self,
        key: str,
        value: Any,
        text_content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Store value in cold memory with embedding"""
        embedding = self._generate_embedding(text_content)
        
        entry = ColdMemoryEntry(
            key=key,
            value=value,
            text_content=text_content,
            embedding=embedding,
            metadata=metadata or {},
            created_at=time.time(),
            relevance_score=0.5  # Default
        )
        
        self.entries[key] = entry
        self._save_entries()
        
        self.logger.debug(f"Archived {key}")
        return True
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """Search cold memory using semantic similarity"""
        query_embedding = self._generate_embedding(query)
        
        # Calculate similarities
        scored = []
        for key, entry in self.entries.items():
            if entry.embedding:
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                scored.append((key, similarity, entry))
        
        # Sort by similarity
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results
        results = []
        for key, score, entry in scored[:limit]:
            results.append({
                "key": key,
                "value": entry.value,
                "similarity": score,
                "metadata": entry.metadata,
                "created_at": entry.created_at
            })
        
        return results
    
    async def update_relevance(self, key: str, new_score: float) -> bool:
        """Update relevance score for an entry"""
        if key in self.entries:
            self.entries[key].relevance_score = new_score
            self._save_entries()
            return True
        return False
    
    async def archive_low_relevance(self, threshold: float = 0.3) -> int:
        """Remove or flag low-relevance entries"""
        low_relevance = [
            k for k, v in self.entries.items()
            if v.relevance_score < threshold
        ]
        
        # In production: might move to even colder storage
        # For now, just log
        if low_relevance:
            self.logger.info(f"Found {len(low_relevance)} low-relevance entries")
        
        return len(low_relevance)
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        total_size = sum(len(str(v.value)) for v in self.entries.values())
        
        return {
            "entries": len(self.entries),
            "size_bytes": total_size,
            "size_mb": total_size / (1024 * 1024)
        }
