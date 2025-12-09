from typing import Dict
from datetime import datetime

from config.crypto import Crypto
from config.redis_config import get_redis
from ieinfo.infrastructure.orm.ie_info import IEInfo, IEType
from ieinfo.infrastructure.repository.ie_info_repository_impl import IEInfoRepositoryImpl
from util.log.log import Log

logger = Log.get_logger()


class IEInfoUseCase:
    __Instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__Instance is None:
            cls.__Instance = super().__new__(cls)
        return cls.__Instance

    @classmethod
    def get_instance(cls):
        if cls.__Instance is None:
            cls.__Instance = cls()
        return cls.__Instance
    
    def __init__(self):
        if not hasattr(self, 'repository'):
            self.repository = IEInfoRepositoryImpl.get_instance()
            self.redis_client = get_redis()
            self.crypto = Crypto.get_instance()
    
    def save_ie_data_from_redis(self, session_id: str, year: int, month: int) -> Dict:
        """
        Redis의 세션 데이터를 IE_INFO 테이블에 저장
        
        Args:
            session_id: 사용자 세션 ID
            year: 저장할 연도
            month: 저장할 월
        
        Returns:
            저장 결과 정보
        """
        try:
            # Redis에서 데이터 가져오기
            encrypted_data = self.redis_client.hgetall(session_id)
            
            if not encrypted_data:
                logger.warning(f"No data found in Redis for session: {session_id}")
                return {
                    "success": False,
                    "message": "Redis에 저장된 데이터가 없습니다."
                }
            
            # 기존 데이터 삭제 (중복 방지)
            self.repository.delete_by_session_and_month(session_id, year, month)
            
            # IE_INFO 객체 리스트 생성
            ie_info_list = []
            skipped_count = 0
            
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
                        logger.warning(f"Invalid key format: {key_plain}")
                        skipped_count += 1
                        continue
                    
                    doc_type, field_name = key_plain.split(":", 1)
                    
                    # IE_Type 결정
                    if "소득" in doc_type or "income" in doc_type.lower():
                        ie_type = IEType.INCOME
                    elif "지출" in doc_type or "expense" in doc_type.lower():
                        ie_type = IEType.EXPENSE
                    else:
                        logger.warning(f"Unknown document type: {doc_type}")
                        skipped_count += 1
                        continue
                    
                    # 금액 값 정수 변환
                    try:
                        value_int = int(value_plain.replace(",", ""))
                    except (ValueError, AttributeError):
                        logger.warning(f"Invalid value for {field_name}: {value_plain}")
                        skipped_count += 1
                        continue
                    
                    # IE_INFO 객체 생성
                    ie_info = IEInfo(
                        session_id=session_id,
                        ie_type=ie_type,
                        key=field_name,
                        value=value_int,
                        year=year,
                        month=month
                    )
                    ie_info_list.append(ie_info)
                    
                except Exception as e:
                    logger.error(f"Error processing item: {str(e)}")
                    skipped_count += 1
                    continue
            
            # DB에 일괄 저장
            if ie_info_list:
                self.repository.bulk_insert(ie_info_list)
                logger.info(f"Saved {len(ie_info_list)} items to IE_INFO table")
                
                return {
                    "success": True,
                    "message": "데이터가 성공적으로 저장되었습니다.",
                    "saved_count": len(ie_info_list),
                    "skipped_count": skipped_count,
                    "year": year,
                    "month": month
                }
            else:
                logger.warning("No valid items to save")
                return {
                    "success": False,
                    "message": "저장할 수 있는 유효한 데이터가 없습니다.",
                    "skipped_count": skipped_count
                }
                
        except Exception as e:
            logger.error(f"Failed to save IE data: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"데이터 저장 중 오류가 발생했습니다: {str(e)}"
            }

