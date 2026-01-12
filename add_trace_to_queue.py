import sys
import os
import base64
import json
import requests
from google import genai
from langfuse import get_client, Langfuse, observe, propagate_attributes
from langfuse.media import LangfuseMedia
from google.genai import types
from PIL import Image
from funcs import login, init, uploadImage, isLangfuseAuthenticated

# Set in init()
auth = ""
baseurl = ""

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
    isLangfuseAuthenticated(langfuse)
    import uuid
    uid = str(uuid.uuid4())
    print(uid)
    queueId = "cmiqo5ad4000pmp07hd7ewg2t"
    
    with propagate_attributes(session_id=uid):
        

        # start trace1
        with langfuse.start_as_current_observation(as_type="span", name="main-span") as span1:
            with span1.start_as_current_observation(as_type="generation", name="chatbot") as gen1:
                inputCost = 0.001 * 1
                outputCost = 0.001 * 2
                gen1.update(
                    model="gemini-2.5-flash", 
                    usage_details={"input": 1, "output": 2},
                    cost_details={"input": inputCost,"output": outputCost,"total":inputCost + outputCost,})
                gen1.update(input="here is something about 1",output="some output 1")

            with span1.start_as_current_observation(as_type="generation", name="chatbot") as gen2:
                inputCost = 0.001 * 3
                outputCost = 0.001 * 4
                gen2.update(
                    model="gemini-2.5-flash", 
                    usage_details={"input": 3, "output": 4},
                    cost_details={"input": inputCost,"output": outputCost,"total":inputCost + outputCost,})
                gen2.update(input="here is something about 2",output="some output 2")
            span1.update_trace(input="trace1 input data here", output="trace1 output here")
        
        # Start trace2
        with langfuse.start_as_current_observation(as_type="span", name="sec-span") as span2:
            with span1.start_as_current_observation(as_type="generation", name="chatbot") as gen3:
                inputCost = 0.001 * 1
                outputCost = 0.001 * 2
                gen3.update(
                    model="gemini-2.5-flash", 
                    usage_details={"input": 1, "output": 2},
                    cost_details={"input": inputCost,"output": outputCost,"total":inputCost + outputCost,})
                gen3.update(input="here is something about 3",output="some output 3")
            span2.update_trace(input="trace2 input data here", output="trace2 output here")
        
        addSessionToQueue(queueId, uid)
    return "success"

# Adds a trace to the queue and returns the ID
def addSessionToQueue(queueId, objectId: str):
    url = f"{baseurl}/api/public/annotation-queues/{queueId}/items"

    payload = json.dumps({
    "objectId": objectId,
    "objectType": "SESSION",
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

if __name__ == "__main__":
    baseurl, pubkey, secret = init()
    auth = login(pubkey, secret)
    main()