import os
import aiohttp
from typing import Any

from util.cache.ai_cache import logger


class NaverNewsClient:
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

    async def search_news(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "date",
    ) -> list[dict[str, Any]]:
        url = "https://openapi.naver.com/v1/search/news.json"
        headers = {
            "X-Naver-Client-Id": self.NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": self.NAVER_CLIENT_SECRET,
        }
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort,
        }

        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise Exception(f"Naver News API Error {resp.status}: {body}")
                data = await resp.json()

        items = data.get("items", []) or []

        logger.info(f"Naver News API search result for '{query}': {len(items)} items")
        for i, item in enumerate(items, start=1):
            logger.info(f"[{i}] {item}")
        logger.info("--- End of result ---")

        return items