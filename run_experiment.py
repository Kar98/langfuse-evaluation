import sys
import json
from google import genai
from google.genai.errors import APIError
from langfuse import Langfuse, get_client, observe, Evaluation
from langfuse.experiment import LocalExperimentItem
from typing import Dict
from google.genai import types
from PIL import Image

langfuse = get_client()
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")
    sys.exit(1)

MODEL_NAME = ["gemini-2.5-flash", "gemini-2.5-pro"]


def task(*, item, **_):
    print("start task")
    filename = 'img/'+item["input"] #abba.jpg
    cropname = 'img/'+item["input"].replace(".jpg", "-cropped.jpg") #abba-cropped.jpg
    with open(filename, 'rb') as f:
        image_bytes = f.read()

    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=["In this image I only want the 2 women shown. If there are already only 2 women, then do not crop the image and simply return the coordinates of the entire image"
        "Otherwise, give me the coordinates to be able to crop the 2 women's faces. Return the crop format as a JSON object. Only return a single set of coordinates"
        "This is the JSON object in python notation: class Coords(TypedDict): left: int top: int right: int bottom: int", types.Part.from_bytes(
            data=image_bytes,
            mime_type='image/jpeg',
        )],
    )

    start = response.text.find("{")
    end = response.text.find("}")+1

    trimmed = response.text[start:end]
    jsonData = json.loads(trimmed)
    print(jsonData)

    image1 = Image.open(filename)
    cropped = image1.crop((jsonData["left"], jsonData["top"], jsonData["right"], jsonData["bottom"]))
    cropped.save(cropname)
    return cropname

def accuracy_eval(*, input, output, expected_output, **_):
    print(f"input is: {input}")
    print(f"output is: {output}")
    print(f"expected_output is: {expected_output}")

    with open(output, 'rb') as f:
        image_bytes = f.read()
    
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=["From this image, can you see only 2 women's faces clearly? If it's not clear or there are less than 2 women, or more than 2 people (women or man) then return false."
        "Only return a simple true or false. If the criteria is invalid, then return invalid.", types.Part.from_bytes(
            data=image_bytes,
            mime_type='image/jpeg',
        )],
    )

    
    retValue = response.text
    if len(response.text) > 7:
        print("an error occurred")
        print(response.text)
        retValue = "ERROR"

    print("retValue")
    print(retValue)
    return Evaluation(name="passed", value=retValue)

@observe()
def main():
    # Experiment runner iterates dataset items, traces calls, and applies evaluators
    localExpData: LocalExperimentItem = [{
        "input": "abba.jpg",
        "expected_output": "true",
        "metadata": {"difficulty": "low", "category": "image-testing", "band": "abba", "manual": "false"}
    },
    {
        "input": "abba-manualcrop.jpg",
        "expected_output": "true",
        "metadata": {"difficulty": "low", "category": "image-testing", "band": "abba", "manual": "true"}
    }]

    print("start experiment")
    result = langfuse.run_experiment(
        name="image cropping test",
        data=localExpData,
        task=task,
        evaluators=[accuracy_eval],
        metadata={"difficulty": "low", "category": "image-testing"}
    )

    print(result.format())

if __name__ == "__main__":
    main()