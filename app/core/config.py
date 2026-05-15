from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    database_url: str = Field(
        "postgresql+asyncpg://postgres:postgres@db:5432/postgres",
        validation_alias="DATABASE_URL",
    )
    celery_broker_url: str = Field(
        "amqp://guest:guest@rabbitmq:5672//",
        validation_alias="CELERY_BROKER_URL",
    )
    celery_task_always_eager: bool = Field(
        False,
        validation_alias="CELERY_TASK_ALWAYS_EAGER",
    )
    log_level: str = "INFO"


settings = Settings()
