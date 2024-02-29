import pytest
from app.main import app as router

from fastapi.testclient import TestClient


def test_healthcheck():
    with TestClient(router) as client:
        response = client.get("/v1/health")
        assert response.status_code == 200
        assert response.json() == dict(status="ok")
