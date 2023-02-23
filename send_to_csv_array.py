import csv
import itertools
import logging
import os
import sys
import time
import traceback

from dotenv import load_dotenv, set_key
from iota_client import IotaClient
from iota_wallet import IotaWallet, StrongholdSecretManager

load_dotenv()

# Global constants
stronghold_password = os.getenv("STRONGHOLD_PASSWORD")
stronghold_db_name = os.getenv("STRONGHOLD_DB_NAME")
wallet_db_name = os.getenv("WALLET_DB_NAME")
shimmer_mnemonic = os.getenv("SHIMMER_MNEMONIC")
shimmer_account_name = os.getenv("SHIMMER_ACCOUNT_NAME")
shimmer_smr_token_amount = os.getenv("SHIMMER_SMR_TOKEN_AMOUNT")
config_done = os.getenv("CONFIG_DONE")
config_done = eval(config_done)
shimmer_address_read_from_filename = os.getenv("SHIMMER_ADDRESS_READ_FROM_FILENAME")
shimmer_address_sent_to_filename = os.getenv("SHIMMER_ADDRESS_SENT_TO_FILENAME")

##########################
# Configure Logger
##########################
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Create a file handler
file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

# Create a stream handler
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# Add the stream handler to the logger
logger.addHandler(stream_handler)

##########################
# Shimmer wallet configurations
##########################
client_options = {
    "nodes": ["https://api.shimmer.network"],
}
coin_type = 4219
secret_manager = StrongholdSecretManager(stronghold_db_name, stronghold_password)
client = IotaClient(client_options)

# Define the chunk size of bulk transactions
chunk_size = 127

##########################
# Start
##########################


def basic_checks():
    """Verify that all variables have non-empty values"""
    env_vars = [
        "STRONGHOLD_PASSWORD",
        "STRONGHOLD_DB_NAME",
        "WALLET_DB_NAME",
        "SHIMMER_MNEMONIC",
        "SHIMMER_ACCOUNT_NAME",
        "SHIMMER_SMR_TOKEN_AMOUNT",
        "CONFIG_DONE",
        "SHIMMER_ADDRESS_READ_FROM_FILENAME",
        "SHIMMER_ADDRESS_SENT_TO_FILENAME",
    ]

    # iterate through each environment variable and check if it has a non-empty value
    for var in env_vars:
        if os.getenv(var) is None or os.getenv(var) == "":
            return False

    # all variables have a non-empty value
    return True


def create_shimmer_profile():
    """Create a new Shimmer wallet profile."""
    logger.debug("I am in create_shimmer_profile")
    if config_done:
        logger.info("Configuration is OK.")
        return
    else:
        logger.debug("Configuration not done.")

        # Check if wallet.stronghold exists and exit if present
        if os.path.isfile("wallet.stronghold"):
            print("Profile already exists. We continue.")
            input("Press Enter to continue...")
            return
        else:
            print("Creating new profile")
            # This creates a new database and account
            try:
                wallet = IotaWallet(
                    wallet_db_name, client_options, coin_type, secret_manager
                )
                account = wallet.store_mnemonic(shimmer_mnemonic)
                account = wallet.create_account(shimmer_account_name)

                print(account)
                set_key(".env", "CONFIG_DONE", "True")
                input("Press Enter to continue...")

                return

            except Exception:
                logger.info(traceback.format_exc())


def verify_content(csv_content, invalid_rows):
    """Verify the address for Shimmer and append the invalid rows to the list."""
    csv_reader = csv.reader(csv_content.splitlines())

    shimmer_client = IotaClient()
    next(csv_reader)  # skip the header row
    for i, row in enumerate(csv_reader):
        if not shimmer_client.is_address_valid(
            str(row[1])
        ):  # address in column B, [0] for column A
            invalid_rows.append(str(row[1]))  # address in column B, [0] for column A
    return invalid_rows


