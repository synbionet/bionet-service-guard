"""
Client API used to talk to service
"""
import httpx
from siwe import SiweMessage
from eth_account import Account
from eth_account.messages import encode_defunct

from bionet.types import (
    AuthenticationResult,
)


def authenticate(url: str, private_key: str) -> str:
    """
    Authenticate to the service at the given URL.

    Params
    url        : The login URL defined by the service
    private_key: The client's private key used to sign a SIWE message

    This call makes 2 requests to the guard via the service.  The first call, requests
    a message to sign. The second call, verifies the signature over the message. On success,
    it returns status code 200 and a JWT token to be used as a bearer token on subsequent requests.

    Otherwise throws an exception
    """
    account = Account.from_key(private_key)

    response = httpx.post(url, json={"address": account.address})
    if response.status_code != 200:
        raise Exception(
            f"Error on challenge request. Status code: {response.status_code}"
        )

    msg_to_sign = response.json()["message"]
    siwe_msg = SiweMessage(msg_to_sign)
    raw = siwe_msg.prepare_message()
    encoded = encode_defunct(text=raw)
    sig = account.sign_message(encoded)

    response = httpx.post(url, json={"message": raw, "signature": sig.signature.hex()})
    if response.status_code != 200:
        raise Exception(
            f"Error on signed message request. Status code: {response.status_code}"
        )

    result = AuthenticationResult.from_json(response.json())

    return result.token
