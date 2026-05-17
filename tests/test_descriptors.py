import pytest
from src.contracts.descriptors import (
    ValidatedField,
    StringField,
    PriorityField,
    StatusField
)
from src.contracts.exceptions import (
    TaskValidationError,
    InvalidTaskStatusTransitionError
)


class TestValidatedField:
    """Тесты базового класса ValidatedField."""
    
    def test_set_name_creates_private_name(self):
        """Проверка, что __set_name__ создаёт приватное имя."""
        class TestClass:
            field = ValidatedField()
        
        descriptor = TestClass.__dict__['field']
        assert descriptor.private_name == '_field'
    
    def test_get_with_instance_none_returns_self(self):
        """Проверка, что при instance=None возвращается сам дескриптор."""
        class TestClass:
            field = ValidatedField()
        
        assert TestClass.field is TestClass.__dict__['field']
    
    def test_get_with_instance_returns_value(self):
        """Проверка получения значения через дескриптор."""
        class TestClass:
            field = ValidatedField()
        
        obj = TestClass()
        obj._field = "test value"
        assert obj.field == "test value"
    
    def test_set_validates_and_stores_value(self):
        """Проверка установки значения с валидацией."""
        class TestField(ValidatedField):
            def validate(self, value):
                if value == "invalid":
                    raise TaskValidationError("Invalid value")
        
        class TestClass:
            field = TestField()
        
        obj = TestClass()
        obj.field = "valid"
        assert obj._field == "valid"
        
        with pytest.raises(TaskValidationError):
            obj.field = "invalid"
    
    def test_validate_method_can_be_overridden(self):
        """Проверка, что метод validate можно переопределить."""
        class CustomField(ValidatedField):
            def validate(self, value):
                if not isinstance(value, int):
                    raise TaskValidationError("Must be integer")
        
        class TestClass:
            field = CustomField()
        
        obj = TestClass()
        obj.field = 42
        assert obj._field == 42
        
        with pytest.raises(TaskValidationError):
            obj.field = "not integer"


class TestStringField:
    """Тесты для дескриптора StringField."""
    
    def test_string_field_validation_success(self):
        """Проверка успешной валидации строк."""
        class TestClass:
            name = StringField(min_length=1, max_length=10)
        
        obj = TestClass()
        obj.name = "John"
        assert obj._name == "John"
        
        obj.name = "A"
        assert obj._name == "A"
        
        obj.name = "1234567890" 
        assert obj._name == "1234567890"
    
    def test_string_field_type_validation(self):
        """Проверка валидации типа данных."""
        class TestClass:
            name = StringField()
        
        obj = TestClass()
        
        with pytest.raises(TaskValidationError, match="должно быть строкой"):
            obj.name = 123
        
        with pytest.raises(TaskValidationError, match="должно быть строкой"):
            obj.name = None
        
        with pytest.raises(TaskValidationError, match="должно быть строкой"):
            obj.name = ["list"]
    
    def test_string_field_min_length_validation(self):
        """Проверка валидации минимальной длины."""
        class TestClass:
            name = StringField(min_length=3)
        
        obj = TestClass()
        
        with pytest.raises(TaskValidationError, match="не может быть короче 3"):
            obj.name = "ab"
        
        with pytest.raises(TaskValidationError, match="не может быть короче 3"):
            obj.name = ""
    
    def test_string_field_max_length_validation(self):
        """Проверка валидации максимальной длины."""
        class TestClass:
            name = StringField(max_length=5)
        
        obj = TestClass()
        
        with pytest.raises(TaskValidationError, match="не может быть длиннее 5"):
            obj.name = "123456"
    
    def test_string_field_without_max_length(self):
        """Проверка работы без ограничения максимальной длины."""
        class TestClass:
            name = StringField(min_length=1)
        
        obj = TestClass()
        long_string = "a" * 1000
        obj.name = long_string
        assert obj._name == long_string


class TestPriorityField:
    """Тесты для дескриптора PriorityField."""
    
    def test_priority_field_valid_values(self):
        """Проверка допустимых значений приоритета."""
        class TestClass:
            priority = PriorityField()
        
        obj = TestClass()
        
        valid_priorities = ["low", "medium", "high", "critical"]
        for priority in valid_priorities:
            obj.priority = priority
            assert obj._priority == priority
        obj.priority = "HIGH"
        assert obj._priority == "HIGH"
        obj.priority = "Low"
        assert obj._priority == "Low"
    
    def test_priority_field_invalid_values(self):
        """Проверка недопустимых значений приоритета."""
        class TestClass:
            priority = PriorityField()
        obj = TestClass()
        invalid_priorities = ["argent", "normal", "1", "", "very-high"]
        for priority in invalid_priorities:
            with pytest.raises(TaskValidationError, match="Недопустимый приоритет"):
                obj.priority = priority
    
    def test_priority_field_type_validation(self):
        """Проверка валидации типа для приоритета."""
        class TestClass:
            priority = PriorityField()
        
        obj = TestClass()
        
        with pytest.raises(TaskValidationError, match="должен быть строкой"):
            obj.priority = 123
        
        with pytest.raises(TaskValidationError, match="должен быть строкой"):
            obj.priority = None
        
        with pytest.raises(TaskValidationError, match="должен быть строкой"):
            obj.priority = ["high"]
    
    def test_priority_field_error_message_contains_valid_values(self):
        """Проверка, что сообщение об ошибке содержит список допустимых значений."""
        class TestClass:
            priority = PriorityField()
        
        obj = TestClass()
        
        with pytest.raises(TaskValidationError) as exc_info:
            obj.priority = "invalid"
        
        error_msg = str(exc_info.value)
        assert "low" in error_msg
        assert "medium" in error_msg
        assert "high" in error_msg
        assert "critical" in error_msg


