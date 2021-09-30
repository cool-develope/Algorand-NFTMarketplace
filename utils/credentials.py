from algosdk.v2client import algod
import yaml
import os
from pathlib import Path
from algosdk.v2client import indexer
from typing import Tuple

def get_project_root_path() -> Path:
    return Path(os.path.dirname(__file__))

def load_config():
    root_path = get_project_root_path()
    config_location = os.path.join(root_path, 'config.yaml')

    with open(config_location) as file:
        return yaml.full_load(file)


def get_client() -> algod.AlgodClient:
    """
    :return:
        Returns algod_client
    """
    config = load_config()

    token = config.get('client_credentials').get('token')
    address = config.get('client_credentials').get('address')
    purestake_token = {'X-Api-key': token}

    algod_client = algod.AlgodClient(token, address, headers=purestake_token)
    return algod_client


def get_indexer() -> indexer.IndexerClient:
    config = load_config()

    token = config.get('client_credentials').get('token')
    headers = {'X-Api-key': token}
    my_indexer = indexer.IndexerClient(indexer_token=token,
                                       indexer_address="https://testnet-algorand.api.purestake.io/idx2",
                                       headers=headers)

    return my_indexer


def get_account_credentials(account_id: int) -> Tuple[str, str, str]:
    """
    Gets the credentials for the account with number: account_id
    :param account_id: Number of the account for which we want the credentials
    :return: (str, str, str) private key, address and mnemonic
    """
    config = load_config()
    account_name = f"account_{account_id}"

    account = config.get("accounts").get(account_name)
    return account.get("private_key"), account.get("address"), account.get("mnemonic")


def get_account_with_name(account_name: str) -> Tuple[str, str, str]:
    config = load_config()
    account = config.get(account_name)
    return account.get("private_key"), account.get("address"), account.get("mnemonic")
