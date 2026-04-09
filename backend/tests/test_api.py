"""
Integration tests for all API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self):
        """Verify health check endpoint returns 200 OK."""
        client = TestClient(app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_returns_correct_body(self):
        """Verify health check response body."""
        client = TestClient(app)
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "propvision-api"
        assert "version" in data


class TestPropertiesEndpoint:
    """Tests for property CRUD endpoints."""

    def test_list_properties_without_auth_returns_401(self):
        """Verify listing properties without API key returns 401."""
        client = TestClient(app)
        response = client.get("/api/v1/properties")
        assert response.status_code == 401

    def test_create_property_without_auth_returns_401(self):
        """Verify creating property without API key returns 401."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/properties",
            json={
                "title": "Test Property",
                "price": 50000,
                "latitude": 41.3,
                "longitude": 69.3,
            },
        )
        assert response.status_code == 401


class TestSearchEndpoint:
    """Tests for AI search endpoint."""

    def test_search_without_auth_returns_401(self):
        """Verify search without API key returns 401."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/search",
            json={"query": "2 rooms near metro"},
        )
        assert response.status_code == 401


class TestComfortEndpoint:
    """Tests for comfort analytics endpoint."""

    def test_comfort_without_auth_returns_401(self):
        """Verify comfort scores without API key returns 401."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/comfort/550e8400-e29b-41d4-a716-446655440000"
        )
        assert response.status_code == 401


class TestReconstructionEndpoint:
    """Tests for 3D reconstruction endpoint."""

    def test_status_without_auth_returns_401(self):
        """Verify reconstruction status without API key returns 401."""
        client = TestClient(app)
        response = client.get(
            "/api/v1/3d/550e8400-e29b-41d4-a716-446655440000/status"
        )
        assert response.status_code == 401


class TestAnalyticsEndpoint:
    """Tests for analytics endpoint."""

    def test_dashboard_without_auth_returns_401(self):
        """Verify dashboard without API key returns 401."""
        client = TestClient(app)
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 401
