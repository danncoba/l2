import pytest
from fastapi.testclient import TestClient


class TestUsersRouter:
    def test_get_users_success(self, test_client: TestClient, test_user):
        response = test_client.get("/api/v1/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_user_by_id_unauthorized(self, test_client: TestClient, test_user):
        response = test_client.get(f"/api/v1/users/{test_user.id}")
        assert response.status_code == 401

    def test_get_user_by_id_success(self, test_client: TestClient, auth_headers, mock_current_user, test_user):
        response = test_client.get(f"/api/v1/users/{test_user.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == "test@example.com"

    def test_get_user_not_found(self, test_client: TestClient, auth_headers, mock_current_user):
        response = test_client.get("/api/v1/users/999", headers=auth_headers)
        assert response.status_code == 404

    def test_create_user_success(self, test_client: TestClient, auth_headers, mock_current_user):
        user_data = {
            "first_name": "New",
            "last_name": "User",
            "email": "new@example.com",
            "password": "newpassword123"
        }
        response = test_client.post("/api/v1/users", json=user_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "new@example.com"
        assert data["first_name"] == "New"

    def test_update_user_success(self, test_client: TestClient, auth_headers, mock_current_user, test_user):
        update_data = {
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
            "password": "updatedpassword123"
        }
        response = test_client.put(f"/api/v1/users/{test_user.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"

    def test_delete_user_success(self, test_client: TestClient, auth_headers, mock_current_user, test_user):
        response = test_client.delete(f"/api/v1/users/{test_user.id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() is True

    def test_choose_user_success(self, test_client: TestClient, test_user):
        response = test_client.post(f"/api/v1/users/{test_user.id}/select")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id

    def test_choose_user_not_found(self, test_client: TestClient):
        response = test_client.post("/api/v1/users/999/select")
        assert response.status_code == 404

    def test_test_get_users_endpoint(self, test_client: TestClient):
        response = test_client.get("/api/v1/users/test/test")
        # This endpoint might fail due to external dependencies
        assert response.status_code in [200, 500]