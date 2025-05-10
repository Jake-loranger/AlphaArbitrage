import json
import os
import asyncio
from dotenv import load_dotenv
from helpers.algo_helpers import (
    opt_in_to_asset,
    check_asset_opt_in,
    create_bet,
    cancel_bet
)
from helpers.alpha_helpers import get_alpha_market_info, get_alpha_orderbook
from helpers.the_odds_helpers import get_matchup_odds
from helpers.data_helpers import decimal_to_probability, round_to_nearest_2_digits
from models.market import Market
from helpers.log_helpers import log_data   
from helpers.orderbook_helper import get_order_book, OrderBook

load_dotenv()


async def main():
    # Read configuration from environment
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")
    ALPHA_MARKET_ID = str(os.getenv("ALPHA_MARKET_ID"))
    ODDS_MARKET_ID = os.getenv("ODDS_MARKET_ID")
    SPREAD_OFFSET = 10

    current_yes_bid_price = None
    current_no_bid_price = None
    no_escrow_app_id = None
    yes_escrow_app_id = None

    # Make market api call to alpha arcade to get market info
    response_data = await get_alpha_market_info(ALPHA_MARKET_ID)

    if response_data:
        try:
            market = Market(**response_data["market"])
            market_app_id = market.marketAppId
        except Exception as e:
            log_data(f"[ERROR] Error parsing Market model: {e}")

    # opt into the assets
    market_assets = [market.yesAssetId, market.noAssetId]
    for asset_id in market_assets:
        if not await check_asset_opt_in(asset_id):
            log_data(f"[INFO] Opting into asset {asset_id}...")
            await opt_in_to_asset(asset_id)
        else:
            log_data(f"[INFO] Already opted into asset {asset_id}.")

    while True:
        try:
            orderbook = get_order_book(market.marketAppId)

            # YES = home_team, NO = away_team
            yes_bids = orderbook.yes
            no_bids = orderbook.no

            sport_key = "baseball_mlb"
            matchup_odds = get_matchup_odds(api_key=ODDS_API_KEY, event_id=ODDS_MARKET_ID, sport=sport_key)
            if not matchup_odds:
                log_data("[ERROR] Target matchup not found. Stopping process.")
                break
    
            # # Convert home_team and away_team odds (decimal) to implied probability.
            home_team = matchup_odds["away_team"]
            away_team = matchup_odds["home_team"]
            home_odds = matchup_odds["odds"].get(home_team)
            away_odds = matchup_odds["odds"].get(away_team)
            if not home_odds or not away_odds:
                log_data("[ERROR] Odds for one or both teams not available. Stopping process.")
                break
            
            home_probability = decimal_to_probability(home_odds)
            away_probability = decimal_to_probability(away_odds)
            log_data(f"[INFO] Implied probabilities — {home_team}: {home_probability}%, {away_team}: {away_probability}%")

            home_limit_price = home_probability - SPREAD_OFFSET
            away_limit_price = away_probability - SPREAD_OFFSET
            log_data(f"[INFO] Calculated new limit prices — {home_team}: {home_limit_price}%, {away_team}: {away_limit_price}% (spread offset: {SPREAD_OFFSET})")


            YES_SHARES = 5
            NO_SHARES = 7
            
            # Handle NO (away_team) bets
            if current_no_bid_price is None:
                log_data(f"[ACTION] Creating NO bet at limit price: {away_limit_price}%")
                no_escrow_app_id = await create_bet(True, quantity=NO_SHARES*1_000_000, price=round_to_nearest_2_digits(int(away_limit_price*10000)), position=0, slippage=0, market=market)
                current_no_bid_price = away_limit_price
                log_data(f"[ACTION] Created NO bet with escrow app ID: {no_escrow_app_id}")
            elif current_no_bid_price - 3 > away_limit_price or current_no_bid_price + 3 < away_limit_price:
                log_data(f"[ACTION] Canceling current NO bet at price: {current_no_bid_price}% and creating new bet at: {away_limit_price}%")
                await cancel_bet(no_escrow_app_id, market=market)
                no_escrow_app_id = await create_bet(True, quantity=NO_SHARES*1_000_000, price=round_to_nearest_2_digits(int(away_limit_price*10000)), position=0, slippage=0, market=market)
                current_no_bid_price = away_limit_price
                log_data(f"[ACTION] Created NO bet with escrow app ID: {no_escrow_app_id}")
            else: 
                log_data(f"[INFO] No new order needed for {away_team} (NO side). Best bid is already {current_no_bid_price}%")

            # Handle YES (home_team) bets
            # if current_yes_bid_price is None:
            #     log_data(f"[ACTION] Creating YES bet at limit price: {home_limit_price}%")
            #     yes_escrow_app_id = await create_bet(True, quantity=YES_SHARES*1_000_000, price=round_to_nearest_2_digits(int(home_limit_price*10000)), position=1, slippage=0, market=market)
            #     current_yes_bid_price = home_limit_price
            #     log_data(f"[ACTION] Created YES bet with escrow app ID: {yes_escrow_app_id}")
            # elif current_yes_bid_price - 3 > home_limit_price or current_yes_bid_price + 3 < home_limit_price:
            #     log_data(f"[ACTION] Canceling current YES bet at price: {current_yes_bid_price}% and creating new bet at: {home_limit_price}%")
            #     await cancel_bet(yes_escrow_app_id, market=market)
            #     yes_escrow_app_id = await create_bet(True, quantity=YES_SHARES*1_000_000, price=round_to_nearest_2_digits(int(home_limit_price*10000)), position=1, slippage=0, market=market)
            #     current_yes_bid_price = home_limit_price
            #     log_data(f"[ACTION] Created YES bet with escrow app ID: {yes_escrow_app_id}")
            # else: 
            #     log_data(f"[INFO] No new order needed for {home_team} (YES side). Best bid is already {current_yes_bid_price}%")

        except Exception as e:
            log_data(f"[ERROR] An error occurred: {e}")

        log_data("[SLEEP] Sleeping for 1 minutes...")
        await asyncio.sleep(60)
   
if __name__ == "__main__":
    asyncio.run(main())
