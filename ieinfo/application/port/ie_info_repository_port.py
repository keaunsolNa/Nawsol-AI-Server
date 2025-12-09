from abc import ABC, abstractmethod
from typing import List
from ieinfo.infrastructure.orm.ie_info import IEInfo

class IEInfoRepositoryPort(ABC):
    
    @abstractmethod
    def bulk_insert(self, ie_info_list: List[IEInfo]) -> bool:
        """IE_INFO 데이터 일괄 저장"""
        pass
    
    @abstractmethod
    def delete_by_session_and_month(self, session_id: str, year: int, month: int) -> bool:
        """특정 세션의 특정 월 데이터 삭제 (중복 방지용)"""
        pass
    
    @abstractmethod
    def get_by_session(self, session_id: str, year: int = None, month: int = None) -> List[IEInfo]:
        """세션별 데이터 조회"""
        pass
