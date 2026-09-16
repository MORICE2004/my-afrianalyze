import pytest
import httpx
from apps.api.main import app

from httpx import ASGITransport

@pytest.mark.asyncio
async def test_health_check():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_start_research():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"ticker": "EQTY", "exchange": "NSE"}
        response = await client.post("/api/v1/research/start", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "research_run_id" in data
        assert data["status"] == "started"

@pytest.mark.asyncio
async def test_get_research_status():
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"ticker": "KCB", "exchange": "NSE"}
        start_response = await client.post("/api/v1/research/start", json=payload)
        run_id = start_response.json()["research_run_id"]
        
        status_response = await client.get(f"/api/v1/research/{run_id}/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["research_run_id"] == run_id
        assert status_data["status"] == "in_progress"
        assert status_data["message"] == "Gathering data..."
