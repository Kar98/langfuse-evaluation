import requests
import json
import os
from funcs import login, init

auth = ""
baseurl = ""

def main():
    # Create scores
    qualityScore = {
    "name": "quality",
    "dataType": "NUMERIC",
    "categories": None,
    "minValue": 0,
    "maxValue": 10,
    "description": "Rate the quality of this crop out of 10"
    }
    qualityScoreRes = createScoreConfig(qualityScore)

    inappropriate = {
    "name": "inappropriate",
    "dataType": "BOOLEAN",
    "description": "Was there any inappropriate content"
    }
    inappropriateRes = createScoreConfig(inappropriate)
    # Create queue
    configIds = [qualityScoreRes.json()["id"], inappropriateRes.json()["id"]]
    queues = {
        "name": "Manual validation",
        "description": "List of queues to manually validate the datasets",
        "scoreConfigIds": configIds
    }
    createAnnotationQueue(queues)

def createScoreConfig(bodyData: dict):
    path = f"{baseurl}/api/public/score-configs"
    payload = json.dumps(bodyData)
    headers = {
    'Content-Type': 'application/json',
    'Authorization': auth
    }
    score = requests.request("POST", path, headers=headers, data=payload)
    if score.status_code > 300:
        raise RuntimeError("status code was not 200", "statusCode", score.status_code, "response",score.text)
    return score

def createAnnotationQueue(bodyData: dict):
    path = f"{baseurl}/api/public/annotation-queues"
    payload = json.dumps(bodyData)
    headers = {
    'Content-Type': 'application/json',
    'Authorization': auth
    }
    score = requests.request("POST", path, headers=headers, data=payload)
    if score.status_code > 300:
        raise RuntimeError("status code was not 200", "statusCode", score.status_code, "response",score.text)

if __name__ == "__main__":
    baseurl, pubkey, secret = init()
    auth = login(pubkey, secret)
    main()
    print('done setup')