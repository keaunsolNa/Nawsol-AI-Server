from fastapi import APIRouter, Body

from product.application.factory.fetch_product_data_usecase_factory import FetchProductDataUsecaseFactory

product_data_router = APIRouter(tags=["product"])
@product_data_router.get("/etf")
async def get_etf_info():
    usecase = FetchProductDataUsecaseFactory.create()
    result = await usecase.get_etf_data()

    return {
        "source": result.source,
        "fetched_at": result.fetched_at.timestamp.isoformat(),
        "items": [
            {
                "fltRt": item.fltRt,
                "nav": item.nav,
                "mkp": item.mkp,
                "hipr": item.hipr,
                "lopr": item.lopr,
                "trqu": item.trqu,
                "trPrc": item.trPrc,
                "mrktTotAmt": item.mrktTotAmt,
                "nPptTotAmt": item.nPptTotAmt,
                "stLstgCnt": item.stLstgCnt,
                "bssIdxIdxNm": item.bssIdxIdxNm,
                "bssIdxClpr": item.bssIdxClpr,
                "basDt": item.basDt,
                "clpr": item.clpr,
                "vs": item.vs
            } for item in result.items
        ]
    }

@product_data_router.get("/etf/{date}")
async def get_etf_info(date:str):
    usecase = FetchProductDataUsecaseFactory.create()
    result = await usecase.get_etf_data_by_date(date)
    return result


@product_data_router.post("/etf/save")
async def fetch_and_save_etf():

    usecase = FetchProductDataUsecaseFactory.create()
    saved_entities = await usecase.fetch_and_save_etf_data()

    return {
        "massage": "ETF 정보가 성공적으로 저장되었습니다.",
        "saved_count": len(saved_entities),
        "items": [
            {
                "fltRt": entity.fltRt,
                "nav": entity.nav,
                "mkp": entity.mkp,
                "hipr": entity.hipr,
                "lopr": entity.lopr,
                "trqu": entity.trqu,
                "trPrc": entity.trPrc,
                "mrktTotAmt": entity.mrktTotAmt,
                "nPptTotAmt": entity.nPptTotAmt,
                "stLstgCnt": entity.stLstgCnt,
                "bssIdxIdxNm": entity.bssIdxIdxNm,
                "bssIdxClpr": entity.bssIdxClpr,
                "basDt": entity.basDt,
                "clpr": entity.clpr,
                "vs": entity.vs,

            } for entity in saved_entities
        ]
    }