"""Интерфейс командной строки для платформы обработки задач."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import typer
from typer import Typer

from src.inbox.core import TaskProcessor
from src.inbox.task_queue import TaskQueue
from src.sources.repository import REGISTRY

cli = Typer(
    no_args_is_help=True,
    help="Платформа обработки задач: приём, очередь и асинхронное выполнение.",
)


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@cli.command("plugins")
def plugins_list() -> None:
    """Показать список доступных плагинов источников задач."""
    typer.echo("Available plugins:")
    for name in sorted(REGISTRY):
        typer.echo(f"  • {name}")


def _build_sources(stdin: bool, jsonl: list[Path]) -> list[Any]:
    """Создать экземпляры источников на основе аргументов командной строки."""
    sources: list[Any] = []
    if stdin:
        sources.append(REGISTRY["stdin"]())
    for path in jsonl:
        sources.append(REGISTRY["file-jsonl"](path))
    return sources


@cli.command("read")
def read(
    stdin: bool = typer.Option(False, "--stdin", help="Read messages from stdin"),
    jsonl: list[Path] = typer.Option(
        help="Path to a .jsonl file with tasks",
        default_factory=list,
        exists=True,
        dir_okay=False,
        readable=True,
    ),
    contains: str | None = typer.Option(None, "--contains", help="Substring filter on payload"),
) -> None:
    """Прочитать и вывести задачи из указанных источников."""
    raw_sources = _build_sources(stdin, jsonl)
    inbox = TaskProcessor(raw_sources)
    count = 0
    for task in inbox.iter_task():
        if contains and contains not in str(task.payload):
            continue
        count += 1
        typer.echo(f"[{task.id}] {task.payload}")
    typer.echo(f"\nTotal tasks: {count}")


@cli.command("execute")
def execute(
    stdin: bool = typer.Option(False, "--stdin", help="Read tasks from stdin"),
    jsonl: list[Path] = typer.Option(
        help="Path to a .jsonl file with tasks",
        default_factory=list,
        exists=True,
        dir_okay=False,
        readable=True,
    ),
    contains: str | None = typer.Option(None, "--contains", help="Substring filter on payload"),
    concurrency: int = typer.Option(4, "--concurrency", "-c", help="Max parallel tasks"),
    handler: list[str] = typer.Option(
        ["print"],
        "--handler",
        "-H",
        help="Handler(s) to use: print, logging. Can be repeated.",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """
    Асинхронно выполнить задачи из указанных источников.

    Задачи сначала загружаются в TaskQueue, затем обрабатываются
    асинхронным исполнителем TaskExecutor с выбранными обработчиками.

    Примеры:

        python -m src execute --jsonl tasks.jsonl

        python -m src execute --jsonl tasks.jsonl -H print -H logging -c 8

        echo "1:pay:desc:high" | python -m src execute --stdin -H logging -v
    """
    _configure_logging(verbose)

    from src.executor.core import TaskExecutor
    from src.executor.handlers import LoggingHandler, PrintHandler

    handler_map = {
        "print": PrintHandler(),
        "logging": LoggingHandler(),
    }
    selected_handlers = []
    for h_name in handler:
        if h_name not in handler_map:
            typer.echo(
                f"[ERROR] Неизвестный обработчик '{h_name}'. "
                f"Доступные: {', '.join(handler_map)}",
                err=True,
            )
            raise typer.Exit(code=1)
        selected_handlers.append(handler_map[h_name])

    raw_sources = _build_sources(stdin, jsonl)
    inbox = TaskProcessor(raw_sources)
    queue = TaskQueue()
    for task in inbox.iter_task():
        if contains and contains not in str(task.payload):
            continue
        queue.add(task)

    if len(queue) == 0:
        typer.echo("Нет задач для выполнения.")
        return

    typer.echo(f"Загружено задач: {len(queue)}")
    typer.echo(f"Обработчики: {', '.join(h.name for h in selected_handlers)}")
    typer.echo(f"Параллелизм: {concurrency}\n")

    async def _run() -> dict[str, int]:
        async with TaskExecutor(
            handlers=selected_handlers,
            concurrency=concurrency,
        ) as executor:
            await executor.run(queue)
            return executor.stats

    stats = asyncio.run(_run())

    typer.echo(
        f"\n Готово. Обработано: {stats['processed']}  "
        f"Ошибок: {stats['failed']}  "
        f"Пропущено: {stats['skipped']}"
    )
