"""
IE_RULE Repository 구현체
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ieinfo.application.port.ie_rule_repository_port import IERuleRepositoryPort
from ieinfo.infrastructure.orm.ie_rule import IERule
from ieinfo.infrastructure.orm.ie_info import IEType
from util.log.log import Log

logger = Log.get_logger()


class IERuleRepositoryImpl(IERuleRepositoryPort):
    """소득/지출 규칙 저장소 구현"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def find_by_keyword(self, keyword: str) -> Optional[IEType]:
        try:
            """
            키워드로 IE 타입 조회
            
            Args:
                keyword: 검색할 키워드
            
            Returns:
                IEType 또는 None (없으면)
            """
            rule = self.session.query(IERule).filter(
                IERule.keyword == keyword
            ).first()

            return rule.ie_type if rule else None
        finally:
            self.session.close()
    def find_all_keywords_by_type(self, ie_type: IEType) -> List[str]:
        try:
            """
            특정 타입의 모든 키워드 조회
            
            Args:
                ie_type: INCOME 또는 EXPENSE
            
            Returns:
                키워드 리스트
            """
            rules = self.session.query(IERule).filter(
                IERule.ie_type == ie_type
            ).all()

            return [rule.keyword for rule in rules]
        finally:
            self.session.close()
    def save_keyword(self, keyword: str, ie_type: IEType) -> bool:
        """
        새 키워드 저장 (중복 시 무시)
        
        Args:
            keyword: 저장할 키워드
            ie_type: INCOME 또는 EXPENSE
        
        Returns:
            성공 여부
        """
        try:
            # 중복 체크
            existing = self.session.query(IERule).filter(
                IERule.keyword == keyword
            ).first()
            
            if existing:
                logger.debug(f"[IE_RULE] 키워드 이미 존재: {keyword}")
                return False
            
            # 새 규칙 추가
            new_rule = IERule(
                keyword=keyword,
                ie_type=ie_type
            )
            
            self.session.add(new_rule)
            self.session.commit()
            
            logger.info(f"✅ [IE_RULE] 새 키워드 저장: {keyword} → {ie_type.value}")
            return True
            
        except IntegrityError as e:
            self.session.rollback()
            logger.warning(f"[IE_RULE] 키워드 저장 실패 (중복): {keyword}")
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"[IE_RULE] 키워드 저장 오류: {str(e)}")
            return False
        finally:
            self.session.close()

    def keyword_exists(self, keyword: str) -> bool:

        try:
            """
            키워드 존재 여부 확인
            
            Args:
                keyword: 확인할 키워드
            
            Returns:
                존재 여부
            """
            count = self.session.query(IERule).filter(
                IERule.keyword == keyword
            ).count()

            return count > 0
        finally:
            self.session.close()

    def get_all_rules(self) -> List[dict]:

        try:
            """
            모든 규칙 조회
            
            Returns:
                규칙 리스트 [{"id": 1, "keyword": "급여", "ie_type": "INCOME"}, ...]
            """
            rules = self.session.query(IERule).all()

            return [
                {
                    "id": rule.id,
                    "keyword": rule.keyword,
                    "ie_type": rule.ie_type.value,
                    "created_at": rule.created_at.isoformat() if rule.created_at else None
                }
                for rule in rules
            ]
        finally:
            self.session.close()