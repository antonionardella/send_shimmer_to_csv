import logging
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from iota_client import IotaClient

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
logger.setLevel(logging.INFO)

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
    "nodes": ["https://api.testnet.shimmer.network"],
}
client = IotaClient(client_options)

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


def compare_files():
    # Read in the two CSV files
    crew3_shimmer_address = pd.read_csv(
        "crew3_shimmer_address.csv"
    )  # The export of the SMR address quest
    crew3_airdrop_export = pd.read_csv(
        "crew3_airdrop_export.csv"
    )  # The export of the airdrop eligibility quest

    # get a list of unique names present in both CSV files
    common_names = set(crew3_shimmer_address["Name"]).intersection(
        set(crew3_airdrop_export["Name"])
    )

    # filter both dataframes to include only rows with common names
    df1_filtered = crew3_shimmer_address[
        crew3_shimmer_address["Name"].isin(common_names)
    ]
    df2_filtered = crew3_shimmer_address[
        crew3_shimmer_address["Name"].isin(common_names)
    ]

    # check that all addresses in the filtered dataframe are unique
    unique_addresses = df1_filtered["answer"].nunique()
    if unique_addresses != len(df1_filtered):
        nonunique_addresses = df1_filtered[
            df1_filtered.duplicated(subset="answer", keep=False)
        ].sort_values(by="answer")
        logger.info(
            f"WARNING: {len(nonunique_addresses)} non-unique addresses found in the crew3_shimmer_address dataframe:"
        )
        for index, row in nonunique_addresses.iterrows():
            logger.info(f"Row {index+1}: {row['answer']}")
        print(
            "WARNING: Non-unique addresses found in the crew3_shimmer_address dataframe. Exiting..."
        )
        sys.exit(1)

    # check that all addresses in the filtered dataframe are valid
    shimmer_client = IotaClient()
    invalid_rows = []
    for i, row in df1_filtered.iterrows():
        if not shimmer_client.is_address_valid(str(row["answer"])):
            invalid_rows.append(i)
    if invalid_rows:
        logger.info(
            f"ERROR: {len(invalid_rows)} invalid addresses found in the crew3_shimmer_address dataframe:"
        )
        for i in invalid_rows:
            logger.info(f"Row {i+1}: {df1_filtered.loc[i, 'answer']}")
        sys.exit(1)

    # merge the two filtered dataframes on the 'Name' column
    merged_df = pd.merge(df1_filtered, df2_filtered, on="Name")
    # logger.info(f"merged_df: {merged_df}")

    # select only the 'Name' and 'Address' columns from the first CSV file and save to a new CSV file
    merged_df[["Name", "answer_x"]].to_csv(
        os.getenv("SHIMMER_ADDRESS_READ_FROM_FILENAME"),
        index=False,
        header=["Name", "answer"],
    )
    logger.info(
        f"Saved {len(merged_df)} rows to {os.getenv('SHIMMER_ADDRESS_READ_FROM_FILENAME')}. Exiting..."
    )


def main():
    if basic_checks():
        # consolidate_accounts() # DEBUG
        compare_files()
    else:
        logger.info(
            "Make sure to fill out the information in the .env file. Rename .env.exmple to .env first."
        )


if __name__ == "__main__":
    main()
