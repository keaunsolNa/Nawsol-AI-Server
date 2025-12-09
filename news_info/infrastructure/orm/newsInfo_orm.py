from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SAEnum, JSON, Index
from enum import Enum as PyEnum
from datetime import datetime

from config.database.session import Base

class NewsProvider(str, PyEnum):
    NAVER_NEWS = "NAVER_NEWS"


class NewsInfoORM(Base):
    __tablename__ = "news_info"

    id = Column(Integer, primary_key=True)

    provider = Column(SAEnum(NewsProvider, native_enum=True), nullable=False, default=NewsProvider.NAVER_NEWS)

    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)

    link = Column(String(2048), nullable=False)
    originallink = Column(String(2048), nullable=True)

    canonical_url = Column(String(2048), nullable=False)
    canonical_url_hash = Column(String(32), nullable=False)  # md5 hex

    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    raw_json = Column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("uq_news_info_provider_urlhash", "provider", "canonical_url_hash", unique=True),
        Index("idx_news_info_published_at", "published_at"),
    )