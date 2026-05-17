"""Тесты для асинхронного исполнителя задач (Лаб 4)."""
from __future__ import annotations

import asyncio
import logging
import pytest

from src.contracts.task import Task
from src.contracts.handler import TaskHandler
from src.executor.core import TaskExecutor
from src.executor.handlers import (
    LoggingHandler,
    PrintHandler,
    DelayHandler,
    CallbackHandler,
    FailingHandler,
)
from src.inbox.task_queue import TaskQueue



def make_task(task_id: str, priority: str = "medium") -> Task:
    return Task(id=task_id, payload=f"payload-{task_id}", priority=priority)


def make_queue(*task_ids: str) -> TaskQueue:
    return TaskQueue([make_task(tid) for tid in task_ids])


@pytest.fixture
def simple_queue() -> TaskQueue:
    return make_queue("1", "2", "3")


@pytest.fixture
def print_handler() -> PrintHandler:
    return PrintHandler()


@pytest.fixture
def logging_handler() -> LoggingHandler:
    return LoggingHandler()



class TestTaskHandlerProtocol:
    """Проверка runtime-checkable Protocol TaskHandler."""

    def test_logging_handler_satisfies_protocol(self, logging_handler):
        assert isinstance(logging_handler, TaskHandler)

    def test_print_handler_satisfies_protocol(self, print_handler):
        assert isinstance(print_handler, TaskHandler)

    def test_delay_handler_satisfies_protocol(self):
        assert isinstance(DelayHandler(), TaskHandler)

    def test_callback_handler_satisfies_protocol(self):
        async def noop(task): pass
        assert isinstance(CallbackHandler(callback=noop), TaskHandler)

    def test_object_without_handle_not_handler(self):
        class NotAHandler:
            name = "bad"
        assert not isinstance(NotAHandler(), TaskHandler)

    def test_object_without_name_not_handler(self):
        class NoName:
            async def handle(self, task): pass
        assert not isinstance(NoName(), TaskHandler)

    def test_custom_class_satisfies_protocol(self):
        """Произвольный класс без наследования реализует контракт."""
        class MyHandler:
            name = "my-handler"
            async def handle(self, task: Task) -> None:
                pass
        assert isinstance(MyHandler(), TaskHandler)



class TestTaskExecutorInit:
    def test_raises_on_empty_handlers(self):
        with pytest.raises(ValueError, match="хотя бы один"):
            TaskExecutor(handlers=[])

    def test_raises_on_invalid_handler(self):
        with pytest.raises(TypeError, match="TaskHandler"):
            TaskExecutor(handlers=[object()])  # type: ignore

    def test_valid_init(self, print_handler):
        executor = TaskExecutor(handlers=[print_handler])
        assert executor is not None

    def test_multiple_handlers(self, print_handler, logging_handler):
        executor = TaskExecutor(handlers=[print_handler, logging_handler])
        assert executor is not None



class TestTaskExecutorContextManager:
    @pytest.mark.asyncio
    async def test_context_manager_enter_exit(self, print_handler):
        async with TaskExecutor(handlers=[print_handler]) as executor:
            assert executor._semaphore is not None

    @pytest.mark.asyncio
    async def test_semaphore_released_after_exit(self, print_handler):
        async with TaskExecutor(handlers=[print_handler]) as executor:
            pass
        assert executor._semaphore is None

    @pytest.mark.asyncio
    async def test_run_without_context_manager_raises(self, print_handler, simple_queue):
        executor = TaskExecutor(handlers=[print_handler])
        with pytest.raises(RuntimeError, match="контекстный менеджер"):
            await executor.run(simple_queue)

    @pytest.mark.asyncio
    async def test_stats_reset_on_enter(self, print_handler, simple_queue):
        executor = TaskExecutor(handlers=[print_handler])
        async with executor:
            await executor.run(simple_queue)
        first_processed = executor.stats["processed"]

        async with executor:
            pass
        assert executor.stats["processed"] == 0



