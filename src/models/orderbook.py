from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class OrderbookEntry:
    """Represents a single entry in the orderbook with price, quantity, and total value."""
    price: int
    quantity: int
    total: int
    timestamp: datetime = datetime.now()

    def __post_init__(self):
        """Calculate total if not provided."""
        if not self.total:
            self.total = self.price * self.quantity

class OrderBook:
    """Represents a complete orderbook with yes and no markets."""
    def __init__(self, yes: Dict[str, List[OrderbookEntry]], no: Dict[str, List[OrderbookEntry]]):
        self.yes = yes
        self.no = no
        self.timestamp = datetime.now()
