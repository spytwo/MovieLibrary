from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    valid_code: str

    cdn: str

    telegram_bot_token: str
    api_base_url: str

    email: str
    email_app_password: str
    receiver_emails: str

    secret_key: str
    access_token_expire_minutes: int
    algorithm: str

    db_pool_size: int
    db_max_overflow: int

    redis_url: str

    @property
    def sqlalchemy_url(self) -> str:
        return f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    model_config = ConfigDict(env_file=".env")


settings = Settings()
