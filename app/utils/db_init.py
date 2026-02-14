import asyncio
import logging

import asyncpg
from sqlalchemy.engine import make_url

from app.config.config import settings

logger = logging.getLogger(__name__)


def _safe_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


async def _ensure_db() -> None:
    dsn = settings.database_url.replace("postgresql+asyncpg", "postgresql")
    url = make_url(dsn)
    target_db = url.database or "giveaway"

    try:
        conn = await asyncpg.connect(dsn)
        await conn.close()
        logger.info("Database %s is reachable", target_db)
        return
    except asyncpg.InvalidCatalogNameError:
        logger.info("Database %s not found, attempting to create", target_db)
    except Exception as exc:
        logger.error("Failed to connect to database %s: %s", target_db, exc)
        raise

    if target_db == "postgres":
        logger.info("Target database is postgres; nothing to create")
        return

    admin_url = url.set(database="postgres")
    conn = await asyncpg.connect(str(admin_url))
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", target_db)
        if not exists:
            await conn.execute(f"CREATE DATABASE {_safe_ident(target_db)}")
            logger.info("Database %s created", target_db)
        else:
            logger.info("Database %s already exists", target_db)
    finally:
        await conn.close()


def main() -> None:
    asyncio.run(_ensure_db())


if __name__ == "__main__":
    main()
