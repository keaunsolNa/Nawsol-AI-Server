from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from account.adapter.input.web.session_helper import get_current_user
from config.redis_config import get_redis
from ieinfo.application.usecase.ie_info_usecase import IEInfoUseCase
from util.log.log import Log

logger = Log.get_logger()
ie_info_router = APIRouter(tags=["ie_info_router"])
usecase = IEInfoUseCase().get_instance()
redis_client = get_redis()


@ie_info_router.post("/save")
async def save_ie_data_to_db(
    year: int = None,
    month: int = None,
    session_id: str = Depends(get_current_user)
):
    """
    Redis의 소득/지출 데이터를 DB(IE_INFO)에 저장
    
    Args:
        year: 저장할 연도 (기본값: 현재 연도)
        month: 저장할 월 (기본값: 현재 월)
        session_id: 사용자 세션 ID (자동 주입)
    
    Returns:
        저장 결과
    """
    try:
        # 로그인 여부 확인
        user_token = redis_client.hget(session_id, "USER_TOKEN")
        
        if not user_token:
            raise HTTPException(
                status_code=401,
                detail="세션이 만료되었습니다. 다시 로그인해주세요."
            )
        
        # GUEST 사용자는 DB 저장 불가
        if isinstance(user_token, bytes):
            user_token = user_token.decode('utf-8')
        
        if user_token == "GUEST":
            raise HTTPException(
                status_code=403,
                detail="로그인한 사용자만 데이터를 저장할 수 있습니다."
            )
        
        # 연도/월 기본값 설정
        now = datetime.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        # 데이터 저장
        result = usecase.save_ie_data_from_redis(session_id, year, month)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in save_ie_data_to_db: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
