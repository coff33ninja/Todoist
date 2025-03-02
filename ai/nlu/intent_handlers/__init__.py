from .search import SearchHandler
from .count import CountHandler
from .value import ValueHandler
from .price_range import PriceRangeHandler
from .repair import RepairHandler
from .purchase_history import PurchaseHistoryHandler

__all__ = [
    "SearchHandler",
    "CountHandler",
    "ValueHandler",
    "PriceRangeHandler",
    "RepairHandler",
    "PurchaseHistoryHandler",
]

def handle_search(filters):
    handler = SearchHandler("inventory.db")
    return handler.handle(filters)

def handle_count(filters):
    handler = CountHandler("inventory.db")
    return handler.handle(filters)

def handle_value(filters):
    handler = ValueHandler("inventory.db")
    return handler.handle(filters)

def handle_price_range(filters):
    handler = PriceRangeHandler("inventory.db")
    return handler.handle(filters)

def handle_repair(filters):
    handler = RepairHandler("inventory.db")
    return handler.handle(filters)

def handle_purchase_history(filters):
    handler = PurchaseHistoryHandler("inventory.db")
    return handler.handle(filters)
