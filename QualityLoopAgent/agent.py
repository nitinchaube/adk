from google.adk.agents import LoopAgent, LlmAgent

drafter = LlmAgent(
    name="Drafter",
    model = "gemini-2.5-flash",
    instruction = """
  You are a writing quality improver.
  Check state['draft']. If it is empty, write a one-paragraph article about Python.
  
  Evaluate the current draft and give it a quality score (1-10) based on clarity,
  grammar, and depth. Store the score in state['quality_score'].
  
  If the score is below 8:
    - Rewrite the draft to improve it.
    - Store the improved version in state['draft'].
  
  If the score is 8 or above:
    - Do NOT rewrite.
    - Respond with exactly: QUALITY_MET
  """
)

root_agent = LoopAgent(
    name = "QualityRefinerLoop",
    sub_agents = [drafter],
    max_iterations = 3
)