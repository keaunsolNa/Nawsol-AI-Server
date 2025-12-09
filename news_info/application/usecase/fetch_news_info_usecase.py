from typing import List

from news_info.application.port.news_info_repository_port import NewsInfoRepositoryPort
from news_info.domain.value_object.news_info import NewsInfo
from news_info.domain.value_object.news_item import NewsItem
from news_info.adapter.output.naver.news_info_api_adapter import NaverNewsInfoAdapter


class FetchNewsInfoUsecase:
    def __init__(self, adapter: NaverNewsInfoAdapter, repository: NewsInfoRepositoryPort):
        self.adapter = adapter
        self.repository = repository

    async def execute(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "date",
        finance_only: bool = True,
        include_content: bool = True,
        require_content: bool = True,
    ) -> NewsInfo:
        return await self.adapter.fetch_news_info(
            query=query,
            display=display,
            start=start,
            sort=sort,
            finance_only=finance_only,
            include_content=include_content,
            require_content=require_content,
        )

    async def execute_latest_save(
        self,
        limit: int = 10,
        display_per_query: int = 20,
        sort: str = "date",
        finance_only: bool = True,
        include_content: bool = True,
        require_content: bool = True,
    ) -> List[NewsItem]:
        news_info = await self.adapter.fetch_latest_finance_news(
            limit=limit,
            display_per_query=display_per_query,
            sort=sort,
            finance_only=finance_only,
            include_content=include_content,
            require_content=require_content,
        )

        if news_info.items:
            await self.repository.save_news_batch(news_info.items)

        return news_info.items