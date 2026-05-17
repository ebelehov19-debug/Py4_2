from typing import Any, Optional
from src.contracts.exceptions import TaskValidationError,InvalidTaskStatusTransitionError

class ValidatedField:
    """Базовый класс data-дескриптора для валидируемых полей."""
    def __init__(self, *args, **kwargs):
        self.private_name = None

    def __set_name__(self, owner, name):
        """Автоматически вызывается при создании класса-владельца."""
        self.private_name = f'_{name}'

    def __get__(self, instance, owner) -> Any:
        if instance is None:
            return self
        return getattr(instance, self.private_name, None)

    def __set__(self, instance, value: Any) -> None:
        self.validate(value)
        setattr(instance, self.private_name, value)

    def validate(self, value: Any) -> None:
        """Метод для переопределения в дочерних классах."""
        pass

class PriorityField(ValidatedField):
    """Дескриптор для поля приоритета задачи."""
    VALID_PRIORITIES = ("low", "medium", "high", "critical")

    def validate(self, value: Any) -> None:
        if not isinstance(value, str):
            raise TaskValidationError(f"Приоритет '{value}' должен быть строкой.")
        if value.lower() not in self.VALID_PRIORITIES:
            raise TaskValidationError(
                f"Недопустимый приоритет '{value}'. "
                f"Допустимые значения: {', '.join(self.VALID_PRIORITIES)}"
            )

class StringField(ValidatedField):
    """Дескриптор для строковых полей с ограничением по длине."""
    def __init__(self, min_length: int = 1, max_length: Optional[int] = None):
        super().__init__()
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value: Any) -> None:
        if not isinstance(value, str):
            raise TaskValidationError(f"Значение '{value}' должно быть строкой.")
        if len(value) < self.min_length:
            raise TaskValidationError(f"Строка не может быть короче {self.min_length} символов.")
        if self.max_length and len(value) > self.max_length:
            raise TaskValidationError(f"Строка не может быть длиннее {self.max_length} символов.")
        
class StatusField(ValidatedField):
    """Дескриптор для поля статуса задачи с проверкой переходов."""
    VALID_STATUSES = ("pending", "in_progress", "completed", "failed", "blocked")

    def __set__(self, instance, value: Any) -> None:
        self.validate(value)
        current_status = getattr(instance, self.private_name, None)
        if instance is not None and current_status is not None:
            self.validate_transition(current_status, value)
        setattr(instance, self.private_name, value)

    def validate(self, value: Any) -> None:
        if not isinstance(value, str):
            raise TaskValidationError(f"Статус '{value}' должен быть строкой.")
        if value.lower() not in self.VALID_STATUSES:
            raise TaskValidationError(
                f"Недопустимый статус '{value}'. "
                f"Допустимые значения: {', '.join(self.VALID_STATUSES)}"
            )
    def validate_transition(self, from_status: str, to_status: str) -> None:
        """Проверяет, можно ли перейти из одного статуса в другой."""
        if from_status in ("completed", "failed"):
            raise InvalidTaskStatusTransitionError(
                f"Нельзя изменить статус с '{from_status}' на '{to_status}'. "
                f"Задача уже в конечном состоянии."
            )
        if from_status == "blocked" and to_status not in ("pending", "failed"):
            raise InvalidTaskStatusTransitionError(
                f"Нельзя перевести задачу из 'blocked' в '{to_status}'. "
                f"Допустимые переходы: 'pending' или 'failed'."
            )
