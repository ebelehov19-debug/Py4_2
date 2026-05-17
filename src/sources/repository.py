from functools import wraps
from typing import Callable, Type

from src.contracts.task_source import TaskSource

SourceFactory = Callable[..., TaskSource]

REGISTRY: dict[str, SourceFactory] = {}

def register_source(name: str):
    def _decorator(class_or_function: Type | Callable):
        REGISTRY[name] = class_or_function
        return class_or_function
    return _decorator