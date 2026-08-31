from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://classified:classified@localhost:5432/classified"
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_ttl_minutes: int = 30
    refresh_ttl_days: int = 14
    cors_origins: str = "http://localhost:9000"


settings = Settings()
