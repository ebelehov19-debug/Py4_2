"""Очередь задач с собственным итератором и ленивой фильтрацией."""
from collections.abc import Iterable, Iterator
from typing import Callable, Optional

from src.contracts.task import Task


class TaskQueue:
    """Очередь задач с поддержкой многократной итерации и ленивой фильтрации."""

    class _TaskIterator(Iterator[Task]):
        """Внутренний итератор, реализующий протокол с __next__ и StopIteration."""

        def __init__(self, tasks: list[Task]) -> None:
            self._tasks = tasks
            self._index = 0

        def __next__(self) -> Task:
            """Возвращает следующий элемент или бросает StopIteration."""
            if self._index >= len(self._tasks):
                raise StopIteration
            task = self._tasks[self._index]
            self._index += 1
            return task

        def __iter__(self) -> Iterator[Task]:
            return self

    def __init__(self, tasks: Optional[Iterable[Task]] = None) -> None:
        """Инициализирует очередь задач."""
        self._tasks: list[Task] = list(tasks) if tasks is not None else []

    def add(self, task: Task) -> None:
        """Добавляет задачу в очередь."""
        self._tasks.append(task)

    def add_all(self, tasks: Iterable[Task]) -> None:
        """Добавляет несколько задач в очередь."""
        for task in tasks:
            self._tasks.append(task)

    def __len__(self) -> int:
        """Возвращает количество задач в очереди."""
        return len(self._tasks)

    def __contains__(self, task: Task) -> bool:
        """Проверяет, содержится ли задача в очереди."""
        return task in self._tasks

    def __iter__(self) -> Iterator[Task]:
        """Возвращает новый итератор (позволяет повторный обход)."""
        return self._TaskIterator(self._tasks)

    def iter_filtered(self,*,status: Optional[str] = None,
        priority: Optional[str] = None,
        predicate: Optional[Callable[[Task], bool]] = None,
    ) -> Iterator[Task]:
        """Возвращает генератор задач, отфильтрованных по статусу, приоритету или предикату."""
        for task in self._tasks:
            if status is not None and task.status != status:
                continue
            if priority is not None and task.priority != priority:
                continue
            if predicate is not None and not predicate(task):
                continue
            yield task

    def pending_tasks(self) -> Iterator[Task]:
        """Возвращает генератор задач со статусом 'pending'."""
        return self.iter_filtered(status="pending")

    def in_progress_tasks(self) -> Iterator[Task]:
        """Возвращает генератор задач со статусом 'in_progress'."""
        return self.iter_filtered(status="in_progress")

    def completed_tasks(self) -> Iterator[Task]:
        """Возвращает генератор задач со статусом 'completed'."""
        return self.iter_filtered(status="completed")

    def high_priority_tasks(self) -> Iterator[Task]:
        """Возвращает генератор задач с приоритетом 'high'."""
        return self.iter_filtered(priority="high")

    def critical_priority_tasks(self) -> Iterator[Task]:
        """Возвращает генератор задач с приоритетом 'critical'."""
        return self.iter_filtered(priority="critical")

    def ready_to_execute(self) -> Iterator[Task]:
        """Возвращает генератор задач, готовых к выполнению."""
        return self.iter_filtered(predicate=lambda t: t.is_ready_to_execute)

    def first(self, predicate: Optional[Callable[[Task], bool]] = None) -> Optional[Task]:
        """Возвращает первую задачу, удовлетворяющую предикату."""
        if predicate is None:
            return self._tasks[0] if self._tasks else None
        for task in self._tasks:
            if predicate(task):
                return task
        return None

    def __repr__(self) -> str:
        return f"TaskQueue(tasks={len(self._tasks)})"