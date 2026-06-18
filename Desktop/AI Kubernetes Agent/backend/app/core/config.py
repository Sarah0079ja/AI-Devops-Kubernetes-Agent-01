from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_model: str = ""
    kubeconfig_path: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
