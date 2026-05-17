# Лабораторная работа №4: Платформа обработки задач (дескрипторы, протоколы, async)

## Цель работы
Освоить реализацию data-дескрипторов Python, структурной типизации через Protocol, асинхронных контекстных менеджеров и паттерна реестра плагинов на примере платформы обработки задач. Научиться разрабатывать async-исполнитель с управлением параллелизмом через `asyncio.Semaphore` и проектировать расширяемый CLI.

## Постановка задачи
Необходимо расширить платформу обработки задач из предыдущей лабораторной, добавив слои валидации, асинхронного выполнения и CLI. Платформа должна поддерживать несколько источников задач, систему обработчиков и контроль параллелизма.

**Ключевые компоненты:**

### Дескрипторы (src/contracts/descriptors.py)
- `ValidatedField` — базовый data-дескриптор (`__get__`, `__set__`, `__set_name__`)
- `StringField` — валидация строк с ограничением длины
- `PriorityField` — допустимые значения: `low`, `medium`, `high`, `critical`
- `StatusField` — валидация статусов и проверка допустимых переходов

### Исключения (src/contracts/exceptions.py)
- `TaskError` — базовое исключение иерархии
- `TaskValidationError` — ошибка валидации полей задачи
- `InvalidTaskStatusTransitionError` — недопустимый переход статуса

### Протоколы (src/contracts/)
- `TaskSource` — структурный контракт для источников задач (метод `fetch`)
- `TaskHandler` — структурный контракт для обработчиков задач (метод `handle`)

### Источники задач (src/sources/)
- `StdinLineSource` — чтение задач из stdin, формат: `id:payload[:description[:priority]]`
- `JsonlSource` — чтение задач из `.jsonl`-файла (по одному JSON-объекту на строку)
- Реестр плагинов `REGISTRY` с декоратором `@register_source`

### Асинхронный исполнитель (src/executor/)
- `TaskExecutor` — `async with`-контекстный менеджер, управляет параллелизмом через `asyncio.Semaphore`
- `LoggingHandler`, `PrintHandler`, `DelayHandler`, `CallbackHandler`, `FailingHandler` — реализации протокола `TaskHandler`

### CLI (src/cli.py)
- `plugins` — список зарегистрированных плагинов источников
- `read` — чтение и вывод задач с фильтром `--contains`
- `execute` — асинхронное выполнение с выбором обработчика `-H` и параллелизма `-c`

## Технические требования
- реализация data-дескрипторов с методами `__get__`, `__set__`, `__set_name__`
- использование `Protocol` с `@runtime_checkable` для структурной типизации
- реализация `__aenter__` / `__aexit__` для управления жизненным циклом исполнителя
- контроль параллелизма через `asyncio.Semaphore`
- паттерн реестра плагинов с декоратором `@register_source`
- корректная обработка переходов статусов задачи
- совместимость с инструментами asyncio: `gather`, `sleep`

## Чему я научился
- Реализации data-дескрипторов и автоматическому вызову `__set_name__`
- Определению структурных контрактов через `Protocol` без наследования
- Написанию асинхронных контекстных менеджеров (`async with`)
- Управлению параллелизмом через `asyncio.Semaphore`
- Паттерну реестра плагинов с декораторами
- Проектированию расширяемого CLI с Typer
- Тестированию async-кода с `pytest-asyncio`

## Дескрипторы

### ValidatedField — базовый дескриптор
- Реализует `__get__`, `__set__`, `__set_name__` для автоматической привязки имён
- Хранит значение в `_<name>` атрибуте экземпляра
- `__set__` вызывает `validate(value)` перед сохранением

### PriorityField — валидация приоритета
- Допустимые значения: `low`, `medium`, `high`, `critical`
- Независим от регистра при проверке
- При ошибке бросает `TaskValidationError`

