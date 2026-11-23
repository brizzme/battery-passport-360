import psycopg
from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    pghost: str = "localhost"
    pgdatabase: str = "passport"
    pguser: str = "passport"
    pgpassword: SecretStr = SecretStr("local-demo")


def connect() -> psycopg.Connection:
    settings = Settings()
    return psycopg.connect(
        host=settings.pghost, dbname=settings.pgdatabase, user=settings.pguser,
        password=settings.pgpassword.get_secret_value(), connect_timeout=2,
        options="-c statement_timeout=2000",
    )
