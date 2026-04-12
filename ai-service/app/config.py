"""Application configuration loaded from environment variables."""

import os


class Settings:
    # Ollama (local)
    OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    EMBED_MODEL: str = os.environ.get("EMBED_MODEL", "nomic-embed-text")
    LLM_MODEL: str = os.environ.get("LLM_MODEL", "llama3.1:8b")

    # Provider toggle
    EMBEDDING_PROVIDER: str = os.environ.get("EMBEDDING_PROVIDER", "ollama")
    LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "ollama")

    # Azure OpenAI (production)
    AZURE_OPENAI_ENDPOINT: str = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.environ.get("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")

    # Qdrant
    QDRANT_URL: str = os.environ.get("QDRANT_URL", "http://localhost:6333")

    # PostgreSQL
    POSTGRES_HOST: str = os.environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.environ.get("POSTGRES_PORT", "5436")
    POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "groceryshop")
    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "grocery")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "changeme")

    # Redis
    REDIS_HOST: str = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.environ.get("REDIS_PORT", "6380"))

    # App
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

    @property
    def postgres_dsn(self) -> str:
        return f"host={self.POSTGRES_HOST} port={self.POSTGRES_PORT} dbname={self.POSTGRES_DB} user={self.POSTGRES_USER} password={self.POSTGRES_PASSWORD}"


settings = Settings()
