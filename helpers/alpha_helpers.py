import requests
from dotenv import load_dotenv


def get_alpha_orderbook(market_id: str) -> dict:
    """
    Fetches the order book for a given Alpha Arcade market by calling the API.
    
    Args:
        market_id (str): The unique identifier for the market.
        
    Returns:
        dict: The order book containing bids and asks for both 'yes' and 'no' outcomes.
    """
    url = f"https://g08245wvl7.execute-api.us-east-1.amazonaws.com/api/get-full-orderbook?marketId={market_id}"
    
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