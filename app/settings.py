from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_port: int
    postgres_url: str

    secret_key: str

    redis_url: str

    mail_server: str
    mail_port: int

    email_user: Optional[str] = None
    email_password: Optional[str] = None
    email_from: str

    postgres_test_db: str
    test_postgres_url: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