class TestStatusField:
    """Тесты для дескриптора StatusField."""
    
    def test_status_field_valid_values(self):
        """Проверка допустимых значений статуса."""
        class TestClass:
            status = StatusField()
        valid_statuses = ["pending", "in_progress", "completed", "failed", "blocked"]
        for status in valid_statuses:
            obj = TestClass()
            obj.status = status
            assert obj._status == status
    
    def test_status_field_invalid_values(self):
        """Проверка недопустимых значений статуса."""
        class TestClass:
            status = StatusField()
        
        obj = TestClass()
        
        invalid_statuses = ["done", "active", "waiting", "new", ""]
        for status in invalid_statuses:
            with pytest.raises(TaskValidationError, match="Недопустимый статус"):
                obj.status = status
    
    def test_status_field_type_validation(self):
        """Проверка валидации типа для статуса."""
        class TestClass:
            status = StatusField()
        
        obj = TestClass()
        
        with pytest.raises(TaskValidationError, match="должен быть строкой"):
            obj.status = 123
        
        with pytest.raises(TaskValidationError, match="должен быть строкой"):
            obj.status = None
    
    def test_status_transition_pending_to_any(self):
        """Проверка переходов из статуса pending."""
        class TestClass:
            status = StatusField()
        
        obj = TestClass()
        obj.status = "pending"

        obj.status = "in_progress"
        assert obj._status == "in_progress"
        
        obj = TestClass()
        obj.status = "pending"
        obj.status = "blocked"
        assert obj._status == "blocked"
        
        obj = TestClass()
        obj.status = "pending"
        obj.status = "completed"
        assert obj._status == "completed"
        
        obj = TestClass()
        obj.status = "pending"
        obj.status = "failed"
        assert obj._status == "failed"
    
    def test_status_transition_from_completed_blocked(self):
        """Проверка, что из completed нельзя изменить статус."""
        class TestClass:
            status = StatusField()
        
        obj = TestClass()
        obj.status = "completed"
        
        with pytest.raises(InvalidTaskStatusTransitionError, match="конечном состоянии"):
            obj.status = "pending"
        
        with pytest.raises(InvalidTaskStatusTransitionError, match="конечном состоянии"):
            obj.status = "in_progress"
        
        with pytest.raises(InvalidTaskStatusTransitionError, match="конечном состоянии"):
            obj.status = "blocked"
    
    def test_status_transition_from_failed_blocked(self):
        """Проверка, что из failed нельзя изменить статус."""
        class TestClass:
            status = StatusField()
    
        obj = TestClass()
        obj.status = "failed"
    
        with pytest.raises(InvalidTaskStatusTransitionError, match="конечном состоянии"):
            obj.status = "pending"
    
        with pytest.raises(InvalidTaskStatusTransitionError, match="конечном состоянии"):
            obj.status = "in_progress"
    
        with pytest.raises(InvalidTaskStatusTransitionError, match="конечном состоянии"):
            obj.status = "completed"
        obj2 = TestClass()
        obj2.status = "failed"
        with pytest.raises(InvalidTaskStatusTransitionError, match="конечном состоянии"):
            obj2.status = "blocked"
    
    def test_status_transition_from_blocked(self):
        """Проверка переходов из статуса blocked."""
        class TestClass:
            status = StatusField()
        obj1 = TestClass()
        obj1.status = "blocked"
        obj1.status = "pending"
        assert obj1._status == "pending"
    

        obj2 = TestClass()
        obj2.status = "blocked"
        obj2.status = "failed"
        assert obj2._status == "failed"

        obj3 = TestClass()
        obj3.status = "blocked"
        with pytest.raises(InvalidTaskStatusTransitionError, match="Допустимые переходы"):
            obj3.status = "in_progress"
        obj4 = TestClass()
        obj4.status = "blocked"
        with pytest.raises(InvalidTaskStatusTransitionError, match="Допустимые переходы"):
            obj4.status = "completed"

    def test_status_transition_from_in_progress(self):
        """Проверка переходов из статуса in_progress."""
        class TestClass:
            status = StatusField()
        obj1 = TestClass()
        obj1.status = "in_progress"
        obj1.status = "pending"
        assert obj1._status == "pending"
        obj2 = TestClass()
        obj2.status = "in_progress"
        obj2.status = "blocked"
        assert obj2._status == "blocked"
        obj3 = TestClass()
        obj3.status = "in_progress"
        obj3.status = "completed"
        assert obj3._status == "completed"
    
        obj4 = TestClass()
        obj4.status = "in_progress"
        obj4.status = "failed"
        assert obj4._status == "failed"
    def test_status_field_error_message_contains_valid_values(self):
        """Проверка сообщения об ошибке при невалидном статусе."""
        class TestClass:
            status = StatusField()
        
        obj = TestClass()
        
        with pytest.raises(TaskValidationError) as exc_info:
            obj.status = "invalid"
        
        error_msg = str(exc_info.value)
        assert "pending" in error_msg
        assert "in_progress" in error_msg
        assert "completed" in error_msg
        assert "failed" in error_msg
        assert "blocked" in error_msg