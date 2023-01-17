import os

from pydantic import BaseSettings, Field

base_dir = os.path.dirname(os.path.abspath(__file__))


class Settings(BaseSettings):
    auth_db_username: str = Field(env="POSTGRES_USER")
    auth_db_password: str = Field(env="POSTGRES_PASSWORD")
    auth_db_name: str = Field(env="POSTGRES_DB")
    auth_db_host: str = Field(env="DB_HOST")

    base_api_url: str = Field(default="/api/v1/auth")

    jwt_secret_key: str = ...
    access_token_expires_in_seconds: int = Field(default=3600)
    refresh_token_expires_in_days: int = Field(default=30)

    class Config:
        env_file = f"{base_dir}/.env"


settings = Settings()