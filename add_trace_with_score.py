import sys
import json
from google import genai
from google.genai.errors import APIError
from langfuse import Langfuse, get_client, observe, Evaluation
from langfuse.experiment import LocalExperimentItem
from langfuse.media import LangfuseMedia
from typing import Dict
from google.genai import types
from PIL import Image
import base64

langfuse = get_client()
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")
    sys.exit(1)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def main():
    with langfuse.start_as_current_observation(as_type="span", name="image-crop") as span:
        
        client = genai.Client()
        filename = 'img/abba.jpg'
        with open(filename, 'rb') as f:
            image_bytes = f.read()
        
        image_b64 = encode_image("img/abba.jpg")
        file_as_bytes = base64.b64encode(image_bytes)
        media = LangfuseMedia(content_bytes=image_bytes, content_type="image/jpeg")

        source = "![Alt text](https://storage.googleapis.com/kablamo-labs-sandbox-langfuse-bucket/media/cmip9nhcs0006pf07htpiovfd/YieRbTlzXvLVkcFXgsceu5.jpeg)"

        span.update(input=source,output="here is an output")
        # response = client.models.generate_content(
        #     model="gemini-2.5-flash",
        #     contents=["In this image I only want the 2 women shown. If there are already only 2 women, then do not crop the image and simply return the coordinates of the entire image"
        #     "Otherwise, give me the coordinates to be able to crop the 2 women's faces. Return the crop format as a JSON object. Only return a single set of coordinates"
        #     "This is the JSON object in python notation: class Coords(TypedDict): left: int top: int right: int bottom: int", types.Part.from_bytes(
        #         data=image_bytes,
        #         mime_type='image/jpeg',
        #     )])
        return source
    langfuse.flush()

    

if __name__ == "__main__":
    main()