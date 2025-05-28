import time
from typing import Dict, Tuple, Optional, Union
from pathlib import Path
import json
import math
import os

from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
from algosdk.abi import Method
from algosdk.abi.method import Argument, Returns
from algosdk.error import AlgodHTTPError
from algosdk.transaction import PaymentTxn, AssetTransferTxn
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    TransactionWithSigner,
)

from algokit_utils import (
    AppClient,
    AlgorandClient,
    AppClientParams,
    AppClientMethodCallParams,
    AlgoAmount,
    ApplicationSpecification
)

from helpers.alpha_helper import AlphaHelper
from helpers.log_helpers import get_logger
from models.market import Market

logger = get_logger(__name__)

class AlgorandHelper:
    """Helper class for interacting with the Algorand blockchain."""
    
    USDC_ASSET_ID = 31566704
    MICRO_UNIT = 1_000_000  # 1 USDC = 1_000_000 microUSDC
    
    def __init__(self):
        """Initialize the AlgorandHelper with mainnet connection."""
        self.algorand = AlgorandClient.mainnet()
        self.algod_client = self.algorand.client.algod
        self._load_app_specs()
    
    def _load_app_specs(self) -> None:
        """Load application specifications from JSON files."""
        base_path = Path(__file__).parent.parent / 'app_specs'
        
        # Load Escrow App Spec
        with open(base_path / 'escrow_app_spec.json', 'r') as file:
            self.ESCROW_APP_SPEC = ApplicationSpecification.from_json(json.dumps(json.load(file)))
            
        # Load Market App Spec
        with open(base_path / 'market_app_spec.json', 'r') as file:
            self.MARKET_APP_SPEC = ApplicationSpecification.from_json(json.dumps(json.load(file)))

    @staticmethod
    def generate_account() -> Dict[str, str]:
        """
        Generate a new Algorand account.
        
        Returns:
            Dict containing address, private_key, and mnemonic
        """
        private_key, address = account.generate_account()
        passphrase = mnemonic.from_private_key(private_key)
        
        return {
            "address": address,
            "private_key": private_key,
            "mnemonic": passphrase
        }

    def connect_wallet(self, mnemonic_phrase: str) -> Tuple[algod.AlgodClient, str, str]:
        """
        Connect to wallet using mnemonic phrase.
        
        Args:
            mnemonic_phrase: The mnemonic phrase for the wallet
            
        Returns:
            Tuple of (algod_client, address, private_key)
            
        Raises:
            ValueError: If mnemonic phrase is not provided
        """
        if not mnemonic_phrase:
            raise ValueError("Mnemonic phrase is required")
            
        private_key = mnemonic.to_private_key(mnemonic_phrase)
        address = account.address_from_private_key(private_key)
        
        return self.algod_client, address, private_key

    async def check_asset_opt_in(self, asset_id: int) -> bool:
        """
        Check if the wallet is opted into a specific asset.
        
        Args:
            asset_id: The asset ID to check
            
        Returns:
            bool: True if opted in, False otherwise
        """
        sender_mnemonic = os.getenv("SENDER_MNEMONIC")
        if not sender_mnemonic:
            raise ValueError("SENDER_MNEMONIC not found in environment")
            
        private_key = mnemonic.to_private_key(sender_mnemonic)
        address = account.address_from_private_key(private_key)
        
        info = self.algod_client.account_info(address)
        return any(asset.get("asset-id") == asset_id for asset in info.get("assets", []))

    async def opt_in_to_asset(self, asset_id: int) -> None:
        """
        Opt into an asset by sending a 0-amount transfer to self.
        
        Args:
            asset_id: The asset ID to opt into
            
        Raises:
            Exception: If environment variables are missing or transaction fails
        """
        sender_mnemonic = os.getenv("SENDER_MNEMONIC")
        if not sender_mnemonic:
            raise ValueError("SENDER_MNEMONIC not found in environment")
            
        private_key = mnemonic.to_private_key(sender_mnemonic)
        address = account.address_from_private_key(private_key)
        
        try:
            params = self.algod_client.suggested_params()
            txn = AssetTransferTxn(
                sender=address,
                sp=params,
                receiver=address,
                amt=0,
                index=asset_id
            )
            signed_txn = txn.sign(private_key)
            txid = self.algod_client.send_transaction(signed_txn)
            logger.info(f"[ACTION] Sent opt-in transaction for asset {asset_id}, txID: {txid}")
            
            transaction.wait_for_confirmation(self.algod_client, txid, 4)
            logger.info(f"[INFO] Successfully opted into asset {asset_id}")
        except Exception as e:
            logger.error(f"[ERROR] Error opting into asset {asset_id}: {e}")
            raise

    @staticmethod
    def to_micro_units(amount: Union[int, float]) -> int:
        """
        Convert a human-readable amount to micro-units.
        
        Args:
            amount: The amount to convert (e.g., 1.5 USDC)
            
        Returns:
            int: The amount in micro-units (e.g., 1_500_000)
        """
        return int(amount * AlgorandHelper.MICRO_UNIT)
    
    @staticmethod
    def from_micro_units(amount: int) -> float:
        """
        Convert micro-units to a human-readable amount.
        
        Args:
            amount: The amount in micro-units (e.g., 1_500_000)
            
        Returns:
            float: The human-readable amount (e.g., 1.5)
        """
        return amount / AlgorandHelper.MICRO_UNIT
    
    @staticmethod
    def to_micro_percentage(percentage: Union[int, float]) -> int:
        """
        Convert a percentage to micro-units.
        
        Args:
            percentage: The percentage to convert (e.g., 1.5%)
            
        Returns:
            int: The percentage in micro-units (e.g., 150)
        """
        return int(percentage * 100)  # 1% = 100 micro-units
    
    @staticmethod
    def from_micro_percentage(percentage: int) -> float:
        """
        Convert micro-units to a percentage.
        
        Args:
            percentage: The percentage in micro-units (e.g., 150)
            
        Returns:
            float: The human-readable percentage (e.g., 1.5)
        """
        return percentage / 100  # 100 micro-units = 1%

    async def create_bet(
        self,
        is_buying: bool,
        quantity: int,
        price: int,
        position: int,
        slippage: int,
        market: Market
    ) -> int:
        """
        Create a bet on the Algorand blockchain.
        
        Args:
            is_buying: Whether this is a buy or sell order
            quantity: Amount of tokens to trade (in USDC, will be converted to micro-units)
            price: Price per token in USDC (will be converted to micro-units)
            position: 1 for YES, 0 for NO
            slippage: Maximum allowed slippage in percentage (will be converted to micro-units)
            market: Market object containing asset IDs and app IDs
            
        Returns:
            int: The escrow app ID
            
        Raises:
            Exception: If environment variables are missing or transaction fails
        """
        # Convert human-readable numbers to micro-units
        micro_quantity = self.to_micro_units(quantity)
        micro_price = self.to_micro_units(price)
        micro_slippage = self.to_micro_percentage(slippage)
        
        sender_mnemonic = os.getenv("SENDER_MNEMONIC")
        if not all([sender_mnemonic, market.marketAppId, self.USDC_ASSET_ID, market.yesAssetId, market.noAssetId]):
            raise ValueError("Missing required environment variables")
            
        private_key = mnemonic.to_private_key(sender_mnemonic)
        sender_address = account.address_from_private_key(private_key)
        signer = AccountTransactionSigner(private_key)
        
        logger.info(f"[INFO] {'Buying' if is_buying else 'Selling'} {'YES' if position else 'NO'} tokens: qty={quantity}, price={price} USDC")
        
        sp = self.algod_client.suggested_params()
        fund_asset_id = self.USDC_ASSET_ID if is_buying else (market.yesAssetId if position == 1 else market.noAssetId)
        
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
        
        # Build transaction group
        atc = AtomicTransactionComposer()
        
        # Add ALGO funding transaction
        atc.add_transaction(TransactionWithSigner(
            PaymentTxn(
                sender_address,
                sp,
                transaction.logic.get_application_address(market.marketAppId),
                967_600,
                note=b"Escrow ALGO Funding"
            ),
            signer
        ))
        
        # Add asset funding transaction
        fee = AlphaHelper.calculate_fee(micro_quantity, micro_price, fee_base=70_000)
        asset_amt = math.floor(micro_quantity * micro_price / self.MICRO_UNIT) + fee
        atc.add_transaction(TransactionWithSigner(
            AssetTransferTxn(
                sender_address,
                sp,
                transaction.logic.get_application_address(market.marketAppId),
                asset_amt,
                fund_asset_id,
                note=b"Escrow Asset Funding"
            ),
            signer
        ))
        
        try:
            atc.add_method_call(
                app_id=market.marketAppId,
                method=create_escrow_method,
                sender=sender_address,
                sp=sp,
                signer=signer,
                method_args=[micro_price, micro_quantity, micro_slippage, position],
                foreign_assets=[self.USDC_ASSET_ID, market.yesAssetId, market.noAssetId]
            )
            
            logger.info("[INFO] Submitting group...")
            res = atc.execute(self.algod_client, 4)
            logger.info(f"[INFO] Success: {res.tx_ids}, confirmed in {res.confirmed_round}")
            return res.abi_results[0].return_value
            
        except AlgodHTTPError as e:
            logger.error(f"[ERROR] ATC error: {e}")
            raise

    async def cancel_bet(self, escrow_app_id: int, market: Market) -> None:
        """
        Cancel an existing bet by deleting the escrow.
        
        Args:
            escrow_app_id: The ID of the escrow application to cancel
            market: Market object containing asset IDs and app IDs
            
        Raises:
            ValueError: If environment variables are missing
            AlgodHTTPError: If transaction fails
        """
        sender_mnemonic = os.getenv("SENDER_MNEMONIC")
        if not sender_mnemonic:
            raise ValueError("Missing sender mnemonic in environment")
            
        private_key = mnemonic.to_private_key(sender_mnemonic)
        sender_address = account.address_from_private_key(private_key)
        signer = AccountTransactionSigner(private_key)
        
        # Initialize app clients
        escrow_app_client = AppClient(
            AppClientParams(
                app_spec=self.ESCROW_APP_SPEC,
                app_id=escrow_app_id,
                algorand=self.algorand,
                default_sender=sender_address
            )
        )
        
        market_app_client = AppClient(
            AppClientParams(
                app_spec=self.MARKET_APP_SPEC,
                app_id=market.marketAppId,
                algorand=self.algorand,
                default_sender=sender_address
            )
        )
        
        # Build transaction group
        atc = AtomicTransactionComposer()
        
        # Add register escrow delete transaction
        register_escrow_delete_txn = market_app_client.create_transaction.call(
            AppClientMethodCallParams(
                method="delete_escrow",
                extra_fee=AlgoAmount(micro_algo=5000),
                args=[escrow_app_id, sender_address],
                asset_references=[self.USDC_ASSET_ID, market.yesAssetId, market.noAssetId],
                app_references=[escrow_app_id],
                signer=signer
            )
        )
        atc.add_transaction(TransactionWithSigner(register_escrow_delete_txn.transactions[0], signer))
        
        try:
            logger.info(f"[ACTION] Submitting cancel order for {escrow_app_id}...")
            res = atc.execute(self.algod_client, 4)
            logger.info(f"[INFO] Success: {res.tx_ids}, confirmed in {res.confirmed_round}")
        except AlgodHTTPError as e:
            logger.error(f"[ERROR] ATC error: {e}")
            raise