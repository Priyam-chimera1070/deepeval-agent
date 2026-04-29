import os
import base64
import httpx
import json
import re
import uuid
import logging
import threading
from typing import Any, AsyncIterator, Iterator, List, Optional, Dict

from dotenv import load_dotenv
load_dotenv(override=True)

from pydantic import Field
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

logger = logging.getLogger(__name__)

# =============================================================================
# 1. AUTHENTICATION (MSAL for Dev / AWS for Prod)
# =============================================================================
USE_AWS_AUTH = os.getenv("USE_AWS_AUTH", "").lower() in ("true", "1", "yes")

CORTEX_CLIENT_ID = os.getenv("CORTEX_CLIENT_ID")
CORTEX_CLIENT_SECRET = os.getenv("CORTEX_CLIENT_SECRET")
CORTEX_AUTHORITY = os.getenv("CORTEX_AUTHORITY")
CORTEX_SCOPE = os.getenv("CORTEX_SCOPE")
CORTEX_COOKIE = os.getenv("CORTEX_COOKIE")

CORTEX_API_BASE = os.getenv("CORTEX_API_BASE", "https://cortex.lilly.com")
CORTEX_OPENAI_BASE = os.getenv("CORTEX_OPENAI_BASE", "https://gateway.apim.lilly.com/cortex/cortex-openai")

_msal_app = None
_msal_lock = threading.Lock()


def _get_azure_ad_token() -> str:
    global _msal_app
    with _msal_lock:
        if _msal_app is None:
            import msal
            _msal_app = msal.ConfidentialClientApplication(
                client_id=CORTEX_CLIENT_ID,
                client_credential=CORTEX_CLIENT_SECRET,
                authority=CORTEX_AUTHORITY,
            )
    result = _msal_app.acquire_token_for_client(scopes=[CORTEX_SCOPE])
    if "access_token" not in result:
        raise Exception(f"MSAL Auth Failed: {result.get('error_description')}")
    return result["access_token"]


def _get_aws_auth_headers() -> dict:
    import boto3
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest
    session = boto3.Session(region_name="us-east-1")
    request = AWSRequest(method="POST", url="https://sts.amazonaws.com/", data="Action=GetCallerIdentity&Version=2011-06-15")
    SigV4Auth(session.get_credentials(), "sts", "us-east-1").add_auth(request)
    headers = {**request.headers, "Accept": "application/json"}
    headers.pop("Host", None)
    return headers


def _get_api_headers() -> dict:
    if USE_AWS_AUTH:
        return _get_aws_auth_headers()
    return {"Authorization": f"Bearer {_get_azure_ad_token()}", "Accept": "application/json"}


