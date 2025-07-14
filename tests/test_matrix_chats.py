import pytest
import uuid
from fastapi.testclient import TestClient
from db.models import MatrixChat


class TestMatrixChatsRouter:
    def test_get_matrix_chats_unauthorized(self, test_client: TestClient, test_user):
        response = test_client.get(f"/api/v1/matrix-chats/users/{test_user.id}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_matrix_chats_success(
        self,
        test_client: TestClient,
        auth_headers,
        mock_current_user,
        test_user,
        test_skill,
        test_session,
    ):
        chat = MatrixChat(
            id=uuid.uuid4(),
            user_id=test_user.id,
            skill_id=test_skill.id,
            status="IN_PROGRESS",
            timespan_start=1000,
            timespan_end=2000,
        )
        test_session.add(chat)
        await test_session.commit()

        response = test_client.get(
            f"/api/v1/matrix-chats/users/{test_user.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_matrix_chat_info_success(
        self,
        test_client: TestClient,
        auth_headers,
        mock_current_user,
        test_user,
        test_skill,
        test_session,
    ):
        chat = MatrixChat(
            id=uuid.uuid4(),
            user_id=test_user.id,
            skill_id=test_skill.id,
            status="IN_PROGRESS",
            timespan_start=1000,
            timespan_end=2000,
        )
        test_session.add(chat)
        await test_session.commit()

        response = test_client.get(
            f"/api/v1/matrix-chats/{chat.id}/info", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(chat.id)

    def test_get_matrix_chat_not_found(
        self, test_client: TestClient, auth_headers, mock_current_user
    ):
        fake_id = uuid.uuid4()
        response = test_client.get(
            f"/api/v1/matrix-chats/{fake_id}/info", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_post_matrix_message_completed_chat(
        self,
        test_client: TestClient,
        auth_headers,
        mock_current_user,
        test_user,
        test_skill,
        test_session,
    ):
        chat = MatrixChat(
            id=uuid.uuid4(),
            user_id=test_user.id,
            skill_id=test_skill.id,
            status="COMPLETED",
            timespan_start=1000,
            timespan_end=2000,
        )
        test_session.add(chat)
        await test_session.commit()

        message_data = {"messages": [{"message": "Test message", "msg_type": "human"}]}
        response = test_client.post(
            f"/api/v1/matrix-chats/{chat.id}", json=message_data, headers=auth_headers
        )
        assert response.status_code == 403
