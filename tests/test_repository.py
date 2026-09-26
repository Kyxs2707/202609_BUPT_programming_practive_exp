"""使用临时 SQLite 文件验证真实持久化和事务行为。"""

import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from team_tasks.errors import StorageError
from team_tasks.repository import TaskRepository


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.path = self.directory / "数据 文件夹" / "tasks.db"
        self.repository = TaskRepository(self.path)
        self.addCleanup(self.repository.close)

    def test_initializes_parent_directory_and_empty_database(self):
        self.assertTrue(self.path.is_file())
        self.assertEqual(self.repository.list_tasks(), [])
        self.assertIsNone(self.repository.get(99))

    def test_create_persists_across_connections(self):
        task = self.repository.create("编写文档", "Alice")
        self.assertEqual(task.id, 1)
        self.assertEqual(task.status, "todo")
        with TaskRepository(self.path) as reopened:
            self.assertEqual(reopened.get(task.id), task)

    def test_filters_combine_with_and_and_keep_id_order(self):
        first = self.repository.create("任务一", "Alice")
        second = self.repository.create("任务二", "Bob")
        third = self.repository.create("任务三", "Alice")
        self.repository.update(replace(third, status="doing"))
        self.assertEqual(self.repository.list_tasks(assignee="Alice"), [first, replace(third, status="doing")])
        self.assertEqual(self.repository.list_tasks(status="todo", assignee="Alice"), [first])
        self.assertEqual(self.repository.list_tasks(status="todo"), [first, second])
        self.assertEqual(self.repository.list_tasks(assignee="alice"), [])

    def test_update_and_missing_record(self):
        task = self.repository.create("原始标题", None)
        updated = replace(task, title="修改标题", assignee="Bob", status="done")
        self.assertTrue(self.repository.update(updated))
        self.assertEqual(self.repository.get(task.id), updated)
        self.assertFalse(self.repository.update(replace(updated, id=99)))

    def test_count_by_status_includes_zeros_for_empty_database(self):
        self.assertEqual(self.repository.count_by_status(), {
            "todo": 0, "doing": 0, "done": 0,
        })

    def test_count_by_status_counts_all_tasks_without_changing_them(self):
        for status in ("todo", "done", "doing", "done", "todo", "done"):
            task = self.repository.create("重复标题", None)
            self.repository.update(replace(task, status=status))
        before = self.repository.list_tasks()
        counts = self.repository.count_by_status()
        self.assertEqual(counts, {"todo": 2, "doing": 1, "done": 3})
        for count in counts.values():
            self.assertIs(type(count), int)
        self.assertEqual(self.repository.list_tasks(), before)

    def test_count_by_status_tracks_updates_deletions_and_missing_states(self):
        task = self.repository.create("待办任务", "Alice")
        self.assertEqual(self.repository.count_by_status(), {
            "todo": 1, "doing": 0, "done": 0,
        })
        self.assertTrue(self.repository.update(replace(task, status="doing")))
        self.assertEqual(self.repository.count_by_status(), {
            "todo": 0, "doing": 1, "done": 0,
        })
        self.assertTrue(self.repository.delete(task.id))
        self.assertEqual(self.repository.count_by_status(), {
            "todo": 0, "doing": 0, "done": 0,
        })

    def test_count_by_status_converts_query_errors(self):
        connection = sqlite3.connect(self.path)
        self.addCleanup(connection.close)
        with connection:
            connection.execute("DROP TABLE tasks")
        with self.assertRaisesRegex(StorageError, "数据库操作失败"):
            self.repository.count_by_status()

    def test_delete_does_not_reuse_ids(self):
        first = self.repository.create("任务一", None)
        self.assertTrue(self.repository.delete(first.id))
        self.assertFalse(self.repository.delete(first.id))
        self.assertIsNone(self.repository.get(first.id))
        second = self.repository.create("任务二", None)
        self.assertGreater(second.id, first.id)

    def test_sql_values_are_stored_as_literal_text(self):
        title = "任务'); DROP TABLE tasks; --"
        assignee = "O'Reilly"
        task = self.repository.create(title, assignee)
        self.assertEqual(self.repository.get(task.id), task)
        self.assertEqual(self.repository.list_tasks(assignee=assignee), [task])
        self.assertEqual(self.repository.list_tasks(assignee="' OR 1=1 --"), [])

    def test_failed_write_rolls_back_and_connection_remains_usable(self):
        task = self.repository.create("原始标题", "Alice")
        with self.assertRaises(StorageError):
            self.repository.update(replace(task, title="不应保存", status="invalid"))
        self.assertEqual(self.repository.get(task.id), task)
        self.assertTrue(self.repository.update(replace(task, status="done")))

    def test_file_in_parent_path_is_reported_as_storage_error(self):
        blocked_parent = self.directory / "a-file"
        blocked_parent.write_text("keep", encoding="utf-8")
        with self.assertRaises(StorageError):
            TaskRepository(blocked_parent / "tasks.db")
        self.assertEqual(blocked_parent.read_text(encoding="utf-8"), "keep")

    def test_corrupt_database_is_not_replaced(self):
        path = self.directory / "corrupt.db"
        content = b"this is not a SQLite database"
        path.write_bytes(content)
        with self.assertRaises(StorageError):
            TaskRepository(path)
        self.assertEqual(path.read_bytes(), content)

    def test_open_failure_is_converted_to_application_error(self):
        # 权限位在 Windows、Linux 上行为不同，用驱动错误模拟无法打开。
        with patch("team_tasks.repository.sqlite3.connect", side_effect=sqlite3.OperationalError("unable to open database file")):
            with self.assertRaisesRegex(StorageError, "无法打开或初始化数据库"):
                TaskRepository(self.directory / "unavailable.db")
