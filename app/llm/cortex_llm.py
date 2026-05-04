"""
CortexAgentChatModel — slim LangChain BaseChatModel that talks to the Cortex
OpenAI-compatible gateway via APIM OAuth2 client-credentials auth.

This is a deliberately minimal wrapper:
  - No tools / multimodal / structured-output features (DeepEval doesn't use them).
  - No agent-config fetch from cortex.lilly.com (was cookie-only).
  - Sends standard OpenAI chat-completions payload via CortexAPIService.

Public surface kept stable for the rest of the app:
  CortexAgentChatModel(agent_name=...).invoke([HumanMessage(...)]) -> AIMessage
  .ainvoke(...)
  .get_profile() -> dict
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

from pydantic import Field
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.core.config import settings
from app.llm.cortex_service import get_cortex_service

logger = logging.getLogger(__name__)


def _to_openai_messages(messages: List[BaseMessage]) -> List[dict]:
    """Convert LangChain messages to OpenAI chat-completion message dicts."""
    role_map = {"human": "user", "ai": "assistant", "system": "system"}
    out: List[dict] = []
    for msg in messages:
        role = role_map.get(msg.type, "user")
        if isinstance(msg.content, str):
            content = msg.content
        elif isinstance(msg.content, list):
            # Flatten any structured content blocks to plain text
            parts = []
            for block in msg.content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            content = "\n".join(p for p in parts if p)
        else:
            content = str(msg.content)
        out.append({"role": role, "content": content})
    return out


def _extract_assistant_text(payload: dict) -> str:
    """Pull the assistant text out of a standard OpenAI chat-completions response."""
    try:
        choices = payload.get("choices") or []
        if not choices:
            raise ValueError("Cortex response has no 'choices'.")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if content is None:
            raise ValueError("Cortex response choice has no message.content.")
        return content if isinstance(content, str) else str(content)
    except Exception as e:
        raise RuntimeError(f"Failed to parse Cortex chat-completions response: {e}; payload={payload!r:.500}")


class CortexAgentChatModel(BaseChatModel):
    """LangChain chat model backed by Cortex's OpenAI-compatible APIM gateway."""

    agent_name: str = Field(description="Cortex agent / deployment name")
    temperature: float = Field(default=0.0)
    max_tokens: int = Field(default=4096)
    api_version: str = Field(default="2023-05-15")

    def __init__(self, agent_name: str, **kwargs: Any) -> None:
        super().__init__(
            agent_name=agent_name,
            temperature=kwargs.pop("temperature", settings.cortex_temperature),
            max_tokens=kwargs.pop("max_tokens", settings.cortex_max_tokens),
            api_version=kwargs.pop("api_version", settings.cortex_api_version),
            **kwargs,
        )

    @property
    def _llm_type(self) -> str:
        return "cortex_agent_chat_model"

    # ------------------------------------------------------------------
    def _endpoint(self) -> str:
        return settings.cortex_endpoint_template.format(agent=self.agent_name)

    def _query_params(self) -> Optional[dict]:
        if settings.cortex_send_api_version:
            return {"api-version": self.api_version}
        return None

    def _extra_headers(self) -> Optional[dict]:
        if settings.cortex_agent_in_header and settings.cortex_agent_header_name:
            return {settings.cortex_agent_header_name: self.agent_name}
        return None

    def _build_payload(self, messages: List[BaseMessage], **kwargs: Any) -> dict:
        payload: dict = {
            "messages": _to_openai_messages(messages),
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        if settings.cortex_agent_in_body and settings.cortex_agent_body_field:
            payload[settings.cortex_agent_body_field] = self.agent_name
        return payload

    # ------------------------------------------------------------------
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        service = get_cortex_service()
        resp = service.call(
            endpoint=self._endpoint(),
            method="POST",
            query_params=self._query_params(),
            data=self._build_payload(messages, **kwargs),
            extra_headers=self._extra_headers(),
        )
        text = _extract_assistant_text(resp.json())
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        service = get_cortex_service()
        resp = await service.acall(
            endpoint=self._endpoint(),
            method="POST",
            query_params=self._query_params(),
            data=self._build_payload(messages, **kwargs),
            extra_headers=self._extra_headers(),
        )
        text = _extract_assistant_text(resp.json())
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    # ------------------------------------------------------------------
    def get_profile(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "api_version": self.api_version,
            "auth_mode": "apim_oauth_client_credentials",
            "base_url": settings.cortex_openai_base,
        }


