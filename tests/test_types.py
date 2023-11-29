import pytest
from dateutil.tz import UTC
from datetime import datetime, timedelta

from bionet.types import Token
from eth_account import Account
from siwe import generate_nonce


def test_good_token():
    issuer = Account.create()
    sk = issuer.key.hex()

    subject = Account.create()

    token = Token.create(subject.address, "example.com", 3)
    jwt = token.sign(sk)

    sub = Token.verify(jwt, "example.com")
    assert sub == subject.address


def test_token_bad_input():
    with pytest.raises(BaseException):
        Token.create("not valid address", "example.com", 3)


def test_expired_token():
    issuer = Account.create()
    subject = Account.create()

    # Create a token that expired an hour ago
    expired_token = Token(subject.address, "example.com", 1)

    now = datetime.now(UTC)
    issued_two_hours_ago = int((now - timedelta(hours=2)).timestamp())
    expires = int((now - timedelta(hours=1)).timestamp())

    expired_token.nbf = issued_two_hours_ago
    expired_token.iat = issued_two_hours_ago
    expired_token.exp = expires

    expired_token.jti = generate_nonce()
    jwt = expired_token.sign(issuer.key.hex())

    with pytest.raises(BaseException):
        Token.verify(jwt, "example.com")


def test_nbf_token():
    issuer = Account.create()
    subject = Account.create()

    # Create a token that can't be used yet
    token = Token(subject.address, "example.com", 1)
    now = datetime.now(UTC)
    issued_in_future = int((now + timedelta(hours=2)).timestamp())
    expires = int((now + timedelta(hours=3)).timestamp())

    token.nbf = issued_in_future
    token.iat = issued_in_future
    token.exp = expires

    token.jti = generate_nonce()
    jwt = token.sign(issuer.key.hex())

    with pytest.raises(BaseException):
        Token.verify(jwt, "example.com")
