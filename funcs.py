import base64

import sys
import os
from datetime import datetime, timezone
import requests
import base64
import hashlib
import uuid
import time
from langfuse.media import LangfuseMedia
from langfuse import get_client

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

    upload_url_response = requests.post(
        f"{base_URL}/api/public/media",
        auth=(public_key or "", secret_key or ""),
        headers={"Content-Type": "application/json"},
        json=create_upload_url_body,
    )
    if upload_url_response.status_code != 201:
        raise RuntimeError(f"{base_URL}/api/public/media returned an error. code: {upload_url_response.status_code} text: {upload_url_response.text}")
    
    upload_response_json = upload_url_response.json()
    if (
        upload_response_json["mediaId"] is not None
        and upload_response_json["uploadUrl"] is not None
    ):
        upload_response = requests.put(
            upload_response_json["uploadUrl"],
            headers={
                "Content-Type": "image/jpeg",
            },
            data=content_bytes,
        )
        if upload_response.status_code != 201:
            raise RuntimeError(f"failed to upload to uploadUrl: {upload_response_json["uploadUrl"]} status: {upload_response.status_code} text: {upload_response.text}")
        # Need to set the status in Langfuse object storage, otherwise it won't think it's been uploaded even though it is.
        requests.patch(
        f"{base_URL}/api/public/media/{upload_response_json['mediaId']}",
        auth=(public_key or "", secret_key or ""),
        headers={"Content-Type": "application/json"},
        json={
            "uploadedAt": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ'), # ISO 8601
            "uploadHttpStatus": upload_response.status_code,
            "uploadHttpError": upload_response.text if upload_response.status_code != 200 else None,
        },
        )
        media = LangfuseMedia(content_bytes=content_bytes, content_type="image/jpeg")
    elif upload_response_json["mediaId"] is not None:
        # Most likely media already uploaded so pull the URL from Langfuse
        # requests.get(f"{base_URL}/api/public/media/{upload_response_json["mediaId"]}")
        media = LangfuseMedia(content_bytes=content_bytes, content_type="image/jpeg")
    else:
        raise RuntimeError("could not create LangfuseMedia object")
    print(f"Successfully uploaded image. MediaID: {media._get_media_id}")
    return media

def isLangfuseAuthenticated(langfuse):
    if langfuse.auth_check():
        print("Langfuse client is authenticated and ready!")
    else:
        print("Authentication failed. Please check your credentials and host.")
        sys.exit(1)