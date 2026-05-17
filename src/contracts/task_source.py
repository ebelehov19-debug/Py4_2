from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from src.contracts.task import Task


@runtime_checkable
class TaskSource(Protocol):
    """Поведенческий контракт для всех источников задач."""
    name: str

    def fetch(self) -> Iterable[Task]: 
        """Получить итератор задач из источника."""
        pass
