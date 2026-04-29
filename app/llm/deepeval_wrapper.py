from deepeval.models.base_model import DeepEvalBaseLLM
from langchain_core.messages import HumanMessage
from app.llm.cortex_llm import CortexAgentChatModel


class CortexDeepEvalLLM(DeepEvalBaseLLM):
    """
    Thin DeepEval-compatible wrapper around CortexAgentChatModel.
    DeepEval uses this as its internal judge when running metrics.
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._llm = CortexAgentChatModel(agent_name=agent_name)

    def load_model(self):
        return self._llm

    def generate(self, prompt: str) -> str:
        response = self._llm.invoke([HumanMessage(content=prompt)])
        return response.content

    async def a_generate(self, prompt: str) -> str:
        response = await self._llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

    def get_model_name(self) -> str:
        return f"CortexAgent:{self.agent_name}"
