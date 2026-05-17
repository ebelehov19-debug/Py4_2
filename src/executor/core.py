"""Асинхронный исполнитель задач."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from types import TracebackType
from typing import Optional, Type

from src.contracts.handler import TaskHandler
from src.contracts.task import Task
from src.inbox.task_queue import TaskQueue

logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    Асинхронный исполнитель задач.

    Поддерживает использование в качестве контекстного менеджера (async with),
    что обеспечивает корректную инициализацию и освобождение ресурсов.

    Пример использования::

        async with TaskExecutor(handlers=[MyHandler()]) as executor:
            await executor.run(queue)
    """

    def __init__(
        self,
        handlers: Sequence[TaskHandler],
        *,
        concurrency: int = 4,
    ) -> None:
        """
        Args:
            handlers:    список обработчиков; каждый должен реализовывать TaskHandler.
            concurrency: максимальное число задач, обрабатываемых параллельно.
        """
        if not handlers:
            raise ValueError("Необходимо передать хотя бы один обработчик.")
        for h in handlers:
            if not isinstance(h, TaskHandler):
                raise TypeError(
                    f"Объект {h!r} не реализует контракт TaskHandler."
                )
        self._handlers = list(handlers)
        self._concurrency = concurrency
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._stats: dict[str, int] = {"processed": 0, "failed": 0, "skipped": 0}

    async def __aenter__(self) -> "TaskExecutor":
        """Инициализация ресурсов исполнителя."""
        self._semaphore = asyncio.Semaphore(self._concurrency)
        self._stats = {"processed": 0, "failed": 0, "skipped": 0}
        handler_names = ", ".join(h.name for h in self._handlers)
        logger.info(
            "TaskExecutor запущен. Обработчики: [%s]. Параллелизм: %d.",
            handler_names,
            self._concurrency,
        )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        """Освобождение ресурсов и вывод итоговой статистики."""
        logger.info(
            "TaskExecutor завершён. Статистика: обработано=%d, ошибок=%d, пропущено=%d.",
            self._stats["processed"],
            self._stats["failed"],
            self._stats["skipped"],
        )
        self._semaphore = None
        return False

    @property
    def stats(self) -> dict[str, int]:
        """Текущая статистика выполнения (копия)."""
        return dict(self._stats)

    async def run(self, queue: TaskQueue) -> None:
        """
        Обработать все задачи из очереди параллельно (с ограничением по semaphore).

        Args:
            queue: очередь задач для обработки.

        Raises:
            RuntimeError: если исполнитель используется без контекстного менеджера.
        """
        if self._semaphore is None:
            raise RuntimeError(
                "TaskExecutor должен использоваться как контекстный менеджер: "
                "`async with TaskExecutor(...) as executor:`"
            )
        tasks_to_run = [
            self._process_task(task)
            for task in queue
            if task.is_ready_to_execute
        ]

        skipped = len(queue) - len(tasks_to_run)
        self._stats["skipped"] += skipped
        if skipped:
            logger.debug("Пропущено %d задач (не готовы к выполнению).", skipped)

        await asyncio.gather(*tasks_to_run, return_exceptions=False)

    async def run_one(self, task: Task) -> None:
        """Обработать одну задачу всеми обработчиками последовательно."""
        if self._semaphore is None:
            raise RuntimeError(
                "TaskExecutor должен использоваться как контекстный менеджер."
            )
        await self._process_task(task)

    async def _process_task(self, task: Task) -> None:
        """Обработать задачу всеми обработчиками с учётом semaphore."""
        assert self._semaphore is not None
        async with self._semaphore:
            logger.debug("Начало обработки задачи [%s].", task.id)
            task.status = "in_progress"
            try:
                for handler in self._handlers:
                    await self._invoke_handler(handler, task)
                task.status = "completed"
                self._stats["processed"] += 1
                logger.info("Задача [%s] успешно обработана.", task.id)
            except Exception as exc:
                task.status = "failed"
                self._stats["failed"] += 1
                logger.error(
                    "Задача [%s] завершилась с ошибкой: %s: %s",
                    task.id,
                    type(exc).__name__,
                    exc,
                )

    async def _invoke_handler(self, handler: TaskHandler, task: Task) -> None:
        """Вызвать один обработчик и залогировать исключение при необходимости."""
        try:
            await handler.handle(task)
        except Exception:
            logger.exception(
                "Обработчик '%s' бросил исключение для задачи [%s].",
                handler.name,
                task.id,
            )
            raise
