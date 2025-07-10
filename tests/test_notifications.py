import pytest
import uuid
from fastapi.testclient import TestClient
from db.models import Notification, UserSkills


class TestNotificationsRouter:
    def test_list_notifications_unauthorized(self, test_client: TestClient, test_user):
        response = test_client.get(f"/api/v1/users/{test_user.id}/notifications")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_notifications_success(self, test_client: TestClient, auth_headers, mock_current_user, test_user, test_session):
        notification = Notification(
            notification_type="TEST",
            message="Test notification",
            user_id=test_user.id,
            status="UNREAD",
            chat_uuid=uuid.uuid4(),
            user_group="USER"
        )
        test_session.add(notification)
        await test_session.commit()
        
        response = test_client.get(f"/api/v1/users/{test_user.id}/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_mark_notification_success(self, test_client: TestClient, auth_headers, mock_current_user, test_user, test_session):
        notification = Notification(
            notification_type="TEST",
            message="Test notification",
            user_id=test_user.id,
            status="UNREAD",
            chat_uuid=uuid.uuid4(),
            user_group="USER"
        )
        test_session.add(notification)
        await test_session.commit()
        await test_session.refresh(notification)
        
        status_data = {
            "notifications": [{"id": notification.id, "status": "READ"}]
        }
        response = test_client.post(f"/api/v1/users/{test_user.id}/notifications/status", json=status_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_create_notification_success(self, test_client: TestClient, auth_headers, mock_current_user, test_user, test_skill, test_session):
        user_skill = UserSkills(user_id=test_user.id, skill_id=test_skill.id, grade_id=None)
        test_session.add(user_skill)
        await test_session.commit()
        
        response = test_client.post(f"/api/v1/users/{test_user.id}/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)