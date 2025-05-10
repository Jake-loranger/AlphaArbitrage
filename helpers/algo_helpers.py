import time
from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
import math
import os
import math
import algosdk
from dotenv import load_dotenv
from algosdk import mnemonic, account
from algosdk.transaction import PaymentTxn, AssetTransferTxn
from algosdk.abi import Method
from algosdk.abi.method import Argument, Returns
from algosdk.error import AlgodHTTPError
from helpers.alpha_helpers import calculate_fee
from helpers.log_helpers import log_data
from models.market import Market
from algokit_utils import (
    AppClient, 
    AlgorandClient,
    AppClientParams, 
    AppClientMethodCallParams,
    AlgoAmount,
    ApplicationSpecification
)
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)
import json
from pathlib import Path

def generate_algorand_account():
    private_key, address = account.generate_account()
    passphrase = mnemonic.from_private_key(private_key)
    
    print("Address:", address)
    print("Mnemonic:", passphrase)

    return {
        "address": address,
        "private_key": private_key,
        "mnemonic": passphrase
    }

def connect_wallet(mnemonic_phrase: str = None) -> tuple:
    """
    Retrieves the user's wallet address, private key, and initializes the algod client.

    Returns:
        tuple:
            - algod_client (AlgodClient): The client used to interact with the Algorand network.
            - address (str): The public Algorand wallet address.
            - private_key (str): The private key derived from the mnemonic, used to sign transactions.
    """
    if not mnemonic_phrase:
        raise ValueError("MNEMONIC_PHRASE not found in environment variables")

    private_key = mnemonic.to_private_key(mnemonic_phrase)
    address = account.address_from_private_key(private_key)

    algod_client = algod.AlgodClient("", "https://mainnet-api.4160.nodely.dev")
    return algod_client, address, private_key

async def check_asset_opt_in(asset_id):
    """
    Checks if the given address is opted into the specified asset.
    
    Args:
        address (str): The wallet address to check.
        asset_id (int): The asset ID to check for opt-in.
        algod_client: The Algorand algod client.

    Returns:
        bool: True if opted in, False otherwise.
    """
    
    sender_mnemonic = os.getenv("SENDER_MNEMONIC")
    algorand = AlgorandClient.mainnet()
    algod_client = algorand.client.algod
    private_key = mnemonic.to_private_key(sender_mnemonic)
    address = account.address_from_private_key(private_key)
    info = algod_client.account_info(address)
    for asset in info.get("assets", []):
        if asset.get("asset-id") == asset_id:
            return True
    return False

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

async def opt_in_to_asset(asset_id: int):
    """
    Sends a 0-amount asset transfer to self to opt into the asset.

    Args:
        algod_client: The Algorand algod client.
        address (str): The wallet address performing the opt-in.
        private_key (str): The private key to sign the transaction.
        asset_id (int): The asset ID to opt into.
    """
    sender_mnemonic = os.getenv("SENDER_MNEMONIC")
    if not sender_mnemonic:
        raise Exception("Missing environment variables")
    
    algorand = AlgorandClient.mainnet()
    algod_client = algorand.client.algod
    private_key = mnemonic.to_private_key(sender_mnemonic)
    address = account.address_from_private_key(private_key)

    try:
        params = algod_client.suggested_params()
        txn = transaction.AssetTransferTxn(
            sender=address,
            sp=params,
            receiver=address,
            amt=0,
            index=asset_id
        )
        signed_txn = txn.sign(private_key)
        txid = algod_client.send_transaction(signed_txn)
        log_data(f"[ACTION] Sent opt-in transaction for asset {asset_id}, txID: {txid}")

        transaction.wait_for_confirmation(algod_client, txid, 4)
        log_data(f"[INFO] Successfully opted into asset {asset_id}")
    except Exception as e:
        log_data(f"[ERROR] Error opting into asset {asset_id}:", e)

