import os

from dotenv import load_dotenv

from finance.adapter.input.web.finance_router import finance_router
from kakao_authentication.adapter.input.web.kakao_authentication_router import kakao_authentication_router
from market_data.adapter.input.web.market_data_router import market_data_router

load_dotenv()

from product.adapter.input.web.product_data_router.product_data_router import product_data_router
from account.adapter.input.web.account_router import account_router
from config.database.session import Base, engine
from documents_multi_agents.adapter.input.web.document_multi_agent_router import documents_multi_agents_router
from ecos.adapter.input.web.ecos_data_router.ecos_data_router import ecos_data_router
from ieinfo.adapter.input.web.ie_info_router import ie_info_router
from kftc.adapter.input.web.kftc_router import kftc_router
from sosial_oauth.adapter.input.web.google_oauth2_router import authentication_router
from recommendation.adapter.output.web.etf_recommendation_router import etf_recommendation_router
from recommendation.adapter.output.web.fund_recommendation_router import fund_recommendation_router
from recommendation.adapter.output.web.bond_recommendation_router import bond_recommendation_router
from recommendation.adapter.output.web.card_news_router import card_news_recommendation
from today_briefing.adapter.output.web.briefing_router import today_briefing_router
from news_info.adapter.input.web.news_info_router import news_info_router
from community.adapter.input.web.community_router import community_router
from jobs import scheduler as jobs_scheduler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
CORS_ALLOWED_FRONTEND_URL = os.getenv("CORS_ALLOWED_FRONTEND_URL")

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    # .env가 이미 로드되어 있다고 가정
    jobs_scheduler.start_scheduler()

@app.on_event("shutdown")
async def on_shutdown():
    jobs_scheduler.stop_scheduler()

origins = [
    CORS_ALLOWED_FRONTEND_URL,  # Next.js 프론트 엔드 URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # 정확한 origin만 허용
    allow_credentials=True,      # 쿠키 허용
    allow_methods=["*"],         # 모든 HTTP 메서드 허용
    allow_headers=["*"],         # 모든 헤더 허용
)

app.include_router(account_router, prefix="/account")
app.include_router(authentication_router, prefix="/authentication")
app.include_router(documents_multi_agents_router, prefix="/documents-multi-agents")
app.include_router(documents_multi_agents_router, prefix="/flow")  # 프론트엔드 호환용
app.include_router(kftc_router, prefix="/kftc")
app.include_router(ecos_data_router, prefix="/ecos")
app.include_router(ie_info_router, prefix="/ie_info")
app.include_router(product_data_router, prefix="/product")
app.include_router(market_data_router, prefix="/market-data")
app.include_router(finance_router, prefix="/finance")
app.include_router(etf_recommendation_router, prefix="/etf-recommendation")
app.include_router(fund_recommendation_router, prefix="/fund-recommendation")
app.include_router(bond_recommendation_router, prefix="/bond-recommendation")
app.include_router(card_news_recommendation, prefix="/card-news-recommendation")
app.include_router(today_briefing_router, prefix="/today-briefing")
app.include_router(news_info_router, prefix="/news_info")
app.include_router(community_router, prefix="/community")
app.include_router(kakao_authentication_router, prefix="/kakao-authentication")

# 앱 실행
if __name__ == "__main__":
    import uvicorn
    from ieinfo.infrastructure.orm.ie_rule import IERule
    from ieinfo.infrastructure.orm.ie_info import IEType
    from asset_allocation.infrastructure.orm.analyze_history import AnalyzeHistory  # 🔥 추가
    from sqlalchemy import select
    
    host = os.getenv("APP_HOST")
    port = int(os.getenv("APP_PORT"))
    
    # 🔥 IE_RULE 데이터 백업 (서버 재시작해도 유지)
    backup_rules = []
    try:
        with engine.connect() as conn:
            # IE_RULE 테이블이 존재하면 데이터 백업
            result = conn.execute(select(IERule))
            backup_rules = [
                {'keyword': row.keyword, 'ie_type': row.ie_type}
                for row in result
            ]
            print(f"📦 IE_RULE 백업: {len(backup_rules)}개 규칙")
    except Exception as e:
        print(f"⚠️  IE_RULE 백업 실패 (첫 실행일 수 있음): {str(e)}")
    
    # 모든 테이블 삭제 및 재생성
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # 🔥 IE_RULE 데이터 복구 또는 초기 데이터 삽입
    from sqlalchemy.orm import Session
    session = Session(bind=engine)
    
    if backup_rules:
        # 백업 데이터가 있으면 복구
        try:
            for rule_data in backup_rules:
                new_rule = IERule(
                    keyword=rule_data['keyword'],
                    ie_type=rule_data['ie_type']
                )
                session.add(new_rule)
            
            session.commit()
            print(f"✅ IE_RULE 복구 완료: {len(backup_rules)}개 규칙")
        except Exception as e:
            session.rollback()
            print(f"❌ IE_RULE 복구 실패: {str(e)}")
    else:
        # 백업 데이터가 없으면 초기 데이터 자동 삽입
        print("🎯 백업 데이터 없음 → 초기 키워드 자동 삽입")
        
        # 초기 소득 키워드
        INITIAL_INCOME_KEYWORDS = [
            "급여", "월급", "연봉", "봉급", "임금",
            "상여", "상여금", "보너스", "성과급", "인센티브",
            "수당", "식대", "교통비", "주거수당",
            "이자", "배당", "배당금", "이자소득"
        ]
        
        # 초기 지출 키워드
        INITIAL_EXPENSE_KEYWORDS = [
            "보험료", "국민연금", "건강보험", "고용보험", "산재보험",
            "세금", "소득세", "지방소득세", "주민세",
            "카드", "신용카드", "체크카드", "카드사용액",
            "공제", "공제액", "차감"
        ]
        
        try:
            # 소득 키워드 삽입
            for keyword in INITIAL_INCOME_KEYWORDS:
                rule = IERule(keyword=keyword, ie_type=IEType.INCOME)
                session.add(rule)
            
            # 지출 키워드 삽입
            for keyword in INITIAL_EXPENSE_KEYWORDS:
                rule = IERule(keyword=keyword, ie_type=IEType.EXPENSE)
                session.add(rule)
            
            session.commit()
            total = len(INITIAL_INCOME_KEYWORDS) + len(INITIAL_EXPENSE_KEYWORDS)
            print(f"✅ 초기 키워드 삽입 완료: {total}개 (소득 {len(INITIAL_INCOME_KEYWORDS)}개, 지출 {len(INITIAL_EXPENSE_KEYWORDS)}개)")
        except Exception as e:
            session.rollback()
            print(f"❌ 초기 키워드 삽입 실패: {str(e)}")
    
    session.close()
    
    uvicorn.run(app, host=host, port=port)
