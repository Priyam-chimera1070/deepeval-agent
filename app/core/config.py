from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Cortex agent / gateway
    cortex_agent_name: str = "CORTEX_AGENT_NAME"
    cortex_openai_base: str = "https://gateway.apim.lilly.com/cortex/cortex-openai"
    cortex_api_version: str = "2023-05-15"
    cortex_temperature: float = 0.0
    cortex_max_tokens: int = 4096

    # How to call the chat-completions endpoint.
    # `cortex_endpoint_template` is appended to cortex_openai_base.
    #   {agent} is substituted with cortex_agent_name.
    # `cortex_agent_in_body` (true/false): also include {"model_config_name": "<agent>"} in the JSON body.
    # `cortex_send_api_version` (true/false): append ?api-version=... query param.
    cortex_endpoint_template: str = "chat/completions"
    cortex_agent_in_body: bool = True
    cortex_agent_body_field: str = "model_config_name"
    cortex_agent_in_header: bool = False
    cortex_agent_header_name: str = "model_config_name"
    cortex_send_api_version: bool = False

    # APIM OAuth2 client-credentials auth (replaces cookie / MSAL / AWS)
    apim_tenant_id: str = ""
    apim_client_id: str = ""
    apim_client_secret: str = ""
    apim_scope: str = ""
    apim_token_url: str = ""  # optional override; defaults to MS v2 endpoint

    # Evaluation thresholds (0–1 scale)
    pass_threshold: float = 0.85
    warn_threshold: float = 0.70

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
