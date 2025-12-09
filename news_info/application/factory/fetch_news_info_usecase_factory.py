from news_info.application.usecase.fetch_news_info_usecase import FetchNewsInfoUsecase
from news_info.adapter.output.naver.news_info_api_adapter import NaverNewsInfoAdapter
from news_info.infrastructure.repository.news_info_repository_impl import NewsInfoRepositoryImpl


class FetchNewsInfoUsecaseFactory:
    @staticmethod
    def create() -> FetchNewsInfoUsecase:
        api_adapter = NaverNewsInfoAdapter()
        repository = NewsInfoRepositoryImpl.get_instance()
        return FetchNewsInfoUsecase(api_adapter, repository)