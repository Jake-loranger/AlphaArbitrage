import requests
import json

def get_poly_markets() -> dict:
    """
    Fetches the Active markets on Polymarkets
        
    Returns:
        dict: The active markets on polymarket and the basic information assocaited with them
    """
    url = f"https://gamma-api.polymarket.com/markets?closed=false&limit=100000"

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
    

def get_poly_market(market_id: str) -> dict:
    """
    Fetches the market data for a given Polymarket market by calling the API.
    
    Args:
        market_id (str): The unique identifier for the market.
        
    Returns:
        dict: The market data containing information about the market, such as question, outcomes, and prices.
    """
    url = f"https://gamma-api.polymarket.com/markets/{market_id}"

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
    

def get_poly_odds(market_data) -> dict:
    """
    Extracts and returns the odds for each outcome (Yes/No) from the market data.
    
    Args:
        market_data (dict or str): The market data, either as a dictionary or a JSON string.
        
    Returns:
        dict: A dictionary with the outcomes ('Yes' and 'No') as keys, and the corresponding prices as values.
    """
    if isinstance(market_data, str):
        market_data = json.loads(market_data)
    
    outcomes = json.loads(market_data.get("outcomes", "[]"))
    outcome_prices = json.loads(market_data.get("outcomePrices", "[]"))
    
    result = {}
    for outcome, price in zip(outcomes, outcome_prices):
        result[outcome] = float(price) * 100  # Convert the price to a percentage
    
    return result