class TestTaskExecutorRun:
    @pytest.mark.asyncio
    async def test_all_tasks_processed(self, print_handler, simple_queue):
        async with TaskExecutor(handlers=[print_handler]) as executor:
            await executor.run(simple_queue)
        assert executor.stats["processed"] == 3

    @pytest.mark.asyncio
    async def test_tasks_status_completed(self, print_handler, simple_queue):
        tasks = list(simple_queue)
        async with TaskExecutor(handlers=[print_handler]) as executor:
            await executor.run(simple_queue)
        for task in tasks:
            assert task.status == "completed"

    @pytest.mark.asyncio
    async def test_non_ready_tasks_skipped(self, print_handler):
        queue = TaskQueue()
        t1 = make_task("1")
        t2 = make_task("2")
        t2.status = "completed"
        queue.add(t1)
        queue.add(t2)

        async with TaskExecutor(handlers=[print_handler]) as executor:
            await executor.run(queue)

        assert executor.stats["processed"] == 1
        assert executor.stats["skipped"] == 1

    @pytest.mark.asyncio
    async def test_empty_queue(self, print_handler):
        queue = TaskQueue()
        async with TaskExecutor(handlers=[print_handler]) as executor:
            await executor.run(queue)
        assert executor.stats["processed"] == 0

    @pytest.mark.asyncio
    async def test_handler_error_marks_task_failed(self):
        queue = make_queue("1", "2")
        async with TaskExecutor(handlers=[FailingHandler()]) as executor:
            await executor.run(queue)

        assert executor.stats["failed"] == 2
        assert executor.stats["processed"] == 0
        for task in queue:
            assert task.status == "failed"

    @pytest.mark.asyncio
    async def test_multiple_handlers_called_in_order(self):
        call_order: list[str] = []

        async def handler_a(task: Task) -> None:
            call_order.append("A")

        async def handler_b(task: Task) -> None:
            call_order.append("B")

        ha = CallbackHandler(callback=handler_a, name="handler-a")
        hb = CallbackHandler(callback=handler_b, name="handler-b")

        queue = make_queue("1")
        async with TaskExecutor(handlers=[ha, hb]) as executor:
            await executor.run(queue)

        assert call_order == ["A", "B"]

    @pytest.mark.asyncio
    async def test_run_one(self, print_handler):
        task = make_task("solo")
        async with TaskExecutor(handlers=[print_handler]) as executor:
            await executor.run_one(task)
        assert task.status == "completed"

    @pytest.mark.asyncio
    async def test_stats_accumulated(self, print_handler):
        queue = make_queue("1", "2", "3")
        async with TaskExecutor(handlers=[print_handler]) as executor:
            await executor.run(queue)
            s = executor.stats
        assert s["processed"] == 3
        assert s["failed"] == 0
        assert s["skipped"] == 0



class TestTaskExecutorConcurrency:
    @pytest.mark.asyncio
    async def test_concurrency_respected(self):
        """Проверяем, что semaphore ограничивает параллелизм."""
        active: list[int] = []
        max_active = [0]

        async def track(task: Task) -> None:
            active.append(1)
            max_active[0] = max(max_active[0], len(active))
            await asyncio.sleep(0.02)
            active.pop()

        handler = CallbackHandler(callback=track, name="tracker")
        queue = make_queue(*[str(i) for i in range(10)])

        async with TaskExecutor(handlers=[handler], concurrency=3) as executor:
            await executor.run(queue)

        assert max_active[0] <= 3

    @pytest.mark.asyncio
    async def test_delay_handler_faster_than_sequential(self):
        """С параллелизмом 4 обработка 8 задач быстрее, чем последовательная."""
        import time
        delay = 0.05
        handler = DelayHandler(delay=delay)
        queue = make_queue(*[str(i) for i in range(8)])

        start = time.perf_counter()
        async with TaskExecutor(handlers=[handler], concurrency=4) as executor:
            await executor.run(queue)
        elapsed = time.perf_counter() - start

        sequential_time = delay * 8
        assert elapsed < sequential_time * 0.8



class TestHandlers:
    @pytest.mark.asyncio
    async def test_logging_handler(self, caplog):
        handler = LoggingHandler(level=logging.INFO)
        task = make_task("log-1")
        with caplog.at_level(logging.INFO):
            await handler.handle(task)
        assert "log-1" in caplog.text

    @pytest.mark.asyncio
    async def test_print_handler(self, capsys):
        handler = PrintHandler(template="TASK:{id}:{payload}")
        task = make_task("p1")
        await handler.handle(task)
        out = capsys.readouterr().out
        assert "TASK:p1:payload-p1" in out

    @pytest.mark.asyncio
    async def test_delay_handler_awaits(self):
        handler = DelayHandler(delay=0.01)
        task = make_task("d1")
        await handler.handle(task)

    @pytest.mark.asyncio
    async def test_callback_handler_called(self):
        called = []

        async def cb(task: Task) -> None:
            called.append(task.id)

        handler = CallbackHandler(callback=cb, name="cb")
        task = make_task("cb1")
        await handler.handle(task)
        assert called == ["cb1"]

    @pytest.mark.asyncio
    async def test_failing_handler_raises(self):
        handler = FailingHandler(error_message="boom")
        task = make_task("f1")
        with pytest.raises(RuntimeError, match="boom"):
            await handler.handle(task)
