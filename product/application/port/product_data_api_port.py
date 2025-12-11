from abc import ABC, abstractmethod

from product.domain.product_etf import ProductEtf
from product.domain.product_fund import ProductFund
from product.domain.product_bond import ProductBond


class ProductDataApiPort(ABC):
    @abstractmethod
    async def get_etf_data(self) -> list[ProductEtf]:
        pass

    @abstractmethod
    async def get_fund_data(self) -> list[ProductFund]:
        pass

    @abstractmethod
    async def get_bond_data(self) -> list[ProductBond]:
        pass