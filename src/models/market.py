from typing import Optional, List, Dict
from pydantic import BaseModel, HttpUrl
from datetime import datetime

class ShareImageItem(BaseModel):
    """Represents a shareable image item with optional image URL and text."""
    image: Optional[HttpUrl] = None
    text: Optional[str] = None

class ShareImage(BaseModel):
    """Represents shareable images for both YES and NO positions."""
    yes: Optional[ShareImageItem] = None
    no: Optional[ShareImageItem] = None

class Market(BaseModel):
    """Represents a prediction market with all its properties."""
    # Market Identification
    id: Optional[str] = None
    marketAppId: Optional[int] = None
    slug: Optional[str] = None
    topic: Optional[str] = None
    
    # Asset Information
    yesAssetId: Optional[int] = None
    noAssetId: Optional[int] = None
    yesTeamColor: Optional[str] = None
    noTeamColor: Optional[str] = None
    
    # Market State
    yesProb: Optional[int] = None
    noProb: Optional[int] = None
    currentMidpoint: Optional[int] = None
    currentSpread: Optional[int] = None
    lastTradePrice: Optional[int] = None
    lastTradePrices: Optional[Dict[str, int]] = None
    
    # Market Details
    rules: Optional[str] = None
    compressedRules: Optional[HttpUrl] = None
    image: Optional[HttpUrl] = None
    shareImage: Optional[ShareImage] = None
    categories: Optional[List[str]] = None
    featured: Optional[bool] = None
    
    # Market Metrics
    volume: Optional[float] = None
    marketVolume: Optional[float] = None
    fees: Optional[int] = None
    totalRewards: Optional[int] = None
    rewardsPaidOut: Optional[int] = None
    lastRewardAmount: Optional[int] = None
    
    # Market Configuration
    feeAddress: Optional[str] = None
    feeBasePercent: Optional[int] = None
    feeTimerThreshhold: Optional[int] = None
    marketFriend: Optional[str] = None
    oracle: Optional[str] = None
    
    # Reward Configuration
    rewardsSpreadDistance: Optional[int] = None
    rewardsMinContracts: Optional[int] = None
    
    # Timestamps and Rounds
    createdAt: Optional[int] = None
    updatedAt: Optional[int] = None
    liveTs: Optional[int] = None
    endTs: Optional[int] = None
    createdRound: Optional[int] = None
    lastRewardTs: Optional[int] = None
    
    # Additional Metadata
    comments: Optional[int] = None
    dataType: Optional[str] = None
    PK: Optional[str] = None
    SK: Optional[str] = None

    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True 