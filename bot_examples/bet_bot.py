
import asyncio
from helpers import algo_helpers

async def main():
    await algo_helpers.create_bet(is_buying=True, quantity=1_000_000, price=990_000, slippage=0, position=0, market=None)

if __name__ == "__main__":
    asyncio.run(main())
