from typing import List

from product.adapter.output.product.product_data_api_adapter import ProductDataApiAdapter
from product.application.port.product_repository_port import ProductRepositoryPort
from product.domain.product_etf import ProductEtf
from product.domain.product_fund import ProductFund
from product.domain.product_bond import ProductBond
from product.domain.product_etf_data import ProductEtfData
from product.domain.product_fund_data import ProductFundData
from product.domain.product_bond_data import ProductBondData
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
            # 필드명 매핑 (API 응답 필드명 -> 모델 필드명)
            # itmsNm: 종목명, vs: 대비, fltRt: 등락률, mkp: 시가, hipr: 고가, lopr: 저가
            # clpr: 종가, trqu: 거래량, trPrc: 거래대금, lstgStCnt: 상장주식수, mrktTotAmt: 시가총액
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

        client = DataGoClient()
        raw_items = await client.get_fund_data()
        fund_entities = []
        for item in raw_items:
            funds = ProductFund(
                basDt=item.get("basDt"),
                srtnCd=item.get("srtnCd"),
                fndNm=item.get("fndNm"),
                ctg=item.get("ctg"),
                setpDt=item.get("setpDt"),
                fndTp=item.get("fndTp"),
                prdClsfCd=item.get("prdClsfCd"),
                asoStdCd=item.get("asoStdCd")
            )
            fund_entities.append(funds)
        if fund_entities:
            await self.repository.get_fund_data_by_date(date)

        return fund_entities

    async def fetch_and_save_fund_data(self) -> List[ProductFund]:
        client = DataGoClient()
        raw_items = await client.get_fund_data()
        fund_entities = []

        for item in raw_items:
            funds = ProductFund(
                basDt=item.get("basDt"),
                srtnCd=item.get("srtnCd"),
                fndNm=item.get("fndNm"),
                ctg=item.get("ctg"),
                setpDt=item.get("setpDt"),
                fndTp=item.get("fndTp"),
                prdClsfCd=item.get("prdClsfCd"),
                asoStdCd=item.get("asoStdCd")
            )
            fund_entities.append(funds)

        if fund_entities:
            await self.repository.save_fund_batch(fund_entities)

        return fund_entities

    async def get_bond_data_by_date(self, date:str) -> List[ProductBondORM]:

        client = DataGoClient()
        raw_items = await client.get_bond_data()
        bond_entities = []
        for item in raw_items:
            bonds = ProductBond(
                basDt = item.get("basDt"),
                crno = item.get("crno"),
                bondIsurNm = item.get("bondIsurNm"),
                bondIssuDt = item.get("bondIssuDt"),
                scrsItmsKcd = item.get("scrsItmsKcd"),
                scrsItmsKcdNm = item.get("scrsItmsKcdNm"),
                isinCd = item.get("isinCd"),
                isinCdNm = item.get("isinCdNm"),
                bondIssuFrmtNm = item.get("bondIssuFrmtNm"),
                bondExprDt = item.get("bondExprDt"),
                bondIssuCurCd = item.get("bondIssuCurCd"),
                bondIssuCurCdNm = item.get("bondIssuCurCdNm"),
                bondPymtAmt = item.get("bondPymtAmt"),
                bondIssuAmt = item.get("bondIssuAmt"),
                bondSrfcInrt = item.get("bondSrfcInrt"),
                irtChngDcd = item.get("irtChngDcd"),
                irtChngDcdNm = item.get("irtChngDcdNm"),
                bondIntTcd = item.get("bondIntTcd"),
                bondIntTcdNm = item.get("bondIntTcdNm")

            )
            bond_entities.append(bonds)
        if bond_entities:
            await self.repository.get_bond_data_by_date(date)

        return bond_entities

    async def fetch_and_save_bond_data(self) -> List[ProductBond]:
        client = DataGoClient()
        raw_items = await client.get_bond_data()
        bond_entities = []

        for item in raw_items:
            bonds = ProductBond(
                basDt=item.get("basDt"),
                crno=item.get("crno"),
                bondIsurNm=item.get("bondIsurNm"),
                bondIssuDt=item.get("bondIssuDt"),
                scrsItmsKcd=item.get("scrsItmsKcd"),
                scrsItmsKcdNm=item.get("scrsItmsKcdNm"),
                isinCd=item.get("isinCd"),
                isinCdNm=item.get("isinCdNm"),
                bondIssuFrmtNm=item.get("bondIssuFrmtNm"),
                bondExprDt=item.get("bondExprDt"),
                bondIssuCurCd=item.get("bondIssuCurCd"),
                bondIssuCurCdNm=item.get("bondIssuCurCdNm"),
                bondPymtAmt=item.get("bondPymtAmt"),
                bondIssuAmt=item.get("bondIssuAmt"),
                bondSrfcInrt=item.get("bondSrfcInrt"),
                irtChngDcd=item.get("irtChngDcd"),
                irtChngDcdNm=item.get("irtChngDcdNm"),
                bondIntTcd=item.get("bondIntTcd"),
                bondIntTcdNm=item.get("bondIntTcdNm")
            )
            bond_entities.append(bonds)

        if bond_entities:
            await self.repository.save_bond_batch(bond_entities)

        return bond_entities
