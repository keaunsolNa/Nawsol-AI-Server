import os

import aiohttp
from util.cache.ai_cache import logger


class NaverShoppingClient:
    NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

    async def search_items(self, query: str, display: int = 10) -> list[dict]:
        url = f"https://openapi.naver.com/v1/search/shop.json?query={query}&display={display}"
        headers = {
            "X-Naver-Client-Id": self.NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": self.NAVER_CLIENT_SECRET,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    raise Exception(f"Naver API Error {resp.status}")
                data = await resp.json()

        items = data.get("items", [])

        logger.info(f"Naver API search result for '{query}': {items}")
        for i, item in enumerate(items, start=1):
            logger.info(f"[{i}] {item}")
        logger.info("--- End of result ---")

        return items
