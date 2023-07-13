from typing import Callable, TypeVar

from fastapi.testclient import TestClient
from pytest import MonkeyPatch, fixture
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from tanks.dependencies import get_session
from tanks.main import create_app


@fixture(name="database_url", autouse=True)
def database_url_fixture(monkeypatch: MonkeyPatch):
    database_url = "sqlite://"
    monkeypatch.setenv("DATABASE_URL", database_url)
    return database_url


@fixture(name="session")
def session_fixture(database_url: str):
    engine = create_engine(
        database_url, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


T = TypeVar("T", bound=SQLModel)

CreateDBRowsFunction = Callable[[T], list[T]]


@fixture(name="create_db_rows")
def create_db_rows_fixture(session: Session) -> CreateDBRowsFunction:
    def create_db_rows(*instances: T) -> list[T]:
        for instance in instances:
            session.add(instance)

        session.commit()

        for instance in instances:
            session.refresh(instance)

        return list(instances)

    return create_db_rows


@fixture(name="client")
def client_fixture(session: Session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)
