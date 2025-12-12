from typing import List

from finance.application.port.finance_repository_port import FinanceRepositoryPort
from finance.infrastructure.orm.finance_orm import FinanceORM
from sqlalchemy.orm import Session
from sqlalchemy import and_

from config.database.session import get_db_session

class FinanceRepositoryImpl(FinanceRepositoryPort):
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

    def save_finance_data(self, finance_data: List[FinanceORM]) -> List[FinanceORM]:

        try:
            if not finance_data:
                return []

            new_finance_data = []

            for finance in finance_data:

                existing = self.db.query(FinanceORM).filter(
                    and_(
                        FinanceORM.user_id == finance.user_id,
                        FinanceORM.type == finance.type,
                        FinanceORM.base_dt == finance.base_dt,
                        FinanceORM.key == finance.key,
                        FinanceORM.value == finance.value
                    )
                ).first()

                if not existing:
                    new_finance_data.append(finance)

            if not new_finance_data:
                return []

            orm_list = [
                FinanceORM(
                    user_id=finance.user_id,
                    type=finance.type,
                    base_dt=finance.base_dt,
                    key=finance.key,
                    value=finance.value
                )
                for finance in new_finance_data
            ]

            self.db.add_all(orm_list)
            self.db.commit()

            for orm_item in orm_list:
                self.db.refresh(orm_item)

            return orm_list
        finally:
            self.db.close()