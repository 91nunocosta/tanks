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


@fixture(name="client")
def client_fixture(session: Session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)
