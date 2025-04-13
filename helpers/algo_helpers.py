from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
import math
from algosdk.transaction import PaymentTxn


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

def check_asset_opt_in(address: str, asset_id: int, algod_client) -> bool:
    """
    Checks if the given address is opted into the specified asset.
    
    Args:
        address (str): The wallet address to check.
        asset_id (int): The asset ID to check for opt-in.
        algod_client: The Algorand algod client.

    Returns:
        bool: True if opted in, False otherwise.
    """
    try:
        account_info = algod_client.account_info(address)
        for asset in account_info.get("assets", []):
            if asset["asset-id"] == asset_id:
                return True
        return False
    except Exception as e:
        print("Error checking asset opt-in:", e)
        return False

def opt_in_to_asset(algod_client, address: str, private_key: str, asset_id: int):
    """
    Sends a 0-amount asset transfer to self to opt into the asset.

    Args:
        algod_client: The Algorand algod client.
        address (str): The wallet address performing the opt-in.
        private_key (str): The private key to sign the transaction.
        asset_id (int): The asset ID to opt into.
    """
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
        print(f"Sent opt-in transaction for asset {asset_id}, txID: {txid}")

        transaction.wait_for_confirmation(algod_client, txid, 4)
        print(f"Successfully opted into asset {asset_id}")
    except Exception as e:
        print(f"Error opting into asset {asset_id}:", e)


def submit_group_transactions(algod_client, txns: list, private_keys: list) -> str:
    '''
    Groups multiple unsigned transactions, signs them with the given private keys,
    and submits the grouped transaction to the Algorand network.

    Parameters:
        algod_client: The Algorand algod client.
        txns (list): A list of Transaction objects.
        private_keys (list): A list of private keys corresponding to txns.
    
    Returns:
        str: The transaction ID of the submitted group.
    
    Example usage:
        txns = [txn1, txn2]
        pks = [private_key1, private_key1]  # same key if all txns are from same account
        txid = submit_group_transactions(algod_client, txns, pks)
    '''
    # Calculate and assign the group id to each transaction
    group_id = transaction.calculate_group_id(txns)
    for txn in txns:
        txn.group = group_id

    # Sign each transaction with its corresponding private key
    signed_txns = [txn.sign(pk) for txn, pk in zip(txns, private_keys)]
    
    # Submit the grouped transactions
    txid = algod_client.send_transactions(signed_txns)
    transaction.wait_for_confirmation(algod_client, txid, 4)
    return txid


def buy_asset(algod_client, address: str, private_key: str, asset_id: int, amount: int, payment: int) -> str:
    '''
    Creates and submits a grouped transaction to "buy" an asset.
    
    This simplified example assumes:
        1. A payment transaction sending funds from the buyer to a market or escrow address.
        2. An asset transfer transaction sending the asset from the market/escrow to the buyer.
    
    Note: In a real decentralized exchange scenario, the market/escrow account should sign the asset
    transfer transaction. This example only signs the buyer's transaction for demonstration.
    
    Parameters:
        algod_client: The Algorand client.
        address (str): The buyer's wallet address.
        private_key (str): The buyer's private key.
        asset_id (int): The asset ID being purchased.
        amount (int): The amount of the asset to buy.
        payment (int): The payment in microAlgos for the purchase.
    
    Returns:
        str: The transaction ID of the submitted payment transaction.
    '''
    params = algod_client.suggested_params()
    market_address = "MARKET_ADDRESS_PLACEHOLDER"  # Replace with your market/escrow address

    # Payment transaction: buyer sends payment to market
    payment_txn = transaction.PaymentTxn(sender=address, sp=params, receiver=market_address, amt=payment)
    
    # Asset transfer transaction: market sends asset to buyer (this would normally be signed by the market)
    asset_txn = transaction.AssetTransferTxn(sender=market_address, sp=params, receiver=address, amt=amount, index=asset_id)
    
    # For demonstration, we group the two transactions (only signing the buyer's tx)
    group_id = transaction.calculate_group_id([payment_txn, asset_txn])
    payment_txn.group = group_id
    asset_txn.group = group_id
    
    # Sign only the buyer's payment transaction (in a real app, asset_txn must also be signed by market)
    signed_payment_txn = payment_txn.sign(private_key)
    
    # Here we are only submitting the buyer's signed transaction; in production, you need the fully signed group.
    txid = algod_client.send_transaction(signed_payment_txn)
    transaction.wait_for_confirmation(algod_client, txid, 4)
    print(f"Buy asset transaction submitted, txID: {txid}")
    return txid


