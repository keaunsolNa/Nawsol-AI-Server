from typing import Dict
from datetime import datetime, timedelta
from config.crypto import Crypto
from config.redis_config import get_redis
from ieinfo.infrastructure.repository.ie_info_repository_impl import IEInfoRepositoryImpl
from ieinfo.infrastructure.orm.ie_info import IEType
from product.infrastructure.repository.product_repository_impl import ProductRepositoryImpl
from recommendation.domain.service.fund_recommendation_service import FundRecommendationService

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class FundRecommendationUseCase:

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
        if not hasattr(self, 'initialized'):
            self.ie_repository = IEInfoRepositoryImpl.get_instance()
            self.product_repository = ProductRepositoryImpl.get_instance()
            self.redis_client = get_redis()
            self.crypto = Crypto.get_instance()
            self.initialized = True

    def _get_financial_data_from_db(self, session_id: str, year: int, month: int) -> Dict:
        """DB에서 자산 정보 가져오기 (로그인 사용자)"""
        try:
            # DB에서 데이터 조회
            ie_records = self.ie_repository.get_by_session(session_id, year, month)
            
            income_data = {}
            expense_data = {}
            total_income = 0
            total_expense = 0
            
            for record in ie_records:
                if record.ie_type == IEType.INCOME:
                    income_data[record.key] = record.value
                    total_income += record.value
                elif record.ie_type == IEType.EXPENSE:
                    expense_data[record.key] = record.value
                    total_expense += record.value
            
            surplus = total_income - total_expense
            
            logger.info(f"Loaded financial data from DB: {len(ie_records)} records")
            
            return {
                "income_data": income_data,
                "expense_data": expense_data,
                "total_income": total_income,
                "total_expense": total_expense,
                "surplus": surplus,
                "source": "database"
            }
            
        except Exception as e:
            logger.error(f"Error loading data from DB: {str(e)}")
            return None            

    def _get_financial_data_from_redis(self, session_id: str) -> Dict:
        """Redis에서 자산 정보 가져오기 (비로그인 사용자)"""
        try:
            encrypted_data = self.redis_client.hgetall(session_id)
            
            if not encrypted_data:
                logger.warning(f"No data found in Redis for session: {session_id}")
                return None
            
            income_data = {}
            expense_data = {}
            total_income = 0
            total_expense = 0
            
            for key_bytes, value_bytes in encrypted_data.items():
                try:
                    # bytes를 문자열로 변환
                    if isinstance(key_bytes, bytes):
                        key_str = key_bytes.decode('utf-8')
                    else:
                        key_str = str(key_bytes)
                    
                    if isinstance(value_bytes, bytes):
                        value_str = value_bytes.decode('utf-8')
                    else:
                        value_str = str(value_bytes)
                    
                    # USER_TOKEN 제외
                    if key_str == "USER_TOKEN":
                        continue
                    
                    # 복호화
                    key_plain = self.crypto.dec_data(key_str)
                    value_plain = self.crypto.dec_data(value_str)
                    
                    # "타입:필드명" 형태 파싱
                    if ":" not in key_plain:
                        continue
                    
                    doc_type, field_name = key_plain.split(":", 1)
                    value_int = int(value_plain.replace(",", ""))
                    
                    if "소득" in doc_type or "income" in doc_type.lower():
                        income_data[field_name] = value_int
                        total_income += value_int
                    elif "지출" in doc_type or "expense" in doc_type.lower():
                        expense_data[field_name] = value_int
                        total_expense += value_int
                        
                except Exception as e:
                    logger.warning(f"Error processing Redis item: {str(e)}")
                    continue
            
            surplus = total_income - total_expense
            
            logger.info(f"Loaded financial data from Redis: income={len(income_data)}, expense={len(expense_data)}")
            
            return {
                "income_data": income_data,
                "expense_data": expense_data,
                "total_income": total_income,
                "total_expense": total_expense,
                "surplus": surplus,
                "source": "redis"
            }
            
        except Exception as e:
            logger.error(f"Error loading data from Redis: {str(e)}")
            return None

    async def get_fund_recommendation(
        self,
        session_id: str,
        year: int = None,
        month: int = None,
        investment_goal: str = None,
        risk_tolerance: str = None
    ) -> Dict:
        """
        ETF 추천 메인 메서드
        
        Args:
            session_id: 사용자 세션 ID
            year: 조회 연도 (DB용, 선택)
            month: 조회 월 (DB용, 선택)
            investment_goal: 투자 목표
            risk_tolerance: 위험 감수도
        
        Returns:
            추천 결과 딕셔너리
        """
        try:
            # 1. 로그인 여부 확인
            user_token = self.redis_client.hget(session_id, "USER_TOKEN")
            
            if isinstance(user_token, bytes):
                user_token = user_token.decode('utf-8')
            
            is_logged_in = user_token and user_token != "GUEST"
            
            #logger.info(f"User logged in: {is_logged_in}")
            
            # 2. 자산 정보 가져오기
            financial_data = None
            
            if is_logged_in and year and month:
                # 로그인 사용자 - DB에서 조회
                financial_data = self._get_financial_data_from_db(session_id, year, month)
                if not financial_data:
                    # DB에 데이터가 없으면 Redis 시도
                    logger.warning("No data in DB, trying Redis...")
                    financial_data = self._get_financial_data_from_redis(session_id)
            else:
                # 비로그인 사용자 또는 연도/월 미지정 - Redis에서 조회
                financial_data = self._get_financial_data_from_redis(session_id)
            
            if not financial_data:
                return {
                    "success": False,
                    "message": "자산 정보를 찾을 수 없습니다. 먼저 소득/지출 데이터를 입력해주세요."
                }
            
            # 3. Fund 데이터 가져오기
            fund_records = self.product_repository.get_all_fund()

            # 3-1. Fund 데이터가 없으면 자동으로 외부 API에서 가져와 저장
            if not fund_records:
                logger.warning("No Fund data in database. Auto-fetching from external API...")
                try:
                    from product.application.factory.fetch_product_data_usecase_factory import FetchProductDataUsecaseFactory
                    fetch_usecase = FetchProductDataUsecaseFactory.create()
                    
                    # 현재 날짜부터 최대 7일 전까지 시도 (주말/공휴일 고려)
                    today = datetime.now()
                    fund_entities = None
                    
                    for days_ago in range(7):
                        target_date = (today - timedelta(days=days_ago)).strftime("%Y%m%d")
                        logger.info(f"Trying to fetch Fund data for date: {target_date}")
                        
                        try:
                            # Fund 데이터 가져오기 (start, end 파라미터 전달)
                            fund_entities = await fetch_usecase.fetch_and_save_fund_data(start=target_date, end=target_date)
                            
                            if fund_entities and len(fund_entities) > 0:
                                logger.info(f"Successfully fetched {len(fund_entities)} Fund records for {target_date}")
                                break
                            else:
                                logger.warning(f"No Fund data found for {target_date}, trying previous day...")
                        except Exception as date_error:
                            logger.warning(f"Failed to fetch Fund data for {target_date}: {str(date_error)}")
                            continue

                    if fund_entities and len(fund_entities) > 0:
                        logger.info(f"Successfully auto-saved {len(fund_entities)} Fund records")
                        # 다시 DB에서 조회
                        fund_records = self.product_repository.get_all_fund()
                    else:
                        logger.error("Failed to auto-fetch Fund data - no data found for the past 7 days")
                except Exception as fetch_error:
                    logger.error(f"Error auto-fetching Fund data: {str(fetch_error)}")
                    import traceback
                    traceback.print_exc()

            if not fund_records:
                return {
                    "success": False,
                    "message": "Fund 데이터를 불러올 수 없습니다."
                }
            
            # Fund 데이터를 딕셔너리 형태로 변환
            fund_data = []
            for fund in fund_records:
                fund_data.append({
                    "fndNm": fund.fndNm,    # 펀드명
                    "ctg": fund.ctg,        # 구분
                    "setpDt": fund.setpDt,  # 설정일
                    "fndTp": fund.fndTp,    # 펀드유형
                    "prdClsfCd": fund.prdClsfCd,    # 상품분류코드
                    "asoStdCd": fund.asoStdCd       # 협회표준코드        
                })
            
            logger.info(f"Loaded {len(fund_data)} Fund records")
            
            # 4. AI 추천 실행
            recommendation_result = await FundRecommendationService.recommend_fund(
                income_data=financial_data["income_data"],
                expense_data=financial_data["expense_data"],
                total_income=financial_data["total_income"],
                total_expense=financial_data["total_expense"],
                surplus=financial_data["surplus"],
                fund_data=fund_data,
                investment_goal=investment_goal,
                risk_tolerance=risk_tolerance
            )

            # 5. 프론트엔드 인터페이스에 맞게 응답 형식 변환
            if recommendation_result.get("success"):
                # 추천된 ETF를 상위 N개로 제한 (프론트엔드 표시용)
                recommended_funds = fund_records[:10]  # 상위 10개 Fund

                return {
                    "success": True,
                    "total_income": financial_data["total_income"],
                    "total_expense": financial_data["total_expense"],
                    "available_amount": financial_data["surplus"],
                    "recommendation_reason": recommendation_result.get("recommendation", ""),
                    "recommended_funds": [
                        {
                            "basDt": fund.basDt.isoformat() if hasattr(fund.basDt, 'isoformat') else str(fund.basDt),
                            "srtnCd": fund.srtnCd,
                            "fndNm": fund.fndNm,
                            "ctg": fund.ctg,
                            "setpDt": fund.setpDt,
                            "fndTp": fund.fndTp,
                            "prdClsfCd": fund.prdClsfCd,
                            "asoStdCd": fund.asoStdCd
                        } for etf in recommended_funds
                    ],
                    "data_source": financial_data["source"],
                    "is_logged_in": is_logged_in
                }
            else:
                return recommendation_result
            
        except Exception as e:
            logger.error(f"Error in Fund recommendation usecase: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Fund 추천 중 오류가 발생했습니다: {str(e)}"
            }