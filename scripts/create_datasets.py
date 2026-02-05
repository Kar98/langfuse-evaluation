from langfuse import Langfuse, get_client, observe
from datetime import datetime
from langfuse.api.resources.commons.errors import NotFoundError

langfuse = get_client()

if not langfuse.auth_check():
    print("auth check failed")

now = datetime.now()
print(now.date())


dsName = "mediabrief/smoketests"

try:
    ds = langfuse.get_dataset(dsName)
except NotFoundError:
    ds = langfuse.create_dataset(
    name=dsName,
    description="Smoke tests for the media briefs",
    metadata={
        "author": "Rory",
        "date": now.date(),
        "type": "smoketest"
    }
)

langfuse.create_dataset_item(
    dataset_name=dsName,
    input={
        "question": "are you gemini 2"
    },
    expected_output={
        "answer": "yes 2"
    },
    metadata={
        "model": "gemini",
    }
)