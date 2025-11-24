import sys
from google import genai
from google.genai.errors import APIError
from langfuse import Langfuse, get_client, observe, Evaluation
from langfuse.experiment import LocalExperimentItem

langfuse = get_client()
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")
    sys.exit(1)

MODEL_NAME = ["gemini-2.5-flash", "gemini-2.5-pro"]


def task(*, item, **_):
    print(f'item.input is {item["input"]}')
    client = genai.Client()
    response = client.models.generate_content(
            model=item["input"],
            contents=f'echo back the text: {item["input"]}',
        )
    

    print(f'gemini returned the following {response.text}')
    return response.text

def accuracy_eval(*, input, output, expected_output, **_):
    ok = expected_output.lower() in output.lower()
    # kick off lambda

    # lambda is complete

    # grab lambda results

    return Evaluation(name="accuracy", value=1.0 if ok else 0.0)

# Experiment runner iterates dataset items, traces calls, and applies evaluators
localExpData: LocalExperimentItem = [{
            "input": MODEL_NAME[0],
            "expected_output": "gemini-2.5-flash",
            "metadata": {"difficulty": "low", "category": "test"}
        },
        {
            "input": MODEL_NAME[1],
            "expected_output": "gemini-2.5-pro",
            "metadata": {"difficulty": "low", "category": "test"}
        }]

print("start experiment")
result = langfuse.run_experiment(
    name="Rory test echoing",
    data=localExpData,
    task=task,
    evaluators=[accuracy_eval],
)

print(result.format())