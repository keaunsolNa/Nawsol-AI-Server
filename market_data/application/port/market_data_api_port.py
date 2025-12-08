from abc import ABC, abstractmethod
from typing import List

from market_data.domain.market_item import MarketItem


class MarketDataAPIPort(ABC):
    @abstractmethod
    async def fetch_market_data(self, query: str) -> List[MarketItem]:
        pass
