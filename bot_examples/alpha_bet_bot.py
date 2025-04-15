"""
Alpha Arcade Betting Bot

This script creates a group transaction to place a bet on Alpha Arcade using an escrow order.
It combines payment transactions, asset transfers, and application calls in a single atomic group.

Requirements:
- python-dotenv: For loading environment variables
- algokit-utils: For Algorand blockchain interactions
- algosdk: The Algorand SDK for Python

Setup:
Create a .env file with:
SENDER_MNEMONIC="your 25-word mnemonic phrase"
MARKET_ADDRESS="Alpha Arcade market address"
MARKET_APP_ID=123456  # The application ID for the Alpha Arcade contract
USDC_ASSET_ID=10458941  # USDC asset ID
YES_ASSET_ID=123456  # YES token asset ID
NO_ASSET_ID=123457  # NO token asset ID
"""

import os
import math
import time
from dotenv import load_dotenv
from algosdk import mnemonic, account
from algosdk.transaction import PaymentTxn, AssetTransferTxn
from algokit_utils import AlgorandClient
from algosdk.transaction import ApplicationCallTxn
from algosdk.atomic_transaction_composer import AtomicTransactionComposer, TransactionWithSigner
from algosdk.atomic_transaction_composer import AccountTransactionSigner
# Load environment variables
load_dotenv()

# Helper function to convert to microAlgos
def micro_algos(amount):
    return int(amount)

# Helper function to check if account has opted into an asset
async def check_asset_opt_in(address, asset_id, algod_client):
    account_info = algod_client.account_info(address)
    for asset in account_info.get("assets", []):
        if asset["asset-id"] == asset_id:
            return True
    return False

async def create_bet(
    is_buying: bool,  # True if buying YES/NO tokens, False if selling
    quantity: int,    # Quantity of tokens
    price: int,       # Price per token in microUSDC (1000000 = 1 USDC)
    position: int,    # 1 for YES, 0 for NO
    fee: int = 1000   # Fee in microUSDC
):
    # Get configuration from environment variables
    sender_mnemonic = os.getenv("SENDER_MNEMONIC")
    if not sender_mnemonic:
        print("Error: SENDER_MNEMONIC not found in environment variables")
        return
    
    market_address = os.getenv("MARKET_ADDRESS")
    if not market_address:
        print("Error: MARKET_ADDRESS not found in environment variables")
        return
    
    market_app_id = int(os.getenv("MARKET_APP_ID", "0"))
    if market_app_id == 0:
        print("Error: MARKET_APP_ID not found in environment variables")
        return
    
    usdc_asset_id = int(os.getenv("USDC_ASSET_ID", "31566704"))
    yes_asset_id = int(os.getenv("YES_ASSET_ID", "0"))
    no_asset_id = int(os.getenv("NO_ASSET_ID", "0"))
    
    if yes_asset_id == 0 or no_asset_id == 0:
        print("Error: YES_ASSET_ID or NO_ASSET_ID not found in environment variables")
        return
    
    # Connect to Algorand network
    algorand = AlgorandClient.mainnet()  # Use .test_net() for testing
    algod_client = algorand.client.algod
    
    # Get sender account from mnemonic
    private_key = mnemonic.to_private_key(sender_mnemonic)
    sender_address = account.address_from_private_key(private_key)
    
    # Create a signer object
    signer = AccountTransactionSigner(private_key)
    
    print(f"Sender account: {sender_address}")
    print(f"Market address: {market_address}")
    print(f"{'Buying' if is_buying else 'Selling'} {'YES' if position == 1 else 'NO'} tokens")
    print(f"Quantity: {quantity}, Price: {price/1000000} USDC per token")
    
    # Create market data structure similar to the example
    market = {
        "marketAppId": market_app_id,
        "yesAssetId": yes_asset_id,
        "noAssetId": no_asset_id
    }
    
    # Get suggested parameters
    sp = algod_client.suggested_params()
    
    try:
        # Create AtomicTransactionComposer
        atc = AtomicTransactionComposer()
        
        # 1) Transfer ALGO to cover escrow contract cost
        payment_txn = PaymentTxn(
            sender=sender_address,
            sp=sp,
            receiver=market_address,
            amt=micro_algos(967600),
            note=b"Escrow ALGO Funding"
        )
        txn_with_signer = TransactionWithSigner(payment_txn, signer)
        atc.add_transaction(txn_with_signer)
        
        # 2) Transfer correct asset (USDC if buying, or YES/NO if selling)
        asset_id = usdc_asset_id if is_buying else (
            yes_asset_id if position == 1 else no_asset_id
        )
        
        fund_amount = (math.floor(quantity * price / 1000000) + fee) if is_buying else math.floor(quantity)
        
        asset_transfer_txn = AssetTransferTxn(
            sender=sender_address,
            sp=sp,
            receiver=market_address,
            amt=fund_amount,
            index=asset_id,
            note=b"Escrow Asset Funding"
        )
        txn_with_signer = TransactionWithSigner(asset_transfer_txn, signer)
        atc.add_transaction(txn_with_signer)

        # 3) Create escrow on market
        app_args = [
            b"create_escrow",
            price.to_bytes(8, 'big') if is_buying else (1000000 - price).to_bytes(8, 'big'),
            quantity.to_bytes(8, 'big'),
            (0).to_bytes(8, 'big'),  # slippage
            position.to_bytes(8, 'big')
        ]
        
        foreign_assets = [usdc_asset_id, yes_asset_id, no_asset_id]
        
        app_call_txn = ApplicationCallTxn(
            sender=sender_address,
            sp=sp,
            index=market_app_id,
            on_complete=0,  # NoOp
            app_args=app_args,
            foreign_assets=foreign_assets
        )
        
        txn_with_signer = TransactionWithSigner(app_call_txn, signer)
        atc.add_transaction(txn_with_signer)

        # 4) Opt-in if needed
        if not is_buying:
            # If selling, might need USDC opt-in
            has_usdc_opt_in = await check_asset_opt_in(sender_address, usdc_asset_id, algod_client)
            if not has_usdc_opt_in:
                opt_in_txn = AssetTransferTxn(
                    sender=sender_address,
                    sp=sp,
                    receiver=sender_address,
                    amt=0,
                    index=usdc_asset_id,
                    note=b"Opt-in USDC"
                )
                txn_with_signer = TransactionWithSigner(opt_in_txn, signer)
                atc.add_transaction(txn_with_signer)
        else:
            # If buying, check opt-in for (YES or NO)
            opt_asset_id = yes_asset_id if position == 1 else no_asset_id
            has_opt_in = await check_asset_opt_in(sender_address, opt_asset_id, algod_client)
            if not has_opt_in:
                opt_in_txn = AssetTransferTxn(
                    sender=sender_address,
                    sp=sp,
                    receiver=sender_address,
                    amt=0,
                    index=opt_asset_id,
                    note=f"Opt-in asset {opt_asset_id}".encode()
                )
                txn_with_signer = TransactionWithSigner(opt_in_txn, signer)
                atc.add_transaction(txn_with_signer)
                
        
        print("Submitting transaction group...")
        result = atc.execute(algod_client, 4)  # Wait for up to 4 rounds
        
        print(f"Bet placed successfully! Transaction ID: {result.tx_ids[0]}")
        print(f"Transaction confirmed in round: {result.confirmed_round}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")


async def main():
    await create_bet(
    is_buying=True,
    quantity=1,
    price=730000,  # 0.73 USDC in micro units
    position=0     # 0 = NO position
)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())