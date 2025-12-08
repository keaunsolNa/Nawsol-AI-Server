from datetime import datetime
from typing import List

from market_data.domain.market_data import MarketData
from market_data.domain.market_item import MarketItem
from market_data.domain.value_object.market_price import MarketPrice
from market_data.domain.value_object.market_source import MarketSource
from market_data.infrastructure.api.naver_shopping_client import NaverShoppingClient


class NaverMarketDataAdapter:
    def __init__(self):
        self.client = NaverShoppingClient()

    async def fetch_market_data(self, query: str) -> MarketData:
        raw_items = await self.client.search_items(query)
        from market_data.domain.value_object.timestamp import Timestamp
        items: List[MarketItem] = [
            MarketItem(
                product_id=item.get("productId", ""),
                name=item.get("title", ""),
                price=MarketPrice(float(item.get("lprice", 0))),
                timestamp=Timestamp(datetime.now())
            )
            for item in raw_items
        ]
        return MarketData(
            items=items,
            source=MarketSource("NaverAPI"),
            fetched_at=Timestamp(datetime.now())
        )
