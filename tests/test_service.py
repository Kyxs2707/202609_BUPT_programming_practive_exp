"""验证业务规则，与命令行展示解耦。"""

import tempfile
import unittest
from pathlib import Path

from team_tasks.errors import TaskNotFoundError, ValidationError
from team_tasks.models import STATUSES
from team_tasks.repository import TaskRepository
from team_tasks.service import TaskService


class ServiceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repository = TaskRepository(Path(temporary.name) / "tasks.db")
        self.addCleanup(repository.close)
        self.service = TaskService(repository)

    def test_create_trims_title_and_assignee(self):
        task = self.service.add_task("  完善文档  ", " Alice ")
        self.assertEqual((task.title, task.assignee, task.status), ("完善文档", "Alice", "todo"))

    def test_missing_or_blank_assignee_means_unassigned(self):
        for value in (None, "", "  "):
            with self.subTest(value=value):
                self.assertIsNone(self.service.add_task("任务", value).assignee)

    def test_rejects_empty_or_non_text_titles(self):
        for value in ("", " \t\n ", None, 42):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.service.add_task(value)
        self.assertEqual(self.service.list_tasks(), [])

    def test_rejects_non_text_assignee(self):
        with self.assertRaises(ValidationError):
            self.service.add_task("任务", 42)

    def test_partial_update_preserves_unspecified_fields(self):
        task = self.service.add_task("任务", "Alice")
        updated = self.service.update_task(task.id, status="doing")
        self.assertEqual((updated.title, updated.assignee, updated.status), ("任务", "Alice", "doing"))
        updated = self.service.update_task(task.id, title=" 新任务 ", assignee=" Bob ", status="done")
        self.assertEqual((updated.title, updated.assignee, updated.status), ("新任务", "Bob", "done"))

    def test_blank_assignee_clears_assignment(self):
        task = self.service.add_task("任务", "Alice")
        updated = self.service.update_task(task.id, assignee="")
        self.assertIsNone(updated.assignee)
        self.assertIsNone(self.service.get_task(task.id).assignee)

    def test_all_status_transitions_are_allowed(self):
        task = self.service.add_task("任务")
        for source in STATUSES:
            for destination in STATUSES:
                with self.subTest(source=source, destination=destination):
                    self.service.update_task(task.id, status=source)
                    updated = self.service.update_task(task.id, status=destination)
                    self.assertEqual(updated.status, destination)

    def test_invalid_status_is_rejected_in_update_and_filter(self):
        task = self.service.add_task("任务")
        for value in ("invalid", "DONE", ""):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    self.service.update_task(task.id, status=value)
                with self.assertRaises(ValidationError):
                    self.service.list_tasks(status=value)
        self.assertEqual(self.service.get_task(task.id), task)

    def test_invalid_update_leaves_all_fields_unchanged(self):
        task = self.service.add_task("任务", "Alice")
        with self.assertRaises(ValidationError):
            self.service.update_task(task.id, title="", assignee="Bob", status="done")
        self.assertEqual(self.service.get_task(task.id), task)

    def test_update_requires_at_least_one_field(self):
        task = self.service.add_task("任务")
        with self.assertRaises(ValidationError):
            self.service.update_task(task.id)

    def test_missing_tasks_raise_domain_error(self):
        with self.assertRaises(TaskNotFoundError):
            self.service.get_task(99)
        with self.assertRaises(TaskNotFoundError):
            self.service.update_task(99, status="done")
        with self.assertRaises(TaskNotFoundError):
            self.service.delete_task(99)

    def test_invalid_ids_are_rejected(self):
        for value in (0, -1, "1", True, 1.5, 2**63):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    self.service.get_task(value)
                with self.assertRaises(ValidationError):
                    self.service.delete_task(value)

    def test_filter_trims_assignee_and_rejects_empty_name(self):
        task = self.service.add_task("任务", "Alice")
        self.assertEqual(self.service.list_tasks(status="todo", assignee=" Alice "), [task])
        with self.assertRaises(ValidationError):
            self.service.list_tasks(assignee=" ")

    def test_delete_removes_task(self):
        task = self.service.add_task("任务")
        self.service.delete_task(task.id)
        self.assertEqual(self.service.list_tasks(), [])
        with self.assertRaises(TaskNotFoundError):
            self.service.get_task(task.id)
