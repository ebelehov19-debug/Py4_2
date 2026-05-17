from datetime import datetime
from typing import Any,Optional

from src.contracts.descriptors import StringField, PriorityField, StatusField

class Task:
    """Контракт данных задачи."""
    _id = StringField(min_length=1, max_length=64)
    _description = StringField(min_length=1, max_length=1024)
    _priority = PriorityField()
    _status = StatusField()
    def __init__(
        self,
        id: str,
        payload: Any,
        description: Optional[str] = None,
        priority: str = "medium",
    ):
        """ Инициализация новой задачи """
        self._id = id
        self._priority = priority
        self._status = "pending"
        self._description = description if description is not None else f"Task with id: {id}"
        self._payload = payload
        self._created_at = datetime.now()
        self._updated_at = self._created_at
        self._completed_at: Optional[datetime] = None

    @property
    def id(self) -> str:
        """Уникальный идентификатор задачи (только для чтения)."""
        return self._id

    @property
    def description(self) -> str:
        """Описание задачи."""
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value
        self._touch()
    @property
    def priority(self) -> str:
        """Приоритет задачи."""
        return self._priority

    @priority.setter
    def priority(self, value: str) -> None:
        self._priority = value
        self._touch()

    @property
    def status(self) -> str:
        """Текущий статус задачи."""
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        self._status = value
        self._touch()
        if value == "completed":
            self._completed_at = datetime.now()
    @property
    def payload(self) -> Any:
        """Произвольные данные задачи."""
        return self._payload

    @property
    def created_at(self) -> datetime:
        """Время создания задачи (только для чтения)."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Время последнего обновления задачи (только для чтения)."""
        return self._updated_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Время завершения задачи (только для чтения)."""
        return self._completed_at

    @property
    def is_ready_to_execute(self) -> bool:
        """
        Вычисляемое свойство: готовность задачи к выполнению.
        Задача готова, если она в статусе 'pending' или 'in_progress'.
        """
        return self._status in ("pending", "in_progress")

    @property
    def is_overdue(self) -> bool:
        """
        Заглушка для демонстрации вычисляемого свойства.
        В реальном приложении здесь была бы логика с дедлайнами.
        """
        return False

    def _touch(self) -> None:
        """Обновляет время последнего изменения задачи."""
        self._updated_at = datetime.now()
    
    def __repr__(self) -> str:
        return (
            f"Task(id={self.id!r}, status={self.status!r}, "
            f"priority={self.priority!r}, created_at={self.created_at})"
        )
    def __eq__(self, other) -> bool:
        if not isinstance(other, Task):
            return NotImplemented
        return self.id == other.id
    def __hash__(self) -> int:
        return hash(self.id)
    