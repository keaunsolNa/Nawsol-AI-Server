from typing import Protocol, Any

class NewsSearchPort(Protocol):
    async def search_news(
        self, query: str, display: int, start: int, sort: str
    ) -> list[dict[str, Any]]: ...