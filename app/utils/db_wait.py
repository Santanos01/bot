import asyncio
import logging

import asyncpg

from app.config.config import settings

logger = logging.getLogger(__name__)


async def _wait_db(retries: int = 60, delay: float = 2.0) -> None:
    for i in range(retries):
        try:
            conn = await asyncpg.connect(settings.database_url.replace("postgresql+asyncpg", "postgresql"))
            await conn.close()
            logger.info("Database is ready")
            return
        except Exception as e:
            logger.warning("DB not ready yet (%s/%s): %s", i + 1, retries, e)
            await asyncio.sleep(delay)
    raise RuntimeError("Database not available after retries")


def main() -> None:
    asyncio.run(_wait_db())


if __name__ == "__main__":
    main()
