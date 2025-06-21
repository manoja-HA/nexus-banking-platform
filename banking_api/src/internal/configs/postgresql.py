from pydantic import Field
from pydantic_settings import BaseSettings


class PostgresqlConfig(BaseSettings):
    host: str = Field("postgresql", alias="POSTGRES_HOST")
    port: str = Field("5432", alias="POSTGRES_PORT")
    database: str = Field("banking_system", alias="POSTGRES_DB")
    user: str = Field("admin", alias="POSTGRES_USER")
    password: str = Field("adminAdmin123!", alias="POSTGRES_PASSWORD")
    echo: bool = Field(True, alias="POSTGRES_ECHO")


def load_postgresql_config() -> PostgresqlConfig:
    return PostgresqlConfig.model_construct(**PostgresqlConfig().model_dump())
