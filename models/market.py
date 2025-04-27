from typing import Optional, List, Dict
from pydantic import BaseModel, HttpUrl

class ShareImageItem(BaseModel):
    image: Optional[HttpUrl] = None
    text: Optional[str] = None

class ShareImage(BaseModel):
    yes: Optional[ShareImageItem] = None
    no: Optional[ShareImageItem] = None

class Market(BaseModel):
    lastRewardAmount: Optional[int]          = None
    feeAddress:         Optional[str]        = None
    noAssetId:          Optional[int]        = None
    topic:              Optional[str]        = None
    feeTimerThreshhold: Optional[int]        = None
    marketFriend:       Optional[str]        = None
    volume:             Optional[float]      = None
    rewardsPaidOut:     Optional[int]        = None
    fees:               Optional[int]        = None
    marketAppId:        Optional[int]        = None
    image:              Optional[HttpUrl]    = None
    compressedRules:    Optional[HttpUrl]    = None
    SK:                 Optional[str]        = None
    id:                 Optional[str]        = None
    featured:           Optional[bool]       = None
    marketVolume:       Optional[float]      = None
    dataType:           Optional[str]        = None
    rules:              Optional[str]        = None
    shareImage:         Optional[ShareImage] = None
    createdRound:       Optional[int]        = None
    slug:               Optional[str]        = None
    comments:           Optional[int]        = None
    createdAt:          Optional[int]        = None
    lastRewardTs:       Optional[int]        = None
    noProb:             Optional[int]        = None
    endTs:              Optional[int]        = None
    feeBasePercent:     Optional[int]        = None
    currentSpread:      Optional[int]        = None
    totalRewards:       Optional[int]        = None
    currentMidpoint:    Optional[int]        = None
    categories:         Optional[List[str]]  = None
    lastTradePrice:     Optional[int]        = None
    updatedAt:          Optional[int]        = None
    rewardsSpreadDistance: Optional[int]    = None
    rewardsMinContracts: Optional[int]      = None
    oracle:             Optional[str]        = None
    PK:                 Optional[str]        = None
    liveTs:             Optional[int]        = None
    yesProb:            Optional[int]        = None
    yesAssetId:         Optional[int]        = None
    lastTradePrices:    Optional[Dict[str, int]] = None
