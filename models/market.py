from typing import Dict, List, Optional
from pydantic import BaseModel, HttpUrl


class ShareImageItem(BaseModel):
    image: HttpUrl
    text: str


class ShareImage(BaseModel):
    yes: ShareImageItem
    no: ShareImageItem


class Market(BaseModel):
    lastRewardAmount: int
    feeAddress: str
    noAssetId: int
    topic: str
    feeTimerThreshhold: int
    marketFriend: str
    volume: float
    rewardsPaidOut: int
    fees: int
    marketAppId: int
    image: HttpUrl
    compressedRules: HttpUrl
    SK: str
    id: str
    featured: bool
    marketVolume: float
    dataType: str
    rules: str
    shareImage: ShareImage
    createdRound: int
    slug: str
    comments: int
    createdAt: int
    lastRewardTs: int
    noProb: int
    endTs: int
    feeBasePercent: int
    currentSpread: int
    totalRewards: int
    currentMidpoint: int
    categories: List[str]
    lastTradePrice: int
    updatedAt: int
    rewardsSpreadDistance: int
    rewardsMinContracts: int
    oracle: str
    PK: str
    liveTs: int
    yesProb: int
    yesAssetId: int
    lastTradePrices: Dict[str, int]