def send_to_list():
    """Read the CSV file and send SMR tokens to the corresponding addresses."""
    global chunk_size
    logger.debug("I am in send_to_list")
    invalid_rows = []
    # Define the outputs array
    outputs = []

    # Read the CSV file in chunks
    with open(shimmer_address_read_from_filename, encoding="UTF8") as file:
        csv_file = file
        csv_content = csv_file.read()
        # Verify the addresses and log any invalid rows
        if verify_content(csv_content, invalid_rows):
            logger.info(f"Invalid rows found\n {invalid_rows}")
            logger.info("Please correct the addresses and try again.")
        else:
            logger.info("Addresses are valid. We continue.")
            logger.debug(f"CSV content: {csv_content}")

    with open(shimmer_address_read_from_filename, encoding="UTF8") as file:
        # csv_reader = csv.reader(file)
        # header = next(csv_reader)  # skip the header row

        while True:
            # Create a new csv_reader object for each chunk of rows
            rows = list(itertools.islice(csv.reader(file), chunk_size))

            # Check if we've reached the end of the file
            if not rows:
                break

            # Process the rows in the chunk
            for row in rows:
                try:
                    logger.debug(f"Line: {row}")
                    address = str(row[1])  # address in column B, [0] for column A
                    # amount = int(row[2])   # amount in column C, [1] for column B
                    amount = shimmer_smr_token_amount  # amount from .env
                    outputs.append({"address": address, "amount": amount})
                except (IndexError, ValueError) as e:
                    logger.warning(f"Error processing row {row}: {e}")
                    invalid_rows.append(row)

            # Call send_smr_tokens with the outputs array
            # send_smr_tokens(str(outputs))
            send_smr_tokens(outputs)
            outputs = []


def get_transaction_status(pending_transactions, outputs):
    """Gets the transaction status and returns the block ID and shimmer receiver address."""
    logger.debug(pending_transactions)
    # Loop through each pending transaction
    for tx in pending_transactions:
        # Check if the transaction's networkId is the mainnet (14364762045254553490)
        if tx["networkId"] == "14364762045254553490":
            # Get the blockId for this transaction
            block_id = tx["blockId"]
            logger.info(f"Block ID: {block_id}")
            # Do something with the blockId
            check_transaction_confirm(block_id, outputs)

    return block_id


def check_transaction_confirm(block_id, outputs):
    """Checks whether the transaction has been confirmed by the ledger and waits until it has been."""
    logger.debug(f"block_id: {block_id}")

    # Loop until the transaction has been confirmed
    while True:
        # Get the ledger inclusion state for the block
        ledger_inclusion_state = client.get_block_metadata(block_id).get(
            "ledgerInclusionState"
        )
        logger.info("Checking transaction status...")
        logger.debug(f"Ledger inclusion state: {ledger_inclusion_state}")

        if ledger_inclusion_state is not None:
            # Transaction has been confirmed
            logger.info("Transaction has been confirmed.")
            for item in outputs:
                address = item["address"]
                write_to_csv(address, shimmer_smr_token_amount, block_id)
            return block_id
        else:
            # Wait for 10 seconds before checking again
            time.sleep(10)


def get_max_chunk_size(account_status):
    global shimmer_smr_token_amount

    available_balance = int(account_status["baseCoin"]["available"])
    max_chunk_size = available_balance // int(shimmer_smr_token_amount)
    return max_chunk_size


def check_enough_balance(account_status):
    """
    Checks whether the account has enough balance to send the tokens.
    """
    global shimmer_smr_token_amount
    global chunk_size

    available_balance = int(account_status["baseCoin"]["available"])
    required_balance = int(shimmer_smr_token_amount) * int(chunk_size)
    logger.info(f"Required balance: {required_balance}")
    logger.info(f"Available balance: {available_balance}")

    if available_balance >= required_balance:
        return
    else:
        get_max_chunk_size(account_status)

        logger.info("Impossible to send")
        raise ValueError("Not enough balance")


