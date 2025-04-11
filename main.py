import os
import json
import asyncio
import time
from dotenv import load_dotenv

# Import helper modules
from helpers.algo_helpers import (
    connect_wallet,
    opt_in_to_asset,
    buy_asset,
    sell_asset,
    cancel_order,
    check_asset_opt_in,
)
from helpers.alpha_helpers import get_alpha_orderbook
from helpers.the_odds_helpers import get_upcoming_matchups_with_odds
from helpers.data_helpers import decimal_to_probability, american_to_probability

# Load environment variables from .env file
load_dotenv()

# Dummy helper to simulate placing a limit order.
def place_limit_order(algod_client, address, private_key, side, asset_id, quantity, limit_price):
    """
    Simulates placing a limit order.
    
    Args:
        algod_client: The Algorand client.
        address (str): Your wallet address.
        private_key (str): Your wallet's private key.
        side (str): "buy" or "sell".
        asset_id (int): The asset ID.
        quantity (int): Amount for the order.
        limit_price (float): The limit price (expressed as a percentage, for demo).
        
    Returns:
        str: A dummy order ID.
    """
    print(f"[Order Placement] Placing {side.upper()} order for asset {asset_id} at limit price {limit_price} for quantity {quantity}")
    # In production, this function would submit an order to your matching engine or DEX smart contract.
    dummy_order_id = f"{side}_{asset_id}_{limit_price}_{int(time.time())}"
    return dummy_order_id


async def main():
    # Read configuration from environment
    MNEMONIC = os.getenv("PRIVATE_KEY")            # Wallet mnemonic phrase
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")
    ALPHA_MARKET_APP = os.getenv("ALPHA_MARKET_APP")
    YES_ASSET_ID = int(os.getenv("YES_ASSET_ID"))
    NO_ASSET_ID = int(os.getenv("NO_ASSET_ID"))
    USDC_ASSET_ID = int(os.getenv("USDC_ASSET_ID"))
    
    # Trading parameters:
    # For this strategy, we maintain a spread offset of 2 percentage points (from 50% to 48%)
    spread_offset = 2
    order_quantity = 100  # Dummy quantity value; update as needed
    poll_interval = 30  # seconds between iterations

    # Connect to Algorand wallet and network
    algod_client, address, pk = connect_wallet(mnemonic_phrase=MNEMONIC)
    print(f"[Info] Connected wallet: {address}")

    # Ensure wallet is opted into USDC (or any required asset)
    if not check_asset_opt_in(address, USDC_ASSET_ID, algod_client):
        print(f"[OptIn] Opting into USDC asset {USDC_ASSET_ID}")
        opt_in_to_asset(algod_client, address, pk, USDC_ASSET_ID)

    # Initialize current order state as empty
    current_orders = {
        "yes": None,  # Order ID for YES side limit order
        "no": None    # Order ID for NO side limit order
    }
    # Store the current limit price for active orders (as a percentage)
    current_limit_price = None

    print("[Main] Starting main trading loop for Alpha Arcade...")

    # Start infinite loop polling odds and updating orders if necessary.
    while True:
        try:
            # Get current order book for our Alpha Arcade market
            orderbook = get_alpha_orderbook(ALPHA_MARKET_APP)
            print("[Alpha Orderbook]")
            print(json.dumps(orderbook, indent=2))
            
            # Fetch upcoming matchups & odds from the Odds API.
            # Here we assume we are interested in the matchup Red Sox vs. Yankees.
            sport_key = "baseball_mlb"
            upcoming_matchups = get_upcoming_matchups_with_odds(api_key=ODDS_API_KEY, sport=sport_key)
            target_matchup = None
            # Look for the matchup containing both "Red Sox" and "Yankees" (case insensitive)
            for matchup in upcoming_matchups:
                teams = [team.lower() for team in (matchup.get("team1", ""), matchup.get("team2", ""))]
                if "red sox" in teams and "yankees" in teams:
                    target_matchup = matchup
                    break

            if not target_matchup:
                print("[Info] Target matchup (Red Sox vs. Yankees) not found. Skipping iteration.")
                await asyncio.sleep(poll_interval)
                continue

            print("[Odds] Target matchup found:")
            print(json.dumps(target_matchup, indent=2))

            # For this strategy, we assume the market odds are even:
            # Convert team1 odds (decimal) to implied probability.
            team1_odds = target_matchup["odds"].get(target_matchup["team1"])
            if not team1_odds:
                print("[Warning] Odds for team1 not available. Skipping iteration.")
                await asyncio.sleep(poll_interval)
                continue

            market_probability = decimal_to_probability(team1_odds)
            print(f"[Odds] Current implied probability for {target_matchup['team1']} (assumed 50%% if even): {market_probability}%")

            # Determine new limit order price (for both sides) as market probability minus the offset.
            new_limit_price = market_probability - spread_offset
            print(f"[Order] Calculated new limit order price: {new_limit_price}% (spread offset: {spread_offset})")

            # Check if orders are already active at this price.
            if current_limit_price is not None and abs(new_limit_price - current_limit_price) < 0.001:
                print("[Info] Odds unchanged. Keeping existing orders. No action required.")
            else:
                # If orders exist from a previous iteration, cancel them.
                if current_orders["yes"]:
                    print(f"[Cancel] Cancelling current YES order: {current_orders['yes']}")
                    cancel_order(algod_client, address, pk, current_orders["yes"])
                    current_orders["yes"] = None

                if current_orders["no"]:
                    print(f"[Cancel] Cancelling current NO order: {current_orders['no']}")
                    cancel_order(algod_client, address, pk, current_orders["no"])
                    current_orders["no"] = None

                # Place new limit orders:
                # For this strategy, we assume that placing a buy order on each outcome is desired.
                print("[Order] Placing new limit orders with updated odds.")
                new_yes_order = place_limit_order(algod_client, address, pk, "buy", YES_ASSET_ID, order_quantity, new_limit_price)
                new_no_order = place_limit_order(algod_client, address, pk, "buy", NO_ASSET_ID, order_quantity, new_limit_price)

                # Update current order state.
                current_orders["yes"] = new_yes_order
                current_orders["no"] = new_no_order
                current_limit_price = new_limit_price

            # Wait for the next polling interval before re-checking.
            await asyncio.sleep(poll_interval)

        except Exception as e:
            print(f"[Error] Exception in main loop: {e}")
            # Optionally log error and continue or break.
            await asyncio.sleep(poll_interval)

if __name__ == "__main__":
    # Run main loop asynchronously.
    asyncio.run(main())
