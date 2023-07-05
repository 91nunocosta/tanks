"""
Provide CRUD operations for SQLModels.
"""
from typing import Any, Generic, Type, TypeVar

import sqlalchemy
from pydantic import BaseModel
from sqlmodel import Session, SQLModel

M = TypeVar("M", bound=SQLModel)
B = TypeVar("B", bound=BaseModel)

T = TypeVar("T")


class CollectionResource(BaseModel, Generic[T]):
    total: int
    offset: int
    limit: int
    items: list[T]


class SQLModelCRUD(Generic[M, B]):
    """A SQLModel wrapper that providing CRUD operations."""

    def __init__(self, session: Session, model_cls: Type[M]):
        self.session = session
        self.model_cls = model_cls
        self.query_set = session.query(model_cls)

    def create(self, content: B, row_id: int | None = None) -> M:
        content_dict = content.dict()
        if id is not None:
            content_dict["id"] = row_id
        row = self.model_cls(**content_dict)
        self.session.add(row)
        self.session.commit()
        return row

    def get_one(self, row_id: int) -> M:
        return self.query_set.filter_by(id=row_id).one()

    def total(self) -> int:
        return self.query_set.count()

    def get_many(
        self,
        offset: int,
        limit: int,
        filters: dict[int, Any] | None = None,
    ) -> CollectionResource[M]:
        if filters is None:
            filters = {}

        query = self.query_set

        for field, value in filters.items():
            query = query.filter(field == value)

        total = query.count()

        items = query.offset(offset).limit(limit).all()

        return CollectionResource(
            items=items,
            offset=offset,
            limit=limit,
            total=total,
        )

    def update(self, row_id: int, content: B) -> M:
        self.delete(row_id)
        return self.create(content, row_id=row_id)

    def delete(self, row_id: int) -> None:
        deleted_rows = self.session.query(self.model_cls).filter_by(id=row_id).delete()
        if deleted_rows < 1:
            raise sqlalchemy.exc.NoResultFound()
