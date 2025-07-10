import pytest
from fastapi.testclient import TestClient
from db.models import UserSkills


class TestMatrixRouter:
    def test_get_matrix_unauthorized(self, test_client: TestClient, test_user):
        response = test_client.get(f"/api/v1/users/{test_user.id}/matrix")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_matrix_success(self, test_client: TestClient, auth_headers, mock_current_user, test_user, test_skill, test_grade, test_session):
        user_skill = UserSkills(user_id=test_user.id, skill_id=test_skill.id, grade_id=test_grade.id)
        test_session.add(user_skill)
        await test_session.commit()
        
        response = test_client.get(f"/api/v1/users/{test_user.id}/matrix", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_matrix_by_skill_success(self, test_client: TestClient, auth_headers, mock_current_user, test_user, test_skill, test_grade, test_session):
        user_skill = UserSkills(user_id=test_user.id, skill_id=test_skill.id, grade_id=test_grade.id)
        test_session.add(user_skill)
        await test_session.commit()
        
        response = test_client.get(f"/api/v1/users/{test_user.id}/matrix/{test_skill.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_populate_matrix_success(self, test_client: TestClient, auth_headers, mock_current_user, test_user, test_skill, test_grade):
        matrix_data = {"grade_id": test_grade.id, "note": "Test note"}
        response = test_client.post(f"/api/v1/users/{test_user.id}/matrix/{test_skill.id}", json=matrix_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["note"] == "Test note"

    def test_delete_matrix_success(self, test_client: TestClient, auth_headers, mock_current_user, test_user, test_skill):
        response = test_client.delete(f"/api/v1/users/{test_user.id}/matrix/{test_skill.id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() is True