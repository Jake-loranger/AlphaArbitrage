
import asyncio
import os
from helpers import algo_helpers
from helpers import alpha_helpers 
from models.market import Market

async def main():
    
    ALPHA_MARKET_ID = str(os.getenv("ALPHA_MARKET_ID"))
    response_data = await alpha_helpers.get_alpha_market_info(ALPHA_MARKET_ID)
    market = Market(**response_data["market"])
    await algo_helpers.cancel_bet(2957730882, market=market)


if __name__ == "__main__":
    asyncio.run(main())
