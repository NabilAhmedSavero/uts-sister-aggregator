from fastapi import FastAPI
from typing import List
import uuid
import datetime
from .aggregator import Aggregator, Event

app = FastAPI(title="Log Aggregator")
aggregator = Aggregator(db_path="data/events.db")

@app.on_event("startup")
async def startup(): aggregator.initialize()

@app.on_event("shutdown")
def shutdown(): aggregator.close()

@app.post("/publish")
async def publish_events(events: List[Event]):
    for event in events:
        await aggregator.process_event(event)
    return {"status": "events received"}

@app.get("/events")
def get_events(topic: str): return aggregator.get_events_by_topic(topic)

@app.get("/stats")
def get_stats(): return aggregator.get_stats()