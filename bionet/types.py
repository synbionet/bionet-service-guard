import json
import base64
from typing import Optional, Dict
from dateutil.tz import UTC

from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from pydantic import BaseModel
from siwe import generate_nonce
from eth_account import Account
from eth_utils.address import is_hex_address
from eth_account.messages import encode_defunct


class ChallengeRequest(BaseModel):
    """Request for a SIWE message to sign"""

    address: str


class ChallengeResponse(BaseModel):
    """message in the SIWE format to be signed by client"""

    message: str


class SignedMessage(BaseModel):
    """
    Structure used to send login requests.
    message: SIWE formatted
    signature: hex encoded
    """

    message: str
    signature: str


class AuthenticationResult(BaseModel):
    """
    Structure used to hold the results of an authentication or token verification
    address: wallet address of caller
    token: JWT token
    """

    address: str
    token: Optional[str] = None

    @classmethod
    def from_json(cls, value: Dict) -> "AuthenticationResult":
        return cls(address=value["address"], token=value["token"])


@dataclass
class Token:
    """
    Represents a JWT Token
    """

    dict = asdict
    sub: str
    aud: str
    iss: str = ""
    nbf: int = 0
    exp: int = 0
    iat: int = 0
    jti: str = ""

    @classmethod
    def create(cls, sub: str, aud: str, expiration_in_hours: int) -> "Token":
        """
        Create an un-signed token with timestamps

        Params:
        sub: the address of the recipient of the token
        aud: the domain of the issuer
        expiration_in_hours: number of hours the token is valid (expiration)

        Returns the populated token
        """
        if not is_hex_address(sub):
            raise Exception("sub must be a valid ethereum address")

        token = cls(sub=sub, aud=aud)
        now = datetime.now(UTC)
        expires = int((now + timedelta(hours=expiration_in_hours)).timestamp())
        now_timestamp = int(now.timestamp())

        token.nbf = now_timestamp
        token.iat = now_timestamp
        token.exp = expires

        token.jti = generate_nonce()
        return token

    def sign(self, issuer_private_key: str) -> str:
        """
        Sign with the issuer's private key and return a JWT

        Params:
        issuer_private_key:  The service owner's private key. Used to sign tokens

        On success, returns the JWT token
        """
        account = Account.from_key(issuer_private_key)
        self.iss = account.address

        payload = json.dumps(self.dict(), separators=(",", ":"))

        encoded = encode_defunct(text=payload)
        signature = account.sign_message(encoded).signature.hex()

        encoded_header = json.dumps(
            {
                "alg": "ES256",
                "typ": "JWT",
            },
            separators=(",", ":"),
        )

        h = _base64_encode(encoded_header)
        p = _base64_encode(payload)
        s = _base64_encode(signature)

        return f"{h}.{p}.{s}"

    @staticmethod
    def verify(token: str, domain: str) -> str:
        """
        Verify a raw token.

        Params:
        token: the JWT token to verify
        domain: the service domain

        Throws exception on any validation errors
        On success, returns the subject's address

        One of the key verifications is that the signer is the issuer
        """
        encoded_payload = token.split(".")[1]
        encoded_signature = token.split(".")[2]

        raw_payload = _base64decode(encoded_payload)
        p_dict = json.loads(raw_payload)
        # thaw the token
        payload = Token(**p_dict)

        # recover the signer's address
        signature = _base64decode(encoded_signature)
        hashed_payload_message = encode_defunct(text=raw_payload)
        recovered_address = Account.recover_message(
            hashed_payload_message, signature=signature
        )

        # ...verification checks...
        now = int(datetime.now(UTC).timestamp())

        # 1. Check the signer is the recorded issuer
        if recovered_address.lower() != payload.iss.lower():
            raise Exception("Signer address does not match the token issuer")

        # 2. Check the token is not being used before the valid date
        if now < payload.nbf:
            raise Exception("The token is not valid yet (nbf) ")

        # 3. Check given domain matches 'aud'
        if domain != payload.aud:
            raise Exception("The given domain does not match the token 'aud'")

        # 4. Check token is not expired
        if now > payload.exp:
            raise Exception("The token has expired")

        # 5. Sanity check the subject field
        if len(payload.sub) == 0:
            raise Exception("Invalid subject field (sub)")

        return payload.sub


# Helpers...
def _base64_encode(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("utf-8")


def _base64decode(value: str) -> str:
    return base64.b64decode(value).decode("utf-8")
