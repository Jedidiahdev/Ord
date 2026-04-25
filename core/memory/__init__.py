import json
import logging
import os
import sqlite3
import time
import importlib
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

CHROMADB_AVAILABLE = "chromadb" in sys.modules or importlib.util.find_spec("chromadb") is not None
chromadb = importlib.import_module("chromadb") if CHROMADB_AVAILABLE else None

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover - optional runtime dependency
    redis = None

from core.memory.cold_memory import ColdMemory
from core.memory.genome import CompanyGenome
from core.memory.hot_memory import HotMemory
from core.memory.working_memory import WorkingMemory

logger = logging.getLogger("ord.core.memory")


class LocalChromaCollection:
    """Small local fallback when chromadb isn't installed."""

    def __init__(self) -> None:
        self._docs: Dict[str, str] = {}
        self._metadatas: Dict[str, Dict[str, Any]] = {}

    def upsert(self, ids: List[str], documents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        for idx, doc_id in enumerate(ids):
            self._docs[doc_id] = documents[idx]
            if metadatas and idx < len(metadatas):
                self._metadatas[doc_id] = metadatas[idx]

    def query(self, query_texts: List[str], n_results: int = 5) -> Dict[str, List[List[str]]]:
        query = (query_texts[0] if query_texts else "").lower()
        ranked: List[tuple[float, str]] = []
        for doc_id, doc in self._docs.items():
            hay = doc.lower()
            score = 1.0 if query in hay else 0.0
            if score > 0:
                ranked.append((score, doc_id))

        if not ranked:
            ranked = [(0.0, doc_id) for doc_id in self._docs.keys()]

        ranked.sort(reverse=True)
        selected_ids = [doc_id for _, doc_id in ranked[:n_results]]
        return {"documents": [[self._docs[doc_id] for doc_id in selected_ids]]}


class LocalChromaClient:
    def __init__(self) -> None:
        self._collections: Dict[str, LocalChromaCollection] = {}

    def get_or_create_collection(self, name: str) -> LocalChromaCollection:
        if name not in self._collections:
            self._collections[name] = LocalChromaCollection()
        return self._collections[name]


@dataclass
class GenomeGraph:
    """Simple adjacency graph for durable company DNA relationships."""

    edges: Dict[str, List[str]] = field(default_factory=dict)

    def link(self, source: str, target: str) -> None:
        self.edges.setdefault(source, [])
        if target not in self.edges[source]:
            self.edges[source].append(target)

    def neighbors(self, node: str) -> List[str]:
        return self.edges.get(node, [])


class FourTierMemorySystem:
    """
    4-tier memory:
    - Hot (Redis) : active tasks/conversations
    - Working (SQLite/Postgres-like local DB) : rolling 30-day context
    - Cold (ChromaDB) : semantic search corpus
    - Genome (JSON + graph) : permanent company DNA and learnings
    """

    def __init__(self) -> None:
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.use_redis = os.getenv("USE_REDIS", "false").lower() == "true"
        self.working_db_path = Path(os.getenv("WORKING_MEMORY_DB", "memory/working_memory.sqlite3"))
        self.working_db_path.parent.mkdir(parents=True, exist_ok=True)

        self.chroma_path = os.getenv("CHROMA_PATH", "memory/chroma")
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)

        self.genome_dir = Path(os.getenv("GENOME_DIR", "memory/genome"))
        self.genome_dir.mkdir(parents=True, exist_ok=True)
        self.genome_json_path = self.genome_dir / "company_genome.json"
        self.genome_graph_path = self.genome_dir / "company_genome_graph.json"

        self.hot_fallback = HotMemory()
        self.working = WorkingMemory(str(self.working_db_path))
        self.cold = ColdMemory("memory/cold_memory")
        self.company_genome = CompanyGenome(str(self.genome_dir))

        self._redis_client = None
        if chromadb is not None:
            self._chroma = chromadb.PersistentClient(path=self.chroma_path)
        else:
            logger.warning("chromadb not installed; using LocalChromaClient fallback")
            self._chroma = LocalChromaClient()
        self._chroma_collections: Dict[str, Any] = {}
        self._genome_graph = GenomeGraph()

        self._initialize_working_schema()
        self._load_graph()

    # ----- setup -----
    def _initialize_working_schema(self) -> None:
        conn = sqlite3.connect(str(self.working_db_path))
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                agent_name TEXT,
                action TEXT,
                metadata_json TEXT,
                timestamp REAL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                task_type TEXT,
                intelligence_score REAL,
                timestamp REAL
            )
            """
        )
        conn.commit()
        conn.close()

    def _load_graph(self) -> None:
        if self.genome_graph_path.exists():
            self._genome_graph.edges = json.loads(self.genome_graph_path.read_text())

    def _save_graph(self) -> None:
        self.genome_graph_path.write_text(json.dumps(self._genome_graph.edges, indent=2))

    async def initialize(self) -> None:
        if self.use_redis and redis is not None:
            try:
                self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
                await self._redis_client.ping()
                logger.info("Hot memory connected to redis")
            except Exception as exc:
                logger.warning("Redis unavailable, using in-process hot memory: %s", exc)
                self._redis_client = None

    # ----- hot tier -----
    async def store_hot(self, key: str, value: Any, ttl: int = 3600) -> None:
        if self._redis_client is not None:
            await self._redis_client.setex(key, ttl, json.dumps(value))
            return
        await self.hot_fallback.store(key, value, agent_id="system", ttl=ttl)

    async def get_hot(self, key: str) -> Optional[Any]:
        if self._redis_client is not None:
            raw = await self._redis_client.get(key)
            return json.loads(raw) if raw else None
        return await self.hot_fallback.retrieve(key)

    # ----- working tier -----
    async def log_task(self, project_id: str, agent_name: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        conn = sqlite3.connect(str(self.working_db_path))
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO task_logs (project_id, agent_name, action, metadata_json, timestamp) VALUES (?, ?, ?, ?, ?)",
            (project_id, agent_name, action, json.dumps(metadata or {}), time.time()),
        )
        conn.commit()
        conn.close()

    async def update_agent_score(self, agent_name: str, task_type: str, score_delta: float) -> float:
        conn = sqlite3.connect(str(self.working_db_path))
        cur = conn.cursor()
        cur.execute(
            "SELECT intelligence_score FROM agent_scores WHERE agent_name = ? ORDER BY timestamp DESC LIMIT 1",
            (agent_name,),
        )
        row = cur.fetchone()
        baseline = row[0] if row else 50.0
        new_score = max(0.0, min(100.0, baseline + score_delta))
        cur.execute(
            "INSERT INTO agent_scores (agent_name, task_type, intelligence_score, timestamp) VALUES (?, ?, ?, ?)",
            (agent_name, task_type, new_score, time.time()),
        )
        conn.commit()
        conn.close()
        return new_score

    async def prune_working_context(self, max_age_days: int = 30) -> int:
        cutoff = time.time() - (max_age_days * 86400)
        conn = sqlite3.connect(str(self.working_db_path))
        cur = conn.cursor()
        cur.execute("DELETE FROM task_logs WHERE timestamp < ?", (cutoff,))
        deleted = cur.rowcount
        conn.commit()
        conn.close()
        return deleted

    # ----- cold tier (Chroma) -----
    def _collection(self, name: str):
        if name not in self._chroma_collections:
            self._chroma_collections[name] = self._chroma.get_or_create_collection(name)
        return self._chroma_collections[name]

    async def add_rag(self, collection: str, ids: List[str], documents: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        col = self._collection(collection)
        col.upsert(ids=ids, documents=documents, metadatas=metadatas)

    async def search_rag(self, collection: str, query: str, n_results: int = 5) -> List[str]:
        col = self._collection(collection)
        result = col.query(query_texts=[query], n_results=n_results)
        return result.get("documents", [[]])[0]

    # ----- genome tier -----
    async def update_genome(self, key: str, value: Any, links_to: Optional[List[str]] = None, append_learning: bool = True) -> None:
        snapshot = {"key": key, "value": value, "timestamp": time.time()}

        existing = {"company_dna": {}, "learnings": []}
        if self.genome_json_path.exists():
            existing = json.loads(self.genome_json_path.read_text())

        existing.setdefault("company_dna", {})[key] = value
        if append_learning:
            existing.setdefault("learnings", []).append(snapshot)

        self.genome_json_path.write_text(json.dumps(existing, indent=2))

        for node in links_to or []:
            self._genome_graph.link(key, node)
        self._save_graph()

    async def query_genome(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        payload = {"company_dna": {}, "learnings": []}
        if self.genome_json_path.exists():
            payload = json.loads(self.genome_json_path.read_text())

        results: List[Dict[str, Any]] = []
        for key, value in payload.get("company_dna", {}).items():
            hay = f"{key} {json.dumps(value)}".lower()
            if query_lower in hay:
                results.append({"type": "dna", "key": key, "value": value, "linked_to": self._genome_graph.neighbors(key)})

        for learning in payload.get("learnings", []):
            hay = json.dumps(learning).lower()
            if query_lower in hay:
                results.append({"type": "learning", **learning})

        return results[:limit]

    # ----- compatibility facade -----
    async def store(self, key: str, value: Any, tier: str = "working", agent_id: str = "system") -> bool:
        if tier == "hot":
            await self.store_hot(key, value)
            return True
        if tier == "working":
            await self.working.store(key, value, agent_id)
            return True
        if tier == "cold":
            await self.add_rag("default", [key], [json.dumps(value)])
            return True
        if tier == "genome":
            await self.update_genome(key, value)
            return True
        return False

    async def retrieve(self, key: str, tier: Optional[str] = None) -> Optional[Any]:
        if tier == "hot":
            return await self.get_hot(key)
        if tier == "working":
            return await self.working.retrieve(key)
        if tier == "cold":
            found = await self.search_rag("default", key, 1)
            return found[0] if found else None

        hot = await self.get_hot(key)
        if hot is not None:
            return hot
        return await self.working.retrieve(key)

    async def semantic_search(self, query: str, context: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        docs = await self.search_rag("default", query, limit)
        return [{"document": d} for d in docs]

    async def store_genome_entry(self, entry_type: str, agent_id: str, content: Dict[str, Any], tags: Optional[List[str]] = None) -> str:
        key = f"{entry_type}:{agent_id}:{int(time.time())}"
        await self.update_genome(key, {"content": content, "tags": tags or []})
        return key

    async def inherit_wisdom(self, project_type: str) -> Dict[str, Any]:
        return {"project_type": project_type, "signals": await self.query_genome(project_type)}

    def get_stats(self) -> Dict[str, Any]:
        return {
            "hot": self.hot_fallback.get_stats(),
            "working": self.working.get_stats(),
            "cold": self.cold.get_stats(),
            "genome": self.company_genome.get_stats(),
        }


MemoryManager = FourTierMemorySystem
memory = FourTierMemorySystem()
