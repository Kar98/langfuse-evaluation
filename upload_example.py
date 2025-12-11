import os
import requests
import base64
import hashlib
import uuid
import time
from langfuse.media import LangfuseMedia
 
base_URL = os.getenv("LANGFUSE_BASE_URL")
public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
secret_key = os.getenv("LANGFUSE_SECRET_KEY")

file_path = "img/abba-cropped.jpg"
with open(file_path, "rb") as f:
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
            #"x-amz-checksum-sha256": content_sha256,
        },
        data=content_bytes,
    )
    print('upload_response.status_code')
    print(upload_response.status_code)
    print('upload langfuse media')
    media = LangfuseMedia(content_bytes=content_bytes, content_type="image/jpeg")
 
time.sleep(3)
# below doesnt work, need to find out why. but image is actually uploaded to GCP
media_request = requests.get(
    f"{base_URL}/api/public/media/{upload_url_response['mediaId']}",
    auth=(public_key or "", secret_key or "")
)
 
media_response = media_request.json()
print("media_response")
print(media_response)
print('done')