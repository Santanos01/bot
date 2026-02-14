from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.db.session import AsyncSessionLocal
from app.models.user import User


async def upsert_user(user_id: int, username: str | None) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.username = username
            await session.commit()
            return
        session.add(
            User(
                user_id=user_id,
                username=username,
                started_at=datetime.now(timezone.utc),
                can_dm=True,
            )
        )
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()


async def mark_user_cant_dm(user_id: int) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(update(User).where(User.user_id == user_id).values(can_dm=False))
        await session.commit()
