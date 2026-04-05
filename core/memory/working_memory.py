"""
Ord v3.0 - Working Memory (SQLite Layer)
Structured storage for medium-term context.

Characteristics:
- Duration: 30 days
- Format: Compressed summaries
- Use: Project context, agent relationships
"""

import json
import sqlite3
import time
import zlib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WorkingMemoryEntry:
    """Working memory entry"""
    key: str
    value: Any
    agent_id: str
    created_at: float
    compressed: bool


class WorkingMemory:
    """
    Working Memory Layer (SQLite)
    
    Structured storage with compression for medium-term context.
    Stores summaries, project state, and agent relationships.
    """
    
    DEFAULT_TTL_DAYS = 30
    COMPRESSION_THRESHOLD = 1024  # Compress if > 1KB
    
    def __init__(self, db_path: str = "memory/working_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        import logging
        return logging.getLogger("Ord.Memory.Working")
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_entries (
                key TEXT PRIMARY KEY,
                agent_id TEXT,
                value BLOB,
                created_at REAL,
                accessed_at REAL,
                access_count INTEGER DEFAULT 0,
                compressed INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_agent ON memory_entries(agent_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created ON memory_entries(created_at)
        ''')
        
        conn.commit()
        conn.close()
    
    def _compress(self, data: str) -> bytes:
        """Compress data using zlib"""
        return zlib.compress(data.encode('utf-8'))
    
    def _decompress(self, data: bytes) -> str:
        """Decompress data"""
        return zlib.decompress(data).decode('utf-8')
    
    async def store(
        self,
        key: str,
        value: Any,
        agent_id: str
    ) -> bool:
        """Store value in working memory"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Serialize value
        json_value = json.dumps(value)
        
        # Compress if large
        compressed = len(json_value) > self.COMPRESSION_THRESHOLD
        if compressed:
            stored_value = self._compress(json_value)
        else:
            stored_value = json_value.encode('utf-8')
        
        now = time.time()
        
        cursor.execute('''
            INSERT OR REPLACE INTO memory_entries
            (key, agent_id, value, created_at, accessed_at, compressed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (key, agent_id, stored_value, now, now, int(compressed)))
        
        conn.commit()
        conn.close()
        
        self.logger.debug(f"Stored {key} for agent {agent_id}")
        return True
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value from working memory"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT value, compressed FROM memory_entries WHERE key = ?
        ''', (key,))
        
        row = cursor.fetchone()
        
        if row:
            value_bytes, compressed = row
            
            # Update access stats
            cursor.execute('''
                UPDATE memory_entries 
                SET accessed_at = ?, access_count = access_count + 1
                WHERE key = ?
            ''', (time.time(), key))
            
            conn.commit()
            conn.close()
            
            # Decompress if needed
            if compressed:
                json_value = self._decompress(value_bytes)
            else:
                json_value = value_bytes.decode('utf-8')
            
            return json.loads(json_value)
        
        conn.close()
        return None
    
    async def retrieve_for_agent(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """Retrieve entries for an agent"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, value, created_at, compressed
            FROM memory_entries
            WHERE agent_id = ?
            ORDER BY accessed_at DESC
            LIMIT ?
        ''', (agent_id, limit))
        
        results = []
        for row in cursor.fetchall():
            key, value_bytes, created_at, compressed = row
            
            try:
                if compressed:
                    json_value = self._decompress(value_bytes)
                else:
                    json_value = value_bytes.decode('utf-8')
                
                results.append({
                    "key": key,
                    "value": json.loads(json_value),
                    "created_at": created_at
                })
            except Exception as e:
                self.logger.error(f"Error decoding {key}: {e}")
        
        conn.close()
        return results
    
    async def compress_tier(self, max_age_days: int = 30) -> int:
        """Compress older entries"""
        cutoff = time.time() - (max_age_days * 24 * 3600)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT key, value, compressed FROM memory_entries
            WHERE created_at < ? AND compressed = 0
        ''', (cutoff,))
        
        compressed_count = 0
        for row in cursor.fetchall():
            key, value_bytes, _ = row
            
            try:
                compressed = self._compress(value_bytes.decode('utf-8'))
                cursor.execute('''
                    UPDATE memory_entries SET value = ?, compressed = 1 WHERE key = ?
                ''', (compressed, key))
                compressed_count += 1
            except Exception as e:
                self.logger.error(f"Error compressing {key}: {e}")
        
        conn.commit()
        conn.close()
        
        if compressed_count:
            self.logger.info(f"Compressed {compressed_count} entries")
        
        return compressed_count
    
    async def prune_old(self, max_age_days: int = 30) -> int:
        """Remove entries older than max_age_days"""
        cutoff = time.time() - (max_age_days * 24 * 3600)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM memory_entries WHERE created_at < ?
        ''', (cutoff,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted:
            self.logger.info(f"Pruned {deleted} old entries")
        
        return deleted
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM memory_entries')
        count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(LENGTH(value)) FROM memory_entries')
        total_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "entries": count,
            "size_bytes": total_size,
            "size_mb": total_size / (1024 * 1024)
        }
