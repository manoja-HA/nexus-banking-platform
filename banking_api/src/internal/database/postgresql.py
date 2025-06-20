import logging
import urllib.parse
from collections.abc import Generator

from internal.configs.postgresql import PostgresqlConfig, load_postgresql_config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def get_engine(
    config: PostgresqlConfig,
):
    scheme: str = "postgresql+pg8000"
    password_encoded: str = urllib.parse.quote_plus(config.password)
    url: str = f"{scheme}://{config.user}:{password_encoded}@{config.host}:{config.port}/{config.database}"
    logging.info(f"Connecting to {scheme}://{config.user}:*****@{config.host}:{config.port}/{config.database}")
    return create_engine(url, echo=config.echo)


session_factory: sessionmaker = sessionmaker(  # type: ignore
    bind=get_engine(load_postgresql_config()), autoflush=True, autocommit=False
)


def get_session() -> Generator[Session, None, None]:
    session: Session = session_factory()
    try:
        yield session
    except:
        session.rollback()
        raise
    finally:
        session.close()
