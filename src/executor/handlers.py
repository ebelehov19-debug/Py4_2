"""Конкретные реализации обработчиков задач."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable, Awaitable

from src.contracts.task import Task

logger = logging.getLogger(__name__)


@dataclass
class LoggingHandler:
    """
    Обработчик-логгер: записывает информацию о задаче в журнал.

    Реализует контракт TaskHandler без явного наследования.
    """

    name: str = "logging-handler"
    level: int = logging.INFO

    async def handle(self, task: Task) -> None:
        """Записать задачу в лог."""
        logger.log(
            self.level,
            "[%s] payload=%r  priority=%s",
            task.id,
            task.payload,
            task.priority,
        )


@dataclass
class PrintHandler:
    """
    Обработчик вывода: печатает задачу в stdout.

    Полезен для отладки и демонстрации.
    """

    name: str = "print-handler"
    template: str = "[{id}] {payload}"

    async def handle(self, task: Task) -> None:
        """Вывести задачу на экран."""
        print(self.template.format(id=task.id, payload=task.payload))


@dataclass
class DelayHandler:
    """
    Обработчик с задержкой: имитирует асинхронную I/O-операцию.

    Используется в тестах для проверки параллелизма.
    """

    name: str = "delay-handler"
    delay: float = 0.01

    async def handle(self, task: Task) -> None:
        """Выдержать паузу (имитация сетевого запроса или I/O)."""
        await asyncio.sleep(self.delay)
        logger.debug("DelayHandler: задача [%s] обработана после %.3f с.", task.id, self.delay)


@dataclass
class CallbackHandler:
    """
    Обработчик с произвольным асинхронным колбэком.

    Позволяет внедрить любую логику без создания нового класса::

        async def my_logic(task: Task) -> None:
            ...

        handler = CallbackHandler(callback=my_logic)
    """

    callback: Callable[[Task], Awaitable[None]]
    name: str = "callback-handler"

    async def handle(self, task: Task) -> None:
        """Вызвать переданный колбэк."""
        await self.callback(task)


@dataclass
class FailingHandler:
    """
    Обработчик, намеренно бросающий исключение.

    Используется в тестах для проверки обработки ошибок в исполнителе.
    """

    name: str = "failing-handler"
    error_message: str = "Simulated handler failure"

    async def handle(self, task: Task) -> None:
        raise RuntimeError(self.error_message)
