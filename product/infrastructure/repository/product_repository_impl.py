from typing import List

from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy.orm import Session

from config.database.session import get_db_session
from product.application.port.product_repository_port import ProductRepositoryPort
from product.domain.product_etf import ProductEtf
from product.infrastructure.orm.product_bond import ProductBondORM
from product.infrastructure.orm.product_etf import ProductETFORM
from product.infrastructure.orm.product_fund import ProductFundORM


class ProductRepositoryImpl(ProductRepositoryPort):
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        if not hasattr(self, 'db'):
            self.db: Session = get_db_session()

    async def get_etf_data_by_date(self, date:str) -> List[ProductETFORM]:

        try:
            rows = (self.db.query(ProductETFORM).
                    filter(func.date_format(ProductETFORM.basDt, "%Y%m%d") == date).
                    all())

            return [
                ProductETFORM(
                    id=row.id,
                    fltRt=row.fltRt,
                    nav=row.nav,
                    mkp=row.mkp,
                    hipr=row.hipr,
                    lopr=row.lopr,
                    trqu=row.trqu,
                    trPrc=row.trPrc,
                    mrktTotAmt=row.mrktTotAmt,
                    nPptTotAmt=row.nPptTotAmt,
                    stLstgCnt=row.stLstgCnt,
                    bssIdxIdxNm=row.bssIdxIdxNm,
                    bssIdxClpr=row.bssIdxClpr,
                    basDt=row.basDt,
                    clpr=row.clpr,
                    vs=row.vs
                )
                for row in rows
            ]
        finally:
            self.db.close()

    async def save_etf_batch(self, etf_list: List[ProductEtf]) -> List[ProductEtf]:
        try:
            if not etf_list:
                return []

            new_etf_list = []

            for etfs in etf_list:

                etfs_date_only = etfs.basDt.date() if hasattr(etfs.basDt, 'basDt') else etfs.basDt

                existing = self.db.query(ProductETFORM).filter(
                    and_(
                        ProductETFORM.basDt == etfs.basDt,
                        # datetime을 날짜만 비교
                        func.DATE(ProductETFORM.basDt) == etfs_date_only,
                    )
                ).first()

                # 중복이 없으면 추가
                if not existing:
                    new_etf_list.append(etfs)

            if not new_etf_list:
                return etf_list

            orm_list = [
                ProductETFORM(
                    fltRt=etf.fltRt,
                    nav=etf.nav,
                    mkp=etf.mkp,
                    hipr=etf.hipr,
                    lopr=etf.lopr,
                    trqu=etf.trqu,
                    trPrc=etf.trPrc,
                    mrktTotAmt=etf.mrktTotAmt,
                    nPptTotAmt=etf.nPptTotAmt,
                    stLstgCnt=etf.stLstgCnt,
                    bssIdxIdxNm=etf.bssIdxIdxNm,
                    bssIdxClpr=etf.bssIdxClpr,
                    basDt=etf.basDt,
                    clpr=etf.clpr,
                    vs=etf.vs
                )
                for etf in new_etf_list
            ]

            self.db.add_all(orm_list)
            self.db.commit()

            for orm_item in orm_list:
                self.db.refresh(orm_item)

            return etf_list
        finally:
            self.db.close()

    def get_all_etf(self, limit: int = 50) -> List[ProductETFORM]:
        """
        ETF 상품 목록 조회
        
        Args:
            limit: 조회할 최대 개수
        
        Returns:
            ETF 상품 리스트
        """
        try:
            # 최신 데이터 기준으로 정렬하여 조회
            etf_list = self.db.query(ProductETFORM).order_by(
                ProductETFORM.basDt.desc(),
                ProductETFORM.mrktTotAmt.desc()  # 시가총액 큰 순서
            ).limit(limit).all()
            
            return etf_list
        except Exception as e:
            from util.log.log import Log
            logger = Log.get_logger()
            logger.error(f"Failed to get ETF list: {str(e)}")
            return []
        finally:
            self.db.close()

    async def get_fund_data_by_date(self, date:str) -> List[ProductFundORM]:

        try:
            rows = (self.db.query(ProductFundORM).
                    filter(func.date_format(ProductFundORM.basDt, "%Y%m%d") == date).
                    all())
            return [
                ProductFundORM(
                    id=row.id,
                    basDt = row.basDt,
                    srtnCd = row.srtnCd,
                    fndNm = row.fndNm,
                    ctg = row.ctg,
                    setpDt = row.setpDt,
                    fndTp = row.fndTp,
                    prdClsfCd = row.prdClsfCd,
                    asoStdCd = row.asoStdCd,
                )
                for row in rows
            ]
        finally:
            self.db.close()

    async def save_fund_batch(self, fund_list: List[ProductFundORM]) -> List[ProductFundORM]:

        try:
            if not fund_list:
                return []

            new_fund_list = []

            for fund in fund_list:

                fund_date_only = fund.basDt.date() if hasattr(fund.basDt, 'date') else fund.basDt

                existing = self.db.query(ProductFundORM).filter(
                    and_(
                        ProductFundORM.basDt == fund.basDt,
                        func.DATE(ProductFundORM.basDt) == fund_date_only,
                    )
                ).first()

                if not existing:
                    new_fund_list.append(fund)

            # 신규 없으면 입력 필요 없음
            if not new_fund_list:
                return fund_list

            orm_list = [
                ProductFundORM(
                    basDt=f.basDt,
                    srtnCd=f.srtnCd,
                    fndNm=f.fndNm,
                    ctg=f.ctg,
                    setpDt=f.setpDt,
                    fndTp=f.fndTp,
                    prdClsfCd=f.prdClsfCd,
                    asoStdCd=f.asoStdCd
                )
                for f in new_fund_list
            ]

            self.db.add_all(orm_list)
            self.db.commit()

            for orm_item in orm_list:
                self.db.refresh(orm_item)

            return fund_list
        finally:
            self.db.close()

    # fund 상품 목록 조회
    def get_all_fund(self, limit: int = 50) -> List[ProductFundORM]:
        try:
            # 최신 데이터 기준으로 정렬하여 조회
            etf_list = self.db.query(ProductFundORM).order_by(
                ProductFundORM.basDt.desc(),
                ProductFundORM.mrktTotAmt.desc()  # 시가총액 큰 순서
            ).limit(limit).all()
            
            return etf_list
        except Exception as e:
            from util.log.log import Log
            logger = Log.get_logger()
            logger.error(f"Failed to get Fund list: {str(e)}")
            return []
        finally:
            self.db.close()

    async def get_bond_data_by_date(self, date:str) -> List[ProductBondORM]:
        try:
            rows = (self.db.query(ProductBondORM).
                    filter(func.date_format(ProductBondORM.basDt, "%Y%m%d") == date).
                    all())

            return [
                ProductBondORM(
                    id = row.id,
                    basDt = row.basDt,
                    crno = row.crno,
                    bondIsurNm = row.bondIsurNm,
                    bondIssuDt = row.bondIssuDt,
                    scrsItmsKcd = row.scrsItmsKcd,
                    scrsItmsKcdNm = row.scrsItmsKcdNm,
                    isinCd = row.isinCd,
                    isinCdNm = row.isinCdNm,
                    bondIssuFrmtNm = row.bondIssuFrmtNm,
                    bondExprDt = row.bondExprDt,
                    bondIssuCurCd = row.bondIssuCurCd,
                    bondIssuCurCdNm = row.bondIssuCurCdNm,
                    bondPymtAmt = row.bondPymtAmt,
                    bondIssuAmt = row.bondIssuAmt,
                    bondSrfcInrt = row.bondSrfcInrt,
                    irtChngDcd = row.irtChngDcd,
                    irtChngDcdNm = row.irtChngDcdNm,
                    bondIntTcd = row.bondIntTcd,
                    bondIntTcdNm = row.bondIntTcdNm,
                )
                for row in rows
            ]
        finally:
            self.db.close()

    async def save_bond_batch(self, bond_list: List[ProductBondORM]) -> List[ProductBondORM]:

        try:
            if not bond_list:
                return []

            new_bond_list = []

            for bond in bond_list:

                bond_date_only = bond.basDt.date() if hasattr(bond.basDt, 'date') else bond.basDt

                existing = self.db.query(ProductBondORM).filter(
                    and_(
                        ProductBondORM.basDt == bond.basDt,
                        func.DATE(ProductBondORM.basDt) == bond_date_only,
                    )
                ).first()

                if not existing:
                    new_bond_list.append(bond)

            if not new_bond_list:
                return bond_list

            orm_list = [
                ProductBondORM(
                    basDt=b.basDt,
                    crno=b.crno,
                    bondIsurNm=b.bondIsurNm,
                    bondIssuDt=b.bondIssuDt,
                    scrsItmsKcd=b.scrsItmsKcd,
                    scrsItmsKcdNm=b.scrsItmsKcdNm,
                    isinCd=b.isinCd,
                    isinCdNm=b.isinCdNm,
                    bondIssuFrmtNm=b.bondIssuFrmtNm,
                    bondExprDt=b.bondExprDt,
                    bondIssuCurCd=b.bondIssuCurCd,
                    bondIssuCurCdNm=b.bondIssuCurCdNm,
                    bondPymtAmt=b.bondPymtAmt,
                    bondIssuAmt=b.bondIssuAmt,
                    bondSrfcInrt=b.bondSrfcInrt,
                    irtChngDcd=b.irtChngDcd,
                    irtChngDcdNm=b.irtChngDcdNm,
                    bondIntTcd=b.bondIntTcd,
                    bondIntTcdNm=b.bondIntTcdNm
                )
                for b in new_bond_list
            ]

            self.db.add_all(orm_list)
            self.db.commit()

            for orm_item in orm_list:
                self.db.refresh(orm_item)

            return bond_list
        finally:
            self.db.close()

    def get_all_bond(self, limit: int = 50) -> List[ProductBondORM]:
        """
        채권 상품 목록 조회

        Args:
            limit: 조회할 최대 개수

        Returns:
            ETF 상품 리스트
        """
        try:
            # 최신 데이터 기준으로 정렬하여 조회
            bond_list = self.db.query(ProductBondORM).order_by(
                ProductBondORM.basDt.desc(),
                ProductBondORM.bondIssuAmt.desc()  # 채권발행금액 큰 순서
            ).limit(limit).all()

            return bond_list
        except Exception as e:
            from util.log.log import Log
            logger = Log.get_logger()
            logger.error(f"Failed to get Bond list: {str(e)}")
            return []
        finally:
            self.db.close()