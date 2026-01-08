from langfuse import get_client
from langfuse.experiment import Evaluation
from langfuse.media import LangfuseMedia
from google import genai
from google.genai import types
import base64

langfuse = get_client()

# Define your task function
def my_task(*, item, **kwargs):
    client = genai.Client()
    b64_string = LangfuseMedia.resolve_media_references(obj=item.input, langfuse_client=langfuse, resolve_with='base64_data_uri')
    b64_string = b64_string.split(",")[1]
    image_bytes = base64.b64decode(b64_string)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=["Which band is in this image", 
                  types.Part.from_bytes(
                    data=image_bytes,
                    mime_type='image/jpeg',
        )])
    
    return response.text

def accuracy_eval(*, input, output, expected_output, **_):
    print(f"input is: {input}")
    print(f"output is: {output}")
    print(f"expected_output is: {expected_output}")

    if expected_output in output:
        return Evaluation(name="passed", value="1")
    else:
        return Evaluation(name="passed", value="0")


dataset = langfuse.get_dataset("images")
result = dataset.run_experiment(
    name="evaluate images",
    description="checks if the LLM returns the expected output",
    task=my_task,
    evaluators=[accuracy_eval]
)
print(result.format())

# for item in dataset.items:
#     res = LangfuseMedia.resolve_media_references(obj=item.input, langfuse_client=langfuse, resolve_with='base64_data_uri')
#     #  Base64 encoded image