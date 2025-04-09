import os
from dotenv import load_dotenv
from helpers.algo_helpers import connect_wallet, check_asset_opt_in, opt_in_to_asset
from helpers.polymarket_helpers import get_poly_market, get_poly_odds
from helpers.alpha_helpers import get_alpha_orderbook

load_dotenv()

# ALPHA_MARKET_ID = os.getenv("ALPHA_MARKET_ID")
# POLY_MARKET_ID = os.getenv("POLY_MARKET_ID")
# MNEMONIC_PHRASE = os.getenv("MNEMONIC_PHRASE")
# ALPHA_MARKET_APP_ID = int(os.getenv("ALPHA_MARKET_APP_ID"))
# YES_ASSET_ID = int(os.getenv("YES_ASSET_ID"))
# NO_ASSET_ID = int(os.getenv("NO_ASSET_ID"))
# USDC_ASSET_ID = int(os.getenv("USDC_ASSET_ID"))

def main():
    # algod_client, address, private_key = connect_wallet(MNEMONIC_PHRASE)

    # for asset_id in [USDC_ASSET_ID, YES_ASSET_ID, NO_ASSET_ID]:
    #     if not check_asset_opt_in(address, asset_id, algod_client):
    #         opt_in_to_asset(algod_client, address, private_key, asset_id)
    #     else:
    #         print(f"Already opted into asset {asset_id}")

    # Example usage
    market_id = "506742"
    market_data = get_poly_market(market_id)
    if market_data:
        odds = get_poly_odds(market_data)
        print(odds)

    # Get AA odds
    market_id = "01JPVHGRMKB2WAGK645SJJ4Y1Z"
    order_book = get_alpha_orderbook(market_id)
    print(order_book)

    # Buy/Sell assets based on data and difference and max loss on that side is not hit


if __name__ == "__main__":
    main()