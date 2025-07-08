from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession


class BaseAnalytics(ABC):

    def __init__(self, session: AsyncSession):
        self.session = session

    @abstractmethod
    def send_event(self, event_name: str, event_data: dict):
        raise NotImplementedError()