def sell_asset(algod_client, address: str, private_key: str, asset_id: int, amount: int, payment: int) -> str:
    '''
    Creates and submits a grouped transaction to "sell" an asset.
    
    This simplified example assumes:
        1. An asset transfer transaction sending the asset from the seller to a market/escrow address.
        2. A payment transaction where the market/escrow sends funds to the seller.
    
    Note: In a real-world scenario, both legs of the transaction would be signed by their respective parties.
    
    Parameters:
        algod_client: The Algorand client.
        address (str): The seller's wallet address.
        private_key (str): The seller's private key.
        asset_id (int): The asset ID to sell.
        amount (int): The amount of the asset to sell.
        payment (int): The payment in microAlgos expected from the sale.
    
    Returns:
        str: The transaction ID of the submitted asset transfer transaction.
    '''
    params = algod_client.suggested_params()
    market_address = "MARKET_ADDRESS_PLACEHOLDER"  # Replace with your market/escrow address

    # Asset transfer transaction: seller sends asset to market
    asset_txn = transaction.AssetTransferTxn(sender=address, sp=params, receiver=market_address, amt=amount, index=asset_id)
    
    # Payment transaction: market sends funds to seller
    payment_txn = transaction.PaymentTxn(sender=market_address, sp=params, receiver=address, amt=payment)
    
    # Group the transactions (for demonstration, we assume only seller signs their transaction)
    group_id = transaction.calculate_group_id([asset_txn, payment_txn])
    asset_txn.group = group_id
    payment_txn.group = group_id

    # Sign the seller's asset transaction
    signed_asset_txn = asset_txn.sign(private_key)
    
    # Submit the seller's signed transaction (in practice both transactions need to be signed and submitted)
    txid = algod_client.send_transaction(signed_asset_txn)
    transaction.wait_for_confirmation(algod_client, txid, 4)
    print(f"Sell asset transaction submitted, txID: {txid}")
    return txid


def cancel_order(algod_client, address: str, private_key: str, order_id: str) -> str:
    '''
    Sends a cancel order request by creating a transaction with a note containing the order ID.
    
    In a real trading bot, cancelling an order might involve interacting with a smart contract.
    In this example, we use a zero-amount payment transaction to a market/escrow address with the
    order ID encoded in the note field.
    
    Parameters:
        algod_client: The Algorand client.
        address (str): The wallet address sending the cancellation.
        private_key (str): The private key to sign the transaction.
        order_id (str): The ID of the order to cancel.
    
    Returns:
        str: The transaction ID of the cancel order transaction.
    '''
    params = algod_client.suggested_params()
    market_address = "MARKET_ADDRESS_PLACEHOLDER"  # Replace with the appropriate address that handles cancellations
    
    # Encode the order ID in the note field
    note = order_id.encode()
    cancel_txn = transaction.PaymentTxn(sender=address, sp=params, receiver=market_address, amt=0, note=note)
    signed_cancel_txn = cancel_txn.sign(private_key)
    
    txid = algod_client.send_transaction(signed_cancel_txn)
    transaction.wait_for_confirmation(algod_client, txid, 4)
    print(f"Cancel order transaction for order {order_id} submitted, txID: {txid}")
    return txid

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
