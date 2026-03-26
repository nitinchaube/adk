import os

import vertexai

project = os.environ["GOOGLE_CLOUD_PROJECT"]
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

client = vertexai.Client(project=project, location=location)
agent_engine = client.agent_engines.create()
print(agent_engine.api_resource.name)