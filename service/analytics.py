import enum
from abc import ABC, abstractmethod
from typing import Self

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from dto.response.analytics import AnalyticsResponseCompletionRate


class AnalyticsServiceType(enum.Enum):
    NORMAL = 0


class BaseAnalytics(ABC):

    def __init__(self, session: AsyncSession):
        self.session = session

    @abstractmethod
    async def get_completion_rate(self) -> AnalyticsResponseCompletionRate:
        raise NotImplementedError()

    @abstractmethod
    async def get_top_skills_by_completion_rate(self):
        raise NotImplementedError()


class AnalyticsService(BaseAnalytics):

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_completion_rate(self) -> AnalyticsResponseCompletionRate:
        query = text(
            """
            select count(*) as total_count, 
                   status, timespan_start, timespan_end 
            from matrix_chats group by status, timespan_start, timespan_end;
            """
        )
        results = await self.session.execute(
            query,
        )
        print("TOTAL RESULTS ->", results.rowcount)
        all_to_create = []
        for result in results:
            print("RESULT ->", result)
            all_to_create.append(
                AnalyticsResponseCompletionRate(
                    count=result[0],
                    status=result[1],
                    evaluation_start=result[2],
                    evaluation_end=result[3],
                )
            )
        return all_to_create

    async def get_top_skills_by_completion_rate(self):
        query = text(
            """
            select count(*) as total_count,
                   status,
                   timespan_start,
                   timespan_end
            from matrix_chats
            group by status, timespan_start, timespan_end;
            """
        )
        results = await self.session.execute(
            query,
        )
        print("TOTAL RESULTS ->", results.rowcount)
        all_to_create = []
        for result in results:
            print("RESULT ->", result)
            all_to_create.append(
                AnalyticsResponseCompletionRate(
                    count=result[0],
                    status=result[1],
                    evaluation_start=result[2],
                    evaluation_end=result[3],
                )
            )


class AnalyticsServiceFactory:

    session: AsyncSession = None

    def __init__(self, service_type: AnalyticsServiceType):
        self.service_type = service_type

    def set_session(self, session: AsyncSession) -> Self:
        self.session = session
        return self

    def build(self) -> BaseAnalytics:
        assert self.session is not None
        return AnalyticsService(self.session)
