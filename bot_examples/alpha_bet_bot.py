"""
Alpha Arcade Betting Bot

This script creates a group transaction to place a bet on Alpha Arcade using an escrow order.
It combines a payment transaction, asset transfer, and application call in a single atomic group.

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
from decimal import Decimal
import os
import math
import time
import asyncio
import algosdk
from dotenv import load_dotenv
from algosdk import mnemonic, account
from algosdk.transaction import PaymentTxn, AssetTransferTxn
from algosdk.atomic_transaction_composer import AtomicTransactionComposer, TransactionWithSigner, AccountTransactionSigner
from algosdk.abi import Method
from algosdk.abi.method import Argument, Returns
from algosdk.error import AlgodHTTPError
from algokit_utils import AlgorandClient

# Load environment variables
load_dotenv()

# Helper: convert to microAlgos
def micro_algos(amount):
    return int(amount)

# Simple wait-for-confirmation
def wait_for_confirmation(client, txid, timeout=10):
    start = time.time()
    while True:
        try:
            result = client.pending_transaction_info(txid)
            if result.get("confirmed-round", 0) > 0:
                return result
        except Exception:
            pass
        if time.time() - start > timeout:
            raise Exception(f"Transaction not confirmed after {timeout}s")
        time.sleep(1)

# Check if account is opted into an asset
async def check_asset_opt_in(address, asset_id, algod_client):
    info = algod_client.account_info(address)
    for asset in info.get("assets", []):
        if asset.get("asset-id") == asset_id:
            return True
    return False

def calculate_fee(quantity: int, price: int, fee_base: int) -> int:
    """
    Calculate a required fee using base formula and Decimal for precision.
    Formula: fee_base * quantity * price * (1 - price) in micro-units, then ceil.
    """
    q = Decimal(str(quantity))
    p = Decimal(str(price)) / Decimal("1000000")
    fb = Decimal(str(fee_base)) / Decimal("1000000")
    fee = fb * q * p * (Decimal("1") - p)
    return math.ceil(fee)

async def create_bet(
    is_buying: bool,
    quantity: int,
    price: int,
    position: int,
    slippage: int
):
    # Load config
    sender_mnemonic = os.getenv("SENDER_MNEMONIC")
    market_address  = os.getenv("MARKET_ADDRESS")
    market_app_id   = int(os.getenv("MARKET_APP_ID", "0"))
    usdc_asset_id   = int(os.getenv("USDC_ASSET_ID", "0"))
    yes_asset_id    = int(os.getenv("YES_ASSET_ID", "0"))
    no_asset_id     = int(os.getenv("NO_ASSET_ID", "0"))

    if not all([sender_mnemonic, market_address, market_app_id, usdc_asset_id, yes_asset_id, no_asset_id]):
        raise Exception("Missing environment variables")

    # Setup clients and keys
    algorand = AlgorandClient.mainnet()
    algod_client = algorand.client.algod
    private_key = mnemonic.to_private_key(sender_mnemonic)
    sender_address = account.address_from_private_key(private_key)
    signer = AccountTransactionSigner(private_key)

    print(f"Sender: {sender_address}\nMarket App ID: {market_app_id}")
    print(f"{'Buying' if is_buying else 'Selling'} {'YES' if position else 'NO'} tokens: qty={quantity}, price={price/1e6} USDC")

    sp = algod_client.suggested_params()
    
    fund_asset_id = usdc_asset_id if is_buying else (yes_asset_id if position == 1 else no_asset_id)
    opt_asset_id = yes_asset_id if is_buying and position == 1 else (
                   no_asset_id  if is_buying and position == 0 else (
                   usdc_asset_id if not is_buying else usdc_asset_id))

    # Pre-opt-in if needed
    if not await check_asset_opt_in(sender_address, opt_asset_id, algod_client):
        print(f"Opting in to asset {opt_asset_id}...")
        txn = AssetTransferTxn(sender_address, sp, sender_address, 0, opt_asset_id, note=b"Opt-in")
        signed = txn.sign(private_key)
        txid = algod_client.send_transaction(signed)
        wait_for_confirmation(algod_client, txid)
        print("Opt-in confirmed.")

    # Build ABI Method
    create_escrow_method = Method(
        name="create_escrow",
        args=[
            Argument(name="price", arg_type="uint64"),
            Argument(name="quantity", arg_type="uint64"),
            Argument(name="slippage", arg_type="uint64"),
            Argument(name="position", arg_type="uint8"),
        ],
        returns=Returns(arg_type="uint64")
    )

    # Atomic group: ALGO, asset, app call
    atc = AtomicTransactionComposer()
    # ALGO funding
    atc.add_transaction(TransactionWithSigner(
        PaymentTxn(
            sender_address, 
            sp, 
            algosdk.logic.get_application_address(market_app_id), # 2829831047
            967_600, 
            note=b"Escrow ALGO Funding"),
        signer
    ))

    # Asset funding
    fee = calculate_fee(quantity, price, fee_base=70_000) 
    asset_amt = math.floor(quantity * price / 1_000_000) + fee
    atc.add_transaction(TransactionWithSigner(
        AssetTransferTxn(
            sender_address, 
            sp, 
            algosdk.logic.get_application_address(market_app_id),
            asset_amt, 
            fund_asset_id,
            note=b"Escrow Asset Funding"
        ),
        signer
    ))
    # App call with correct asset order
    try:
        result = atc.add_method_call(
            app_id=market_app_id,
            method=create_escrow_method,
            sender=sender_address,
            sp=sp,
            signer=signer,
            method_args=[
                price,    
                quantity, 
                slippage, 
                position  
            ],
            foreign_assets=[usdc_asset_id, yes_asset_id, no_asset_id]
        )
        print("Submitting group...")
        res = atc.execute(algod_client, 4)
        print(f"Success: {res.tx_ids}, confirmed in {res.confirmed_round}")
    except AlgodHTTPError as e:
        print(f"ATC error: {e}")

async def main():
    await create_bet(is_buying=True, quantity=2_000_000, price=730_000, slippage=0, position=0)

if __name__ == "__main__":
    asyncio.run(main())
