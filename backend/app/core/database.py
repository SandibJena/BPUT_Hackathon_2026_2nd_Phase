from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Alias for test compatibility
session_factory = SessionLocal

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables. Safe to call multiple times."""
    # Import models to ensure they're registered with Base before create_all
    import app.models.user  # noqa: F401
    import app.models.patient  # noqa: F401
    import app.models.consent_record  # noqa: F401
    import app.models.triage_note  # noqa: F401
    import app.models.upload  # noqa: F401
    import app.models.audit_log  # noqa: F401
    Base.metadata.create_all(bind=engine)

