import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
