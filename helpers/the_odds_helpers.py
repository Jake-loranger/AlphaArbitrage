import requests

def get_upcoming_matchups_with_odds(api_key, sport, region="us", market="h2h"):
    '''
    Fetches upcoming matchups and odds from The Odds API.

    Returns a list of dictionaries containing:
        - event_id: Unique game ID
        - team1: First team
        - team2: Second team
        - odds: Dictionary with odds for each team from the first bookmaker

    Parameters:
        api_key (str): Your Odds API key
        sport (str): The sport key (e.g., 'basketball_nba', 'americanfootball_nfl', 'baseball_mlb)
        region (str): Betting region (e.g., 'us', 'uk', etc.)
        market (str): Betting market (usually 'h2h')

    Returns:
        list of dicts
    '''
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
    params = {
        "regions": region,
        "markets": market,
        "apiKey": api_key
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code} - {response.text}")

    data = response.json()
    results = []

    for event in data:
        event_id = event.get("id")
        teams = event.get("teams", [])
        bookmakers = event.get("bookmakers", [])

        if len(teams) == 2 and bookmakers:
            # Get the first bookmaker's head-to-head odds
            h2h_odds = bookmakers[0].get("markets", [])[0].get("outcomes", [])

            odds = { outcome["name"]: outcome["price"] for outcome in h2h_odds }

            results.append({
                "event_id": event_id,
                "team1": teams[0],
                "team2": teams[1],
                "odds": odds
            })

    return results