### StatusField — валидация статуса и переходов
- Допустимые статусы: `pending`, `in_progress`, `completed`, `failed`, `blocked`
- Запрещает изменение статуса из `completed` и `failed` (конечные состояния)
- Из `blocked` допустимы переходы только в `pending` или `failed`
- При нарушении бросает `InvalidTaskStatusTransitionError`

## Асинхронный исполнитель

### TaskExecutor
```
async with TaskExecutor(handlers=[...], concurrency=4) as executor:
    await executor.run(queue)
```

1. `__aenter__` — создаёт `asyncio.Semaphore`, сбрасывает статистику
2. `run(queue)` — пропускает неготовые задачи, запускает `asyncio.gather`
3. `_process_task(task)` — захватывает semaphore, меняет статус на `in_progress`, вызывает обработчики. При исключении — переводит в `failed`
4. `__aexit__` — логирует итоговую статистику, освобождает ресурсы

### Обработчики

| Класс | Ключ `-H` | Описание |
|-------|-----------|----------|
| `PrintHandler` | `print` | Печатает задачу в stdout |
| `LoggingHandler` | `logging` | Пишет задачу в `logging` |
| `DelayHandler` | — | Имитирует I/O через `asyncio.sleep` |
| `CallbackHandler` | — | Произвольный `async`-колбэк |
| `FailingHandler` | — | Всегда бросает `RuntimeError` (для тестов) |

## Протоколы

### TaskSource
```python
class TaskSource(Protocol):
    name: str
    def fetch(self) -> Iterable[Task]: ...
```

### TaskHandler
```python
class TaskHandler(Protocol):
    name: str
    async def handle(self, task: Task) -> None: ...
```

Оба протокола помечены `@runtime_checkable`, что позволяет использовать `isinstance()` без наследования.

## Инструкции по запуску

1. **Клонирование репозитория**
```bash
https://github.com/ebelehov19-debug/Py4_2
cd Py4_2
```

2. **Создание виртуального окружения**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. **Установка зависимостей**
```bash
pip install typer pytest pytest-asyncio
```

4. **Просмотр команд**
```bash
python -m src --help
```

5. **Просмотр плагинов**
```bash
python -m src plugins
```

## Примеры использования программы

1. **Чтение задач из .jsonl файла**
```bash
python -m src read --jsonl src/tasks.jsonl
```

2. **Чтение из stdin**
```bash
printf "1:Send report::high\n2:Review code\n" | python -m src read --stdin
```

3. **Асинхронное выполнение задач**
```bash
python -m src execute --jsonl src/tasks.jsonl -H print -H logging -c 8 -v
```

4. **Интерактивная проверка**
```bash
python -c "
import asyncio
from src.contracts.task import Task
from src.inbox.task_queue import TaskQueue
from src.executor.core import TaskExecutor
from src.executor.handlers import PrintHandler

queue = TaskQueue()
queue.add(Task(id='1', payload='Send report', priority='high'))
queue.add(Task(id='2', payload='Review code', priority='medium'))
queue.add(Task(id='3', payload='Deploy application', priority='critical'))

async def main():
    async with TaskExecutor(handlers=[PrintHandler()], concurrency=2) as executor:
        await executor.run(queue)
        print(executor.stats)

asyncio.run(main())
"
```

## Формат .jsonl файла

```jsonl
{"id": "1", "payload": "Send report", "description": "Send PDF via email", "priority": "high"}
{"id": "2", "payload": "Review code"}
{"id": "3", "payload": "Deploy service", "priority": "critical"}
```

| Поле | Обязательное | Допустимые значения |
|------|:---:|---|
| `id` | да | непустая строка до 64 символов |
| `payload` | да | любые данные |
| `description` | нет | строка до 1024 символов |
| `priority` | нет | `low`, `medium` (умолч.), `high`, `critical` |

## Запуск тестов

1. **Запуск всех тестов**
```bash
python -m pytest tests/ -v
```

2. **Только тесты исполнителя**
```bash
python -m pytest tests/test_executor.py -v
```

