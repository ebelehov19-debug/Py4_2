import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.contracts.task import Task
from src.sources.repository import register_source


def parse_json_file(line: str, path: str, line_no: int) -> dict[str, Any]:
    try:
        return json.loads(line)
    except json.JSONDecodeError as error:
        raise ValueError(f"Bad JSON at {path}:{line_no}: {error}") from error


@dataclass(frozen=True)
class JsonlSource:
    path: Path
    name: str = "file-jsonl"

    def fetch(self) -> Iterable[Task]:
        with self.path.open("r", encoding="utf-8") as file:
            for line_no, line in enumerate(file, start=1):
                line = line.strip()
                if not line:
                    continue
                task = parse_json_file(line, str(self.path), line_no)
                task_id = task["id"]
                task_payload = task.get("payload")
                description = task.get("description")
                priority = task.get("priority", "medium")
                yield Task(
                    id=task_id,
                    payload=task_payload,
                    description=description,
                    priority=priority
                    )


@register_source("file-jsonl")
def create_json_source(path: Path) -> JsonlSource:
    return JsonlSource(path=path)