from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = ""  # OpenRouter 사용 시 https://openrouter.ai/api/v1
    # 무료 우선 → 전부 실패 시 최저가 유료로 폴백 (콤마구분 체인)
    text_model: str = ("qwen/qwen3.8-27b:free,google/gemma-4-26b-a4b-it:free,"
                       "google/gemma-4-31b-it:free,deepseek/deepseek-chat")
    vision_model: str = ("qwen/qwen3.8-27b:free,google/gemma-4-26b-a4b-it:free,"
                         "thinkingmachines/inkling:free,openai/gpt-4o-mini")
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
