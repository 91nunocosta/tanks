import pytest
import sqlalchemy
from pydantic import BaseModel
from pytest import fixture
from sqlmodel import Field, Session, SQLModel, create_engine

from tanks.crud import CollectionResource, SQLModelCRUD


class Base(BaseModel):
    value: int


class Model(SQLModel, table=True):
    id: int = Field(primary_key=True)
    value: int


@fixture(name="session")
def session_fixture() -> Session:
    engine = create_engine("sqlite://")
    Model.metadata.create_all(engine)
    return Session(engine)


@fixture(name="rows")
def rows_fixture(session) -> list[Model]:
    rows = [
        Model(id=0, value=1),
        Model(id=1, value=2),
        Model(id=2, value=3),
    ]
    for row in rows:
        session.add(row)
    session.commit()
    return rows


@fixture(name="sqlmodel_crud")
def sqlmodel_crud_fixture(session: Session):
    return SQLModelCRUD[Model, Base](session, Model)


def test_create(session: Session, sqlmodel_crud: SQLModelCRUD):
    content: Base = Base(value=1)

    result = sqlmodel_crud.create(content)

    assert isinstance(result, Model)
    created_row = session.query(Model).filter_by(id=result.id).first()
    assert created_row
    assert created_row.value == content.value


def test_get_one(session: Session, sqlmodel_crud: SQLModelCRUD):
    row = Model(id=0, value=1)
    session.add(row)
    session.commit()

    result = sqlmodel_crud.get_one(0)

    assert isinstance(result, Model)
    assert result == row


def test_get_one_miss(sqlmodel_crud: SQLModelCRUD):
    with pytest.raises(sqlalchemy.exc.NoResultFound):
        sqlmodel_crud.get_one(1)


def test_total(sqlmodel_crud: SQLModelCRUD, rows):
    assert sqlmodel_crud.total() == len(rows)


def test_get_many(sqlmodel_crud: SQLModelCRUD, rows: list[Model]):
    assert sqlmodel_crud.get_many(offset=0, limit=10) == CollectionResource(
        items=rows,
        offset=0,
        limit=10,
        total=len(rows),
    )


def test_get_many_offset(sqlmodel_crud: SQLModelCRUD, rows: list[Model]):
    assert sqlmodel_crud.get_many(offset=1, limit=10) == CollectionResource(
        items=rows[1:],
        offset=1,
        limit=10,
        total=len(rows),
    )


def test_get_many_limit(sqlmodel_crud: SQLModelCRUD, rows: list[Model]):
    assert sqlmodel_crud.get_many(offset=0, limit=2) == CollectionResource(
        items=rows[:2],
        offset=0,
        limit=2,
        total=len(rows),
    )


def test_get_many_filter(sqlmodel_crud: SQLModelCRUD, rows: list[Model]):
    assert sqlmodel_crud.get_many(
        offset=0, limit=10, filters={Model.value: 1}
    ) == CollectionResource(
        items=[rows[0]],
        offset=0,
        limit=10,
        total=1,
    )


def test_update(
    session: Session, sqlmodel_crud: SQLModelCRUD, rows
):  # pylint: disable=unused-argument
    content = Base(value=1000)

    result = sqlmodel_crud.update(row_id=1, content=content)

    assert isinstance(result, Model)
    assert result.id == 1
    assert result.value == 1000
    updated_row = session.query(Model).filter_by(id=1).first()
    assert updated_row
    assert updated_row.value == 1000


def test_update_miss(sqlmodel_crud: SQLModelCRUD):
    content = Base(value=1000)

    with pytest.raises(sqlalchemy.exc.NoResultFound):
        sqlmodel_crud.update(row_id=1, content=content)


def test_delete(
    session: Session, sqlmodel_crud: SQLModelCRUD, rows
):  # pylint: disable=unused-argument
    sqlmodel_crud.delete(row_id=0)

    assert session.query(Model).filter_by(id=0).count() == 0


def test_delete_miss(sqlmodel_crud: SQLModelCRUD):
    with pytest.raises(sqlalchemy.exc.NoResultFound):
        sqlmodel_crud.delete(1)
