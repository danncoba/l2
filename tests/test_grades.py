import pytest
from fastapi.testclient import TestClient


class TestGradesRouter:
    def test_get_grades_unauthorized(self, test_client: TestClient):
        response = test_client.get("/api/v1/grades")
        assert response.status_code == 401

    def test_get_grades_success(
        self, test_client: TestClient, auth_headers, mock_current_user, test_grade
    ):
        response = test_client.get("/api/v1/grades", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["label"] == "Beginner"

    def test_get_grade_by_id_success(
        self, test_client: TestClient, auth_headers, mock_current_user, test_grade
    ):
        response = test_client.get(
            f"/api/v1/grades/{test_grade.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_grade.id
        assert data["label"] == "Beginner"

    def test_get_grade_not_found(
        self, test_client: TestClient, auth_headers, mock_current_user
    ):
        response = test_client.get("/api/v1/grades/999", headers=auth_headers)
        assert response.status_code == 404

    def test_create_grade_success(
        self, test_client: TestClient, auth_headers, mock_current_user
    ):
        grade_data = {"label": "Advanced", "value": 5}
        response = test_client.post(
            "/api/v1/grades", json=grade_data, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "Advanced"
        assert data["value"] == 5

    def test_update_grade_success(
        self, test_client: TestClient, auth_headers, mock_current_user, test_grade
    ):
        update_data = {"label": "Intermediate", "value": 3}
        response = test_client.put(
            f"/api/v1/grades/{test_grade.id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "Intermediate"

    def test_delete_grade_success(
        self, test_client: TestClient, auth_headers, mock_current_user, test_grade
    ):
        response = test_client.delete(
            f"/api/v1/grades/{test_grade.id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() is True
