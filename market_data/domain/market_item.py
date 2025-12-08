from market_data.domain.value_object.market_price import MarketPrice
from market_data.domain.value_object.timestamp import Timestamp


class MarketItem:
    def __init__(self, product_id: str, name: str, price: MarketPrice, timestamp: Timestamp):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.timestamp = timestamp
