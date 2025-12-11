from abc import ABC, abstractmethod
from typing import List

from product.domain.product_etf import ProductEtf
from product.domain.product_fund import ProductFund
from product.domain.product_bond import ProductBond
from product.infrastructure.orm.product_bond import ProductBondORM
from product.infrastructure.orm.product_etf import ProductETFORM
from product.infrastructure.orm.product_fund import ProductFundORM


class ProductRepositoryPort(ABC):

    @abstractmethod
    async def get_etf_data_by_date(self, date:str) -> List[ProductETFORM]:
        pass

    @abstractmethod
    async def save_etf_batch(self, etf_list: List[ProductEtf]) -> List[ProductEtf]:
        pass

    @abstractmethod
    async def get_fund_data_by_date(self, date:str) -> List[ProductFundORM]:
        pass

    @abstractmethod
    async def save_fund_batch(self, etf_list: List[ProductFund]) -> List[ProductFund]:
        pass

    @abstractmethod
    async def get_bond_data_by_date(self, date:str) -> List[ProductBondORM]:
        pass

    @abstractmethod
    async def save_bond_batch(self, etf_list: List[ProductBond]) -> List[ProductBond]:
        pass