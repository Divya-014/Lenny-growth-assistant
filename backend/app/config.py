import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and optional .env file.
    Uses Pydantic v2 BaseSettings.
    """
    APP_NAME: str = Field(default="Lenny Growth Assistant")
    APP_ENV: str = Field(default="local")
    DEBUG: bool = Field(default=True)
    PORT: int = Field(default=8000)
    HOST: str = Field(default="0.0.0.0")

    # Supabase / Database Settings
    SUPABASE_URL: str = Field(default="https://your-project-id.supabase.co")
    SUPABASE_KEY: str = Field(default="your-supabase-anon-key")

    # LLM Settings
    OPENAI_API_KEY: str = Field(default="")
    ANTHROPIC_API_KEY: str = Field(default="")
    OLLAMA_HOST: str = Field(default="http://localhost:11434")

    # Vector Database Settings
    CHROMADB_PATH: str = Field(default="./data/chromadb")
    MAX_TRANSCRIPTS: int | None = Field(default=50)



    # Configure Pydantic Settings to load from environment and .env file
    # We resolve the path to backend/.env
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings
settings = Settings()
