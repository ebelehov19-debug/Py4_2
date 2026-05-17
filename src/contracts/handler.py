"""Контракт обработчика задач."""
from typing import Protocol, runtime_checkable

from src.contracts.task import Task


@runtime_checkable
class TaskHandler(Protocol):
    """
    Поведенческий контракт для всех обработчиков задач.

    Обработчик — компонент, выполняющий прикладную логику над задачей.
    Он не обязан наследоваться от общего базового класса; достаточно
    реализовать метод handle(task) с нужной сигнатурой.
    """

    name: str

    async def handle(self, task: Task) -> None:
        """
        Обработать задачу.

        Raises:
            Exception: любое исключение, возникшее при обработке;
                       исполнитель перехватит его и залогирует.
        """
        ...
