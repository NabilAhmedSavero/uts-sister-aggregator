import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app, aggregator
import os
import uuid

TEST_DB_PATH = "data/test_events.db"

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    aggregator.db_path = TEST_DB_PATH
    
   
    if aggregator.conn:
        aggregator.close()

   
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
   
    aggregator.initialize()

    yield

    
    aggregator.close()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest.mark.asyncio
async def test_deduplication_and_stats():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        event_id = str(uuid.uuid4())
        unique_event = {
            "topic": "testing", 
            "event_id": event_id, 
            "source": "pytest", 
            "timestamp": "2025-01-01T00:00:00Z", 
            "payload": {"test": "dedup"}
        }
        
        await ac.post("/publish", json=[unique_event])
        await ac.post("/publish", json=[unique_event])

        stats_res = await ac.get("/stats")
        stats = stats_res.json()
        
        assert stats["received"] == 2
        assert stats["unique_processed"] == 1
        assert stats["duplicate_dropped"] == 1

@pytest.mark.asyncio
async def test_get_events_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        event1 = {"topic": "invoices", "event_id": "inv-001", "source": "pytest", "timestamp": "2025-01-01T01:00:00Z", "payload": {}}
        
        await ac.post("/publish", json=[event1])
        
        res = await ac.get("/events?topic=invoices")
        data = res.json()
        
        assert len(data) == 1
        assert data[0]["event_id"] == "inv-001"
        
        res_empty = await ac.get("/events?topic=nonexistent")
        assert res_empty.json() == []

@pytest.mark.asyncio
async def test_schema_validation_error():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        invalid_event = {
            "event_id": "invalid-001", 
            "source": "pytest", 
            "timestamp": "2025-01-01T00:00:00Z", 
            "payload": {}
        }
        response = await ac.post("/publish", json=[invalid_event])
        
        assert response.status_code == 422