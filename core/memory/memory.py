import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, select
from sqlalchemy.orm import declarative_base
import chromadb

logger = logging.getLogger("ord.memory")
Base = declarative_base()


class AgentScore(Base):
    __tablename__ = "agent_scores"
    id = Column(Integer, primary_key=True)
    agent_name = Column(String, index=True)
    task_type = Column(String)
    intelligence_score = Column(Float, default=50.0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TaskLog(Base):
    __tablename__ = "task_logs"
    id = Column(Integer, primary_key=True)
    project_id = Column(String, index=True)
    agent_name = Column(String)
    action = Column(String)
    metadata = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MemorySystem:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///ord_working.db")
        self.chroma_path = os.getenv("CHROMA_PATH", "./memory/chroma")
        self.genome_path = os.getenv("GENOME_PATH", "./memory/genome.json")
        self._redis: Optional[redis.Redis] = None
        self._session_factory = None
        self._chroma = None
        self._genome: Dict[str, Any] = {}

    async def initialize(self):
        # Hot: Redis
        self._redis = redis.from_url(self.redis_url, decode_responses=True)
        await self._redis.ping()
        logger.info("✅ Hot Memory (Redis) connected")
        
        # Working: SQLite/PostgreSQL
        engine = create_async_engine(self.db_url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self._session_factory = async_sessionmaker(engine, expire_on_commit=False)
        logger.info("✅ Working Memory (SQLAlchemy) initialized")
        
        # Cold: ChromaDB
        self._chroma = chromadb.PersistentClient(path=self.chroma_path)
        for col in ["projects", "designs", "financials", "genome"]:
            self._chroma.get_or_create_collection(col)
        logger.info("✅ Cold Memory (ChromaDB) initialized")
        
        # Genome: JSON
        if os.path.exists(self.genome_path):
            with open(self.genome_path, "r") as f:
                self._genome = json.load(f)
        else:
            os.makedirs(os.path.dirname(self.genome_path), exist_ok=True)
            self._genome = {"company_dna": {"tone": "sweet_loving", "design": "shadcn/ui + #FD651E"}, "learnings": []}
            self._save_genome()
        logger.info("✅ Genome Memory initialized")

    # Hot: Redis
    async def store_hot(self, key: str, value: Any, ttl: int = 3600):
        await self._redis.setex(key, ttl, json.dumps(value))

    async def get_hot(self, key: str) -> Optional[Any]:
        val = await self._redis.get(key)
        return json.loads(val) if val else None

    # Working: SQLAlchemy
    async def log_task(self, project_id: str, agent_name: str, action: str, metadata: Dict = None):
        async with self._session_factory() as session:
            session.add(TaskLog(project_id=project_id, agent_name=agent_name, action=action, metadata=json.dumps(metadata or {})))
            await session.commit()

    async def update_agent_score(self, agent_name: str, task_type: str, score_delta: float):
        async with self._session_factory() as session:
            stmt = select(AgentScore).where(AgentScore.agent_name == agent_name).order_by(AgentScore.timestamp.desc()).limit(1)
            current = (await session.execute(stmt)).scalar_one_or_none()
            new_score = max(0, min(100, (current.intelligence_score if current else 50) + score_delta))
            session.add(AgentScore(agent_name=agent_name, task_type=task_type, intelligence_score=new_score))
            await session.commit()
            return new_score

    # Cold: ChromaDB
    async def add_rag(self, collection: str, ids: List[str], documents: List[str], metadatas: List[Dict] = None):
        col = self._chroma.get_collection(collection)
        await asyncio.to_thread(col.upsert, ids=ids, documents=documents, metadatas=metadatas)

    async def search_rag(self, collection: str, query: str, n_results: int = 5) -> List[str]:
        col = self._chroma.get_collection(collection)
        results = await asyncio.to_thread(col.query, query_texts=[query], n_results=n_results)
        return results.get("documents", [[]])[0]

    # Genome: JSON
    def update_genome(self, key: str, value: Any, append: bool = False):
        if append and isinstance(self._genome.get("learnings"), list):
            self._genome["learnings"].append({key: value, "timestamp": datetime.now(timezone.utc).isoformat()})
        else:
            self._genome["company_dna"][key] = value
        self._save_genome()

    def _save_genome(self):
        with open(self.genome_path, "w") as f:
            json.dump(self._genome, f, indent=2)


memory = MemorySystem()