# =============================================================================
# 2. THE LANGCHAIN CORTEX WRAPPER
# =============================================================================
class CortexAgentChatModel(BaseChatModel):
    agent_name: str = Field(description="The exact name of the agent in the Cortex UI")

    _agent_config: Dict[str, Any] = {}
    _model_versions: List[Dict[str, Any]] = []

    temperature: float = 0.0
    max_tokens: int = 4096
    multimodal: bool = False

    def __init__(self, agent_name: str, **kwargs):
        super().__init__(agent_name=agent_name, **kwargs)
        self._fetch_and_apply_config()

    @property
    def _llm_type(self) -> str:
        return "cortex_agent_chat_model"

    @property
    def _auth_mode(self) -> str:
        if USE_AWS_AUTH:
            return "aws"
        if CORTEX_CLIENT_ID and CORTEX_CLIENT_SECRET:
            return "msal"
        if CORTEX_COOKIE:
            return "cookie"
        raise ValueError("No authentication configured! Set USE_AWS_AUTH, MSAL credentials, or CORTEX_COOKIE.")

    def _fetch_and_apply_config(self):
        url = f"{CORTEX_API_BASE.rstrip('/')}/model/{self.agent_name}"
        logger.info(f"Fetching agent config for: {self.agent_name} using Cookie...")
        headers = {"accept": "application/json", "cookie": CORTEX_COOKIE}
        response = httpx.get(url, headers=headers, timeout=15.0, follow_redirects=False)
        if response.status_code == 302:
            raise Exception("HTTP 302 Redirect: Your CORTEX_COOKIE is expired or missing. Please update it in your .env file.")
        response.raise_for_status()
        self._agent_config = response.json()
        self.temperature = self._agent_config.get("temperature", 0.0)
        self.max_tokens = self._agent_config.get("max_response_token_size", 40960)
        self.multimodal = self._agent_config.get("multimodal", False)
        self._model_versions = self._agent_config.get("model_versions", [])
        if not self._model_versions:
            raise ValueError(f"Agent '{self.agent_name}' has no model_versions configured!")

    def _build_client_for_version(self, version_config: Dict[str, Any]) -> BaseChatModel:
        top_p = self._agent_config.get("top_p", 0.95)
        model_kwargs = {}
        if version_config.get("enable_thinking"):
            model_kwargs["reasoning_effort"] = version_config.get("reasoning_effort", "medium")
            temp = 1.0
        else:
            temp = self.temperature
        model_class = (version_config.get("model_class") or "").lower()
        is_claude = "claude" in model_class or "anthropic" in model_class
        model_id = self.agent_name
        if USE_AWS_AUTH:
            from langchain_openai import ChatOpenAI
            client_kwargs = dict(
                model=model_id,
                base_url=CORTEX_OPENAI_BASE,
                default_headers=_get_aws_auth_headers(),
                api_key="aws_placeholder",
                temperature=temp,
                max_tokens=self.max_tokens,
                model_kwargs=model_kwargs,
            )
            if not is_claude:
                client_kwargs["top_p"] = top_p
            return ChatOpenAI(**client_kwargs)
        else:
            from langchain_openai import AzureChatOpenAI
            client_kwargs = dict(
                openai_api_version="2023-05-15",
                azure_endpoint=CORTEX_OPENAI_BASE,
                deployment_name=model_id,
                model=model_id,
                azure_ad_token_provider=_get_azure_ad_token,
                temperature=temp,
                max_tokens=self.max_tokens,
                model_kwargs=model_kwargs,
            )
            if not is_claude:
                client_kwargs["top_p"] = top_p
            return AzureChatOpenAI(**client_kwargs)

    @staticmethod
    def _extract_images_and_text(messages: List[BaseMessage]) -> tuple:
        text_parts = []
        images_b64 = []
        role_map = {"human": "User", "ai": "Assistant", "system": "System"}
        for msg in messages:
            role_prefix = role_map.get(msg.type, "")
            if isinstance(msg.content, str):
                text_parts.append(f"{role_prefix}: {msg.content}" if role_prefix else msg.content)
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, str):
                        text_parts.append(f"{role_prefix}: {block}" if role_prefix else block)
                    elif isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(f"{role_prefix}: {block['text']}" if role_prefix else block["text"])
                        elif block.get("type") == "image_url":
                            url_data = block.get("image_url", {})
                            url_str = url_data.get("url", "") if isinstance(url_data, dict) else str(url_data)
                            if url_str.startswith("data:"):
                                url_str = url_str.split(",", 1)[-1]
                            images_b64.append(url_str)
        return "\n\n".join(text_parts), images_b64

    @staticmethod
    def _build_schema_repr(schema_obj, definitions=None):
        if definitions is None:
            definitions = schema_obj.get("$defs", {})
        if schema_obj.get("type") == "object":
            result = {}
            for field, props in schema_obj.get("properties", {}).items():
                desc = props.get("description", "")
                field_type = props.get("type", "")
                if field_type == "array" and "items" in props:
                    items = props["items"]
                    if "$ref" in items:
                        ref_name = items["$ref"].split("/")[-1]
                        ref_schema = definitions.get(ref_name, {})
                        result[field] = [CortexAgentChatModel._build_schema_repr(ref_schema, definitions)]
                    elif items.get("type") == "object":
                        result[field] = [CortexAgentChatModel._build_schema_repr(items, definitions)]
                    else:
                        result[field] = [f"<{items.get('type', 'any')}> {items.get('description', '')}"]
                elif "$ref" in props:
                    ref_name = props["$ref"].split("/")[-1]
                    ref_schema = definitions.get(ref_name, {})
                    result[field] = CortexAgentChatModel._build_schema_repr(ref_schema, definitions)
                else:
                    result[field] = f"<{field_type}> {desc}" if desc else f"<{field_type}>"
            return result
        return schema_obj

    @staticmethod
    def _inject_tool_descriptions(combined_text: str, tools: list) -> str:
        tool_lines = []
        for tool_schema in tools:
            func = tool_schema.get("function", tool_schema)
            name = func.get("name", "unknown")
            desc = func.get("description", "")
            params = func.get("parameters", {}).get("properties", {})
            param_parts = [f"{pname}: {pinfo.get('type', 'any')}" + (f" ({pinfo.get('description', '')})" if pinfo.get("description") else "") for pname, pinfo in params.items()]
            tool_lines.append(f"  - {name}({', '.join(param_parts)}): {desc}")
        injection = (
            f"\n\nYou have access to the following tools:\n{chr(10).join(tool_lines)}\n\n"
            "If you need to call a tool, respond with ONLY this JSON:\n"
            '{"tool_calls": [{"name": "tool_name", "arguments": {"param1": "value1"}}]}\n\n'
            "If you can answer without tools, respond normally."
        )
        return combined_text + injection

    @staticmethod
    def _parse_tool_calls(raw_message: str) -> Optional[AIMessage]:
        text = raw_message.strip()
        try:
            parsed = json.loads(text, strict=False)
            if isinstance(parsed, dict) and "tool_calls" in parsed:
                return AIMessage(content="", tool_calls=[
                    {"id": f"call_{uuid.uuid4().hex[:8]}", "name": tc["name"], "args": tc.get("arguments", tc.get("args", {}))}
                    for tc in parsed["tool_calls"]
                ])
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(1), strict=False)
                if isinstance(parsed, dict) and "tool_calls" in parsed:
                    return AIMessage(content="", tool_calls=[
                        {"id": f"call_{uuid.uuid4().hex[:8]}", "name": tc["name"], "args": tc.get("arguments", tc.get("args", {}))}
                        for tc in parsed["tool_calls"]
                    ])
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        return None

    def _call_cookie_endpoint(self, combined_text: str, images_b64: list) -> str:
        url = f"{CORTEX_API_BASE.rstrip('/')}/model/ask/{self.agent_name}"
        params = {"stream": "false", "use_responses_api": "false"}
        headers = {"accept": "application/json", "cookie": CORTEX_COOKIE}
        data = {"q": combined_text}
        timeout = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=30.0)
        if images_b64:
            files = [("uploaded_files", (f"image{i+1}.jpg", base64.b64decode(b64), "image/jpeg")) for i, b64 in enumerate(images_b64)] if len(images_b64) > 1 else {"uploaded_file": ("image.jpg", base64.b64decode(images_b64[0]), "image/jpeg")}
        else:
            files = {"uploaded_file": (None, "")}
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.post(url, headers=headers, params=params, data=data, files=files)
        if response.status_code in (301, 302, 303, 307, 308):
            raise Exception("HTTP Redirect: Your CORTEX_COOKIE is expired. Please update it in your .env file.")
        if response.status_code in (500, 502, 503, 504, 429):
            raise Exception(f"API Error {response.status_code}: {response.text[:500]}")
        response.raise_for_status()
        return response.json().get("message", "").strip()

    async def _call_cookie_endpoint_async(self, combined_text: str, images_b64: list) -> str:
        url = f"{CORTEX_API_BASE.rstrip('/')}/model/ask/{self.agent_name}"
        params = {"stream": "false", "use_responses_api": "false"}
        headers = {"accept": "application/json", "cookie": CORTEX_COOKIE}
        data = {"q": combined_text}
        timeout = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=30.0)
        if images_b64:
            files = [("uploaded_files", (f"image{i+1}.jpg", base64.b64decode(b64), "image/jpeg")) for i, b64 in enumerate(images_b64)] if len(images_b64) > 1 else {"uploaded_file": ("image.jpg", base64.b64decode(images_b64[0]), "image/jpeg")}
        else:
            files = {"uploaded_file": (None, "")}
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.post(url, headers=headers, params=params, data=data, files=files)
        if response.status_code in (301, 302, 303, 307, 308):
            raise Exception("HTTP Redirect: Your CORTEX_COOKIE is expired. Please update it in your .env file.")
        if response.status_code in (500, 502, 503, 504, 429):
            raise Exception(f"API Error {response.status_code}: {response.text[:500]}")
        response.raise_for_status()
        return response.json().get("message", "").strip()

    def _generate_via_cookie(self, messages: List[BaseMessage], stop=None, **kwargs) -> ChatResult:
        combined_text, images_b64 = self._extract_images_and_text(messages)
        tools = kwargs.pop("tools", None)
        if tools:
            combined_text = self._inject_tool_descriptions(combined_text, tools)
        raw_message = self._call_cookie_endpoint(combined_text, images_b64)
        if tools and raw_message:
            tool_call_msg = self._parse_tool_calls(raw_message)
            if tool_call_msg:
                return ChatResult(generations=[ChatGeneration(message=tool_call_msg)])
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=raw_message))])

    async def _agenerate_via_cookie(self, messages: List[BaseMessage], stop=None, **kwargs) -> ChatResult:
        combined_text, images_b64 = self._extract_images_and_text(messages)
        tools = kwargs.pop("tools", None)
        if tools:
            combined_text = self._inject_tool_descriptions(combined_text, tools)
        raw_message = await self._call_cookie_endpoint_async(combined_text, images_b64)
        if tools and raw_message:
            tool_call_msg = self._parse_tool_calls(raw_message)
            if tool_call_msg:
                return ChatResult(generations=[ChatGeneration(message=tool_call_msg)])
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=raw_message))])

    def _check_multimodal(self, messages: List[BaseMessage]):
        if self.multimodal:
            return
        for msg in messages:
            if isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "image_url":
                        raise ValueError(f"Agent '{self.agent_name}' has multimodal=False but an image was provided.")

    def _generate(self, messages: List[BaseMessage], stop=None, **kwargs) -> ChatResult:
        self._check_multimodal(messages)
        errors = []
        for version in self._model_versions:
            try:
                if self._auth_mode == "cookie":
                    return self._generate_via_cookie(messages, stop=stop, **kwargs)
                return self._build_client_for_version(version)._generate(messages, stop=stop, **kwargs)
            except Exception as e:
                logger.warning(f"Model version {version.get('model_class')} failed: {e}. Trying next fallback...")
                errors.append(str(e))
        raise Exception(f"All model versions failed! Errors: {errors}")

    async def _agenerate(self, messages: List[BaseMessage], stop=None, **kwargs) -> ChatResult:
        self._check_multimodal(messages)
        errors = []
        for version in self._model_versions:
            try:
                if self._auth_mode == "cookie":
                    return await self._agenerate_via_cookie(messages, stop=stop, **kwargs)
                return await self._build_client_for_version(version)._agenerate(messages, stop=stop, **kwargs)
            except Exception as e:
                logger.warning(f"Model version {version.get('model_class')} failed: {e}. Trying next fallback...")
                errors.append(str(e))
        raise Exception(f"All model versions failed! Errors: {errors}")

    def _stream(self, messages: List[BaseMessage], stop=None, **kwargs) -> Iterator[ChatGenerationChunk]:
        if self._auth_mode == "cookie":
            result = self._generate_via_cookie(messages, stop=stop, **kwargs)
            yield ChatGenerationChunk(message=AIMessageChunk(content=result.generations[0].message.content))
            return
        yield from self._build_client_for_version(self._model_versions[0])._stream(messages, stop=stop, **kwargs)

    async def _astream(self, messages: List[BaseMessage], stop=None, **kwargs) -> AsyncIterator[ChatGenerationChunk]:
        if self._auth_mode == "cookie":
            result = await self._agenerate_via_cookie(messages, stop=stop, **kwargs)
            yield ChatGenerationChunk(message=AIMessageChunk(content=result.generations[0].message.content))
            return
        async for chunk in self._build_client_for_version(self._model_versions[0])._astream(messages, stop=stop, **kwargs):
            yield chunk

    def with_structured_output(self, schema: Any, **kwargs) -> Runnable:
        if self._auth_mode == "cookie":
            return self._build_cookie_structured_chain(schema)
        return self._build_client_for_version(self._model_versions[0]).with_structured_output(schema, **kwargs)

    def _build_cookie_structured_chain(self, schema: Any) -> Runnable:
        schema_dict = schema.model_json_schema()
        example_structure = CortexAgentChatModel._build_schema_repr(schema_dict)
        schema_str = json.dumps(example_structure, indent=2)
        schema_instructions = (
            "\n\n=========================================\n"
            "OUTPUT FORMAT INSTRUCTIONS:\n"
            "You must output ONLY a valid, raw JSON object.\n"
            "Do not include any text before or after the JSON.\n"
            "Do not wrap your response in ```json markdown blocks.\n"
            f"Your JSON must perfectly match this schema:\n\n{schema_str}\n"
            "=========================================\n"
        )
        llm_ref = self
        target_schema = schema

        def _invoke(input_val):
            from langchain_core.messages import HumanMessage as HM, SystemMessage as SM
            if isinstance(input_val, str):
                messages = [HM(content=input_val + schema_instructions)]
            elif isinstance(input_val, list):
                messages = list(input_val)
                if messages and hasattr(messages[-1], "content") and isinstance(messages[-1].content, str):
                    last = messages[-1]
                    messages[-1] = type(last)(content=last.content + schema_instructions)
                else:
                    messages.append(SM(content=schema_instructions))
            else:
                messages = [HM(content=str(input_val) + schema_instructions)]
            response = llm_ref.invoke(messages)
            raw_text = response.content.strip()
            match = re.search(r"^```(?:json)?\s*(.*?)\s*```$", raw_text, re.DOTALL | re.IGNORECASE)
            cleaned = match.group(1) if match else raw_text
            cleaned = cleaned.strip("` \n")
            parsed = json.loads(cleaned, strict=False)
            if "properties" in parsed and isinstance(parsed["properties"], dict):
                inner = parsed["properties"]
                parsed = {k: v["value"] if isinstance(v, dict) and "value" in v else v for k, v in inner.items()}
            return target_schema.model_validate(parsed)

        return RunnableLambda(_invoke)

    def bind_tools(self, tools: Any, **kwargs) -> Runnable:
        if self._auth_mode == "cookie":
            from langchain_core.utils.function_calling import convert_to_openai_tool
            return self.bind(tools=[convert_to_openai_tool(t) for t in tools])
        client = self._build_client_for_version(self._model_versions[0])
        bound_client = client.bind_tools(tools, **kwargs)
        return self.bind(**bound_client.kwargs)

    def get_profile(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "primary_model": self._model_versions[0].get("model_class") if self._model_versions else "None",
            "fallbacks_available": len(self._model_versions) - 1,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "multimodal": self.multimodal,
            "auth_mode": self._auth_mode,
        }
