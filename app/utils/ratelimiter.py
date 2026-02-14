import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimits:
    global_per_sec: int = 30
    per_user_per_sec: int = 1
    per_chat_per_min: int = 20


class RateLimiter:
    def __init__(self, limits: RateLimits) -> None:
        self.limits = limits
        self._global_times = deque()
        self._per_user_times: dict[int, deque] = {}
        self._per_chat_times: dict[int, deque] = {}
        self._lock = asyncio.Lock()
        self._sent_count = 0
        self._last_report = time.monotonic()

    async def acquire(self, chat_id: int, user_id: int | None = None) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                self._cleanup(now)

                if len(self._global_times) >= self.limits.global_per_sec:
                    wait = 1 - (now - self._global_times[0])
                    logger.debug("Global rate limit hit, wait %.3fs", wait)
                elif user_id is not None and len(self._per_user_times.get(user_id, deque())) >= self.limits.per_user_per_sec:
                    wait = 1 - (now - self._per_user_times[user_id][0])
                    logger.debug("User rate limit hit for %s, wait %.3fs", user_id, wait)
                elif len(self._per_chat_times.get(chat_id, deque())) >= self.limits.per_chat_per_min:
                    wait = 60 - (now - self._per_chat_times[chat_id][0])
                    logger.debug("Chat rate limit hit for %s, wait %.3fs", chat_id, wait)
                else:
                    self._mark(now, chat_id, user_id)
                    return

            if wait < 0:
                wait = 0.05
            await asyncio.sleep(wait)

    def _mark(self, now: float, chat_id: int, user_id: int | None) -> None:
        self._global_times.append(now)
        if user_id is not None:
            self._per_user_times.setdefault(user_id, deque()).append(now)
        self._per_chat_times.setdefault(chat_id, deque()).append(now)
        self._sent_count += 1
        self._report_if_needed(now)

    def _cleanup(self, now: float) -> None:
        while self._global_times and now - self._global_times[0] >= 1:
            self._global_times.popleft()
        for dq in list(self._per_user_times.values()):
            while dq and now - dq[0] >= 1:
                dq.popleft()
        for dq in list(self._per_chat_times.values()):
            while dq and now - dq[0] >= 60:
                dq.popleft()

    def _report_if_needed(self, now: float) -> None:
        if now - self._last_report >= 60:
            rate = self._sent_count / (now - self._last_report)
            logger.info("Average send rate: %.2f msg/sec", rate)
            self._sent_count = 0
            self._last_report = now
