from decimal import Decimal
import math
import requests
from dotenv import load_dotenv

async def get_alpha_market_info(market_id: str) -> dict:
    """
    Fetches the information for a given Alpha Arcade market by calling the API.
    
    Args:
        market_id (str): The unique identifier for the market.
        
    Returns:
        dict: The market information including details like volume, fees, and rules.
    """
    url = f"https://g08245wvl7.execute-api.us-east-1.amazonaws.com/api/get-market?marketId={market_id}"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Received status code {response.status_code}")
            return {}
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}


def get_alpha_orderbook(market_app_id: str) -> dict:
    """
    Fetches the order book for a given Alpha Arcade market by calling the API.
    
    Args:
        market_id (str): The unique identifier for the market.
        
    Returns:
        dict: The order book containing bids and asks for both 'yes' and 'no' outcomes.
    """
    url = f"https://g08245wvl7.execute-api.us-east-1.amazonaws.com/api/get-full-orderbook?marketId={market_app_id}"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Received status code {response.status_code}")
            return {}
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}
    
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
