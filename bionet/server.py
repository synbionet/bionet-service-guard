"""
Guard Server
Supports the following endpoints:

POST  /authenticate/request
Request Body: {address: '...'}
Response    : {message: 'msg to sign...'}
Status Code 200 on success, 400 on error

POST  /authenticate/verify
Request Body: {message: 'siwe msg...', signature: '...'}
Response    : {address: 'callers wallet address', token: 'jwt token'}
Status Code 200 on success, 400 on error

GET /token/verify{jwt token}
Response    : {address: 'callers wallet address'}
Status Code 200 on success, 400 on error
"""

from urllib.parse import urlparse
from dateutil.tz import UTC
from datetime import datetime, timedelta

from starlette.config import Config
from fastapi import FastAPI, HTTPException
from starlette.datastructures import Secret

from siwe import SiweMessage, generate_nonce

from bionet.w3 import is_authorized_user


from bionet.types import (
    Token,
    SignedMessage,
    ChallengeRequest,
    ChallengeResponse,
    AuthenticationResult,
)


config = Config(".env")
app = FastAPI()


@app.post("/authenticate/request")
async def siwe_request(req: ChallengeRequest):
    """
    Given the input return a SIWE message for the user to sign.
    Called from the service.
    """
    input = {}
    url = config("LOGIN_URL", cast=str)
    input["uri"] = url
    input["domain"] = urlparse(url).netloc
    input["address"] = req.address
    input["chain_id"] = config("CHAIN_ID", cast=int)
    input["version"] = config("VERSION", cast=str)
    input["nonce"] = generate_nonce()

    delta = config("CHALLENGE_EXPIRATION", cast=int)
    issued = datetime.utcnow()
    ex = issued + timedelta(seconds=delta)

    input["issued_at"] = issued.isoformat("T") + "Z"
    input["expiration_time"] = ex.isoformat("T") + "Z"

    try:
        siwe_message = SiweMessage(message=input).prepare_message()
        return ChallengeResponse(message=siwe_message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"challenge error: {e}")


@app.post("/authenticate/verify")
async def verify_signed_siwe_message(req: SignedMessage):
    """
    Verify signed SIWE message.
    Called from the service.
    """
    sk = config("SECRET_KEY", cast=Secret)
    aud = config("DOMAIN", cast=str)
    expires = config("TOKEN_EXPIRATION", cast=int)

    try:
        message = SiweMessage(message=req.message)
        message.verify(req.signature)
        token = Token.create(message.address, aud, expires)
        jwt = token.sign(str(sk))
        return AuthenticationResult(address=message.address, token=jwt).model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"verification error: {e}")


@app.get("/token/verify/{token}")
async def verify_token(token: str):
    """
    Verify the given JWT token and if the user is registered with the contract
    Called from the service.
    """
    domain = config("DOMAIN", cast=str)
    try:
        subject_address = Token.verify(token, domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"token error: {e}")

    # Check the contract here...
    is_valid = is_authorized_user(subject_address)
    if not is_valid:
        raise HTTPException(
            status_code=400, detail="Not a registered user of the service"
        )

    # Check the contract here...
    return AuthenticationResult(address=subject_address).model_dump()
