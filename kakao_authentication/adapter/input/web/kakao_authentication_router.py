import os
import uuid
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from account.application.usecase.account_usecase import AccountUseCase
from account.infrastructure.repository.account_repository_impl import AccountRepositoryImpl
from config.redis_config import get_redis
from kakao_authentication.application.usecase.kakao_oauth_usecase import KakaoOAuthUseCase
from kakao_authentication.infrastructure.client.kakao_oauth_client import KakaoOAuthClient
from util.log.log import Log
from util.security.crsf import CSRF_COOKIE_NAME, generate_csrf_token

kakao_authentication_router = APIRouter()

# Infrastructure
kakao_client = KakaoOAuthClient()
kakao_usecase = KakaoOAuthUseCase(kakao_client)

account_repository = AccountRepositoryImpl()
account_usecase = AccountUseCase(account_repository)

redis_client = get_redis()

CORS_ALLOWED_FRONTEND_URL = os.getenv("CORS_ALLOWED_FRONTEND_URL")

logger = Log.get_logger()

@kakao_authentication_router.get("/login")
async def redirect_to_kakao():
    login_url = kakao_usecase.get_authorization_url()
    logger.debug(f"Redirecting to Kakao: {login_url}")
    return RedirectResponse(login_url)

@kakao_authentication_router.get("/redirection")
async def kakao_redirect(code: str):
    logger.debug("Kakao redirect called")

    # 카카오 사용자 조회 (VO 포함)
    result = kakao_usecase.get_kakao_user(code)

    kakao_user = result["user"]          # KakaoUser
    access_token = result["access_token"]  # str

    # session_id 생성
    session_id = str(uuid.uuid4())
    logger.debug("Generated session_id")

    logger.debug(f"Kakao User ID: {kakao_user.user_id.value}")
    logger.debug(f"Kakao Email: {kakao_user.email.value}")

    # Account 생성 또는 조회
    session_id = await kakao_usecase.create_or_get_account(
        kakao_user, session_id
    )

    print(f"[DEBUG] Generated session_id:", session_id)

    # Redis에 session 저장 (1시간 TTL)
    redis_client.hset(
        session_id,
        "USER_TOKEN",
        access_token,
    )
    redis_client.expire(session_id, 24 * 60 * 60)

    logger.debug(f"Kakao User ID: {session_id}")
    logger.debug("Session saved in Redis: %s", redis_client.exists(session_id))

    logger.debug("CSRF token generated")

    # CSRF 토큰 생성
    csrf_token = generate_csrf_token()
    logger.debug("CSRF token generated")

    # 브라우저 쿠키 발급
    response = RedirectResponse(CORS_ALLOWED_FRONTEND_URL)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,  # HTTPS 필수
        samesite="lax",  # cross-site 리다이렉트 허용
        max_age=86400
    )

    # CSRF 토큰 쿠키 발급
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=False,
        samesite="lax",
        max_age=3600
    )

    logger.debug(f"response: {response}")
    logger.debug("Cookie set in RedirectResponse directly")
    return response
