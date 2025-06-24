import uuid
from typing import Sequence, Tuple, Any, Optional, Dict, Iterator

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    ChannelVersions,
    CheckpointTuple,
)
from langgraph_sdk.auth.exceptions import HTTPException

from db.models import Runnable
from service.service import BaseService


class PGSaver(BaseCheckpointSaver):

    def __init__(self, get_session):
        self._db_session_getter = get_session

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        print("def put ->")
        print(config, checkpoint, metadata, new_versions)
        return super().put(config, checkpoint, metadata, new_versions)

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        print("def list ->")
        print(config, filter, before, limit)
        return super().list(config, filter=filter, before=before, limit=limit)

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        print("def get_tuple ->")
        print(config)
        return super().get_tuple(config)

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        print("def put_writes ->")
        print(config, writes, task_id, task_path)
        super().put_writes(config, writes, task_id, task_path)

    def delete_thread(self, thread_id: str) -> None:
        print("def delete_thread ->")
        print(thread_id)
        super().delete_thread(thread_id)

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        print("def aget_tuple ->")
        print(config)
        async for session in self._db_session_getter():
            try:
                runnable_service: BaseService[Runnable, uuid.UUID, Any, Any] = (
                    BaseService(Runnable, session)
                )
                thread_data = await runnable_service.get(
                    config["configurable"]["thread_id"]
                )
                print("RUNNABLES")
                print(f"Runnables {thread_data}")
                return CheckpointTuple()
            except Exception as exception:
                print(exception)
                return None
        return None

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        print("def aput ->")
        print("CONFIG", config)
        print("CHECKPOINT", checkpoint)
        print("METADATA", metadata)
        print("NEW_VERSIONS", new_versions)
        return await super().aput(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        print("def aput_writes ->")
        print(config, writes, task_id, task_path)
        return await super().aput_writes(config, writes, task_id, task_path)

    async def adelete_thread(self, thread_id: str) -> None:
        print("def adelete_thread ->")
        print(thread_id)
        return await super().adelete_thread(thread_id)
