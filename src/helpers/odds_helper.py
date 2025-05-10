import requests
from helpers.log_helpers import get_logger
from config import get_settings
from models.odds_orderbook import OddsOrderbook
from typing import Optional
import json


logger = get_logger(__name__)

class OddsAPIHelper:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.ODDS_API_KEY
        self.region = "us"
        self.market = "h2h,spreads"  # Include both h2h and spreads markets
        self.base_url = "https://api.the-odds-api.com/v4/sports"
        
        if not self.api_key:
            logger.warning("ODDS_API_KEY not found in environment variables")

    def get_matchup_odds(self, sport: str, event_id: str) -> Optional[OddsOrderbook]:
        """
        Fetches details (team names and odds) for a specific event using its event_id.
        Returns an OddsOrderbook object if found, None otherwise.
        """
        url = f"{self.base_url}/{sport}/odds/"
        params = {
            "regions": self.region,
            "markets": self.market,
            "apiKey": self.api_key,
            "eventIds": event_id
        }
        
        logger.debug(f"Making request to: {url}")
        logger.debug(f"With params: {json.dumps(params, indent=2)}")
        
        try:
            response = requests.get(url, params=params)
            logger.debug(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Error fetching odds data: {response.status_code} - {response.text}")
                return None
                
            data = response.json()
            logger.debug(f"Raw API response: {json.dumps(data, indent=2)}")
            
            if not data:
                logger.warning(f"Event with id {event_id} not found")
                return None
                
            # Create OddsOrderbook object from the first (and should be only) event
            try:
                odds_orderbook = OddsOrderbook(**data[0])
                logger.debug(f"Created OddsOrderbook: {odds_orderbook.model_dump_json(indent=2)}")
                return odds_orderbook
            except Exception as e:
                logger.error(f"Failed to create OddsOrderbook: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to fetch odds data: {str(e)}")
            return None