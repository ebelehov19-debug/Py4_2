"""Расширенные тесты для stdin источника с поддержкой новых полей."""

import pytest
from io import StringIO
from src.sources.stdin import StdinLineSource, extract_task_fields
from src.contracts.task import Task
from src.contracts.exceptions import TaskValidationError


class TestExtractTaskFields:
    """Тесты для функции extract_task_fields."""
    
    def test_extract_basic_format(self):
        """Тест базового формата id:payload."""
        lines = ["1", "test payload"]
        task_id, payload, description, priority = extract_task_fields(lines, 1)
        
        assert task_id == "1"
        assert payload == "test payload"
        assert description is None
        assert priority == "medium"
    
    def test_extract_with_description(self):
        """Тест формата с описанием id:payload:description."""
        lines = ["1", "test payload", "This is a description"]
        task_id, payload, description, priority = extract_task_fields(lines, 1)
        
        assert task_id == "1"
        assert payload == "test payload"
        assert description == "This is a description"
        assert priority == "medium"
    
    def test_extract_full_format(self):
        """Тест полного формата id:payload:description:priority."""
        lines = ["1", "test payload", "This is a description", "high"]
        task_id, payload, description, priority = extract_task_fields(lines, 1)
        
        assert task_id == "1"
        assert payload == "test payload"
        assert description == "This is a description"
        assert priority == "high"
    
    def test_extract_with_empty_description(self):
        """Тест с пустым описанием между двоеточиями."""
        lines = ["1", "test payload", "", "high"]
        task_id, payload, description, priority = extract_task_fields(lines, 1)
        
        assert task_id == "1"
        assert payload == "test payload"
        assert description is None
        assert priority == "high"
    
    def test_extract_with_whitespace(self):
        """Тест с пробелами вокруг значений."""
        lines = [" 1 ", " test payload ", " Description ", " high "]
        task_id, payload, description, priority = extract_task_fields(lines, 1)
        
        assert task_id == "1"
        assert payload == "test payload"
        assert description == "Description"
        assert priority == "high"
    
    def test_extract_error_on_insufficient_items(self):
        """Проверка ошибки при недостаточном количестве элементов."""
        lines = ["only_one"]
        
        with pytest.raises(ValueError, match="at least 2 items"):
            extract_task_fields(lines, 5)
    
    def test_extract_error_message_contains_line_number(self):
        """Проверка, что сообщение об ошибке содержит номер строки."""
        lines = ["incomplete"]
        
        with pytest.raises(ValueError) as exc_info:
            extract_task_fields(lines, 42)
        
        assert "42" in str(exc_info.value)


class TestStdinLineSourceExtended:
    """Тесты для расширенной функциональности StdinLineSource."""
    
    def test_fetch_basic_format(self):
        """Тест чтения задачи в базовом формате."""
        fake_stream = StringIO("1:test payload\n")
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "test payload"
        assert tasks[0].description == "Task with id: 1"
        assert tasks[0].priority == "medium"
    
    def test_fetch_with_description(self):
        """Тест чтения задачи с описанием."""
        fake_stream = StringIO("1:test payload:Important task\n")
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "test payload"
        assert tasks[0].description == "Important task"
        assert tasks[0].priority == "medium"
    
    def test_fetch_with_priority(self):
        """Тест чтения задачи с приоритетом."""
        fake_stream = StringIO("1:test payload:Important task:high\n")
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "test payload"
        assert tasks[0].description == "Important task"
        assert tasks[0].priority == "high"
    
    def test_fetch_mixed_formats(self):
        """Тест чтения задач в разных форматах в одном потоке."""
        fake_stream = StringIO(
            "1:basic task\n"
            "2:task with desc:Important description\n"
            "3:full task:Very important:critical\n"
            "4:skip description::medium\n"
        )
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        
        assert len(tasks) == 4
        
        assert tasks[0].id == "1"
        assert tasks[0].payload == "basic task"
        assert tasks[0].description == "Task with id: 1"
        assert tasks[0].priority == "medium"

        assert tasks[1].id == "2"
        assert tasks[1].payload == "task with desc"
        assert tasks[1].description == "Important description"
        assert tasks[1].priority == "medium"

        assert tasks[2].id == "3"
        assert tasks[2].payload == "full task"
        assert tasks[2].description == "Very important"
        assert tasks[2].priority == "critical"

        assert tasks[3].id == "4"
        assert tasks[3].payload == "skip description"
        assert tasks[3].description == "Task with id: 4"
        assert tasks[3].priority == "medium"
    
    def test_fetch_skip_empty_lines(self):
        """Тест пропуска пустых строк."""
        fake_stream = StringIO(
            "1:task1\n"
            "\n"
            "2:task2\n"
            "   \n"
            "3:task3\n"
        )
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        
        assert len(tasks) == 3
        assert tasks[0].id == "1"
        assert tasks[1].id == "2"
        assert tasks[2].id == "3"
    
    def test_fetch_with_invalid_priority(self):
        """Тест обработки невалидного приоритета."""
        fake_stream = StringIO("1:task:description:invalid_priority\n")
        source = StdinLineSource(stream=fake_stream)
        
        with pytest.raises(TaskValidationError, match="Недопустимый приоритет"):
            list(source.fetch())
    
    def test_fetch_with_unicode(self):
        """Тест обработки Unicode символов."""
        fake_stream = StringIO("1:Задача:Описание с эмодзи 🎉:high\n")
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "Задача"
        assert tasks[0].description == "Описание с эмодзи 🎉"
        assert tasks[0].priority == "high"
    
    def test_fetch_large_input(self):
        """Тест обработки большого количества строк."""
        lines = []
        for i in range(1000):
            if i % 3 == 0:
                lines.append(f"{i}:task{i}\n")
            elif i % 3 == 1:
                lines.append(f"{i}:task{i}:description{i}\n")
            else:
                lines.append(f"{i}:task{i}:description{i}:high\n")
        
        fake_stream = StringIO("".join(lines))
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        
        assert len(tasks) == 1000
        assert tasks[0].id == "0"
        assert tasks[500].id == "500"
        assert tasks[999].id == "999"
    
    def test_source_name(self):
        """Проверка имени источника."""
        source = StdinLineSource()
        assert source.name == "stdin"
    
    def test_create_source_factory(self):
        """Проверка фабрики создания источника."""
        from src.sources.stdin import create_source
        
        source = create_source()
        assert isinstance(source, StdinLineSource)
        assert source.name == "stdin"