"""
Algorand Automated Payment Script

This script sends a specified amount of Algos from one account to another at regular 5-minute intervals.
It uses the AlgoKit Utils library to interact with the Algorand blockchain.

How it works:
1. Loads environment variables from a .env file (SENDER_MNEMONIC, TARGET_ADDRESS, AMOUNT_TO_SEND)
2. Connects to the Algorand MainNet (can be changed to TestNet for testing)
3. Creates a sender account from the provided mnemonic phrase
4. Runs in an infinite loop:
   - Checks the sender's current balance
   - If sufficient funds are available, sends the specified amount to the target address
   - Waits 5 minutes before the next transaction
   - Handles errors gracefully with a 1-minute retry interval

Requirements:
- python-dotenv: For loading environment variables
- algokit-utils: For Algorand blockchain interactions
- algosdk: The Algorand SDK for Python

Setup:
Create a .env file with:
SENDER_MNEMONIC="your 25-word mnemonic phrase"
TARGET_ADDRESS="recipient's Algorand address"
AMOUNT_TO_SEND=0.1  # Amount in Algos to send each time
"""

import os
import time
from dotenv import load_dotenv
from algokit_utils import AlgorandClient, SigningAccount, AlgoAmount
from algosdk import mnemonic
from algokit_utils import AlgoAmount, PaymentParams

load_dotenv()

def main():
    sender_mnemonic = os.getenv("SENDER_MNEMONIC")
    if not sender_mnemonic:
        print("Error: SENDER_MNEMONIC not found in environment variables")
        return
    
    target_address = os.getenv("TARGET_ADDRESS")
    if not target_address:
        print("Error: TARGET_ADDRESS not found in environment variables")
        return
    
    amount_to_send = float(os.getenv("AMOUNT_TO_SEND", "0.1"))  # Default to 0.1 Algo if not specified
    
    # Connect to Algorand network
    # Use mainnet() for production or test_net() for testing
    algorand = AlgorandClient.mainnet()
    
    # Get sender account from mnemonic
    sender_account = algorand.account.from_mnemonic(mnemonic=sender_mnemonic)
    print(f"Sender account: {sender_account.address}")
    print(f"Target account: {target_address}")
    print(f"Will send {amount_to_send} Algos every 5 minutes")
    
    # Main loop - send Algos every 5 minutes
    while True:
        try:
            # Check sender balance
            account_info = algorand.client.algod.account_info(sender_account.address)
            balance = account_info["amount"] / 1_000_000  # Convert microAlgos to Algos
            print(f"Current balance: {balance} Algos")
            
            if balance < amount_to_send + 0.001:  # Add a small buffer for fees
                print("Insufficient balance to send transaction")
            else:
                print(f"Sending {amount_to_send} Algos to {target_address}...")
                
                # Create and send payment transaction
                txn_response = algorand.send.payment(
                    params=PaymentParams(
                        sender=sender_account.address,
                        receiver=target_address,
                        amount=AlgoAmount(algo=amount_to_send),
                        signer=sender_account.signer,  # Note: this is a property, not a method
                        note="Automated payment"
                    )
                )
            
                print(f"Transaction sent! ID: {txn_response.tx_id}")
            
            print("Waiting 5 minutes for next transaction...")
            time.sleep(300)  # 300 seconds = 5 minutes
            
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            print("Retrying in 1 minute...")
            time.sleep(60)

if __name__ == "__main__":
    main()