from collections.abc import Sequence, Iterable

from src.contracts.task import Task
from src.contracts.task_source import TaskSource


class TaskProcessor:
    """Обработчик задач из различных источников."""
    def __init__(self, sources: Sequence[TaskSource] = None):
        """Инициализация процессора задач."""
        self._sources = sources or []

    def iter_task(self) -> Iterable[Task]:
        """Итерироваться по задачам из всех источников."""
        for src in self._sources:
            if not isinstance(src, TaskSource):
                raise TypeError("Source object must be TaskSource")
            for message in src.fetch():
                yield message