def write_to_csv(shimmer_receiver_address, shimmer_smr_token_amount, block_id):
    """Writes the transaction details to a CSV file."""
    # assuming you have the following variables available:
    # - address
    # - token_amount
    # - date_time
    # - block_id

    # construct the explorer link
    explorer_link = f"https://explorer.shimmer.network/shimmer/block/{block_id}"
    # Get the current date and time
    date_time = time.strftime("%Y-%m-%d %H:%M:%S")

    # create a list with the data to write to the CSV file
    data = [
        [shimmer_receiver_address, explorer_link, shimmer_smr_token_amount, date_time]
    ]

    # open the CSV file in 'append' mode
    with open(shimmer_address_sent_to_filename, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # write the data to the CSV file
        writer.writerows(data)
        logger.info(
            f"Transaction details appended to CSV file for address: {shimmer_receiver_address}"
        )


def send_smr_tokens(outputs):
    """Sends SMR tokens to a single address."""
    global shimmer_smr_token_amount
    logger.info("Received bulk outputs.")
    logger.debug(f"Received bulk outputs: {outputs}")
    try:
        # Sync account with the node
        wallet = IotaWallet(wallet_db_name, client_options, coin_type, secret_manager)
        account = wallet.get_account(shimmer_account_name)
        logger.info("Account retrieved")
        address = account.addresses()
        logger.info(f"Address: {address}")
        balance = account.get_balance()
        logger.info(f"Balance: {balance}")
        time.sleep(5)
        account_status = account.sync()
        logger.info("Account Synced")

        # Verify if there is enough balance
        # check_enough_balance(account_status, shimmer_receiver_address)
        check_enough_balance(account_status)

        # Set the Stronghold password
        wallet.set_stronghold_password(stronghold_password)

        # Define the output transaction
        logger.debug(f"Shimmer amount: {shimmer_smr_token_amount}")
        logger.debug(f"Outputs: {outputs}")

        try:
            # Send the transaction with the defined outputs
            account.send_amount(outputs)
            logger.info("Transaction sent")
            pending_transactions = account.pending_transactions()
            logger.debug(f"Pending transactions: {pending_transactions}")
            get_transaction_status(pending_transactions, outputs)

        except Exception:
            logger.info(traceback.format_exc())
        return

    except ValueError as e:  # Catch the raised ValueError
        logger.info(f"Stopping the program: {e}")  # Add a log message
        sys.exit(1)  # Stop the program

    except Exception:
        logger.info(traceback.format_exc())


####################
# DEBUG STUFF
####################

# def consolidate_accounts():
#     # Sync account with the node
#     wallet = IotaWallet(wallet_db_name, client_options, coin_type, secret_manager)
#     #account = wallet.create_account(alias="ttea", bech32_hrp="smr")

#     account = wallet.get_account("TEst")
#     #account = wallet.get_account("tea")
#     #account = wallet.get_account("ttea")
#     address = wallet.get_account_data("TEst")
#     logger.debug(f"Address: {address}")
# accounts = wallet.get_accounts()
# logger.debug(f"Accounts: {accounts}")
# time.sleep(15)
# sys.exit(1)


# account_status = account.sync()
# logger.info("Account Synced")
# logger.debug(f"Account status: {account_status}")
# balance = account.get_balance()
# logger.info(f"Balance: {balance}")

# consolidate_account = account.consolidate_outputs(force=True, output_consolidation_threshold=127)
# logger.info("Account Consolidated")
# logger.debug(f"Account consolidation: {consolidate_account}")
# account_status = account.sync()
# logger.info("Account Synced")
# logger.debug(f"Account status: {account_status}")
# balance = account.get_balance()
# logger.info(f"Balance: {balance}")

# outputs_count = []
# outputs = account.unspent_outputs()
# logger.debug(f"Outputs: {outputs}")
# outputs_list = outputs
# for output in outputs_list:
#     outputs_count.append(output['outputId'])

# output_number = len(outputs_count)

# logger.info(f"Outputs count: {output_number}")

# # while outputs_count > 0:
# consolidate_account = account.consolidate_outputs(force=True, output_consolidation_threshold=1)
# logger.info("Account Consolidated")
# logger.debug(f"Account consolidation: {consolidate_account}")

# time.sleep(15)
# account_status = account.sync()
# logger.info("Account Synced")
# logger.debug(f"Account status: {account_status}")
# balance = account.get_balance()
# logger.info(f"Balance: {balance}")
# outputs = [
#     {
#     "address": "smr1qz8vmj53g25ss2ssdm7u3ugm6ehxxepxn05fzqwltdjxu4l9jek32kt350w",
#     "amount": "763000000",
#     }
# ]
# account.send_amount(outputs)


def main():
    if basic_checks():
        # consolidate_accounts() # DEBUG
        create_shimmer_profile()
        send_to_list()
    else:
        logger.info(
            "Make sure to fill out the information in the .env file. Rename .env.exmple to .env first."
        )


if __name__ == "__main__":
    main()
