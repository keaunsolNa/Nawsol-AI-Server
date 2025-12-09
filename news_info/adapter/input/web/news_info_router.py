from fastapi import APIRouter

from news_info.application.factory.fetch_news_info_usecase_factory import FetchNewsInfoUsecaseFactory

news_info_router = APIRouter(tags=["news_info"])

@news_info_router.get("/fetch")
async def fetch_news_info(query: str, display: int = 10, start: int = 1, sort: str = "date",
                          finance_only: bool = True, include_content: bool = True, require_content: bool = True):
    usecase = FetchNewsInfoUsecaseFactory.create()
    result = await usecase.execute(
        query=query,
        display=display,
        start=start,
        sort=sort,
        finance_only=finance_only,
        include_content=include_content,
        require_content=require_content
    )

    return {
        "source": result.source.name,
        "fetched_at": result.fetched_at.timestamp.isoformat(),
        "items": [
            {
                "title": item.title,
                "description": item.description,
                "content": item.content,
                "link": item.link,
                "originallink": item.originallink,
                "published_at": item.published_at.timestamp.isoformat(),
            }
            for item in result.items
        ]
    }

@news_info_router.get("/latest")
async def get_latest_news(
    limit: int = 10,
    display_per_query: int = 20,
    sort: str = "date",
    finance_only: bool = True,
    include_content: bool = True,
    require_content: bool = True,
):
    usecase = FetchNewsInfoUsecaseFactory.create()
    items = await usecase.execute_latest_save(
        limit=limit,
        display_per_query=display_per_query,
        sort=sort,
        finance_only=finance_only,
        include_content=include_content,
        require_content=require_content,
    )

    return {
        "message": "최신 금융 기사 크롤링 및 저장 완료",
        "saved_count": len(items),
        "items": [
            {
                "title": it.title,
                "description": it.description,
                "content": it.content,
                "link": it.link,
                "originallink": it.originallink,
                "published_at": it.published_at.timestamp.isoformat(),
            }
            for it in items
        ],
    }