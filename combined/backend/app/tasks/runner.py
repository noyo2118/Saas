"""Background task runner — lightweight asyncio task manager.

Production deployments should replace this with ARQ or Celery by
reimplementing ``enqueue`` and ``run_worker``. Callers don't change.
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from app.telemetry.logger import get_logger

log = get_logger(__name__)


class TaskRunner:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[tuple[str, Callable[..., Awaitable[Any]], tuple, dict]] = asyncio.Queue()
        self._worker: asyncio.Task | None = None

    async def start(self) -> None:
        if self._worker and not self._worker.done():
            return
        self._worker = asyncio.create_task(self._run())
        log.info("task_runner_started")

    async def stop(self) -> None:
        if self._worker:
            self._worker.cancel()
            self._worker = None

    async def enqueue(self, name: str, fn: Callable[..., Awaitable[Any]], *args, **kwargs) -> None:
        await self._queue.put((name, fn, args, kwargs))

    async def _run(self) -> None:
        while True:
            name, fn, args, kwargs = await self._queue.get()
            try:
                await fn(*args, **kwargs)
                log.info("task_done", extra={"task": name})
            except Exception as exc:  # noqa: BLE001
                log.exception("task_failed", extra={"task": name, "err": str(exc)[:200]})
            finally:
                self._queue.task_done()


runner = TaskRunner()
