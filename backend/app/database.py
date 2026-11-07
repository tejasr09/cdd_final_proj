import os
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class DatabaseConfigurationError(RuntimeError):
    pass


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str) -> Engine:
    engine = create_engine(database_url, pool_pre_ping=True)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(
            connection: DBAPIConnection, _connection_record: object
        ) -> None:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise DatabaseConfigurationError("DATABASE_URL must be configured before database access.")
    return make_engine(database_url)


def get_session() -> Iterator[Session]:
    factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    with factory() as session:
        yield session


def database_is_ready() -> bool:
    import logging

    from sqlalchemy.exc import SQLAlchemyError

    logger = logging.getLogger(__name__)
    try:
        with get_engine().connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except DatabaseConfigurationError as error:
        logger.warning("Database readiness check unavailable: %s", error)
        return False
    except SQLAlchemyError:
        logger.exception("Database readiness check failed.")
        return False
    return True
