"""
AnalyzeHistory Repository 구현체
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
import re

from asset_allocation.application.port.analyze_history_repository_port import AnalyzeHistoryRepositoryPort
from asset_allocation.infrastructure.orm.analyze_history import AnalyzeHistory
from util.log.log import Log

logger = Log.get_logger()


class AnalyzeHistoryRepositoryImpl(AnalyzeHistoryRepositoryPort):
    """미래 자산 예측 분석 이력 저장소 구현"""
    
    def __init__(self, session: Session):
        self.session = session
    
    @staticmethod
    def _remove_html_tags(text: str) -> str:
        """
        HTML 태그 제거 (줄바꿈 보존)
        
        Args:
            text: HTML이 포함된 텍스트
            
        Returns:
            순수 텍스트 (줄바꿈 유지)
        """
        # <br>, <br/>, <br /> → 줄바꿈으로 변환
        clean_text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        
        # <p>, <div>, <h1-6> 등 블록 요소 → 줄바꿈으로 변환
        clean_text = re.sub(r'</?(p|div|h[1-6]|li|ul|ol|table|tr|td|th)[^>]*>', '\n', clean_text, flags=re.IGNORECASE)
        
        # 나머지 HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        
        # HTML 엔티티 디코딩
        clean_text = clean_text.replace('&nbsp;', ' ')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&quot;', '"')
        
        # 연속된 줄바꿈을 최대 2개로 제한
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)
        
        # 각 줄의 앞뒤 공백 제거 (줄바꿈은 유지)
        lines = [line.strip() for line in clean_text.split('\n')]
        clean_text = '\n'.join(lines)
        
        # 전체 텍스트 앞뒤 공백 제거
        clean_text = clean_text.strip()
        
        return clean_text
    
    def find_similar_pattern(self, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        유사한 패턴 검색
        
        Args:
            pattern: 소비 패턴 정보
        
        Returns:
            유사한 패턴 정보 또는 None
        """
        try:
            # 유사도 계산 SQL
            query = text("""
                SELECT 
                    ANALYZE_ID,
                    MONTHLY_INCOME,
                    MONTHLY_EXPENSE,
                    MONTHLY_SURPLUS,
                    EXPENSE_RATIO,
                    SAVINGS_RATIO,
                    ASSET_LEVEL,
                    GPT_ADVICE,
                    USE_COUNT,
                    (
                        -- 소득 차이 (±30% 범위)
                        ABS(MONTHLY_INCOME - :income) / :income * 100 +
                        -- 지출 차이 (±30% 범위)
                        ABS(MONTHLY_EXPENSE - :expense) / :expense * 100 +
                        -- 지출 비율 차이
                        ABS(EXPENSE_RATIO - :expense_ratio) * 5 +
                        -- 저축 비율 차이
                        ABS(SAVINGS_RATIO - :savings_ratio) * 5
                    ) AS similarity_score
                FROM ANALYZE_HISTORY
                WHERE 
                    -- 소득이 ±30% 범위 내
                    MONTHLY_INCOME BETWEEN :income * 0.7 AND :income * 1.3
                    -- 지출이 ±30% 범위 내
                    AND MONTHLY_EXPENSE BETWEEN :expense * 0.7 AND :expense * 1.3
                    -- 자산 수준 동일
                    AND ASSET_LEVEL = :asset_level
                ORDER BY similarity_score ASC
                LIMIT 1
            """)
            
            result = self.session.execute(query, {
                "income": pattern["monthly_income"],
                "expense": pattern["monthly_expense"],
                "expense_ratio": pattern["expense_ratio"],
                "savings_ratio": pattern["savings_ratio"],
                "asset_level": pattern["asset_level"]
            }).fetchone()
            
            if result:
                logger.info(f"[ANALYZE_HISTORY] 유사 패턴 발견 (ID: {result[0]}, 유사도: {result[9]:.2f})")
                
                return {
                    "analyze_id": result[0],
                    "gpt_advice": result[7],
                    "use_count": result[8],
                    "similarity_score": float(result[9])
                }
            else:
                logger.info("[ANALYZE_HISTORY] 유사 패턴 없음 - GPT 호출 필요")
                return None
                
        except Exception as e:
            logger.error(f"[ANALYZE_HISTORY] 유사 패턴 검색 실패: {str(e)}")
            return None
        finally:
            self.session.close()
    def save_gpt_advice(self, pattern: Dict[str, Any], gpt_advice: str) -> bool:
        """
        GPT 조언 저장 (HTML 태그 제거)
        
        Args:
            pattern: 소비 패턴 정보
            gpt_advice: GPT 조언 (HTML 포함 가능)
        
        Returns:
            성공 여부
        """
        try:
            # 🔥 HTML 태그 제거 후 저장
            clean_advice = self._remove_html_tags(gpt_advice)
            
            new_record = AnalyzeHistory(
                monthly_income=pattern["monthly_income"],
                monthly_expense=pattern["monthly_expense"],
                monthly_surplus=pattern["monthly_surplus"],
                expense_ratio=pattern["expense_ratio"],
                savings_ratio=pattern["savings_ratio"],
                essential_ratio=pattern["essential_ratio"],
                leisure_ratio=pattern["leisure_ratio"],
                investment_ratio=pattern["investment_ratio"],
                other_ratio=pattern["other_ratio"],
                asset_level=pattern["asset_level"],
                gpt_advice=clean_advice  # 🔥 순수 텍스트만 저장
            )
            
            self.session.add(new_record)
            self.session.commit()
            
            logger.info(f"✅ [ANALYZE_HISTORY] GPT 조언 저장 완료 (ID: {new_record.analyze_id}, 길이: {len(clean_advice)}자)")
            return True
            
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"[ANALYZE_HISTORY] GPT 조언 저장 실패 (무결성 오류): {str(e)}")
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"[ANALYZE_HISTORY] GPT 조언 저장 실패: {str(e)}")
            return False
        finally:
            self.session.close()

    def increment_use_count(self, analyze_id: int) -> bool:
        """
        사용 횟수 증가
        
        Args:
            analyze_id: 분석 ID
        
        Returns:
            성공 여부
        """
        try:
            record = self.session.query(AnalyzeHistory).filter(
                AnalyzeHistory.analyze_id == analyze_id
            ).first()
            
            if record:
                record.use_count += 1
                self.session.commit()
                logger.debug(f"[ANALYZE_HISTORY] 사용 횟수 증가 (ID: {analyze_id}, Count: {record.use_count})")
                return True
            else:
                logger.warning(f"[ANALYZE_HISTORY] 레코드 없음 (ID: {analyze_id})")
                return False
                
        except Exception as e:
            self.session.rollback()
            logger.error(f"[ANALYZE_HISTORY] 사용 횟수 증가 실패: {str(e)}")
            return False
        finally:
            self.session.close()

    def get_total_count(self) -> int:
        """
        전체 레코드 수 조회
        
        Returns:
            레코드 수
        """
        try:
            count = self.session.query(AnalyzeHistory).count()
            logger.debug(f"[ANALYZE_HISTORY] 전체 레코드 수: {count}")
            return count
        except Exception as e:
            logger.error(f"[ANALYZE_HISTORY] 레코드 수 조회 실패: {str(e)}")
            return 0
        finally:
            self.session.close()