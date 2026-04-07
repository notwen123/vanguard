from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Auth — set AUTH_MODE=local to skip Auth0 entirely (free demo mode)
    AUTH_MODE: str = "local"  # "local" | "auth0"
    AUTH0_DOMAIN: str = "your-tenant.auth0.com"
    AUTH0_CLIENT_ID: str = ""
    AUTH0_CLIENT_SECRET: str = ""
    AUTH0_AUDIENCE: str = "vanguard-api"

    # Vault encryption key — generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    VAULT_ENCRYPTION_KEY: str = ""

    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"

    # App
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    DATABASE_URL: str = "sqlite+aiosqlite:///./vanguard.db"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
