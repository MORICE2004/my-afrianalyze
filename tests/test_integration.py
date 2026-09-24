import pytest
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from apps.api.main import app

from httpx import ASGITransport

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_celery_task():
    with patch("apps.api.main.run_research_task") as mock_task:
        mock_result = MagicMock()
        mock_result.id = "mock-task-id-123"
        mock_result.state = "STARTED"
        mock_result.result = "mock_research_run_id"
        mock_task.delay.return_value = mock_result
        
        with patch("apps.api.main.AsyncResult") as mock_async_result:
            mock_async_result.return_value = mock_result
            yield

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
