from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def build_engine(url: str) -> Engine:
    if not url.startswith('sqlite:'):
        raise ValueError('Phase 1 supports SQLite only; PostgreSQL needs migrations and audit controls.')
    engine = create_engine(url, connect_args={'check_same_thread': False})

    @event.listens_for(engine, 'connect')
    def sqlite_pragmas(connection, _):
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.execute('PRAGMA busy_timeout=5000')
        cursor.close()

    return engine


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def initialize(engine: Engine) -> None:
    import app.models.entities  # noqa: F401 -- register metadata
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        for operation in ('UPDATE', 'DELETE'):
            connection.exec_driver_sql(f'''
                CREATE TRIGGER IF NOT EXISTS audit_no_{operation.lower()}
                BEFORE {operation} ON audit_log
                BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
            ''')
