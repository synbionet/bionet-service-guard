"""
Web3 helpers and Contract Meta for the ServiceRegistry Contract
"""
import json

from web3 import Web3
from eth_account import Account
from starlette.config import Config
from eth_account.signers.local import LocalAccount
from web3.middleware import construct_sign_and_send_raw_middleware
from web3.exceptions import ContractLogicError


ABI = r"""
[
    {
      "inputs": [],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": true,
          "internalType": "address",
          "name": "from",
          "type": "address"
        },
        {
          "indexed": true,
          "internalType": "address",
          "name": "to",
          "type": "address"
        }
      ],
      "name": "Register",
      "type": "event"
    },
    {
      "anonymous": false,
      "inputs": [
        {
          "indexed": true,
          "internalType": "address",
          "name": "from",
          "type": "address"
        },
        {
          "indexed": true,
          "internalType": "address",
          "name": "to",
          "type": "address"
        }
      ],
      "name": "Removed",
      "type": "event"
    },
    {
      "inputs": [],
      "name": "admin",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "user",
          "type": "address"
        }
      ],
      "name": "isValidUser",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "user",
          "type": "address"
        }
      ],
      "name": "registerUser",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "user",
          "type": "address"
        }
      ],
      "name": "remove",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    }
]
"""

BYTECODE = "0x608060405234801561001057600080fd5b50600080546001600160a01b0319163317905561034b806100326000396000f3fe608060405234801561001057600080fd5b506004361061004c5760003560e01c80632199d5cd1461005157806329092d0e14610066578063f3c95c6014610079578063f851a440146100ba575b600080fd5b61006461005f3660046102e5565b6100e5565b005b6100646100743660046102e5565b6101ed565b6100a56100873660046102e5565b6001600160a01b031660009081526001602052604090205460ff1690565b60405190151581526020015b60405180910390f35b6000546100cd906001600160a01b031681565b6040516001600160a01b0390911681526020016100b1565b6000546001600160a01b031633146101345760405162461bcd60e51b815260206004820152600d60248201526c2737ba103a34329030b236b4b760991b60448201526064015b60405180910390fd5b6001600160a01b03811660009081526001602052604090205460ff161561019d5760405162461bcd60e51b815260206004820152601760248201527f5573657220616c72656164792072656769737465726564000000000000000000604482015260640161012b565b6001600160a01b0381166000818152600160208190526040808320805460ff19169092179091555130917f98ada70a1cb506dc4591465e1ee9be3fd7a2b6c73ecf3b949009718c9a35151991a350565b6000546001600160a01b031633146102375760405162461bcd60e51b815260206004820152600d60248201526c2737ba103a34329030b236b4b760991b604482015260640161012b565b6001600160a01b03811660009081526001602081905260409091205460ff1615151461029b5760405162461bcd60e51b8152602060048201526013602482015272155cd95c881b9bdd081c9959da5cdd195c9959606a1b604482015260640161012b565b6001600160a01b038116600081815260016020526040808220805460ff191690555130917f40e634d0e26d9ec2e860e4dd9b7b2cfbb569b6058362a1a54d3a94718bc4958791a350565b6000602082840312156102f757600080fd5b81356001600160a01b038116811461030e57600080fd5b939250505056fea2646970667358221220d50485b1173c14ee0f3f84a1cfcb4274687fd499a202cfac6e2dc6c7d3b58e2f64736f6c63430008140033"


def is_authorized_user(user: str) -> bool:
    config = Config(".env")
    rpc_url = config("RPC_NODE_URL", cast=str)
    contract = config("SERVICE_CONTRACT_ADDRESS", cast=str)
    if len(contract) == 0:
        raise Exception("Config file missing service contract address!")

    w3 = Web3(Web3.HTTPProvider(rpc_url))

    assert w3.is_connected()

    abi = json.loads(ABI)
    registry = w3.eth.contract(address=contract, abi=abi)
    result = registry.functions.isValidUser(user).call()
    return result


def setup_web3():
    config = Config(".env")
    rpc_url = config("RPC_NODE_URL", cast=str)
    secret_key = config("SECRET_KEY", cast=str)
    # contract_address = config("SERVICE_CONTRACT_ADDRESS", cast=str)

    # if len(contract_address) > 0:
    #    raise Exception("Existing contract address found in .env file")

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise Exception("Cannot connect to an an Ethereum node ")

    account: LocalAccount = Account.from_key(secret_key)
    # assert account.address == "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    w3.middleware_onion.add(construct_sign_and_send_raw_middleware(secret_key))
    return (w3, account.address)


def deploy_contract() -> str:
    w3, address = setup_web3()
    abi = json.loads(ABI)

    registry = w3.eth.contract(abi=abi, bytecode=BYTECODE)
    tx_hash = registry.constructor().transact({"from": address})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt.contractAddress


def register_user(user: str):
    config = Config(".env")
    contract = config("SERVICE_CONTRACT_ADDRESS", cast=str)
    if len(contract) == 0:
        raise Exception("Config file missing service contract address!")

    w3, from_address = setup_web3()
    abi = json.loads(ABI)

    registry = w3.eth.contract(address=contract, abi=abi)
    tx_hash = registry.functions.registerUser(user).transact({"from": from_address})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt["transactionHash"].hex()


def remove_user(user: str):
    config = Config(".env")
    contract = config("SERVICE_CONTRACT_ADDRESS", cast=str)
    if len(contract) == 0:
        raise Exception("Config file missing service contract address!")

    w3, from_address = setup_web3()
    abi = json.loads(ABI)
    registry = w3.eth.contract(address=contract, abi=abi)
    tx_hash = registry.functions.remove(user).transact({"from": from_address})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt["transactionHash"].hex()
