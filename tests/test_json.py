"""Расширенные тесты для JSONL источника с поддержкой новых полей."""

import pytest
from pathlib import Path
from src.sources.json import JsonlSource, create_json_source
from src.contracts.task import Task
from src.contracts.exceptions import TaskValidationError


class TestJsonlSourceExtended:
    """Тесты для расширенной функциональности JsonlSource."""
    
    def test_fetch_basic_format(self, tmp_path):
        """Тест чтения задачи в базовом формате."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"id": "1", "payload": "test payload"}\n')
        
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "test payload"
        assert tasks[0].description == "Task with id: 1"
        assert tasks[0].priority == "medium"
    
    def test_fetch_with_description(self, tmp_path):
        """Тест чтения задачи с описанием."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "test", "description": "Important task"}\n'
        )
        
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "test"
        assert tasks[0].description == "Important task"
        assert tasks[0].priority == "medium"
    
    def test_fetch_with_priority(self, tmp_path):
        """Тест чтения задачи с приоритетом."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "test", "priority": "high"}\n'
        )
        
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "test"
        assert tasks[0].description == "Task with id: 1"
        assert tasks[0].priority == "high"
    
    def test_fetch_full_format(self, tmp_path):
        """Тест чтения задачи со всеми полями."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "test", "description": "Full task", "priority": "critical"}\n'
        )
        
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "test"
        assert tasks[0].description == "Full task"
        assert tasks[0].priority == "critical"
    
    def test_fetch_mixed_formats(self, tmp_path):
        """Тест чтения задач в разных форматах в одном файле."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "basic"}\n'
            '{"id": "2", "payload": "with desc", "description": "Description"}\n'
            '{"id": "3", "payload": "with priority", "priority": "low"}\n'
            '{"id": "4", "payload": "full", "description": "Full task", "priority": "critical"}\n'
        )
        
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        
        assert len(tasks) == 4
        
        assert tasks[0].id == "1"
        assert tasks[0].payload == "basic"
        assert tasks[0].priority == "medium"
        
        assert tasks[1].id == "2"
        assert tasks[1].payload == "with desc"
        assert tasks[1].description == "Description"
        assert tasks[1].priority == "medium"
        
        assert tasks[2].id == "3"
        assert tasks[2].payload == "with priority"
        assert tasks[2].priority == "low"
        
        assert tasks[3].id == "4"
        assert tasks[3].payload == "full"
        assert tasks[3].description == "Full task"
        assert tasks[3].priority == "critical"
    
    def test_fetch_with_complex_payload(self, tmp_path):
        """Тест чтения задачи со сложным payload."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": {"nested": {"key": "value"}, "array": [1, 2, 3]}, "priority": "high"}\n'
        )
        
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == {"nested": {"key": "value"}, "array": [1, 2, 3]}
        assert tasks[0].priority == "high"
    
    def test_fetch_with_invalid_priority(self, tmp_path):
        """Тест обработки невалидного приоритета."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "test", "priority": "invalid"}\n'
        )
        
        source = JsonlSource(path=jsonl_file)
        
        with pytest.raises(TaskValidationError, match="Недопустимый приоритет"):
            list(source.fetch())
    
    def test_fetch_with_invalid_id(self, tmp_path):
        """Тест обработки невалидного ID."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "", "payload": "test"}\n'
        )
        
        source = JsonlSource(path=jsonl_file)
        
        with pytest.raises(TaskValidationError, match="не может быть короче"):
            list(source.fetch())
    
    def test_fetch_with_unicode(self, tmp_path):
        """Тест обработки Unicode символов."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "Задача", "description": "Описание с эмодзи 🎉", "priority": "high"}\n',
            encoding='utf-8'
        )
        
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "Задача"
        assert tasks[0].description == "Описание с эмодзи 🎉"
        assert tasks[0].priority == "high"
    
    def test_fetch_large_file(self, tmp_path):
        """Тест обработки большого файла."""
        jsonl_file = tmp_path / "large.jsonl"
        
        lines = []
        for i in range(1000):
            if i % 3 == 0:
                lines.append(f'{{"id": "{i}", "payload": "task{i}"}}\n')
            elif i % 3 == 1:
                lines.append(f'{{"id": "{i}", "payload": "task{i}", "description": "desc{i}"}}\n')
            else:
                lines.append(f'{{"id": "{i}", "payload": "task{i}", "description": "desc{i}", "priority": "high"}}\n')
        
        jsonl_file.write_text("".join(lines))
        
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        
        assert len(tasks) == 1000
        assert tasks[0].id == "0"
        assert tasks[500].id == "500"
        assert tasks[999].id == "999"
    
    def test_fetch_skip_empty_lines(self, tmp_path):
        """Тест пропуска пустых строк."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "first"}\n'
            '\n'
            '{"id": "2", "payload": "second"}\n'
            '   \n'
            '{"id": "3", "payload": "third"}\n'
        )
        
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        
        assert len(tasks) == 3
        assert tasks[0].id == "1"
        assert tasks[1].id == "2"
        assert tasks[2].id == "3"
    
    def test_source_name(self, tmp_path):
        """Проверка имени источника."""
        jsonl_file = tmp_path / "test.jsonl"
        source = JsonlSource(path=jsonl_file)
        
        assert source.name == "file-jsonl"
    
    def test_create_source_factory(self, tmp_path):
        """Проверка фабрики создания источника."""
        jsonl_file = tmp_path / "test.jsonl"
        source = create_json_source(jsonl_file)
        
        assert isinstance(source, JsonlSource)
        assert source.name == "file-jsonl"
        assert source.path == jsonl_file