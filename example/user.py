"""
Alice is a client of Bob's Service
"""
import httpx
from bionet.api import authenticate

ALICE_ADDRESS = "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f"
ALICE_SECRET_KEY = "0xdbda1821b80551c9d65939329250298aa3472ba22feea921c0cf5d620ea67b97"


def can_access_service():
    """
    This demonstrates Alice authenticating and accessing the service.  It makes several
    HTTP calls to the service.   This will fail if Alice is not a registered user of the
    service.
    """
    token = authenticate("http://localhost:8080/login", ALICE_SECRET_KEY)

    result = httpx.post("http://localhost:8080/dna", headers={"Bearer": token})

    if result.status_code == 200:
        return True
    return False
