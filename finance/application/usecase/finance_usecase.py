from typing import List

from finance.adapter.input.web.request.create_finance_request import CreateFinanceRequest
from finance.adapter.input.web.response.finance_response import FinanceResponse
from finance.infrastructure.orm.finance_orm import FinanceORM
from finance.infrastructure.repository.finance_repository_impl import FinanceRepositoryImpl

from util.log.log import Log

logger = Log.get_logger()
class FinanceUseCase:

    __instance = None
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.repository = FinanceRepositoryImpl.get_instance()
        return cls.__instance

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def save_finance_data(self, create_finance: List[CreateFinanceRequest]) -> List[FinanceResponse]:

        finance_list = [
            FinanceORM(
                user_id=finance.user_id,
                type=finance.type,
                base_dt=finance.base_dt,
                key=finance.key,
                value=finance.value
            )
            for finance in create_finance
        ]

        saved_orm = self.repository.save_finance_data(finance_list)
        responses = [
            FinanceResponse(
                id=orm.id,
                user_id=orm.user_id,
                type=orm.type,
                base_dt=orm.base_dt.isoformat(),
                key=orm.key,
                value=orm.value
            )
            for orm in saved_orm
        ]

        return responses