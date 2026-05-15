import asyncio
import logging
import uuid

from app.infrastructure.celery_app import celery_app
from app.repositories.storage.postgres.db_helper import db_helper
from app.repositories.storage.postgres.repositories import repository


logger = logging.getLogger(__name__)


@celery_app.task(name="analytics.recalculate_device_analytics")
def recalculate_device_analytics(device_id: str) -> None:
    asyncio.run(_recalculate_device_analytics(uuid.UUID(device_id)))


async def _recalculate_device_analytics(device_id: uuid.UUID) -> None:
    async with db_helper.transaction() as session:
        analytics = await repository.get_device_analytics(device_id, None, None, session)
        await repository.upsert_device_analytics_cache(device_id, analytics, session)
        logger.info(
            "Recalculate device analytics device_id=%s count=%s",
            device_id,
            analytics["x_count"],
        )
