import sys
import os
import base64
import json
import requests
from google import genai
from langfuse import get_client, Langfuse, observe
from langfuse.media import LangfuseMedia
from google.genai import types
from PIL import Image
from funcs import login, init, uploadImage

# Set in init()
auth = ""
baseurl = ""

def encode_image(image_path):
    if not os.path.exists(image_path):
        raise RuntimeError(f"filepath doesn't exist: {image_path}")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def promptWithImage(image_bytes):
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=["In this image I only want the 2 women shown. If there are already only 2 women, then do not crop the image and simply return the coordinates of the entire image"
        "Otherwise, give me the coordinates to be able to crop the 2 women's faces. Return the crop format as a JSON object. Only return a single set of coordinates"
        "This is the JSON object in python notation: class Coords(TypedDict): left: int top: int right: int bottom: int", types.Part.from_bytes(
            data=image_bytes,
            mime_type='image/jpeg',
        )])
    return response

# Adds a trace to the queue and returns the ID
def addToQueue(queueId, objectId: str):
    url = f"{baseurl}/api/public/annotation-queues/{queueId}/items"

    payload = json.dumps({
    "objectId": objectId,
    "objectType": "OBSERVATION",
    "status": "PENDING"
    })
    headers = {
    'Content-Type': 'application/json',
    'Authorization': auth
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code > 300:
        raise RuntimeError("status code was not 200", "statusCode", response.status_code, "error", response.text)
    return response.json()["id"]

def main():
    langfuse = get_client()
    bucketId = "kablamo-labs-sandbox-langfuse-bucket"
    projectId = "cmip9nhcs0006pf07htpiovfd"
    imgFilepath = 'img/abba.jpg'
    if langfuse.auth_check():
        print("Langfuse client is authenticated and ready!")
    else:
        print("Authentication failed. Please check your credentials and host.")
        sys.exit(1)

    
    with langfuse.start_as_current_observation(as_type="generation", name="image-crop") as obvs:
        with open(imgFilepath, 'rb') as f:
            image_bytes = f.read()

        media = LangfuseMedia(content_bytes=image_bytes, content_type="image/jpeg")
        # using alt text will make it be able to be loaded inline
        source = f"![image](https://storage.googleapis.com/{bucketId}/media/{projectId}/{media._media_id}.jpeg)"
        
        # Send image prompt
        # left: int top: int right: int bottom: int
        promptRes = promptWithImage(image_bytes)
        # Assume 1 token == 0.1 cents
        inputCost = 0.001 * promptRes.usage_metadata.prompt_token_count
        outputCost = 0.001 * promptRes.usage_metadata.candidates_token_count
        obvs.update(
            model="gemini-2.5-flash", 
            usage_details={
                "input": promptRes.usage_metadata.prompt_token_count, 
                "output": promptRes.usage_metadata.candidates_token_count
                },
            cost_details={
                "input": inputCost,
                "output": outputCost,
                "total":inputCost + outputCost, # Set this otherwise langfuse does terrible rounding in the dashboard when it calculates the totals
            })
        print(promptRes.text)
        try:
            #trim out JSON info
            start = promptRes.text.find("{")
            end = promptRes.text.find("}")+1
            trimmed = promptRes.text[start:end]
            # Get details
            promptJson = json.loads(trimmed)
            print(promptJson)
            left = promptJson["left"]
            top = promptJson["top"]
            right = promptJson["right"]
            bottom = promptJson["bottom"]
            img = Image.open(imgFilepath)
            croppedImg = img.crop((left, top, right, bottom))
            croppedName = "img/cropped.jpg"
            # Save cropped image via langfuse media
            croppedImg.save(croppedName)
            croppedLfMedia = uploadImage(croppedName)
            cropSource = f"![image](https://storage.googleapis.com/{bucketId}/media/{projectId}/{croppedLfMedia._media_id}.jpeg)"
            obvs.update(input=source,output=cropSource)
        except Exception as e:
            print(e)
            print("could not crop image")
            print(promptJson)
            obvs.update(input=media,output="error occurred")
            return "failed"
        
        
        # Add trace to the queue
        queueId = "cmiqo5ad4000pmp07hd7ewg2t"
        addToQueue(queueId, obvs.id)

    return "success"

if __name__ == "__main__":
    baseurl, pubkey, secret = init()
    auth = login(pubkey, secret)
    main()