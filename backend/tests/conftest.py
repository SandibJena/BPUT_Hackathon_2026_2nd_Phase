import pytest

from app.core.database import build_engine, initialize


@pytest.fixture
def engine(tmp_path):
    database = build_engine(f"sqlite:///{tmp_path / 'test.db'}")
    initialize(database)
    yield database
    database.dispose()
