"""
Example of a service endpoint that integrates with the bionet guard for authentication/authorization
"""
import httpx
from fastapi import FastAPI, HTTPException, Header
from bionet.types import ChallengeRequest, SignedMessage

app = FastAPI()


def _endpoint(path: str) -> str:
    return f"http://localhost:5000/{path}"


@app.post("/login")
async def login(req: ChallengeRequest | SignedMessage):
    """
    Take the request and forward to guard
    """
    # Check which message is being sent...
    if isinstance(req, ChallengeRequest):
        try:
            response = httpx.post(
                _endpoint("authenticate/request"), json=req.model_dump()
            )
            return response.json()
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=400, detail=f"authenticate: challenge request error: {e}"
            )
    elif isinstance(req, SignedMessage):
        try:
            response = httpx.post(
                _endpoint("authenticate/verify"), json=req.model_dump()
            )
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"authenticate: verify request error: {e}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="authenticate: expected either a challenge request or signed message",
        )


@app.post("/dna")
async def dna_data(bearer: str | None = Header(default=None)):
    if not bearer:
        raise HTTPException(status_code=401, detail="Please login...")
    url = _endpoint(f"token/verify/{bearer}")
    resp = httpx.get(url)
    if resp.status_code != 200:
        raise HTTPException(
            status_code=401, detail=f"authenticate: token verification failed"
        )
    # My name as a DNA sequence :-)  dave == GAT GCT GTC GAG
    return "GATGCTGTCGAG"
