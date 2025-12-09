from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from config.database.session import get_db_session
from ieinfo.application.port.ie_info_repository_port import IEInfoRepositoryPort
from ieinfo.infrastructure.orm.ie_info import IEInfo
from util.log.log import Log

logger = Log.get_logger()


class IEInfoRepositoryImpl(IEInfoRepositoryPort):
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
        if not hasattr(self, 'db'):
            self.db: Session = get_db_session()
    
    def bulk_insert(self, ie_info_list: List[IEInfo]) -> bool:
        """IE_INFO 데이터 일괄 저장"""
        try:
            self.db.add_all(ie_info_list)
            self.db.commit()
            logger.info(f"Successfully inserted {len(ie_info_list)} IE_INFO records")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to insert IE_INFO records: {str(e)}")
            raise
    
    def delete_by_session_and_month(self, session_id: str, year: int, month: int) -> bool:
        """특정 세션의 특정 월 데이터 삭제 (중복 방지용)"""
        try:
            deleted_count = self.db.query(IEInfo).filter(
                and_(
                    IEInfo.session_id == session_id,
                    IEInfo.year == year,
                    IEInfo.month == month
                )
            ).delete()
            self.db.commit()
            logger.info(f"Deleted {deleted_count} IE_INFO records for session {session_id}, {year}-{month}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete IE_INFO records: {str(e)}")
            raise
    
    def get_by_session(self, session_id: str, year: int = None, month: int = None) -> List[IEInfo]:
        """세션별 데이터 조회"""
        try:
            query = self.db.query(IEInfo).filter(IEInfo.session_id == session_id)
            
            if year is not None:
                query = query.filter(IEInfo.year == year)
            if month is not None:
                query = query.filter(IEInfo.month == month)
            
            return query.all()
        except Exception as e:
            logger.error(f"Failed to fetch IE_INFO records: {str(e)}")
            raise