"""
ETF 추천 UseCase
로그인 여부에 따라 DB 또는 Redis에서 자산 정보를 가져와 ETF 추천
"""
from typing import Dict, List
from datetime import datetime, timedelta
from config.crypto import Crypto
from config.redis_config import get_redis
from ieinfo.infrastructure.repository.ie_info_repository_impl import IEInfoRepositoryImpl
from ieinfo.infrastructure.orm.ie_info import IEType
from product.infrastructure.repository.product_repository_impl import ProductRepositoryImpl
from recommendation.domain.service.etf_recommendation_service import ETFRecommendationService
from util.log.log import Log

logger = Log.get_logger()


class ETFRecommendationUseCase:
    """ETF 추천 UseCase"""
    
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
    
    async def get_etf_recommendation(
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
            
            logger.info(f"User logged in: {is_logged_in}")
            
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
            
            # 3. ETF 데이터 가져오기
            etf_records = self.product_repository.get_all_etf()

            # 3-1. ETF 데이터가 없으면 자동으로 외부 API에서 가져와 저장
            if not etf_records:
                logger.warning("No ETF data in database. Auto-fetching from external API...")
                try:
                    from product.application.factory.fetch_product_data_usecase_factory import FetchProductDataUsecaseFactory
                    fetch_usecase = FetchProductDataUsecaseFactory.create()
                    
                    # 현재 날짜부터 최대 7일 전까지 시도 (주말/공휴일 고려)
                    today = datetime.now()
                    etf_entities = None
                    
                    for days_ago in range(7):
                        target_date = (today - timedelta(days=days_ago)).strftime("%Y%m%d")
                        logger.info(f"Trying to fetch ETF data for date: {target_date}")
                        
                        try:
                            # ETF 데이터 가져오기 (start, end 파라미터 전달)
                            etf_entities = await fetch_usecase.fetch_and_save_etf_data(start=target_date, end=target_date)
                            
                            if etf_entities and len(etf_entities) > 0:
                                logger.info(f"Successfully fetched {len(etf_entities)} ETF records for {target_date}")
                                break
                            else:
                                logger.warning(f"No ETF data found for {target_date}, trying previous day...")
                        except Exception as date_error:
                            logger.warning(f"Failed to fetch ETF data for {target_date}: {str(date_error)}")
                            continue

                    if etf_entities and len(etf_entities) > 0:
                        logger.info(f"Successfully auto-saved {len(etf_entities)} ETF records")
                        # 다시 DB에서 조회
                        etf_records = self.product_repository.get_all_etf()
                    else:
                        logger.error("Failed to auto-fetch ETF data - no data found for the past 7 days")
                except Exception as fetch_error:
                    logger.error(f"Error auto-fetching ETF data: {str(fetch_error)}")
                    import traceback
                    traceback.print_exc()

            if not etf_records:
                return {
                    "success": False,
                    "message": "ETF 데이터를 불러올 수 없습니다."
                }
            
            # ETF 데이터를 딕셔너리 형태로 변환
            etf_data = []
            for etf in etf_records:
                etf_data.append({
                    "bssIdxIdxNm": etf.bssIdxIdxNm,
                    "clpr": etf.clpr,
                    "fltRt": etf.fltRt,
                    "mrktTotAmt": etf.mrktTotAmt,
                    "nav": etf.nav,
                    "trPrc": etf.trPrc
                })
            
            logger.info(f"Loaded {len(etf_data)} ETF records")
            
            # 4. AI 추천 실행
            recommendation_result = await ETFRecommendationService.recommend_etf(
                income_data=financial_data["income_data"],
                expense_data=financial_data["expense_data"],
                total_income=financial_data["total_income"],
                total_expense=financial_data["total_expense"],
                surplus=financial_data["surplus"],
                etf_data=etf_data,
                investment_goal=investment_goal,
                risk_tolerance=risk_tolerance
            )

            # 5. 프론트엔드 인터페이스에 맞게 응답 형식 변환
            if recommendation_result.get("success"):
                # 추천된 ETF를 3~10개로 제한
                total_etfs = len(etf_records)
                min_etfs = min(3, total_etfs)  # 최소 3개 (또는 전체 개수)
                max_etfs = min(10, total_etfs)  # 최대 10개 (또는 전체 개수)
                
                # 실제로는 GPT가 추천한 ETF를 사용해야 하지만, 
                # 현재는 상위 N개 ETF를 사용 (시가총액 기준 정렬된 상태)
                recommended_count = max_etfs  # 최대 10개까지
                recommended_etfs = etf_records[:recommended_count]
                
                # 저축률 계산
                surplus_ratio = round(financial_data["surplus"] / financial_data["total_income"] * 100, 1) if financial_data["total_income"] > 0 else 0

                return {
                    "success": True,
                    "total_income": financial_data["total_income"],
                    "total_expense": financial_data["total_expense"],
                    "available_amount": financial_data["surplus"],
                    "surplus_ratio": surplus_ratio,
                    "recommendation_reason": recommendation_result.get("recommendation", ""),
                    "recommended_etfs": [
                        {
                            "fltRt": etf.fltRt,
                            "nav": etf.nav,
                            "mkp": etf.mkp,
                            "hipr": etf.hipr,
                            "lopr": etf.lopr,
                            "trqu": etf.trqu,
                            "trPrc": etf.trPrc,
                            "mrktTotAmt": etf.mrktTotAmt,
                            "nPptTotAmt": etf.nPptTotAmt,
                            "stLstgCnt": etf.stLstgCnt,
                            "bssIdxIdxNm": etf.bssIdxIdxNm,
                            "bssIdxClpr": etf.bssIdxClpr,
                            "basDt": etf.basDt.isoformat() if hasattr(etf.basDt, 'isoformat') else str(etf.basDt),
                            "clpr": etf.clpr,
                            "vs": etf.vs
                        } for etf in recommended_etfs
                    ],
                    "data_source": financial_data["source"],
                    "is_logged_in": is_logged_in
                }
            else:
                return recommendation_result
            
        except Exception as e:
            logger.error(f"Error in ETF recommendation usecase: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"ETF 추천 중 오류가 발생했습니다: {str(e)}"
            }
