import asyncio
import sys

import asyncpg

from app.config.config import settings


async def _check_db() -> None:
    dsn = settings.database_url.replace("postgresql+asyncpg", "postgresql")
    conn = await asyncpg.connect(dsn, timeout=5)
    try:
        await conn.execute("SELECT 1")
    finally:
        await conn.close()


def main() -> None:
    try:
        asyncio.run(_check_db())
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
