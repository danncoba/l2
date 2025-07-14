import pytest
from fastapi.testclient import TestClient


class TestProfileRouter:
    def test_get_profile_unauthorized(self, test_client: TestClient):
        response = test_client.get("/api/v1/profile/me")
        assert response.status_code == 401

    def test_get_profile_success(
        self, test_client: TestClient, auth_headers, mock_current_user
    ):
        response = test_client.get("/api/v1/profile/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"

    def test_update_profile_success(
        self, test_client: TestClient, auth_headers, mock_current_user
    ):
        update_data = {
            "first_name": "Updated",
            "last_name": "User",
            "email": "test@example.com",
            "password": "password123",
            "description": "Updated description",
            "city": "New York",
            "address": "123 Main St",
            "phone_number": "+1234567890",
        }
        response = test_client.put(
            "/api/v1/profile/me", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["description"] == "Updated description"
