from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    @field_validator("postgres_url", mode="before")
    @classmethod
    def postgres_url_validator(cls, v: str) -> str:
        strs = ["postgres://", "postgresql://"]
        replacement = "postgresql+asyncpg://"
        for s in strs:
            v = v.replace(s, replacement)
        return v

    postgres_url: str

    secret_key: str

    redis_url: str

    mail_server: str
    mail_port: int

    email_user: Optional[str] = None
    email_password: Optional[str] = None
    email_from: str

    test_postgres_url: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
