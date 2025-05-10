import base64
from algokit_utils import AlgorandClient
from algosdk import encoding
from typing import Dict, Any, Optional
from typing import List, Dict


class OrderbookEntry:
    def __init__(self, price: int, quantity: int, total: int):
        self.price = price
        self.quantity = quantity
        self.total = total

class OrderBook:
    def __init__(self, yes: Dict[str, List[OrderbookEntry]], no: Dict[str, List[OrderbookEntry]]):
        self.yes = yes
        self.no = no


def aggregate_orders(orders: List[Dict[str, Any]]) -> List[OrderbookEntry]:
    price_map: Dict[int, int] = {}

    for order in orders:
        quantity = order.get("quantity", 0)
        quantity_filled = order.get("quantity_filled", 0)
        remaining_qty = quantity - quantity_filled
        price = order.get("price", 0)

        if remaining_qty > 0 and price > 0:
            price_map[price] = price_map.get(price, 0) + remaining_qty

    return [OrderbookEntry(price, quantity, price * quantity) for price, quantity in price_map.items()]


def get_aggregated_order_book(orders: List[Dict[str, Any]]) -> OrderBook:
    yes_buy_orders = [
        order for order in orders
        if order.get('side') == 1 and 
           order.get('position') == 1 and 
           order.get('quantity', 0) > order.get('quantity_filled', 0) and 
           order.get('slippage', 0) == 0
    ]
    yes_sell_orders = [
        order for order in orders
        if order.get('side') == 0 and 
           order.get('position') == 1 and 
           order.get('quantity', 0) > order.get('quantity_filled', 0) and 
           order.get('slippage', 0) == 0
    ]
    no_buy_orders = [
        order for order in orders
        if order.get('side') == 1 and 
           order.get('position') == 0 and 
           order.get('quantity', 0) > order.get('quantity_filled', 0) and 
           order.get('slippage', 0) == 0
    ]
    no_sell_orders = [
        order for order in orders
        if order.get('side') == 0 and 
           order.get('position') == 0 and 
           order.get('quantity', 0) > order.get('quantity_filled', 0) and 
           order.get('slippage', 0) == 0
    ]

    return OrderBook(
        yes={"bids": aggregate_orders(yes_buy_orders), "asks": aggregate_orders(yes_sell_orders)},
        no={"bids": aggregate_orders(no_buy_orders), "asks": aggregate_orders(no_sell_orders)}
    )

def decode_global_state(app_info):
    global_state = {}

    if app_info.get("application") and app_info["application"].get("params") and "global-state" in app_info["application"]["params"]:
        raw_global_state = app_info["application"]["params"]["global-state"]

        for state_item in raw_global_state:
            key = base64.b64decode(state_item["key"]).decode()

            # Process value based on type
            value = None
            if state_item["value"]["type"] == 1:  # bytes value
                if key == "owner":
                    try:
                        # Decode the bytes and use algosdk to encode address
                        address_bytes = base64.b64decode(state_item["value"]["bytes"])
                        if len(address_bytes) == 32:
                            value = encoding.encode_address(address_bytes)
                        else:
                            # Fallback if bytes aren't the right length for an address
                            value = state_item["value"]["bytes"]
                    except Exception as e:
                        print("Error decoding owner address:", e)
                        value = state_item["value"]["bytes"]
                else:
                    # For other byte values, try normal string decoding
                    try:
                        value = base64.b64decode(state_item["value"]["bytes"]).decode()
                    except Exception:
                        value = state_item["value"]["bytes"]
            else:  # uint value
                value = int(state_item["value"]["uint"])

            global_state[key] = value

    return global_state


def get_order_book(market_app_id: int) -> OrderBook:
    # Get the Algorand client
    algorand = AlgorandClient.mainnet()
    app_info = algorand.app.get_by_id(market_app_id)

    indexer_client = algorand.client.indexer
    orders = indexer_client.lookup_account_application_by_creator(app_info.app_address)

    order_details = []
    for order in orders["applications"]:
        app_id = order["id"]
        app_info = indexer_client.applications(app_id)
        global_state = decode_global_state(app_info)
        order_details.append(global_state)

    aggregate_order_book = get_aggregated_order_book(order_details)
    return aggregate_order_book

