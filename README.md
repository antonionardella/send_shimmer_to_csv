# Send Shimmer to CSV
## Introduction

`send_shimmer_to_csv` is a command line tool that uses Python bindings of the [iota.rs](github.com/iotaledger/iota.rs) and [wallet.rs](github.com/iotaledger/wallet.rs) libraries, and allows you to send Shimmer tokens to the corresponding addresses from a list of addresses present in a CSV file.

The tool reads the list of receiver addresses from a specified file, verifies if they are valid, and sends Shimmer (SMR) tokens to each corresponding address present in the list.
Requirements

- Python 3.x
- BIP39 mnemonic
- Shimmer python libraries installed following these instruction for [iota.rs](https://wiki.iota.org/shimmer/iota.rs/getting_started/python/) and [wallet.rs](https://wiki.iota.org/shimmer/wallet.rs/getting_started/python/)

## Installation

```
git clone https://github.com/antonionardella/send_shimmer_to_csv.git
cd send_shimmer_to_csv
pip install -r requirements.txt
```

## Configuration

Configure the environment variables in the .env file with the following values:

| Variable | Description |
|-------------|-------------|
| STRONGHOLD_PASSWORD | The password for your stronghold |
| STRONGHOLD_DB_NAME | The stronghold database name |  
| WALLET_DB_NAME | The wallet database name |
| SHIMMER_MNEMONIC | A 24 words BIP39 wallet mnemonic |
| SHIMMER_ACCOUNT_NAME | Your Shimmer account name |
| SHIMMER_SMR_TOKEN_AMOUNT | The amount of SMR tokens to be sent |
| CONFIG_DONE | Set to False initially, and then True once the configuration is done |
| SHIMMER_ADDRESS_READ_FROM_FILENAME | The name of the CSV file that contains the addresses to send Shimmer tokens, Address should be in the Column B |
| SHIMMER_ADDRESS_SENT_TO_FILENAME | The name of the CSV file that contains the addresses where the Shimmer tokens have been sent |

## Usage

After the configuration, run the following command:

`python send_shimmer_to_csv.py`

## Troubleshooting

In case of issues with the tool, check the application logs present in the app.log file.

## Contributions

Contributions are always welcome! Feel free to create issues, pull requests, or contact me.

## License

This tool is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for more information.
