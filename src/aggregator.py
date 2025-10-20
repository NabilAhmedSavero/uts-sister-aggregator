import sqlite3
import threading
import time
from pydantic import BaseModel
from typing import List, Dict, Any
import os

class Event(BaseModel):
    topic: str
    event_id: str
    timestamp: str
    source: str
    payload: Dict[str, Any]

class Aggregator:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._lock = threading.Lock()
        self.stats = {}

    def initialize(self):
        self.stats = {
            "received": 0,
            "unique_processed": 0,
            "duplicate_dropped": 0,
            "start_time": time.time()
        }
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_events (
                id INTEGER PRIMARY KEY,
                topic TEXT NOT NULL,
                event_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                payload TEXT NOT NULL,
                UNIQUE(topic, event_id)
            )
        """)
        self.conn.commit()

    async def process_event(self, event: Event):
        with self._lock:
            self.stats["received"] += 1
            try:
                self.cursor.execute(
                    "INSERT INTO processed_events (topic, event_id, timestamp, source, payload) VALUES (?, ?, ?, ?, ?)",
                    (event.topic, event.event_id, event.timestamp, event.source, str(event.payload))
                )
                self.conn.commit()
                self.stats["unique_processed"] += 1
                print(f"✅ Event unik diproses: ID {event.event_id}")
            except sqlite3.IntegrityError:
                self.stats["duplicate_dropped"] += 1
                print(f"❌ Event duplikat ditolak: ID {event.event_id}")

    def get_events_by_topic(self, topic: str) -> List[Dict]:
        with self._lock:
            self.cursor.execute("SELECT topic, event_id, timestamp, source, payload FROM processed_events WHERE topic = ?", (topic,))
            return [dict(zip([column[0] for column in self.cursor.description], row)) for row in self.cursor.fetchall()]

    def get_stats(self) -> Dict:
        with self._lock:
            self.cursor.execute("SELECT DISTINCT topic FROM processed_events")
            topics = [row[0] for row in self.cursor.fetchall()]
            
            current_stats = self.stats.copy()
            current_stats["topics"] = topics
            current_stats["uptime_seconds"] = round(time.time() - current_stats.get("start_time", 0))
            return current_stats

    def close(self):
        if self.conn:
            self.conn.close()

