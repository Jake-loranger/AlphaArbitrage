from decimal import Decimal
import math
import requests
import base64
from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv
from algokit_utils import AlgorandClient
from algosdk import encoding

from helpers.log_helpers import get_logger
from models.orderbook import OrderbookEntry, OrderBook
from models.market import Market, ShareImage, ShareImageItem

logger = get_logger(__name__)

class AlphaHelper:
    """Helper class for interacting with Alpha Arcade API and calculations."""
    
    BASE_API_URL = "https://g08245wvl7.execute-api.us-east-1.amazonaws.com/api"
    MICRO_UNIT = 1_000_000  # 1 USDC = 1_000_000 microUSDC
    
    def __init__(self):
        """Initialize the AlphaHelper with environment variables."""
        self.algorand = AlgorandClient.mainnet()
    
    async def get_market_info(self, market_id: str) -> Market:
        """
        Fetches the information for a given Alpha Arcade market.
        
        Args:
            market_id: The unique identifier for the market
            
        Returns:
            Market object containing market information including volume, fees, and rules
            
        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.BASE_API_URL}/get-market"
        params = {"marketId": market_id}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            response_data = response.json()
            
            # Extract market data from the nested response
            data = response_data.get("market", {})
            
            # Create ShareImage objects if they exist in the response
            share_image = None
            if "shareImage" in data:
                share_image_data = data["shareImage"]
                share_image = ShareImage(
                    yes=ShareImageItem(**share_image_data.get("yes", {})) if "yes" in share_image_data else None,
                    no=ShareImageItem(**share_image_data.get("no", {})) if "no" in share_image_data else None
                )
            
            # Create Market object
            market = Market(
                id=data.get("id"),
                marketAppId=data.get("marketAppId"),
                slug=data.get("slug"),
                topic=data.get("topic"),
                yesAssetId=data.get("yesAssetId"),
                noAssetId=data.get("noAssetId"),
                yesTeamColor=data.get("yesTeamColor"),
                noTeamColor=data.get("noTeamColor"),
                yesProb=data.get("yesProb"),
                noProb=data.get("noProb"),
                currentMidpoint=data.get("currentMidpoint"),
                currentSpread=data.get("currentSpread"),
                lastTradePrice=data.get("lastTradePrice"),
                lastTradePrices=data.get("lastTradePrices"),
                rules=data.get("rules"),
                compressedRules=data.get("compressedRules"),
                image=data.get("image"),
                shareImage=share_image,
                categories=data.get("categories"),
                featured=data.get("featured"),
                volume=data.get("volume"),
                marketVolume=data.get("marketVolume"),
                fees=data.get("fees"),
                totalRewards=data.get("totalRewards"),
                rewardsPaidOut=data.get("rewardsPaidOut"),
                lastRewardAmount=data.get("lastRewardAmount"),
                feeAddress=data.get("feeAddress"),
                feeBasePercent=data.get("feeBasePercent"),
                feeTimerThreshhold=data.get("feeTimerThreshhold"),
                marketFriend=data.get("marketFriend"),
                oracle=data.get("oracle"),
                rewardsSpreadDistance=data.get("rewardsSpreadDistance"),
                rewardsMinContracts=data.get("rewardsMinContracts"),
                createdAt=data.get("createdAt"),
                updatedAt=data.get("updatedAt"),
                liveTs=data.get("liveTs"),
                endTs=data.get("endTs"),
                createdRound=data.get("createdRound"),
                lastRewardTs=data.get("lastRewardTs"),
                comments=data.get("comments"),
                dataType=data.get("dataType"),
                PK=data.get("PK"),
                SK=data.get("SK")
            )
            
            # Log the market object
            logger.info(f"Fetched market info for {market_id}: {market}")
            
            # Return the Market object
            return market
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch market info for {market_id}: {str(e)}")
            return Market()  # Return empty Market object on error
    
    def get_orderbook(self, market_app_id: int) -> OrderBook:
        """
        Fetches and aggregates the orderbook for a given market from the Algorand blockchain.
        
        Args:
            market_app_id: The application ID of the market
            
        Returns:
            OrderBook object containing aggregated bids and asks for both YES and NO positions
            
        Raises:
            Exception: If there's an error fetching or processing the orderbook
        """
        try:
            app_info = self.algorand.app.get_by_id(market_app_id)
            indexer_client = self.algorand.client.indexer
            orders = indexer_client.lookup_account_application_by_creator(app_info.app_address)
            
            order_details = []
            for order in orders["applications"]:
                app_id = order["id"]
                app_info = indexer_client.applications(app_id)
                global_state = self._decode_global_state(app_info)
                order_details.append(global_state)
            
            logger.info(f"Fetched {len(order_details)} orders for market {market_app_id}: {order_details}")
            aggregated_orderbook = self._aggregate_orderbook(order_details)
            logger.info(f"Aggregated orderbook for market {market_app_id}: {aggregated_orderbook}")
            return aggregated_orderbook
            
        except Exception as e:
            logger.error(f"Failed to get aggregated orderbook for market {market_app_id}: {str(e)}")
            return OrderBook(yes={"bids": [], "asks": []}, no={"bids": [], "asks": []})
    
    def _decode_global_state(self, app_info: Dict) -> Dict:
        """
        Decodes the global state of an application.
        
        Args:
            app_info: Application information from the indexer
            
        Returns:
            Dict containing the decoded global state
        """
        global_state = {}
        
        if not (app_info.get("application") and 
                app_info["application"].get("params") and 
                "global-state" in app_info["application"]["params"]):
            return global_state
            
        raw_global_state = app_info["application"]["params"]["global-state"]
        
        for state_item in raw_global_state:
            try:
                key = base64.b64decode(state_item["key"]).decode()
                value = self._decode_state_value(state_item["value"], key)
                global_state[key] = value
            except Exception as e:
                logger.warning(f"Failed to decode state item: {str(e)}")
                continue
                
        return global_state
    
    def _decode_state_value(self, value: Dict, key: str) -> Any:
        """
        Decodes a single state value based on its type.
        
        Args:
            value: The state value to decode
            key: The key of the state value
            
        Returns:
            The decoded value
        """
        if value["type"] == 1:  # bytes value
            if key == "owner":
                try:
                    address_bytes = base64.b64decode(value["bytes"])
                    if len(address_bytes) == 32:
                        return encoding.encode_address(address_bytes)
                except Exception as e:
                    logger.warning(f"Failed to decode owner address: {str(e)}")
            try:
                return base64.b64decode(value["bytes"]).decode()
            except Exception:
                return value["bytes"]
        else:  # uint value
            return int(value["uint"])
    
    def _aggregate_orderbook(self, orders: List[Dict[str, Any]]) -> OrderBook:
        """
        Aggregates orders into an OrderBook structure.
        
        Args:
            orders: List of order details
            
        Returns:
            OrderBook object containing aggregated bids and asks
        """
        yes_buy_orders = self._filter_orders(orders, side=1, position=1)
        yes_sell_orders = self._filter_orders(orders, side=0, position=1)
        no_buy_orders = self._filter_orders(orders, side=1, position=0)
        no_sell_orders = self._filter_orders(orders, side=0, position=0)
        
        return OrderBook(
            yes={
                "bids": self._aggregate_orders(yes_buy_orders),
                "asks": self._aggregate_orders(yes_sell_orders)
            },
            no={
                "bids": self._aggregate_orders(no_buy_orders),
                "asks": self._aggregate_orders(no_sell_orders)
            }
        )
    
    def _filter_orders(self, orders: List[Dict[str, Any]], side: int, position: int) -> List[Dict[str, Any]]:
        """
        Filters orders based on side and position.
        
        Args:
            orders: List of order details
            side: 1 for buy, 0 for sell
            position: 1 for YES, 0 for NO
            
        Returns:
            Filtered list of orders
        """
        return [
            order for order in orders
            if (order.get('side') == side and 
                order.get('position') == position and 
                order.get('quantity', 0) > order.get('quantity_filled', 0) and 
                order.get('slippage', 0) == 0)
        ]
    
    def _aggregate_orders(self, orders: List[Dict[str, Any]]) -> List[OrderbookEntry]:
        """
        Aggregates orders at the same price level and converts micro-units to standard units.
        
        Args:
            orders: List of order details
            
        Returns:
            List of aggregated OrderbookEntry objects
        """
        price_map: Dict[int, int] = {}
    
        for order in orders:
            quantity = order.get("quantity", 0)
            quantity_filled = order.get("quantity_filled", 0)
            remaining_qty = quantity - quantity_filled
            price = order.get("price", 0)
    
            if remaining_qty > 0 and price > 0:
                price_map[price] = price_map.get(price, 0) + remaining_qty
    
        return [
            OrderbookEntry(
                price=round(price / self.MICRO_UNIT, 6),  # Convert to units, round for precision
                quantity=round(quantity / self.MICRO_UNIT, 6),
                total=round((price * quantity) / (self.MICRO_UNIT ** 2), 6)
            )
            for price, quantity in price_map.items()
        ]
    
    @staticmethod
    def calculate_fee(quantity: int, price: int, fee_base: int) -> int:
        """
        Calculate a required fee using base formula and Decimal for precision.
        Formula: fee_base * quantity * price * (1 - price) in micro-units, then ceil.
        """
        q = Decimal(str(quantity))
        p = Decimal(str(price)) / Decimal("1000000")
        fb = Decimal(str(fee_base)) / Decimal("1000000")
        fee = fb * q * p * (Decimal("1") - p)
        return math.ceil(fee)
    
    @staticmethod
    def to_micro_units(amount: float) -> int:
        """
        Convert a human-readable amount to micro-units.
        
        Args:
            amount: The amount to convert (e.g., 1.5 USDC)
            
        Returns:
            int: The amount in micro-units (e.g., 1_500_000)
        """
        return int(amount * AlphaHelper.MICRO_UNIT)
    
    @staticmethod
    def from_micro_units(amount: int) -> float:
        """
        Convert micro-units to a human-readable amount.
        
        Args:
            amount: The amount in micro-units (e.g., 1_500_000)
            
        Returns:
            float: The human-readable amount (e.g., 1.5)
        """
        return amount / AlphaHelper.MICRO_UNIT 