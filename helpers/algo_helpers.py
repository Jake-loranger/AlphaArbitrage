from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod


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
