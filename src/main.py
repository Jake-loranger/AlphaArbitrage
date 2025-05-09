import asyncio
from helpers.algorand_helper import AlgorandHelper
from helpers.alpha_helper import AlphaHelper
from helpers.odds_helper import OddsAPIHelper
from math import log10, floor

def round_to_nearest_2_digits(x):
    """
    Rounds a number to the nearest value with two significant digits.

    For example:
    - 356200 becomes 360000
    - 724 becomes 720
    - 0 remains 0

    Args:
        x (int or float): The number to round.

    Returns:
        int: The rounded number.
    """
    from math import log10, floor
    if x == 0:
        return 0
    digits = int(floor(log10(abs(x))))
    return round(x, -digits + 1)

async def main():

    MARKET_ID = "01JTGR27C84ZKV68TA8FE5GBEY" 
    ODDS_MARKET_ID = "fe3e8dc29347048c12b0e42752801b15"

    # Initialize the helpers
    algo = AlgorandHelper()
    alpha = AlphaHelper()
    odds = OddsAPIHelper()

    # Get market information # Replace with actual market ID
    market = await alpha.get_market_info(MARKET_ID)

    # Get odds for sports
    # matchup_odds = odds.get_matchup_odds(  
    #     event_id=ODDS_MARKET_ID
    # )

    # get current orderbook
    alpha_orderbook = alpha.get_orderbook(
        market_app_id=market.marketAppId
    )
    
    # create a bet
    escrow_app_id = await algo.create_bet(
        is_buying=True, 
        quantity=1, 
        price=0.10, 
        position=0, 
        slippage=0, 
        market=market
    )
    print(f"Escrow app id: {escrow_app_id}")

    
if __name__ == "__main__":
    asyncio.run(main()) 