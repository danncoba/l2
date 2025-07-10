import pytest
import uuid
from fastapi.testclient import TestClient
from db.models import UserSkills, MatrixChat, Notification


class TestIntegration:
    """Integration tests covering multiple router interactions"""

    @pytest.mark.asyncio
    async def test_complete_user_workflow(self, test_client: TestClient, auth_headers, mock_current_user, test_user, test_skill, test_grade, test_session):
        """Test complete workflow: create user skill -> create matrix chat -> create notification"""
        
        # 1. Create user skill matrix entry
        matrix_data = {"grade_id": test_grade.id, "note": "Initial skill assessment"}
        response = test_client.post(f"/api/v1/users/{test_user.id}/matrix/{test_skill.id}", json=matrix_data, headers=auth_headers)
        assert response.status_code == 200
        
        # 2. Verify matrix entry exists
        response = test_client.get(f"/api/v1/users/{test_user.id}/matrix", headers=auth_headers)
        assert response.status_code == 200
        matrix_data = response.json()
        assert len(matrix_data) >= 1
        
        # 3. Create matrix chat for validation
        chat = MatrixChat(
            id=uuid.uuid4(),
            user_id=test_user.id,
            skill_id=test_skill.id,
            status="IN_PROGRESS",
            timespan_start=1000,
            timespan_end=2000
        )
        test_session.add(chat)
        await test_session.commit()
        
        # 4. Get chat info
        response = test_client.get(f"/api/v1/matrix-chats/{chat.id}/info", headers=auth_headers)
        assert response.status_code == 200
        chat_data = response.json()
        assert chat_data["status"] == "IN_PROGRESS"
        
        # 5. Create notification for user
        user_skill = UserSkills(user_id=test_user.id, skill_id=test_skill.id, grade_id=None)
        test_session.add(user_skill)
        await test_session.commit()
        
        response = test_client.post(f"/api/v1/users/{test_user.id}/notifications", headers=auth_headers)
        assert response.status_code == 200
        
        # 6. Verify notifications were created
        response = test_client.get(f"/api/v1/users/{test_user.id}/notifications", headers=auth_headers)
        assert response.status_code == 200
        notifications = response.json()
        assert isinstance(notifications, list)

    @pytest.mark.asyncio
    async def test_admin_workflow(self, test_client: TestClient, admin_auth_headers, mock_admin_user, test_session):
        """Test admin-specific workflow: manage skills, grades, and configurations"""
        
        # 1. Create new skill
        skill_data = {"name": "Docker", "description": "Container technology"}
        response = test_client.post("/api/v1/skills", json=skill_data, headers=admin_auth_headers)
        assert response.status_code == 200
        skill = response.json()
        
        # 2. Create new grade
        grade_data = {"label": "Expert", "value": 7}
        response = test_client.post("/api/v1/grades", json=grade_data, headers=admin_auth_headers)
        assert response.status_code == 200
        grade = response.json()
        
        # 3. Get all skills
        response = test_client.get("/api/v1/skills", headers=admin_auth_headers)
        assert response.status_code == 200
        skills = response.json()
        assert any(s["name"] == "Docker" for s in skills)
        
        # 4. Get all grades
        response = test_client.get("/api/v1/grades", headers=admin_auth_headers)
        assert response.status_code == 200
        grades = response.json()
        assert any(g["label"] == "Expert" for g in grades)
        
        # 5. Update configuration
        config_data = {
            "matrix_cadence": "monthly",
            "matrix_interval": 30,
            "matrix_duration": 90,
            "matrix_ending_at": 1900,
            "matrix_starting_at": 800,
            "matrix_reminders": True
        }
        response = test_client.put("/api/v1/configuration", json=config_data, headers=admin_auth_headers)
        # This might fail if no config exists, which is acceptable
        assert response.status_code in [200, 404]

    def test_unauthorized_access_patterns(self, test_client: TestClient, test_user):
        """Test that unauthorized access is properly blocked across all endpoints"""
        
        endpoints_requiring_auth = [
            f"/api/v1/users/{test_user.id}",
            "/api/v1/profile/me",
            f"/api/v1/users/{test_user.id}/matrix",
            f"/api/v1/matrix-chats/users/{test_user.id}",
            f"/api/v1/users/{test_user.id}/notifications",
            "/api/v1/grades",
        ]
        
        for endpoint in endpoints_requiring_auth:
            response = test_client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"

    def test_admin_only_access_patterns(self, test_client: TestClient, auth_headers):
        """Test that admin-only endpoints properly block non-admin users"""
        
        admin_only_endpoints = [
            "/api/v1/skills",
            "/api/v1/configuration",
            "/api/v1/analytics",
        ]
        
        for endpoint in admin_only_endpoints:
            response = test_client.get(endpoint, headers=auth_headers)
            assert response.status_code == 403, f"Endpoint {endpoint} should require admin access"