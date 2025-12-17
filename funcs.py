import base64
import os
import requests
import base64
import hashlib
import uuid
import time
from langfuse.media import LangfuseMedia

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

# Uploads via the langfuse media API. Gets the URL via langfuse, then uploads directly to that link in GCS
def uploadImage(filepath):
    base_URL = os.getenv("LANGFUSE_BASE_URL")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    with open(filepath, "rb") as f:
        content_bytes = f.read()
    
    content_type = "image/jpeg"
    content_sha256 = base64.b64encode(hashlib.sha256(content_bytes).digest()).decode()
    trace_id = str(uuid.uuid4())
    content_length = len(content_bytes)
    field = "input"  # or "output" or "metadata"
    
    create_upload_url_body = {
        "traceId": trace_id,
        "contentType": content_type,
        "contentLength": content_length,
        "sha256Hash": content_sha256,
        "field": field,
    }

    upload_url_request = requests.post(
        f"{base_URL}/api/public/media",
        auth=(public_key or "", secret_key or ""),
        headers={"Content-Type": "application/json"},
        json=create_upload_url_body,
    )
    
    upload_url_response = upload_url_request.json()
    print("upload_url_response")
    print(upload_url_response)

    if (
        upload_url_response["mediaId"] is not None
        and upload_url_response["uploadUrl"] is not None
    ):
        upload_response = requests.put(
            upload_url_response["uploadUrl"],
            headers={
                "Content-Type": "image/jpeg",
            },
            data=content_bytes,
        )
        print('upload_response.status_code')
        print(upload_response.status_code)
        print('upload langfuse media')
        media = LangfuseMedia(content_bytes=content_bytes, content_type="image/jpeg")
    else:
        raise RuntimeError("mediaId or uploadUrl was None")
    return media