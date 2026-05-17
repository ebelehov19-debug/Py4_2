import sys
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TextIO, Optional

from src.contracts.task import Task
from src.sources.repository import register_source


def extract_task_fields(lines: list[str], line_no: int) -> tuple[str, str, Optional[str], str]:
    """
    Извлекает поля задачи из строки, разделенной двоеточиями.
    Формат: id:payload[:description[:priority]]
    """
    try:
        task_id = lines[0].strip()
        payload = lines[1].strip()
        
        description = None
        if len(lines) > 2:
            description = lines[2].strip()
            if not description:
                description = None
        priority = "medium"
        if len(lines) > 3:
            priority_value = lines[3].strip()
            if priority_value: 
                priority = priority_value
                
    except IndexError:
        raise ValueError(
            f"Line: {line_no}. Task must contain at least 2 items, separated by ':' "
        )
    return task_id, payload, description, priority


@dataclass(frozen=True)
class StdinLineSource:
    """Источник задач из стандартного потока ввода."""
    
    stream: TextIO = sys.stdin
    name: str = "stdin"

    def fetch(self) -> Iterable[Task]:
        """
        Читает задачи из потока ввода.
        Формат строк:
        - Базовый: id:payload
        - Расширенный: id:payload:description
        - Полный: id:payload:description:priority
        """
        for line_no, line in enumerate(self.stream, start=1):
            if not line.strip():
                continue
            line = line.rstrip('\n')
            parts = line.split(":")
            task_id, payload, description, priority = extract_task_fields(parts, line_no)
            yield Task(
                id=task_id,
                payload=payload,
                description=description,
                priority=priority
            )


@register_source("stdin")
def create_source() -> StdinLineSource:
    """Фабрика для создания источника stdin."""
    return StdinLineSource()
