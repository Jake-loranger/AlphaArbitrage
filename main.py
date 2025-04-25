import os
import json
import asyncio
import time
import algokit_utils
from dotenv import load_dotenv
from helpers import algo_helpers
from helpers.algo_helpers import (
    connect_wallet,
    opt_in_to_asset,
    check_asset_opt_in,
    create_bet,
    cancel_bet
)
from helpers.alpha_helpers import get_alpha_orderbook
from helpers.the_odds_helpers import get_matchup_odds
from helpers.data_helpers import decimal_to_probability, american_to_probability

load_dotenv()

async def main():
    # Read configuration from environment
    MNEMONIC = os.getenv("PRIVATE_KEY") 
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")
    ALPHA_MARKET_APP = os.getenv("ALPHA_MARKET_APP")
    YES_ASSET_ID = int(os.getenv("YES_ASSET_ID"))
    NO_ASSET_ID = int(os.getenv("NO_ASSET_ID"))
    USDC_ASSET_ID = int(os.getenv("USDC_ASSET_ID"))
    ODDS_MARKET_ID = os.getenv("ODDS_MARKET_ID")
    
    # Trading parameters:
    # spread_offset = 2
    # order_quantity = 100  # Dummy quantity value; update as needed
    # poll_interval = 6000  # milliseconds between iterations

    # # Connect to Algorand wallet and network
    # algod_client, address, pk = connect_wallet(mnemonic_phrase=MNEMONIC)
    # print(f"[Info] Connected wallet: {address}")

    # # Ensure wallet is opted into USDC (or any required asset)
    # if not check_asset_opt_in(address, USDC_ASSET_ID, algod_client):
    #     print(f"[OptIn] Opting into USDC asset {USDC_ASSET_ID}, YES asset {YES_ASSET_ID}, and NO asset {NO_ASSET_ID}")
    #     opt_in_to_asset(algod_client, address, pk, USDC_ASSET_ID)
    #     opt_in_to_asset(algod_client, address, pk, YES_ASSET_ID)
    #     opt_in_to_asset(algod_client, address, pk, NO_ASSET_ID)

    # print("[Main] Starting main trading loop for Alpha Arcade...")
    # while True:
    #     try:
    #         # Get current order book for our Alpha Arcade market.
    #         orderbook = get_alpha_orderbook(2829831047)
    #         # print("[Alpha Orderbook]")
    #         # print(json.dumps(orderbook, indent=2))

    #         # YES = home_team, NO = away_team
    #         yes_bids = orderbook[str(2921928414)]["yes"]["bids"]
    #         no_bids = orderbook[str(2921928414)]["no"]["bids"]

    #         # Get best current bid prices (convert to decimal %)
    #         best_yes_bid_price = yes_bids[0]["price"] / 10000 if yes_bids else None
    #         best_no_bid_price = no_bids[0]["price"] / 10000 if no_bids else None
    #         print(f"[Orderbook] Best YES (home) bid: {best_yes_bid_price}%, Best NO (away) bid: {best_no_bid_price}%")

    #         # Fetch upcoming matchups & odds from the Odds API.
    #         sport_key = "baseball_mlb"
    #         matchup_odds = get_matchup_odds(api_key=ODDS_API_KEY, event_id=ODDS_MARKET_ID, sport=sport_key)
    #         # print("[Odds API] Upcoming matchups:")

    #         if not matchup_odds:
    #             print("[Info] Target matchup not found. Stopping process.")
    #             break

    #         # print("[Odds] Target matchup found:")
    #         # print(json.dumps(matchup_odds, indent=2))
    
    #         # # Convert home_team and away_team odds (decimal) to implied probability.
    #         home_team = matchup_odds["away_team"]
    #         away_team = matchup_odds["home_team"]
    #         home_odds = matchup_odds["odds"].get(home_team)
    #         away_odds = matchup_odds["odds"].get(away_team)

    #         if not home_odds or not away_odds:
    #             print("[Error] Odds for one or both teams not available. Stopping process.")
    #             break
            
    #         home_probability = decimal_to_probability(home_odds)
    #         away_probability = decimal_to_probability(away_odds)
    #         print(f"[Odds] Implied probabilities — {home_team}: {home_probability}%, {away_team}: {away_probability}%")

    #         home_limit_price = home_probability - spread_offset
    #         away_limit_price = away_probability - spread_offset
    #         print(f"[Order] Calculated new limit prices — {home_team}: {home_limit_price}%, {away_team}: {away_limit_price}% (spread offset: {spread_offset})")

    #         # Determine action for home team (YES side)
    #         if best_yes_bid_price is None or best_yes_bid_price < home_limit_price:
    #             print(f"[Action] Set new limit order at {home_limit_price}% for {home_team} (YES side)")
    #         else:
    #             print(f"[Action] No new order needed for {home_team} (YES side). Best bid is already {best_yes_bid_price}%")

    #         # Determine action for away team (NO side)
    #         if best_no_bid_price is None or best_no_bid_price < away_limit_price:
    #             print(f"[Action] Set new limit order at {away_limit_price}% for {away_team} (NO side)")
    #         else:
    #             print(f"[Action] No new order needed for {away_team} (NO side). Best bid is already {best_no_bid_price}%")

    #         await asyncio.sleep(poll_interval)

    #     except Exception as e:
    #         print(f"[Error] Exception in main loop: {e}")
    #         print(f"[Error] Process Stopping. Please check the logs.")
    #         break
    # await algo_helpers.create_bet(is_buying=True, quantity=100_000, price=10_000, slippage=0, position=0, market=None)
    # await algo_helpers.cancel_bet(escrow_app_id=2953106831, market_app_id=2829831047)

if __name__ == "__main__":
    asyncio.run(main())
