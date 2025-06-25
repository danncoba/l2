from abc import ABC
from typing import (
    Optional,
    TypeVar,
    Generic,
    List,
    Any,
    Sequence,
    Type,
)

from fastapi import HTTPException
from sqlalchemy import Row, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, or_

from service.filters import FilterModel, FilterType

T = TypeVar("T")
I = TypeVar("I")
CR = TypeVar("CR")
UR = TypeVar("UR")


class __AbstractService(ABC, Generic[T, I, CR, UR]):
    model: Type[T]
    session: AsyncSession

    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, model_id: I) -> Optional[T]:
        model = await self.session.get(self.model, model_id)
        if model is None:
            raise HTTPException(status_code=404, detail="Not found")
        return model

    async def get_by_field(self, field: str, value: Any) -> Optional[T]:
        confirmed_field = None
        if hasattr(self.model, field):
            confirmed_field = getattr(self.model, field)
        if confirmed_field is None:
            raise HTTPException(status_code=404, detail="Not found")
        statement = select(self.model).where(confirmed_field == value)
        await self.session.execute(statement)

    async def list_all(
        self,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        filters: dict = None,
        order_by: Optional[list] = None,
    ) -> Sequence[Row[Any] | RowMapping | Any]:
        statement = select(self.model)
        if filters is not None and len(filters) > 0:
            clauses = [
                getattr(self.model, key) == value for key, value in filters.items()
            ]
            statement = statement.where(*clauses)
        statement = statement.limit(limit).offset(offset)
        if order_by is not None and len(order_by) > 0:
            statement = statement.order_by(*order_by)
        result = await self.session.execute(statement)
        models = result.scalars().all()
        return models

    async def in_field(
        self,
        field: str,
        in_list: List[I],
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
    ) -> Sequence[Row[Any] | RowMapping | Any]:
        statement = select(self.model).where(getattr(self.model, field).in_(in_list))
        statement = statement.limit(limit).offset(offset)
        result = await self.session.execute(statement)
        models = result.scalars().all()
        return models

    async def filter(
        self,
        fields: List[FilterModel],
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Row[Any] | RowMapping | Any]:
        statement = select(self.model)
        for field in fields:
            if field.f_type == FilterType.EQUALS:
                statement = select(self.model).where(
                    getattr(self.model, field.f_attribute) == field.f_value
                )
            elif field.f_type == FilterType.GTE:
                statement = select(self.model).where(
                    getattr(self.model, field.f_attribute) >= field.f_value
                )
            elif field.f_type == FilterType.LTE:
                statement = select(self.model).where(
                    getattr(self.model, field.f_attribute) <= field.f_value
                )
            elif field.f_type == FilterType.GT:
                statement = select(self.model).where(
                    getattr(self.model, field.f_attribute) > field.f_value
                )
            elif field.f_type == FilterType.LT:
                statement = select(self.model).where(
                    getattr(self.model, field.f_attribute) < field.f_value
                )

        statement = statement.limit(limit).offset(offset)
        result = await self.session.execute(statement)
        models = result.scalars().all()
        return models

    async def list_all_with_or(
        self,
        filters: dict = None,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        order_by: Optional[list] = None,
    ) -> Sequence[Row[Any] | RowMapping | Any]:
        statement = select(self.model)
        if (
            filters is not None
            and len(filters) > 0
            and "or_" in filters
            and isinstance(filters["or_"], dict)
        ):
            clauses = [
                getattr(self.model, key) == value
                for key, value in filters["or_"].items()
            ]
            statement = statement.where(or_(*clauses))
        if order_by is not None and len(order_by) > 0:
            statement = statement.order_by(*order_by)
        statement = statement.limit(limit).offset(offset)
        result = await self.session.execute(statement)
        models = result.scalars().all()
        return models

    async def create(self, create_dto: CR) -> T:
        created_model = self.model(**create_dto.model_dump())
        self.session.add(created_model)
        await self.session.commit()
        await self.session.refresh(created_model)
        return created_model

    async def create_many(self, create_dtos: List[CR]) -> List[T]:
        created_models = []
        for create_dto in create_dtos:
            created_model = self.model(**create_dto.model_dump())
            self.session.add(created_model)
            created_models.append(created_model)
        await self.session.commit()
        return created_models

    async def update(self, model_id: I, update_dto: UR) -> T:
        model = await self.get(model_id)
        model.sqlmodel_update(update_dto.model_dump(exclude_unset=True))
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def update_many(self, model_dtos: List[UR], id_field: str) -> List[T]:
        updated_models = []
        for model_dto in model_dtos:
            if getattr(model_dto, id_field):
                model = await self.get(getattr(model_dto, id_field))
                model.sqlmodel_update(model_dto.model_dump(exclude_unset=True))
                self.session.add(model)
                updated_models.append(model)
        await self.session.commit()
        return updated_models

    async def delete(self, model_id: I) -> bool:
        model = await self.get(model_id)
        await self.session.delete(model)
        await self.session.commit()
        return True

    async def save_model(self, model: T) -> T:
        print("SAVING MODEL", model)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model


class BaseService(__AbstractService[T, I, CR, UR]):

    def __init__(self, model: Type[T], session: AsyncSession):
        super().__init__(model, session)
