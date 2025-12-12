from typing import List

from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy.orm import Session

from config.database.session import get_db_session
from ecos.application.port.ecos_repository_port import EcosRepositoryPort
from ecos.domain.ecos import Ecos
from ecos.domain.ecos_interest import EcosInterest
from ecos.infrastructure.orm.exchange_rate import ExchangeRateORM
from ecos.infrastructure.orm.interest_rate import InterestRateORM


class EcosRepositoryImpl(EcosRepositoryPort):
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

    async def save_exchange_rate(self, ecos: Ecos) -> Ecos:

        try:
            orm_exchange_rate = ExchangeRateORM(
                exchange_type=ecos.exchange_type,
                exchange_rate=ecos.exchange_rate,
                erm_date=ecos.erm_date,
                created_at=ecos.created_at
            )

            self.db.add(orm_exchange_rate)
            self.db.commit()
            self.db.refresh(orm_exchange_rate)

            # 도메인 엔티티에 id 업데이트 (필요한 경우)
            return ecos
        finally:
            self.db.close()

    async def save_exchange_rates_batch(self, ecos_list: List[Ecos]) -> List[Ecos]:

        try:
            """
            배치로 환율 데이터를 저장한다.
            erm_date, exchange_type, exchange_rate가 동일한 레코드는 중복 저장하지 않는다.
            """
            if not ecos_list:
                return []

            # 중복 체크: 각 항목을 개별적으로 조회하여 정확한 비교 수행
            new_ecos_list = []

            for ecos in ecos_list:
                # 날짜는 날짜 부분만 비교 (시간 제거)

                erm_date_only = ecos.erm_date.date() if hasattr(ecos.erm_date, 'date') else ecos.erm_date

                # 기존 레코드 조회 (exchange_type, erm_date 일치하는지 확인)
                # datetime을 날짜만 비교하기 위해 DATE() 함수 사용
                existing = self.db.query(ExchangeRateORM).filter(
                    and_(
                        ExchangeRateORM.exchange_type == ecos.exchange_type,
                        # datetime을 날짜만 비교
                        func.DATE(ExchangeRateORM.erm_date) == erm_date_only,
                    )
                ).first()

                # 중복이 없으면 추가
                if not existing:
                    new_ecos_list.append(ecos)

            if not new_ecos_list:
                return ecos_list

            # 새로운 항목만 ORM 객체로 변환
            orm_list = [
                ExchangeRateORM(
                    exchange_type=ecos.exchange_type,
                    exchange_rate=ecos.exchange_rate,
                    erm_date=ecos.erm_date,
                    created_at=ecos.created_at
                )
                for ecos in new_ecos_list
            ]

            self.db.add_all(orm_list)
            self.db.commit()

            for orm_item in orm_list:
                self.db.refresh(orm_item)

            return ecos_list
        finally:
            self.db.close()

    def get_exchange_rate_by_date(self, date: str) -> List[Ecos]:

        try:
            rows = (self.db.query(ExchangeRateORM).
                    filter(func.date_format(ExchangeRateORM.erm_date, "%Y%m") == date).
                    all())

            return [
                Ecos(
                    exchange_type=row.exchange_type.name,
                    exchange_rate=row.exchange_rate,
                    erm_date=row.erm_date,
                    created_at=row.created_at
                )
                for row in rows
            ]
        finally:
            self.db.close()

    async def save_interest_rate(self, ecos: EcosInterest) -> EcosInterest:

        try:
            orm_interest_rate = InterestRateORM(
                interest_type=ecos.interest_type,
                interest_rate=ecos.interest_rate,
                erm_date=ecos.erm_date,
                created_at=ecos.created_at
            )

            self.db.add(orm_interest_rate)
            self.db.commit()
            self.db.refresh(orm_interest_rate)

            # 도메인 엔티티에 id 업데이트 (필요한 경우)
            return ecos
        finally:
            self.db.close()

    async def save_interest_rates_batch(self, ecos_list: List[EcosInterest]) -> List[EcosInterest]:

        try:
            """
            배치로 금리 데이터를 저장한다.
            erm_date, interest_type, interest_rate가 동일한 레코드는 중복 저장하지 않는다.
            """
            if not ecos_list:
                return []

            # 중복 체크: 각 항목을 개별적으로 조회하여 정확한 비교 수행
            new_ecos_list = []

            for ecos in ecos_list:
                # 날짜는 날짜 부분만 비교 (시간 제거)

                erm_date_only = ecos.erm_date.date() if hasattr(ecos.erm_date, 'date') else ecos.erm_date

                # 기존 레코드 조회 (interest_type, erm_date 일치하는지 확인)
                # datetime을 날짜만 비교하기 위해 DATE() 함수 사용
                existing = self.db.query(InterestRateORM).filter(
                    and_(
                        InterestRateORM.interest_type == ecos.interest_type,
                        # datetime을 날짜만 비교
                        func.DATE(InterestRateORM.erm_date) == erm_date_only,
                    )
                ).first()

                # 중복이 없으면 추가
                if not existing:
                    new_ecos_list.append(ecos)

            if not new_ecos_list:
                return ecos_list

            # 새로운 항목만 ORM 객체로 변환
            orm_list = [
                InterestRateORM(
                    interest_type=ecos.interest_type,
                    interest_rate=ecos.interest_rate,
                    erm_date=ecos.erm_date,
                    created_at=ecos.created_at
                )
                for ecos in new_ecos_list
            ]

            self.db.add_all(orm_list)
            self.db.commit()

            for orm_item in orm_list:
                self.db.refresh(orm_item)

            return ecos_list
        finally:
            self.db.close()

    def get_interest_rate_by_date(self, date: str) -> List[EcosInterest]:

        try:
            rows = (self.db.query(InterestRateORM).
                    filter(func.date_format(InterestRateORM.erm_date, "%Y%m") == date).
                    all())

            return [
                EcosInterest(
                    interest_type=row.interest_type,
                    interest_rate=row.interest_rate,
                    erm_date=row.erm_date,
                    created_at=row.created_at
                )
                for row in rows
            ]
        finally:
            self.db.close()