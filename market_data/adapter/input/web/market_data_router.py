from fastapi import APIRouter

from market_data.application.factory.fetch_market_data_usecase_factory import FetchMarketDataUsecaseFactory

market_data_router = APIRouter(tags=["market_data"])

@market_data_router.get("/fetch")
async def fetch_market_data(query: str):
    usecase = FetchMarketDataUsecaseFactory.create()
    result = await usecase.execute(query)

    return {
        "source": result.source,
        "fetched_at": result.fetched_at.timestamp.isoformat(),
        "items": [
            {
                "product_id": item.product_id,
                "name": item.name,
                "price": item.price.value,
                "currency": item.price.currency,
                "timestamp": item.timestamp.timestamp.isoformat()
            } for item in result.items
        ]
    }
