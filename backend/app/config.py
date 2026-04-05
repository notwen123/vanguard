from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Auth0
    AUTH0_DOMAIN: str
    AUTH0_CLIENT_ID: str
    AUTH0_CLIENT_SECRET: str
    AUTH0_AUDIENCE: str
    AUTH0_TOKEN_VAULT_BASE_URL: str = ""

    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # App
    SECRET_KEY: str = "change-me-in-production"
    DATABASE_URL: str = "sqlite+aiosqlite:///./vanguard.db"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
