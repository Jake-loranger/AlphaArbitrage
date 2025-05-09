import asyncio
from helpers.algorand_helper import AlgorandHelper
from helpers.alpha_helper import AlphaHelper
from helpers.odds_helper import OddsAPIHelper

async def main():

    MARKET_ID = "ALPHA_MARKET_ID"  # Replace with actual market ID
    ODDS_MARKET_ID = "ODDS_MARKET_ID"  # Replace with actual odds market ID

    # Initialize the helpers
    algo = AlgorandHelper()
    alpha = AlphaHelper()
    odds = OddsAPIHelper()

    # Get market information # Replace with actual market ID
    market = await alpha.get_market_info(MARKET_ID)

    # Get odds for sports
    matchup_odds = odds.get_matchup_odds(  
        event_id=ODDS_MARKET_ID
    )

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

    
if __name__ == "__main__":
    asyncio.run(main()) 