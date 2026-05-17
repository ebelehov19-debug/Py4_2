import pytest
from datetime import datetime
from src.contracts.task import Task
from src.contracts.exceptions import (
    TaskValidationError,
    InvalidTaskStatusTransitionError
)
class TestTaskCreation:
    """Тесты создания задачи."""
    
    def test_create_task_with_required_fields(self):
        """Проверка создания задачи с обязательными полями."""
        task = Task(id="1", payload="test payload")
        assert task.id == "1"
        assert task.payload == "test payload"
        assert task.description == "Task with id: 1"
        assert task.priority == "medium"
        assert task.status == "pending"
        assert task.created_at is not None
        assert task.updated_at is not None
        assert task.completed_at is None
    
    def test_create_task_with_all_fields(self):
        """Проверка создания задачи со всеми полями."""
        task = Task(
            id="task-123",
            payload={"data": "value"},
            description="Important task",
            priority="high"
        )
        
        assert task.id == "task-123"
        assert task.payload == {"data": "value"}
        assert task.description == "Important task"
        assert task.priority == "high"
        assert task.status == "pending"
    
    def test_create_task_with_different_payload_types(self):
        """Проверка создания задач с разными типами payload."""
        payloads = [
            "string payload",
            42,
            3.14,
            True,
            False,
            None,
            {"key": "value"},
            [1, 2, 3],
            (1, 2, 3),
            {"nested": {"deep": "value"}}
        ]
        for i, payload in enumerate(payloads):
            task = Task(id=str(i), payload=payload)
            assert task.payload == payload
    
    def test_task_id_validation(self):
        """Проверка валидации ID задачи."""
        with pytest.raises(TaskValidationError, match="не может быть короче 1"):
            Task(id="", payload="test")
        long_id = "a" * 65
        with pytest.raises(TaskValidationError, match="не может быть длиннее 64"):
            Task(id=long_id, payload="test")
        with pytest.raises(TaskValidationError, match="должно быть строкой"):
            Task(id=123, payload="test")  # type: ignore
    
    def test_task_description_validation(self):
        """Проверка валидации описания задачи."""
        with pytest.raises(TaskValidationError, match="не может быть короче 1"):
            Task(id="1", payload="test", description="")
        long_desc = "a" * 1025
        with pytest.raises(TaskValidationError, match="не может быть длиннее 1024"):
            Task(id="1", payload="test", description=long_desc)
    def test_task_priority_validation(self):
        """Проверка валидации приоритета при создании."""
        with pytest.raises(TaskValidationError, match="Недопустимый приоритет"):
            Task(id="1", payload="test", priority="urgent")
    def test_task_created_at_and_updated_at(self):
        """Проверка установки времени создания и обновления."""
        before = datetime.now()
        task = Task(id="1", payload="test")
        after = datetime.now()
        assert before <= task.created_at <= after
        assert task.created_at == task.updated_at


class TestTaskProperties:
    """Тесты свойств задачи.""" 
    def test_id_is_readonly(self):
        """Проверка, что id доступен только для чтения."""
        task = Task(id="1", payload="test")
        with pytest.raises(AttributeError):
            task.id = "2"  
    
    def test_created_at_is_readonly(self):
        """Проверка, что created_at доступен только для чтения."""
        task = Task(id="1", payload="test")
        
        with pytest.raises(AttributeError):
            task.created_at = datetime.now() 
    
    def test_updated_at_is_readonly(self):
        """Проверка, что updated_at доступен только для чтения."""
        task = Task(id="1", payload="test")
        
        with pytest.raises(AttributeError):
            task.updated_at = datetime.now()  
    
    def test_completed_at_is_readonly(self):
        """Проверка, что completed_at доступен только для чтения."""
        task = Task(id="1", payload="test")
        with pytest.raises(AttributeError):
            task.completed_at = datetime.now()  
    
    def test_description_setter_updates_updated_at(self):
        """Проверка, что изменение описания обновляет updated_at."""
        task = Task(id="1", payload="test")
        original_updated_at = task.updated_at
        import time
        time.sleep(0.001)
        task.description = "New description"
        assert task.description == "New description"
        assert task.updated_at > original_updated_at
    
    def test_priority_setter_updates_updated_at(self):
        """Проверка, что изменение приоритета обновляет updated_at."""
        task = Task(id="1", payload="test")
        original_updated_at = task.updated_at
        import time
        time.sleep(0.001)
        task.priority = "high"
        assert task.priority == "high"
        assert task.updated_at > original_updated_at
    
    def test_status_setter_updates_updated_at(self):
        """Проверка, что изменение статуса обновляет updated_at."""
        task = Task(id="1", payload="test")
        original_updated_at = task.updated_at
        import time
        time.sleep(0.001)
        task.status = "in_progress"
        assert task.status == "in_progress"
        assert task.updated_at > original_updated_at
    
    def test_status_setter_sets_completed_at(self):
        """Проверка, что при установке статуса completed устанавливается completed_at."""
        task = Task(id="1", payload="test")
        assert task.completed_at is None
        task.status = "completed"
        assert task.status == "completed"
        assert task.completed_at is not None
        assert isinstance(task.completed_at, datetime)
    
    def test_status_transition_validation(self):
        """Проверка валидации переходов статусов."""
        task = Task(id="1", payload="test")
        task.status = "completed"
        with pytest.raises(InvalidTaskStatusTransitionError):
            task.status = "in_progress"


