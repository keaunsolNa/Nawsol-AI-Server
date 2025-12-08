from ..usecase.fetch_market_data_usecase import FetchMarketDataUsecase
from ...adapter.output.naver.market_data_api_adapter import NaverMarketDataAdapter


class FetchMarketDataUsecaseFactory:
    @staticmethod
    def create() -> FetchMarketDataUsecase:
        api_adapter = NaverMarketDataAdapter()
        return FetchMarketDataUsecase(api_adapter)
