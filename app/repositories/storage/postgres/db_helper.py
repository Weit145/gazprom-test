from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
import logging


logger = logging.getLogger(__name__)


class DatabaseHellper:
    def __init__(self, url: str, echo: bool = False):
        self.engine = create_async_engine(url=url, echo=echo)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def transaction(self):
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Falid transaction error:{e}")
                raise e


db_helper = DatabaseHellper(url=settings.database_url)