class TestTaskComputedProperties:
    """Тесты вычисляемых свойств задачи."""
    
    def test_is_ready_to_execute_pending(self):
        """Проверка готовности задачи в статусе pending."""
        task = Task(id="1", payload="test")
        assert task.status == "pending"
        assert task.is_ready_to_execute is True
    
    def test_is_ready_to_execute_in_progress(self):
        """Проверка готовности задачи в статусе in_progress."""
        task = Task(id="1", payload="test")
        task.status = "in_progress"
        assert task.is_ready_to_execute is True
    
    def test_is_ready_to_execute_completed(self):
        """Проверка, что завершённая задача не готова к выполнению."""
        task = Task(id="1", payload="test")
        task.status = "completed"
        assert task.is_ready_to_execute is False
    
    def test_is_ready_to_execute_failed(self):
        """Проверка, что проваленная задача не готова к выполнению."""
        task = Task(id="1", payload="test")
        task.status = "failed"
        assert task.is_ready_to_execute is False
    
    def test_is_ready_to_execute_blocked(self):
        """Проверка, что заблокированная задача не готова к выполнению."""
        task = Task(id="1", payload="test")
        task.status = "blocked"
        assert task.is_ready_to_execute is False
    
    def test_is_overdue(self):
        """Проверка вычисляемого свойства is_overdue."""
        task = Task(id="1", payload="test")
        assert task.is_overdue is False


class TestTaskSpecialMethods:
    """Тесты специальных методов задачи."""
    
    def test_task_equality(self):
        """Проверка равенства задач."""
        task1 = Task(id="1", payload="test1")
        task2 = Task(id="1", payload="test2")
        task3 = Task(id="2", payload="test1")
        assert task1 == task2
        assert task1 != task3
        assert task1 != "not a task hihihihih"
        assert task1 != None
    
    def test_task_hash(self):
        """Проверка хеширования задач."""
        task1 = Task(id="1", payload="test1")
        task2 = Task(id="1", payload="test2")
        task3 = Task(id="2", payload="test1")
        assert hash(task1) == hash(task2)
        assert hash(task1) != hash(task3)
        task_set = {task1, task2, task3}
        assert len(task_set) == 2
    
    def test_task_repr(self):
        """Проверка строкового представления задачи."""
        task = Task(id="123", payload="test", description="Test task", priority="high")
        repr_str = repr(task)
        
        assert "Task" in repr_str
        assert "123" in repr_str
        assert "pending" in repr_str
        assert "high" in repr_str


class TestTaskIntegration:
    """Интеграционные тесты для Task."""
    def test_task_with_complex_payload(self):
        """Проверка работы со сложным payload."""
        complex_payload = {
            "user": {
                "id": 123,
                "name": "John Doe",
                "email": "john@example.com"
            },
            "items": [
                {"id": 1, "name": "Item 1", "price": 10.99},
                {"id": 2, "name": "Item 2", "price": 20.50}
            ],
            "total": 31.49,
            "metadata": {
                "created": "2024-01-01T00:00:00Z",
                "source": "api",
                "tags": ["important", "urgent"]
            }
        }
        
        task = Task(id="complex-1", payload=complex_payload)
        
        assert task.payload == complex_payload
        assert task.payload["user"]["name"] == "John Doe"
        assert len(task.payload["items"]) == 2
        assert task.payload["metadata"]["tags"][0] == "important"