from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class TimestampMixin:
    """Mixin to add timestamp fields to models."""
    
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now()
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now()
    )


class BaseModel(Base, TimestampMixin):
    """
    Abstract base model with primary key and timestamps.
    
    All models should inherit from this class to get:
    - id: Primary key
    - created_at: Timestamp of creation
    - updated_at: Timestamp of last update
    """
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }