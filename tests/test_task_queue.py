"""Тесты для очереди задач TaskQueue."""
import pytest

from src.contracts.task import Task
from src.inbox.task_queue import TaskQueue


def create_sample_tasks():
    """Возвращает список тестовых задач."""
    t1 = Task(id="1", payload="data1", priority="high")
    t2 = Task(id="2", payload="data2", priority="medium")
    t3 = Task(id="3", payload="data3", priority="high")
    t4 = Task(id="4", payload="data4", priority="critical")
    t1.status = "pending"
    t2.status = "in_progress"
    t3.status = "completed"
    t4.status = "blocked"
    return [t1, t2, t3, t4]


class TestTaskQueueInit:
    def test_empty_queue(self):
        queue = TaskQueue()
        assert len(queue) == 0
        assert list(queue) == []

    def test_queue_from_iterable(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        assert len(queue) == 4
        assert [t.id for t in queue] == ["1", "2", "3", "4"]

    def test_queue_from_generator(self):
        def gen():
            yield Task(id="1", payload="a")
            yield Task(id="2", payload="b")
        queue = TaskQueue(gen())
        assert len(queue) == 2


class TestTaskQueueAdd:
    def test_add_single(self):
        queue = TaskQueue()
        task = Task(id="1", payload="test")
        queue.add(task)
        assert len(queue) == 1
        assert task in queue

    def test_add_all(self):
        tasks = create_sample_tasks()
        queue = TaskQueue()
        queue.add_all(tasks)
        assert len(queue) == 4

    def test_add_all_empty(self):
        queue = TaskQueue()
        queue.add_all([])
        assert len(queue) == 0


class TestTaskQueueIteration:
    def test_iteration_protocol(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        ids = [task.id for task in queue]
        assert ids == ["1", "2", "3", "4"]

    def test_repeated_iteration(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        first_pass = [task.id for task in queue]
        second_pass = [task.id for task in queue]
        assert first_pass == second_pass == ["1", "2", "3", "4"]

    def test_iteration_does_not_modify_queue(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        list(queue)
        assert len(queue) == 4

    def test_iterator_raises_stop_iteration(self):
        queue = TaskQueue([Task(id="1", payload="x")])
        it = iter(queue)
        assert next(it).id == "1"
        with pytest.raises(StopIteration):
            next(it)

    def test_for_loop_handles_stop_iteration(self):
        queue = TaskQueue([Task(id="1", payload="x")])
        count = 0
        for _ in queue:
            count += 1
        assert count == 1
        for _ in queue:
            count += 1
        assert count == 2

    def test_compatibility_with_list(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        assert list(queue) == tasks

    def test_compatibility_with_sum(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        assert sum(1 for _ in queue) == 4


class TestTaskQueueContains:
    def test_contains_true(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks[:2])
        assert tasks[0] in queue

    def test_contains_false(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks[:2])
        assert tasks[2] not in queue


class TestTaskQueueLazyFilters:
    def test_iter_filtered_returns_generator(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = queue.iter_filtered(status="pending")
        assert not isinstance(result, list)
        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")

    def test_filter_by_status_pending(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.iter_filtered(status="pending"))
        assert len(result) == 1
        assert result[0].id == "1"

    def test_filter_by_status_in_progress(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.iter_filtered(status="in_progress"))
        assert len(result) == 1
        assert result[0].id == "2"

    def test_filter_by_status_completed(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.iter_filtered(status="completed"))
        assert len(result) == 1
        assert result[0].id == "3"

    def test_filter_by_priority_high(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.iter_filtered(priority="high"))
        assert len(result) == 2
        assert {t.id for t in result} == {"1", "3"}

    def test_filter_by_priority_critical(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.iter_filtered(priority="critical"))
        assert len(result) == 1
        assert result[0].id == "4"

    def test_filter_by_status_and_priority(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.iter_filtered(status="pending", priority="high"))
        assert len(result) == 1
        assert result[0].id == "1"

    def test_filter_with_custom_predicate(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)

        def is_high_or_critical(task):
            return task.priority in ("high", "critical")

        result = list(queue.iter_filtered(predicate=is_high_or_critical))
        assert len(result) == 3
        assert {t.id for t in result} == {"1", "3", "4"}

    def test_filter_no_matches(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.iter_filtered(status="nonexistent"))
        assert result == []


class TestTaskQueueConvenienceFilters:
    def test_pending_tasks(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.pending_tasks())
        assert len(result) == 1
        assert result[0].id == "1"

    def test_in_progress_tasks(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.in_progress_tasks())
        assert len(result) == 1
        assert result[0].id == "2"

    def test_completed_tasks(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.completed_tasks())
        assert len(result) == 1
        assert result[0].id == "3"

    def test_high_priority_tasks(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.high_priority_tasks())
        assert len(result) == 2
        assert {t.id for t in result} == {"1", "3"}

    def test_critical_priority_tasks(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.critical_priority_tasks())
        assert len(result) == 1
        assert result[0].id == "4"

    def test_ready_to_execute(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        result = list(queue.ready_to_execute())
        assert len(result) == 2
        assert {t.id for t in result} == {"1", "2"}


class TestTaskQueueFirst:
    def test_first_without_predicate(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        assert queue.first().id == "1"

    def test_first_with_predicate(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        assert queue.first(lambda t: t.id == "3").id == "3"

    def test_first_not_found(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        assert queue.first(lambda t: t.id == "99") is None

    def test_first_empty_queue(self):
        queue = TaskQueue()
        assert queue.first() is None
        assert queue.first(lambda t: t.id == "1") is None


class TestTaskQueueStopIterationExplicit:
    """Специальные тесты, демонстрирующие явную работу StopIteration."""
    def test_manual_next_with_stop_iteration(self):
        queue = TaskQueue([Task(id="1", payload="a"), Task(id="2", payload="b")])
        it = iter(queue)
        assert next(it).id == "1"
        assert next(it).id == "2"
        with pytest.raises(StopIteration):
            next(it)

    def test_multiple_iterators_independent(self):
        queue = TaskQueue([Task(id="1", payload="a"), Task(id="2", payload="b")])
        it1 = iter(queue)
        it2 = iter(queue)
        assert next(it1).id == "1"
        assert next(it1).id == "2"
        with pytest.raises(StopIteration):
            next(it1)
        assert next(it2).id == "1"
        assert next(it2).id == "2"
        with pytest.raises(StopIteration):
            next(it2)


class TestTaskQueueRepr:
    def test_repr_empty(self):
        queue = TaskQueue()
        assert repr(queue) == "TaskQueue(tasks=0)"

    def test_repr_with_tasks(self):
        tasks = create_sample_tasks()
        queue = TaskQueue(tasks)
        assert repr(queue) == "TaskQueue(tasks=4)"