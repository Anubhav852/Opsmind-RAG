from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql://opsmind:opsmind@localhost:5432/opsmind"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap: str = "localhost:19092"
    kafka_topic: str = "events.raw"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen2.5:7b-instruct"
    llm_model_cheap: str = "qwen2.5:3b-instruct"
    embed_model: str = "BAAI/bge-small-en-v1.5"
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    jwt_secret: str = "change-me"
    demo_mode: bool = True
    rate_limit_per_min: int = 30
    otlp_endpoint: str = "http://localhost:4317"


settings = Settings()
