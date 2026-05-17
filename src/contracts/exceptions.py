class TaskError(Exception):
    """Базовое исключение для ошибок, связанных с задачей."""
    pass

class TaskValidationError(TaskError, ValueError):
    """Ошибка валидации данных задачи."""
    pass

class InvalidTaskStatusTransitionError(TaskError):
    """Ошибка при попытке некорректного изменения статуса задачи."""
    pass