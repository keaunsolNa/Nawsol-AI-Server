from typing import List

from product.adapter.output.product.product_data_api_adapter import ProductDataApiAdapter
from product.application.port.product_repository_port import ProductRepositoryPort
from product.domain.product_etf import ProductEtf
from product.domain.product_etf_data import ProductEtfData
from product.infrastructure.api.data_go_client import DataGoClient
from product.infrastructure.orm.product_bond import ProductBondORM
from product.infrastructure.orm.product_etf import ProductETFORM
from product.infrastructure.orm.product_fund import ProductFundORM
from util.log.log import Log

logger = Log.get_logger()
class FetchProductUseCase:
    def __init__(self, adapter: ProductDataApiAdapter, repository: ProductRepositoryPort):
        self.adapter = adapter
        self.repository = repository

    async def get_etf_data(self) -> ProductEtfData:
        return await self.adapter.get_etf_data()

    async def get_etf_data_by_date(self, date: str) -> List[ProductETFORM]:
        return await self.repository.get_etf_data_by_date(date)

    async def fetch_and_save_etf_data(self, start:str, end:str) -> List[ProductEtf]:

        client = DataGoClient()
        raw_items = await client.get_etf_data(start, end)
        etf_entities = []
        for item in raw_items:
            etfs = ProductEtf(
                fltRt=item.get("fltRt"),
                nav=item.get("nav"),
                mkp=item.get("mkp"),
                hipr=item.get("hipr"),
                lopr=item.get("lopr"),
                trqu=item.get("trqu"),
                trPrc=item.get("trPrc"),
                mrktTotAmt=item.get("mrktTotAmt"),
                nPptTotAmt=item.get("nPptTotAmt"),
                stLstgCnt=item.get("stLstgCnt"),
                bssIdxIdxNm=item.get("bssIdxIdxNm"),
                bssIdxClpr=item.get("bssIdxClpr"),
                basDt=item.get("basDt"),
                clpr=item.get("clpr"),
                vs=item.get("vs")
            )
            etf_entities.append(etfs)
        if etf_entities:
            await self.repository.save_etf_batch(etf_entities)

        return etf_entities

    async def get_fund_data_by_date(self, date:str) -> List[ProductFundORM]:
        return await self.repository.get_fund_data_by_date(date)

    async def get_bond_data_by_date(self, date:str) -> List[ProductBondORM]:
        return await self.repository.get_bond_data_by_date(date)