from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = ""  # OpenRouter 사용 시 https://openrouter.ai/api/v1
    text_model: str = "gpt-4o-mini"
    vision_model: str = "gpt-4o-mini"
    database_url: str = "sqlite:///./pennywise.db"
    upload_dir: str = "./data/uploads"
    cors_origins: str = "http://localhost:5173"
    batch_size: int = 20

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
