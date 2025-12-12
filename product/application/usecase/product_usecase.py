from typing import List

from product.adapter.output.product.product_data_api_adapter import ProductDataApiAdapter
from product.application.port.product_repository_port import ProductRepositoryPort
from product.domain.product_bond_data import ProductBondData
from product.domain.product_etf import ProductEtf
from product.domain.product_fund import ProductFund
from product.domain.product_fund_data import ProductFundData
from product.domain.product_bond import ProductBond
from product.domain.product_etf_data import ProductEtfData
from datetime import datetime, timedelta
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

    async def get_fund_data(self) -> ProductFundData:
        return await self.adapter.get_fund_data()
      
    async def get_fund_data_by_date(self, date:str) -> List[ProductFundORM]:
        return await self.repository.get_fund_data_by_date(date)

    async def fetch_and_save_fund_data(self, start:str = None, end:str = None) -> List[ProductFund]:
        client = DataGoClient()
        all_fund_entities = []

        if start not in (None, "") and end not in (None, ""):
            start_date = datetime.strptime(start, "%Y%m%d")
            end_date = datetime.strptime(end, "%Y%m%d")

            current_date = start_date

            while current_date <= end_date:
                today = current_date.strftime("%Y%m%d")

                raw_items = await client.get_fund_data(today)
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

                all_fund_entities.extend(fund_entities)
                current_date += timedelta(days=1)
            return all_fund_entities
        else :
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

    async def get_bond_data(self) -> ProductBondData:
        return await self.adapter.get_bond_data()

    async def get_bond_data_by_date(self, date:str) -> List[ProductBondORM]:

        return await self.repository.get_bond_data_by_date(date)

    async def fetch_and_save_bond_data(self, start:str, end:str) -> List[ProductBond]:
        client = DataGoClient()
        all_bond_entities = []

        if start is not None and end is not None:
            start_date = datetime.strptime(start, "%Y%m%d")
            end_date = datetime.strptime(end, "%Y%m%d")

            current_date = start_date
            while current_date <= end_date:
                today = current_date.strftime("%Y%m%d")

                raw_items = await client.get_bond_data(today)
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

                all_bond_entities.extend(bond_entities)
                current_date += timedelta(days=1)
            return all_bond_entities
        else:
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
