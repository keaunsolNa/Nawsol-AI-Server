from ...adapter.output.naver.market_data_api_adapter import NaverMarketDataAdapter
from ...domain.market_data import MarketData

class FetchMarketDataUsecase:
    def __init__(self, adapter: NaverMarketDataAdapter):
        self.adapter = adapter

    async def execute(self, query: str) -> MarketData:
        return await self.adapter.fetch_market_data(query)
