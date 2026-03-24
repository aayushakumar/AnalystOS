from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    analyst_primary_model: str = "groq/llama-3.3-70b-versatile"
    analyst_cheap_model: str = "groq/llama-3.1-8b-instant"

    # Database
    duckdb_path: str = "data/analystos.duckdb"

    # Tracing
    trace_db_path: str = "data/traces.db"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    allowed_origins: str = ""

    @property
    def duckdb_abs_path(self) -> Path:
        return Path(__file__).parent.parent / self.duckdb_path

    @property
    def trace_db_abs_path(self) -> Path:
        return Path(__file__).parent.parent / self.trace_db_path


settings = Settings()
