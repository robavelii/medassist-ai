import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, orm
from sqlalchemy.orm import Session

from src.core.config import configs
from src.models.llm_cache_model import LLMCache

# Configure SQLAlchemy logging based on configuration
if configs.SQLALCHEMY_LOGGING:
    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)


class Database:
    def __init__(self, db_url: str) -> None:
        self._engine = create_engine(
            db_url,
            echo=configs.SQLALCHEMY_LOGGING,
            echo_pool=configs.SQLALCHEMY_LOGGING,
            pool_pre_ping=True,
            pool_recycle=3600,
            query_cache_size=0,
        )
        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            ),
        )

    def create_database(self) -> None:
        LLMCache.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_db(self) -> Generator[Session, None, None]:
        """FastAPI-compatible dependency injection."""
        session: Session = self._session_factory()
        try:
            yield session
        finally:
            session.close()


db = Database(configs.DATABASE_URI)
