from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum as SAEnum, Integer, String, ForeignKey

from config.database.session import Base


class IEType(PyEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class IEInfo(Base):
    __tablename__ = "ie_info"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("account.session_id"), nullable=False, index=True)
    ie_type = Column(SAEnum(IEType, native_enum=True), nullable=False, index=True)
    key = Column(String(255), nullable=False)
    value = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

