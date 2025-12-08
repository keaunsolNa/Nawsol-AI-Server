from typing import List

from .market_item import MarketItem
from .value_object.market_source import MarketSource
from .value_object.timestamp import Timestamp


class MarketData:
    def __init__(self, items: List[MarketItem], source: MarketSource, fetched_at: Timestamp):
        self.items = items
        self.source = source
        self.fetched_at = fetched_at

    def add_item(self, item: MarketItem):
        self.items.append(item)
