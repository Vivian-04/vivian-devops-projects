"""Unit tests for the API with Redis mocked."""
import sys
import os
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client_and_redis():
    """Create a test client with a FRESH Redis mock per test."""
    import main
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    mock_redis.lpush.return_value = 1
    mock_redis.hset.return_value = 1
    mock_redis.hget.return_value = None
    with patch.object(main, "r", mock_redis):
        yield TestClient(main.app), mock_redis


def test_health_endpoint_returns_200(client_and_redis):
    """Health check returns 200 when Redis is reachable."""
    test_client, _ = client_and_redis
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_job_returns_job_id(client_and_redis):
    """Creating a job returns a valid job_id and queued status."""
    test_client, _ = client_and_redis
    response = test_client.post("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    assert len(data["job_id"]) > 0


def test_get_missing_job_returns_404(client_and_redis):
    """Getting a non-existent job returns HTTP 404."""
    test_client, mock_redis = client_and_redis
    mock_redis.hget.return_value = None
    response = test_client.get("/jobs/nonexistent-id")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_get_existing_job_returns_status(client_and_redis):
    """Getting an existing job returns its status."""
    test_client, mock_redis = client_and_redis
    mock_redis.hget.return_value = "completed"
    response = test_client.get("/jobs/abc-123")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "abc-123"
    assert data["status"] == "completed"


def test_create_job_generates_unique_ids(client_and_redis):
    """Each job submission creates a unique job_id."""
    test_client, _ = client_and_redis
    response1 = test_client.post("/jobs")
    response2 = test_client.post("/jobs")
    assert response1.json()["job_id"] != response2.json()["job_id"]
