import pytest
import pathlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base
import app


@pytest.fixture(scope="session")
def db_engine(tmp_path_factory):
    # create a temporary file-backed sqlite DB for the test session
    db_path = tmp_path_factory.mktemp("db") / "test_db.sqlite"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    # create tables
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def db_session(db_engine):
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        yield db
        # rollback any changes made during the test to keep DB clean between tests
        db.rollback()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def override_get_session(monkeypatch, db_session):
    # Replace app.get_session with a generator yielding the test session
    def _get_session():
        try:
            yield db_session
        finally:
            pass

    monkeypatch.setattr(app, 'get_session', _get_session)
    yield