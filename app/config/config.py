import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _parse_admins(value: str | None) -> set[int]:
    if not value:
        return set()
    result: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.add(int(part))
        except ValueError:
            continue
    return result


def _build_database_url() -> str:
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit

    if any(
        os.getenv(key)
        for key in (
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "DB_HOST",
            "DB_PORT",
        )
    ):
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        host = os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "db"))
        port = os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5432"))
        db = os.getenv("POSTGRES_DB", "giveaway")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    return ""


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    admins: set[int]


settings = Settings(
    bot_token=os.getenv("BOT_TOKEN", ""),
    database_url=_build_database_url(),
    admins=_parse_admins(os.getenv("ADMINS")),
)

if not settings.bot_token:
    raise RuntimeError("BOT_TOKEN is not set")

if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not set")
