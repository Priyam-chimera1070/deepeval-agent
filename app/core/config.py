from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    cortex_agent_name: str = "CORTEX_AGENT_NAME"
    cortex_cookie: str = ""
    cortex_api_base: str = "https://cortex.lilly.com"
    cortex_openai_base: str = "https://gateway.apim.lilly.com/cortex/cortex-openai"
    use_aws_auth: bool = False

    pass_threshold: float = 0.85
    warn_threshold: float = 0.70

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
