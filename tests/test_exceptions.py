"""Тесты для специализированных исключений."""

import pytest
from src.contracts.exceptions import (
    TaskError,
    TaskValidationError,
    InvalidTaskStatusTransitionError
)


class TestExceptions:
    """Тесты для иерархии исключений."""
    
    def test_task_error_is_base_exception(self):
        """Проверка, что TaskError - базовое исключение."""
        error = TaskError("Base error")
        assert isinstance(error, Exception)
        assert str(error) == "Base error"
    
    def test_task_validation_error_inheritance(self):
        """Проверка наследования TaskValidationError."""
        error = TaskValidationError("Validation failed")
        assert isinstance(error, TaskError)
        assert isinstance(error, ValueError)
        assert issubclass(TaskValidationError, TaskError)
        assert issubclass(TaskValidationError, ValueError)
    
    def test_invalid_status_transition_error_inheritance(self):
        """Проверка наследования InvalidTaskStatusTransitionError."""
        error = InvalidTaskStatusTransitionError("Invalid transition")
        assert isinstance(error, TaskError)
        assert isinstance(error, Exception)
        assert issubclass(InvalidTaskStatusTransitionError, TaskError)
    
    def test_exception_messages(self):
        """Проверка сообщений исключений."""
        with pytest.raises(TaskValidationError, match="Недопустимый приоритет"):
            raise TaskValidationError("Недопустимый приоритет 'argent'")
        
        with pytest.raises(InvalidTaskStatusTransitionError, match="Нельзя изменить статус"):
            raise InvalidTaskStatusTransitionError("Нельзя изменить статус с 'completed'")
    
    def test_exception_catching_order(self):
        """Проверка порядка перехвата исключений."""
        try:
            raise TaskValidationError("Test")
        except TaskError:
            pass
        except Exception:
            pytest.fail("TaskValidationError should be caught as TaskError")
        try:
            raise InvalidTaskStatusTransitionError("Test")
        except TaskError:
            pass
        except Exception:
            pytest.fail("InvalidTaskStatusTransitionError should be caught as TaskError")