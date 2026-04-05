import json
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GenomeEntry:
    """Single entry in the Company Genome"""
    entry_id: str
    entry_type: str  # project, reflection, decision, learning, hiring
    agent_id: str
    content: Dict
    timestamp: float
    tags: List[str]
    importance: float  # 0-1, used for prioritization


@dataclass
class ProjectDNA:
    """Project-specific DNA"""
    project_id: str
    name: str
    what_was_built: str
    why_decisions_made: str
    what_was_learned: str
    how_it_performed: Dict
    created_at: float


class CompanyGenome:
    """
    Company Genome - Living Knowledge System
    
    Unified memory system: Vector + Graph + Relational
    Every project, decision, and reflection updates the genome.
    
    Agents query like a second brain: "What did we learn about auth systems?"
    New projects start with accumulated wisdom.
    """
    
    def __init__(self, storage_path: str = "memory/genome"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.entries: List[GenomeEntry] = []
        self.project_dna: Dict[str, ProjectDNA] = {}
        
        self._load_genome()
        
        self.logger = self._setup_logging()
        self.logger.info("🧬 Company Genome initialized")
    
    def _setup_logging(self):
        import logging
        return logging.getLogger("Ord.Genome")
    
    def _load_genome(self):
        """Load genome from disk"""
        genome_file = self.storage_path / "genome.json"
        if genome_file.exists():
            with open(genome_file, 'r') as f:
                data = json.load(f)
                for entry_data in data.get("entries", []):
                    self.entries.append(GenomeEntry(**entry_data))
                for proj_id, proj_data in data.get("projects", {}).items():
                    self.project_dna[proj_id] = ProjectDNA(**proj_data)
    
    def _save_genome(self):
        """Save genome to disk"""
        genome_file = self.storage_path / "genome.json"
        with open(genome_file, 'w') as f:
            data = {
                "entries": [
                    {
                        "entry_id": e.entry_id,
                        "entry_type": e.entry_type,
                        "agent_id": e.agent_id,
                        "content": e.content,
                        "timestamp": e.timestamp,
                        "tags": e.tags,
                        "importance": e.importance
                    }
                    for e in self.entries
                ],
                "projects": {
                    k: {
                        "project_id": v.project_id,
                        "name": v.name,
                        "what_was_built": v.what_was_built,
                        "why_decisions_made": v.why_decisions_made,
                        "what_was_learned": v.what_was_learned,
                        "how_it_performed": v.how_it_performed,
                        "created_at": v.created_at
                    }
                    for k, v in self.project_dna.items()
                }
            }
            json.dump(data, f, indent=2)
    
    async def store_entry(
        self,
        entry_type: str,
        agent_id: str,
        content: Dict,
        tags: Optional[List[str]] = None,
        importance: float = 0.5
    ) -> str:
        """Store entry in the genome"""
        entry_id = f"genome-{int(time.time())}-{len(self.entries)}"
        
        entry = GenomeEntry(
            entry_id=entry_id,
            entry_type=entry_type,
            agent_id=agent_id,
            content=content,
            timestamp=time.time(),
            tags=tags or [],
            importance=importance
        )
        
        self.entries.append(entry)
        self._save_genome()
        
        self.logger.info(f"🧬 Genome entry added: {entry_type} by {agent_id}")
        
        return entry_id
    
    async def store_project_dna(
        self,
        project_id: str,
        name: str,
        what_was_built: str,
        why_decisions_made: str,
        what_was_learned: str,
        how_it_performed: Dict
    ) -> str:
        """Store project DNA for future reference"""
        dna = ProjectDNA(
            project_id=project_id,
            name=name,
            what_was_built=what_was_built,
            why_decisions_made=why_decisions_made,
            what_was_learned=what_was_learned,
            how_it_performed=how_it_performed,
            created_at=time.time()
        )
        
        self.project_dna[project_id] = dna
        self._save_genome()
        
        self.logger.info(f"🧬 Project DNA stored: {name}")
        
        return project_id
    
    async def query(
        self,
        query: str,
        entry_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Query the genome like a second brain.
        
        Example: "What did we learn about auth systems?"
        """
        query_lower = query.lower()
        
        # Simple keyword matching (in production: use embeddings)
        results = []
        for entry in self.entries:
            if entry_type and entry.entry_type != entry_type:
                continue
            
            # Calculate relevance
            relevance = 0
            content_str = json.dumps(entry.content).lower()
            
            for word in query_lower.split():
                if word in content_str:
                    relevance += 1
                if word in entry.tags:
                    relevance += 2
            
            if relevance > 0:
                results.append({
                    "entry_id": entry.entry_id,
                    "entry_type": entry.entry_type,
                    "agent_id": entry.agent_id,
                    "content": entry.content,
                    "timestamp": entry.timestamp,
                    "relevance": relevance,
                    "importance": entry.importance
                })
        
        # Sort by relevance and importance
        results.sort(key=lambda x: (x["relevance"], x["importance"]), reverse=True)
        
        return results[:limit]
    
    async def get_project_dna(self, project_id: str) -> Optional[Dict]:
        """Get DNA for a specific project"""
        dna = self.project_dna.get(project_id)
        if dna:
            return {
                "project_id": dna.project_id,
                "name": dna.name,
                "what_was_built": dna.what_was_built,
                "why_decisions_made": dna.why_decisions_made,
                "what_was_learned": dna.what_was_learned,
                "how_it_performed": dna.how_it_performed
            }
        return None
    
    async def get_learnings(self, topic: Optional[str] = None) -> List[Dict]:
        """Get accumulated learnings on a topic"""
        learnings = []
        
        for entry in self.entries:
            if entry.entry_type in ["reflection", "learning"]:
                if topic is None or topic in json.dumps(entry.content).lower():
                    learnings.append({
                        "agent": entry.agent_id,
                        "learning": entry.content.get("learning", ""),
                        "timestamp": entry.timestamp,
                        "tags": entry.tags
                    })
        
        return learnings
    
    async def inherit_wisdom(self, project_type: str) -> Dict:
        """
        Inherit wisdom for new project.
        New projects start with accumulated knowledge.
        """
        # Query relevant past projects
        relevant_projects = []
        for dna in self.project_dna.values():
            if project_type.lower() in dna.what_was_built.lower():
                relevant_projects.append({
                    "name": dna.name,
                    "what_was_built": dna.what_was_built,
                    "what_was_learned": dna.what_was_learned,
                    "how_it_performed": dna.how_it_performed
                })
        
        # Get general learnings
        general_learnings = await self.get_learnings(project_type)
        
        return {
            "relevant_projects": relevant_projects[:3],
            "general_learnings": general_learnings[:5],
            "recommendations": [
                "Consider patterns from similar past projects",
                "Apply learnings from previous iterations"
            ]
        }
    
    def get_stats(self) -> Dict:
        """Get genome statistics"""
        entry_types = {}
        for entry in self.entries:
            entry_types[entry.entry_type] = entry_types.get(entry.entry_type, 0) + 1
        
        return {
            "total_entries": len(self.entries),
            "projects_archived": len(self.project_dna),
            "entry_types": entry_types,
            "size_mb": len(json.dumps(self.entries)) / (1024 * 1024)
        }
