import base64
import os

# Returns the Authorization for the APIs
def login(pubkey, secret):
    auth = "Basic "+base64.b64encode(f"{pubkey}:{secret}".encode("utf-8")).decode()
    return auth

# Loads the env vars and fails if not found
def init():
    baseurl = os.getenv("LANGFUSE_BASE_URL")
    if not baseurl:
        raise ValueError("LANGFUSE_BASE_URL needs to be set")

    pubkey = os.getenv("LANGFUSE_PUBLIC_KEY")
    if not pubkey:
        raise ValueError("LANGFUSE_PUBLIC_KEY needs to be set")

    secret = os.getenv("LANGFUSE_SECRET_KEY")
    if not secret:
        raise ValueError("LANGFUSE_SECRET_KEY needs to be set")
    
    return baseurl, pubkey, secret
