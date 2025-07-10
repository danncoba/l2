import pytest
from fastapi.testclient import TestClient


class TestSkillsRouter:
    def test_get_skills_unauthorized(self, test_client: TestClient):
        response = test_client.get("/api/v1/skills")
        assert response.status_code == 401

    def test_get_skills_forbidden_non_admin(self, test_client: TestClient, auth_headers):
        response = test_client.get("/api/v1/skills", headers=auth_headers)
        assert response.status_code == 403

    def test_get_skills_success(self, test_client: TestClient, admin_auth_headers, mock_admin_user, test_skill):
        response = test_client.get("/api/v1/skills", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == "Python"

    def test_get_skill_by_id_success(self, test_client: TestClient, admin_auth_headers, mock_admin_user, test_skill):
        response = test_client.get(f"/api/v1/skills/{test_skill.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_skill.id
        assert data["name"] == "Python"

    def test_get_skill_not_found(self, test_client: TestClient, admin_auth_headers, mock_admin_user):
        response = test_client.get("/api/v1/skills/999", headers=admin_auth_headers)
        assert response.status_code == 404

    def test_create_skill_success(self, test_client: TestClient, admin_auth_headers, mock_admin_user):
        skill_data = {"name": "JavaScript", "description": "JavaScript programming"}
        response = test_client.post("/api/v1/skills", json=skill_data, headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "JavaScript"
        assert data["description"] == "JavaScript programming"

    def test_delete_skill_success(self, test_client: TestClient, admin_auth_headers, mock_admin_user, test_skill):
        response = test_client.delete(f"/api/v1/skills/{test_skill.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        assert response.json() is True