import pytest
from fastapi.testclient import TestClient


class TestConfigsRouter:
    def test_get_configs_unauthorized(self, test_client: TestClient):
        response = test_client.get("/api/v1/configuration")
        assert response.status_code == 401

    def test_get_configs_forbidden_non_admin(
        self, test_client: TestClient, auth_headers
    ):
        response = test_client.get("/api/v1/configuration", headers=auth_headers)
        assert response.status_code == 403

    def test_get_configs_success(
        self, test_client: TestClient, admin_auth_headers, mock_admin_user, test_config
    ):
        response = test_client.get("/api/v1/configuration", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["matrix_cadence"] == "weekly"

    def test_update_config_success(
        self, test_client: TestClient, admin_auth_headers, mock_admin_user, test_config
    ):
        update_data = {
            "matrix_cadence": "daily",
            "matrix_interval": 1,
            "matrix_duration": 60,
            "matrix_ending_at": 2000,
            "matrix_starting_at": 800,
            "matrix_reminders": False,
        }
        response = test_client.put(
            "/api/v1/configuration", json=update_data, headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["matrix_cadence"] == "daily"
