import pytest
from fastapi.testclient import TestClient


class TestAnalyticsRouter:
    def test_get_analytics_unauthorized(self, test_client: TestClient):
        response = test_client.get("/api/v1/analytics")
        assert response.status_code == 401

    def test_get_analytics_forbidden_non_admin(
        self, test_client: TestClient, auth_headers
    ):
        response = test_client.get("/api/v1/analytics", headers=auth_headers)
        assert response.status_code == 403

    def test_get_analytics_success(
        self, test_client: TestClient, admin_auth_headers, mock_admin_user
    ):
        response = test_client.get("/api/v1/analytics", headers=admin_auth_headers)
        assert response.status_code == 200
