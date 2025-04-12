import requests

def get_matchup_odds(api_key, sport, event_id, region="us", market="h2h"):
    """
    Fetches details (team names and odds) for a specific event using its event_id.
    
    Parameters:
        api_key (str): Your Odds API key.
        sport (str): The sport key (e.g., 'baseball_mlb').
        event_id (str): The unique ID of the event you want details for.
        region (str): Betting region (default is 'us').
        market (str): Betting market (default is 'h2h').
    
    Returns:
        dict: A dictionary containing:
              - event_id: The unique event identifier.
              - home_team: The home team.
              - away_team: The away team.
              - odds: A dictionary mapping team names to their odds.
    
    Raises:
        Exception: If the API request fails or the event_id is not found.
    """
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
    params = {
        "regions": region,
        "markets": market,
        "apiKey": api_key
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code} - {response.text}")
    
    events = response.json()
    
    for event in events:
        if event.get("id") == event_id:
            # Extract team names using the correct keys
            home_team = event.get("home_team")
            away_team = event.get("away_team")
            
            # Assuming that we want to use odds from the first bookmaker and first market
            bookmakers = event.get("bookmakers", [])
            odds = {}
            if bookmakers:
                markets = bookmakers[0].get("markets", [])
                if markets:
                    outcomes = markets[0].get("outcomes", [])
                    odds = { outcome["name"]: outcome["price"] for outcome in outcomes }
            
            return {
                "event_id": event_id,
                "home_team": home_team,
                "away_team": away_team,
                "odds": odds
            }
    
    # If event_id was not found among returned events:
    raise Exception(f"Event with id {event_id} not found.")