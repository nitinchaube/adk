import vertexai

client = vertexai.Client(project="deft-shade-490204-h4", location="us-central1")
agent_engine = client.agent_engines.create()
print(agent_engine.api_resource.name)