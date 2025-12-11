from datetime import datetime
from typing import List

from ecos.domain.value_object.timestamp import Timestamp
from product.domain.product_etf import ProductEtf
from product.domain.product_fund import ProductFund
from product.domain.product_bond import ProductBond
from product.domain.product_etf_data import ProductEtfData
from product.domain.product_fund_data import ProductFundData
from product.domain.product_bond_data import ProductBondData
from product.domain.value_object.product_source import ProductSource
from product.infrastructure.api.data_go_client import DataGoClient


class ProductDataApiAdapter:
    def __init__(self):
        self.client = DataGoClient()
    pass

    async def get_etf_data(self) -> ProductEtfData:
        raw_items = await self.client.get_etf_data()
        items: List[ProductEtf] = [
            ProductEtf(
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
                vs=item.get("vs"),
            )
            for item in raw_items
        ]
        return ProductEtfData(
            items=items,
            source=ProductSource("PRODUCT_ETF"),
            fetched_at=Timestamp(datetime.now())
        )

    async def get_fund_data(self) -> ProductFundData:
        raw_items = await self.client.get_fund_data()

        items: List[ProductFund] = [
            ProductFund(
                basDt=item.get("basDt"),
                srtnCd=item.get("srtnCd"),
                fndNm=item.get("fndNm"),
                ctg=item.get("ctg"),
                setpDt=item.get("setpDt"),
                fndTp=item.get("fndTp"),
                prdClsfCd=item.get("prdClsfCd"),
                asoStdCd=item.get("asoStdCd"),
            )
            for item in raw_items
        ]

        return ProductFundData(
            items=items,
            source=ProductSource("PRODUCT_FUND"),
            fetched_at=Timestamp(datetime.now())
        )


    async def get_bond_data(self) -> ProductBondData:
        raw_items = await self.client.get_bond_data()

        items: List[ProductBond] = [
            ProductBond(
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
                bondIntTcdNm=item.get("bondIntTcdNm"),
            )
            for item in raw_items
        ]

        return ProductBondData(
            items=items,
            source=ProductSource("PRODUCT_BOND"),
            fetched_at=Timestamp(datetime.now())
        )