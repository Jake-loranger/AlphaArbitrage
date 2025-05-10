from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class Outcome(BaseModel):
    """
    Represents a betting outcome with its name, price, and optional point spread.
    
    Attributes:
        name (str): The name of the outcome (e.g., team name)
        price (float): The decimal odds price for this outcome
        point (Optional[float]): The point spread for this outcome, if applicable
    """
    name: str = Field(description="The name of the outcome (e.g., team name)")
    price: float = Field(description="The decimal odds price for this outcome")
    point: Optional[float] = Field(None, description="The point spread for this outcome, if applicable")

class Market(BaseModel):
    """
    Represents a betting market with its key, last update time, and list of outcomes.
    
    Attributes:
        key (str): The market type (e.g., 'h2h', 'spreads')
        last_update (datetime): When this market was last updated
        outcomes (List[Outcome]): List of possible outcomes for this market
    """
    key: str = Field(description="The market type (e.g., 'h2h', 'spreads')")
    last_update: datetime = Field(description="When this market was last updated")
    outcomes: List[Outcome] = Field(description="List of possible outcomes for this market")

class Bookmaker(BaseModel):
    """
    Represents a bookmaker with their key, title, last update time, and available markets.
    
    Attributes:
        key (str): The bookmaker's unique identifier
        title (str): The bookmaker's display name
        last_update (datetime): When this bookmaker's odds were last updated
        markets (List[Market]): List of markets offered by this bookmaker
    """
    key: str = Field(description="The bookmaker's unique identifier")
    title: str = Field(description="The bookmaker's display name")
    last_update: datetime = Field(description="When this bookmaker's odds were last updated")
    markets: List[Market] = Field(description="List of markets offered by this bookmaker")

class OddsOrderbook(BaseModel):
    """
    Represents a complete odds orderbook for a sporting event.
    
    Attributes:
        id (str): Unique identifier for the event
        sport_key (str): The sport's unique identifier
        sport_title (str): The sport's display name
        commence_time (datetime): When the event starts
        home_team (str): Name of the home team
        away_team (str): Name of the away team
        bookmakers (List[Bookmaker]): List of bookmakers offering odds for this event
    """
    id: str = Field(description="Unique identifier for the event")
    sport_key: str = Field(description="The sport's unique identifier")
    sport_title: str = Field(description="The sport's display name")
    commence_time: datetime = Field(description="When the event starts")
    home_team: str = Field(description="Name of the home team")
    away_team: str = Field(description="Name of the away team")
    bookmakers: List[Bookmaker] = Field(description="List of bookmakers offering odds for this event")