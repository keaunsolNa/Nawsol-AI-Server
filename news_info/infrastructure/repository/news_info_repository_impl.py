import hashlib
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from config.database.session import get_db_session
from news_info.application.port.news_info_repository_port import NewsInfoRepositoryPort
from news_info.domain.value_object.news_item import NewsItem
from news_info.infrastructure.orm.newsInfo_orm import NewsInfoORM, NewsProvider
from datetime import datetime, date, time

def _md5_hex(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


class NewsInfoRepositoryImpl(NewsInfoRepositoryPort):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        if not hasattr(self, "db"):
            self.db: Session = get_db_session()

    async def save_news_batch(self, news_list: List[NewsItem]) -> List[NewsItem]:

        try:
            if not news_list:
                return []

            new_list: List[NewsItem] = []

            for item in news_list:
                canonical_url = (item.originallink or item.link or "").strip()
                if not canonical_url:
                    continue

                canonical_url_hash = _md5_hex(canonical_url)

                existing = self.db.query(NewsInfoORM).filter(
                    and_(
                        NewsInfoORM.provider == NewsProvider.NAVER_NEWS,
                        NewsInfoORM.canonical_url_hash == canonical_url_hash,
                    )
                ).first()

                if not existing:
                    new_list.append(item)

            if not new_list:
                return news_list

            orm_list = []
            for item in new_list:
                canonical_url = (item.originallink or item.link or "").strip()
                canonical_url_hash = _md5_hex(canonical_url)

                orm_list.append(
                    NewsInfoORM(
                        provider=NewsProvider.NAVER_NEWS,
                        title=item.title,
                        description=item.description,
                        content=getattr(item, "content", None),
                        link=item.link,
                        originallink=item.originallink,
                        canonical_url=canonical_url,
                        canonical_url_hash=canonical_url_hash,
                        published_at=item.published_at.timestamp if item.published_at else None,
                        raw_json={
                            "title": item.title,
                            "description": item.description,
                            "content": getattr(item, "content", None),
                            "link": item.link,
                            "originallink": item.originallink,
                            "published_at": item.published_at.timestamp.isoformat() if item.published_at else None,
                        },
                    )
                )

            self.db.add_all(orm_list)
            self.db.commit()

            for orm_item in orm_list:
                self.db.refresh(orm_item)

            return news_list
        finally:
            self.db.close()

    async def get_three_month_news_for_card_news(self) -> List[NewsInfoORM]:

        target_date = date.today()  # 또는 datetime.utcnow().date()

        start = datetime.combine(target_date, time.min)  # 00:00:00
        end = datetime.combine(target_date, time.max)  # 23:59:59.999999

        try:
            rows = (
                self.db.query(NewsInfoORM)
                .filter(NewsInfoORM.published_at >= start)
                .filter(NewsInfoORM.published_at <= end)
                .order_by(NewsInfoORM.published_at.desc())
                .all()
            )

            return rows

        finally:
            self.db.close()