async def create_bet(
    is_buying: bool,
    quantity: int,
    price: int,
    position: int,
    slippage: int,
    market: Market
) -> int:
    # Load config
    sender_mnemonic = os.getenv("SENDER_MNEMONIC")
    market_app_id = market.marketAppId
    usdc_asset_id  = 31566704
    yes_asset_id = market.yesAssetId
    no_asset_id  = market.noAssetId

    if not all([sender_mnemonic, market_app_id, usdc_asset_id, yes_asset_id, no_asset_id]):
        raise Exception("Missing environment variables")

    # Setup clients and keys
    algorand = AlgorandClient.mainnet()
    algod_client = algorand.client.algod
    private_key = mnemonic.to_private_key(sender_mnemonic)
    sender_address = account.address_from_private_key(private_key)
    signer = AccountTransactionSigner(private_key)

    log_data(f"[INFO] {'Buying' if is_buying else 'Selling'} {'YES' if position else 'NO'} tokens: qty={quantity/1e6}, price={price/1e6} USDC")

    sp = algod_client.suggested_params()
    fund_asset_id = usdc_asset_id if is_buying else (yes_asset_id if position == 1 else no_asset_id)

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
    atc.add_transaction(TransactionWithSigner(
        PaymentTxn(
            sender_address, 
            sp, 
            algosdk.logic.get_application_address(market_app_id),
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
    
    try:
        atc.add_method_call(
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
        log_data("[INFO] Submitting group...")
        res = atc.execute(algod_client, 4)
        log_data(f"[INFO] Success: {res.tx_ids}, confirmed in {res.confirmed_round}")
        return res.abi_results[0].return_value
    except AlgodHTTPError as e:
        log_data(f"[ERROR] ATC error: {e}")


async def cancel_bet(
    escrow_app_id: int,
    market: Market
) -> None:
    sender_mnemonic = os.getenv("SENDER_MNEMONIC")
    if not sender_mnemonic:
        raise ValueError("Missing sender mnemonic in environment.")

    usdc_asset_id  = 31566704
    yes_asset_id = market.yesAssetId
    no_asset_id  = market.noAssetId
    algorand = AlgorandClient.mainnet()
    algod_client = algorand.client.algod
    private_key = mnemonic.to_private_key(sender_mnemonic)
    sender_address = account.address_from_private_key(private_key)
    signer = AccountTransactionSigner(private_key)

    escrow_app_spec_path = Path(__file__).parent.parent / 'app_specs' / 'escrow_app_spec.json'
    with open(escrow_app_spec_path, 'r') as file:
        ESCROW_APP_SPEC_JSON = json.load(file)
        ESCROW_APP_SPEC_STR = json.dumps(ESCROW_APP_SPEC_JSON)

    ESCROW_APP_SPEC = ApplicationSpecification.from_json(ESCROW_APP_SPEC_STR)
    escrow_app_client = AppClient(
        AppClientParams(
            app_spec=ESCROW_APP_SPEC,
            app_id=escrow_app_id,
            algorand=algorand,
            default_sender=sender_address
        )
    )

    market_app_spec_path = Path(__file__).parent.parent / 'app_specs' / 'market_app_spec.json'
    with open(market_app_spec_path, 'r') as file:
        MARKET_APP_SPEC_JSON = json.load(file)
        MARKET_APP_SPEC_STR = json.dumps(MARKET_APP_SPEC_JSON)

    MARKET_APP_SPEC = ApplicationSpecification.from_json(MARKET_APP_SPEC_STR)
    market_app_client = AppClient(
        AppClientParams(
            app_spec=MARKET_APP_SPEC,
            app_id=market.marketAppId,
            algorand=algorand,
            default_sender=sender_address
        )
    )

    atc = AtomicTransactionComposer()

    delete_escrow_txn = escrow_app_client.create_transaction.delete(
        AppClientMethodCallParams(
            method="delete",
            extra_fee=AlgoAmount(micro_algo=4000),
            args=[],
            asset_references=[
                usdc_asset_id,
                yes_asset_id,
                no_asset_id,
            ],
            app_references=[market.marketAppId],
            signer=signer
        )
    )
    atc.add_transaction(TransactionWithSigner(delete_escrow_txn.transactions[0], signer))

    register_escrow_delete_txn = market_app_client.create_transaction.call(
        AppClientMethodCallParams(
            method="register_escrow_delete",
            extra_fee=AlgoAmount(micro_algo=1000),
            args=[sender_address],  
            asset_references=[
                usdc_asset_id,
                yes_asset_id,
                no_asset_id,
            ],
            app_references=[escrow_app_id],
            signer=signer
        )
    )
    atc.add_transaction(TransactionWithSigner(register_escrow_delete_txn.transactions[0], signer))

    try:
        log_data(f"[ACTION] Submitting cancel order for {escrow_app_id}...")
        res = atc.execute(algod_client, 4)
        log_data(f"[INFO] Success: {res.tx_ids}, confirmed in {res.confirmed_round}")
    except AlgodHTTPError as e:
        log_data(f"[ERROR] ATC error: {e}")