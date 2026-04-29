"""
Direct LLM connection test — no server needed.
Tests that CortexAgentChatModel can connect and respond.
Run: venv\Scripts\activate.bat && py test_llm.py
"""
from dotenv import load_dotenv
load_dotenv(override=True)

from app.llm.cortex_llm import CortexAgentChatModel
from app.core.config import settings
import json

print(f"Testing LLM connection for agent: {settings.cortex_agent_name}")
print("Initializing CortexAgentChatModel...")

llm = CortexAgentChatModel(agent_name=settings.cortex_agent_name)
print(f"Profile: {json.dumps(llm.get_profile(), indent=2)}")

print("\nSending test prompt...")
response = llm.invoke("In one sentence, what is LangChain?")
print(f"Response: {response.content}")
print("\nLLM connection test PASSED.")
