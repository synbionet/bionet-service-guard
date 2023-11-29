import os
import pytest

from siwe import SiweMessage
from eth_account import Account
from fastapi.testclient import TestClient
from eth_account.messages import encode_defunct
from bionet.types import AuthenticationResult, ChallengeRequest


@pytest.fixture
def client():
    from bionet.server import app

    client = TestClient(app)
    return client


def test_good_challenge_request(client: TestClient):
    sk = os.environ["TEST_CLIENT_SK"]
    account = Account.from_key(sk)

    response = client.post("/authenticate/request", json={"address": account.address})
    assert response.status_code == 200
    result = response.json()

    # Test the message is correct
    assert result["message"]
    back = SiweMessage(result["message"])
    assert back.address == account.address


def test_bad_challenge_request(client: TestClient):
    req = ChallengeRequest(address="0x")
    response = client.post("/authenticate/request", json={"address": "0x"})
    assert response.status_code == 400


def test_good_authetication(client: TestClient):
    sk = os.environ["TEST_CLIENT_SK"]
    account = Account.from_key(sk)

    # req = ChallengeRequest(address=account.address)
    response = client.post("/authenticate/request", json={"address": account.address})
    assert response.status_code == 200
    result = response.json()

    msg = SiweMessage(result["message"])
    raw = msg.prepare_message()
    encoded = encode_defunct(text=raw)
    sig = account.sign_message(encoded)

    response = client.post(
        "/authenticate/verify", json={"message": raw, "signature": sig.signature.hex()}
    )
    assert response.status_code == 200
    result = AuthenticationResult.from_json(response.json())

    assert account.address == result.address
    assert len(result.token) > 0


def test_bad_authetication(client: TestClient):
    response = client.post(
        "/authenticate/verify", json={"message": "bad", "signature": "bad"}
    )
    assert response.status_code == 400


def test_bad_token(client: TestClient):
    r = client.get(f"/token/verify/bad")
    assert r.status_code == 400


def test_good_token(client: TestClient):
    sk = os.environ["TEST_CLIENT_SK"]
    account = Account.from_key(sk)

    # get the siwe message to sign
    response = client.post("/authenticate/request", json={"address": account.address})
    assert response.status_code == 200
    result = response.json()
    assert result["message"]

    # Sign the message and authenticate with it
    msg = SiweMessage(result["message"])
    raw = msg.prepare_message()
    encoded = encode_defunct(text=raw)
    sig = account.sign_message(encoded)

    response = client.post(
        "/authenticate/verify", json={"message": raw, "signature": sig.signature.hex()}
    )
    assert response.status_code == 200
    result = AuthenticationResult.from_json(response.json())
    assert account.address == result.address
