from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import and_

from config.database.session import get_db_session
from community.application.port.community_repository_port import CommunityRepositoryPort
from community.domain.value_object.community_post import CommunityPost
from community.infrastructure.orm.community_post_orm import CommunityPostORM


class CommunityRepositoryImpl(CommunityRepositoryPort):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @classmethod
    def get_instance(cls) -> "CommunityRepositoryImpl":
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        if not hasattr(self, "db"):
            self.db: Session = get_db_session()

    def save_post_batch(self, posts: List[CommunityPost]) -> List[CommunityPost]:

        try:
            """
            provider + board_id + external_post_id 기준으로
            이미 DB에 있는 글은 건너뛰고, 새로운 글만 insert
            """
            if not posts:
                return []

            new_list: List[CommunityPost] = []

            for p in posts:
                existing = (
                    self.db.query(CommunityPostORM)
                    .filter(
                        and_(
                            CommunityPostORM.provider == p.provider,
                            CommunityPostORM.board_id == p.board_id,
                            CommunityPostORM.external_post_id == p.external_post_id,
                        )
                    )
                    .first()
                )

                if not existing:
                    new_list.append(p)

            # 전부 중복이면 그냥 원본 리스트 리턴
            if not new_list:
                return posts

            orm_list: List[CommunityPostORM] = []
            for p in new_list:
                orm_list.append(
                    CommunityPostORM(
                        provider=p.provider,
                        board_id=p.board_id,
                        external_post_id=p.external_post_id,
                        title=p.title,
                        author=p.author,
                        content=p.content,
                        url=p.url,
                        view_count=p.view_count,
                        recommend_count=p.recommend_count,
                        comment_count=p.comment_count,
                        posted_at=p.posted_at,
                        fetched_at=p.fetched_at,
                    )
                )

            self.db.add_all(orm_list)
            self.db.commit()

            for orm_item in orm_list:
                self.db.refresh(orm_item)

            return posts
        finally:
            self.db.close()