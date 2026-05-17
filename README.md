# Платформа обработки задач — Лабораторные работы №1–4

## Обзор

Учебный проект, реализующий абстрактную платформу обработки задач.
Каждая лабораторная работа добавляет новый слой архитектуры поверх предыдущего.

```
src/
├── contracts/          # Лаб 1 & 2: контракты и модель задачи
│   ├── exceptions.py   # Иерархия исключений
│   ├── descriptors.py  # Data-дескрипторы валидации
│   ├── task.py         # Класс Task
│   ├── task_source.py  # Protocol TaskSource
│   └── handler.py      # Protocol TaskHandler (Лаб 4)
├── sources/            # Лаб 1: источники задач
│   ├── repository.py   # Реестр плагинов
│   ├── stdin.py        # Источник из stdin
│   └── json.py         # Источник из .jsonl файла
├── inbox/              # Лаб 3: очередь и процессор
│   ├── core.py         # TaskProcessor
│   └── task_queue.py   # TaskQueue с итератором и генераторами
├── executor/           # Лаб 4: асинхронный исполнитель
│   ├── core.py         # TaskExecutor (async context manager)
│   └── handlers.py     # LoggingHandler, PrintHandler, DelayHandler, …
└── cli.py              # CLI: read, execute, plugins
```

---

## Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/ebelehov19-debug/LABPY3
cd LABPY3
```

### 2. Установить зависимости

```bash
python -m pip install typer pytest pytest-asyncio
```

> Для отчёта о покрытии тестами дополнительно:
> ```bash
> python -m pip install pytest-cov
> ```

---

## Запуск — быстрый старт

```bash
python -m src --help
```

Вывод:
```
Usage: python -m src [OPTIONS] COMMAND [ARGS]...

  Платформа обработки задач: приём, очередь и асинхронное выполнение.

Commands:
  execute  Асинхронно выполнить задачи из указанных источников.
  plugins  Показать список доступных плагинов источников задач.
  read     Прочитать и вывести задачи из указанных источников.
```

---

## Команды CLI

### `plugins` — список доступных плагинов

```bash
python -m src plugins
```

Вывод:
```
Available plugins:
  • file-jsonl
  • stdin
```

---

### `read` — чтение и вывод задач

#### Из .jsonl файла

```bash
python -m src read --jsonl tasks.jsonl
```

Вывод:
```
[1] Отправить отчёт
[2] Проверить код
[3] Задеплоить сервис
[4] Обновить зависимости

Total tasks: 4
```

#### С фильтром по подстроке в payload

```bash
python -m src read --jsonl tasks.jsonl --contains "код"
```

Вывод:
```
[2] Проверить код

Total tasks: 1
```

#### Из stdin (одна задача)

```bash
echo "task-1:Обработать заявку" | python -m src read --stdin
```

#### Из stdin (несколько задач, полный формат)

```bash
printf "1:Купить молоко\n2:Позвонить клиенту:Срочно:high\n3:Подготовить отчёт\n" | \
  python -m src read --stdin
```

Формат строки stdin: `id:payload[:description[:priority]]`
— `description` и `priority` необязательны, по умолчанию `priority = medium`

---

### `execute` — асинхронное выполнение задач

#### С обработчиком вывода (по умолчанию)

```bash
python -m src execute --jsonl tasks.jsonl
```

Вывод:
```
Загружено задач: 4
Обработчики: print-handler
Параллелизм: 4

[1] Отправить отчёт
[2] Проверить код
[3] Задеплоить сервис
[4] Обновить зависимости

 Готово. Обработано: 4  Ошибок: 0  Пропущено: 0
```

#### С обработчиком логирования

```bash
python -m src execute --jsonl tasks.jsonl -H logging
```

#### Оба обработчика одновременно

```bash
python -m src execute --jsonl tasks.jsonl -H print -H logging
```

#### С ограничением параллелизма и verbose-логами

```bash
python -m src execute --jsonl tasks.jsonl -c 2 -v
```

`-c 2` — максимум 2 задачи выполняются одновременно.
`-v` — включает DEBUG-уровень логирования.

#### Из stdin

```bash
printf "t1:Задача первая:Описание:high\nt2:Задача вторая\n" | \
  python -m src execute --stdin -H logging -v
```

#### С фильтрацией при выполнении

```bash
python -m src execute --jsonl tasks.jsonl --contains "отчёт"
```

Выполнятся только задачи, в payload которых содержится подстрока «отчёт».

---

## Формат файла .jsonl

Каждая строка — отдельный JSON-объект:

```jsonl
{"id": "1", "payload": "Отправить отчёт", "description": "Отправить PDF на почту", "priority": "high"}
{"id": "2", "payload": "Проверить код"}
{"id": "3", "payload": "Задеплоить сервис", "priority": "critical"}
{"id": "4", "payload": "Обновить зависимости", "priority": "low"}
```

| Поле | Обязательное | Допустимые значения |
|------|:---:|---|
| `id` | да | любая непустая строка (до 64 символов) |
| `payload` | да | любые данные |
| `description` | нет | строка до 1024 символов |
| `priority` | нет | `low`, `medium` (умолч.), `high`, `critical` |

---

## Допустимые статусы задачи

| Статус | Описание |
|--------|----------|
| `pending` | Ожидает выполнения (начальный) |
| `in_progress` | Выполняется |
| `completed` | Успешно завершена |
| `failed` | Завершена с ошибкой |
| `blocked` | Заблокирована |

Переходы `completed → *` и `failed → *` запрещены дескриптором `StatusField`.

---

## Запуск тестов

```bash
# Все тесты
python -m pytest tests/ -v

# Только Лаб 4 (исполнитель)
python -m pytest tests/test_executor.py -v

# С отчётом о покрытии
python -m pytest tests/ --cov=src --cov-report=term-missing
```

---

## Архитектура Лаб 4 — TaskExecutor

```
async with TaskExecutor(handlers=[...], concurrency=4) as executor:
    await executor.run(queue)
```

1. `__aenter__` — создаёт `asyncio.Semaphore`, сбрасывает статистику, логирует старт.
2. `run(queue)` — пропускает неготовые задачи, запускает `asyncio.gather` по остальным.
3. `_process_task(task)` — захватывает semaphore, меняет статус на `in_progress`, вызывает все обработчики последовательно. При исключении — `failed`.
4. `__aexit__` — логирует итоговую статистику, освобождает ресурсы.

### Обработчики

| Класс | Ключ `-H` | Описание |
|-------|-----------|----------|
| `PrintHandler` | `print` | Печатает задачу в stdout |
| `LoggingHandler` | `logging` | Пишет задачу в `logging` |
| `DelayHandler` | — | `asyncio.sleep(delay)` — имитация I/O |
| `CallbackHandler` | — | Произвольный `async` колбэк |
| `FailingHandler` | — | Всегда бросает `RuntimeError` (для тестов) |
