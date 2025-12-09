from abc import ABC, abstractmethod
from typing import List

from news_info.domain.value_object.news_item import NewsItem


class NewsInfoRepositoryPort(ABC):

    @abstractmethod
    async def save_news_batch(self, news_list: List[NewsItem]) -> List[NewsItem]:
        pass