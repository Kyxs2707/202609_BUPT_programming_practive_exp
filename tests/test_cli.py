"""通过独立 Python 进程验证命令、输出、退出码及跨进程持久化。"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.db = self.directory / "数据 文件夹" / "tasks.db"
        self.environment = os.environ.copy()
        self.environment["PYTHONIOENCODING"] = "utf-8"
        self.environment["PYTHONUTF8"] = "1"
        self.environment["PYTHONPATH"] = str(ROOT)

    def run_cli(self, *arguments, default_db=False):
        command = [sys.executable, "-m", "team_tasks"]
        if not default_db:
            command += ["--db", str(self.db)]
        return subprocess.run(
            command + list(arguments), cwd=self.directory, env=self.environment,
            text=True, encoding="utf-8", capture_output=True, timeout=15,
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    def assert_failure(self, result, code):
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_help_does_not_create_database(self):
        for arguments in (("--help",), ("update", "--help"), ("list", "--help")):
            with self.subTest(arguments=arguments):
                result = self.run_cli(*arguments, default_db=True)
                self.assert_success(result)
                self.assertIn("--", result.stdout)
                if arguments[0] == "list":
                    self.assertIn("--json", result.stdout)
        self.assertFalse((self.directory / ".data").exists())

    def test_default_database_is_relative_to_working_directory(self):
        self.assert_success(self.run_cli("add", "默认路径", default_db=True))
        self.assertTrue((self.directory / ".data" / "tasks.db").is_file())
        result = self.run_cli("show", "1", default_db=True)
        self.assert_success(result)
        self.assertIn("默认路径", result.stdout)

    def test_full_lifecycle_across_independent_processes(self):
        created = self.run_cli("add", "完善协作指南", "--assignee", "Alice")
        self.assert_success(created)
        self.assertEqual(created.stdout.strip(), "已创建任务 #1。")
        shown = self.run_cli("show", "1")
        self.assert_success(shown)
        self.assertEqual(shown.stdout.splitlines(), ["ID: 1", "标题: 完善协作指南", "负责人: Alice", "状态: todo"])
        self.assert_success(self.run_cli("update", "1", "--status", "doing"))
        listing = self.run_cli("list", "--status", "doing", "--assignee", "Alice")
        self.assert_success(listing)
        self.assertIn("1\t完善协作指南\tAlice\tdoing", listing.stdout)
        self.assert_success(self.run_cli("update", "1", "--status", "done"))
        self.assert_success(self.run_cli("delete", "1"))
        self.assertEqual(self.run_cli("list").stdout.strip(), "暂无任务。")
        self.assert_failure(self.run_cli("show", "1"), 1)

    def test_list_combines_filters_and_orders_by_id(self):
        self.assert_success(self.run_cli("add", "任务一", "--assignee", "Alice"))
        self.assert_success(self.run_cli("add", "任务二", "--assignee", "Bob"))
        self.assert_success(self.run_cli("add", "任务三", "--assignee", "Alice"))
        self.assert_success(self.run_cli("add", "任务四"))
        self.assert_success(self.run_cli("update", "3", "--status", "done"))
        result = self.run_cli("list")
        self.assert_success(result)
        self.assertEqual(result.stdout.splitlines(), [
            "ID\t标题\t负责人\t状态",
            "1\t任务一\tAlice\ttodo",
            "2\t任务二\tBob\ttodo",
            "3\t任务三\tAlice\tdone",
            "4\t任务四\t未分配\ttodo",
        ])
        result = self.run_cli("list", "--status", "todo", "--assignee", "Alice")
        self.assert_success(result)
        self.assertEqual(result.stdout.splitlines()[1:], ["1\t任务一\tAlice\ttodo"])
        result = self.run_cli("list", "--status", "doing")
        self.assert_success(result)
        self.assertEqual(result.stdout.strip(), "暂无任务。")

    def test_list_json_preserves_fields_types_and_unicode(self):
        title = '检查"输出"与\\路径\n第二行\t内容'
        self.assert_success(self.run_cli("add", title, "--assignee", "小明"))
        self.assert_success(self.run_cli("add", "待分配任务"))
        result = self.run_cli("list", "--json")
        self.assert_success(result)
        tasks = json.loads(result.stdout)
        self.assertEqual(tasks, [
            {"id": 1, "title": title, "assignee": "小明", "status": "todo"},
            {"id": 2, "title": "待分配任务", "assignee": None, "status": "todo"},
        ])
        for task in tasks:
            self.assertIs(type(task["id"]), int)
        self.assertIn("检查", result.stdout)
        self.assertIn("小明", result.stdout)
        self.assertIn("待分配任务", result.stdout)

    def test_list_json_combines_filters_and_orders_by_id(self):
        for task_id, (assignee, status) in enumerate((
            ("Alice", "doing"), ("Bob", "doing"), ("Alice", "todo"),
            ("Alice", "doing"), ("Alice", "done"),
        ), start=1):
            self.assert_success(self.run_cli("add", f"任务{task_id}", "--assignee", assignee))
            self.assert_success(self.run_cli("update", str(task_id), "--status", status))
        cases = (
            ((), [1, 2, 3, 4, 5]),
            (("--status", "doing"), [1, 2, 4]),
            (("--assignee", "Alice"), [1, 3, 4, 5]),
            (("--status", "doing", "--assignee", "Alice"), [1, 4]),
            (("--status", "doing", "--assignee", " Alice "), [1, 4]),
            (("--assignee", "alice"), []),
        )
        for arguments, expected_ids in cases:
            with self.subTest(arguments=arguments):
                result = self.run_cli("list", "--json", *arguments)
                self.assert_success(result)
                tasks = json.loads(result.stdout)
                self.assertEqual([task["id"] for task in tasks], expected_ids)
                if "--status" in arguments:
                    self.assertTrue(all(task["status"] == "doing" for task in tasks))
                if "--assignee" in arguments:
                    self.assertTrue(all(task["assignee"] == "Alice" for task in tasks))

    def test_empty_json_list_is_successful(self):
        result = self.run_cli("list", "--json")
        self.assert_success(result)
        self.assertEqual(json.loads(result.stdout), [])
        self.assertEqual(result.stdout.strip(), "[]")

    def test_json_list_without_matches_is_successful(self):
        self.assert_success(self.run_cli("add", "已有任务", "--assignee", "Alice"))
        for arguments in (
            ("--status", "done"), ("--assignee", "Bob"),
            ("--status", "doing", "--assignee", "Alice"),
        ):
            with self.subTest(arguments=arguments):
                result = self.run_cli("list", *arguments, "--json")
                self.assert_success(result)
                self.assertEqual(json.loads(result.stdout), [])
                self.assertEqual(result.stdout.strip(), "[]")

    def test_empty_list_is_successful(self):
        result = self.run_cli("list")
        self.assert_success(result)
        self.assertEqual(result.stdout.strip(), "暂无任务。")

    def test_invalid_arguments_exit_two_without_creating_database(self):
        cases = (
            (), ("unknown",), ("add",), ("show", "abc"), ("show", "0"),
            ("delete", "-1"), ("show", str(2**63)),
            ("list", "--status", "invalid"), ("update", "1", "--status", "DONE"),
            ("update", "1"), ("list", "--unknown"),
            ("list", "--json", "--status", "invalid"),
            ("list", "--json", "--status"), ("list", "--json", "--assignee"),
            ("list", "--json", "--unknown"),
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                self.assert_failure(self.run_cli(*arguments), 2)
        self.assertFalse(self.db.exists())

    def test_empty_title_is_business_error(self):
        for title in ("", "   "):
            with self.subTest(title=title):
                result = self.run_cli("add", title)
                self.assert_failure(result, 1)
                self.assertIn("标题不能为空", result.stderr)
        self.assertEqual(self.run_cli("list").stdout.strip(), "暂无任务。")

    def test_missing_tasks_exit_one(self):
        for arguments in (("show", "99"), ("delete", "99"), ("update", "99", "--status", "doing")):
            with self.subTest(arguments=arguments):
                result = self.run_cli(*arguments)
                self.assert_failure(result, 1)
                self.assertIn("任务 #99 不存在", result.stderr)

    def test_title_update_and_assignment_clear(self):
        self.assert_success(self.run_cli("add", "旧标题", "--assignee", "Alice"))
        self.assert_success(self.run_cli("update", "1", "--title", "新标题", "--assignee="))
        shown = self.run_cli("show", "1")
        self.assert_success(shown)
        self.assertIn("标题: 新标题", shown.stdout)
        self.assertIn("负责人: 未分配", shown.stdout)

    def test_invalid_update_does_not_change_saved_task(self):
        self.assert_success(self.run_cli("add", "原始标题", "--assignee", "Alice"))
        self.assert_failure(self.run_cli("update", "1", "--title=", "--assignee", "Bob"), 1)
        result = self.run_cli("show", "1")
        self.assert_success(result)
        self.assertIn("标题: 原始标题", result.stdout)
        self.assertIn("负责人: Alice", result.stdout)

    def test_blank_assignee_filter_is_business_error(self):
        for options in ((), ("--json",)):
            for assignee in ("", "   "):
                with self.subTest(options=options, assignee=assignee):
                    result = self.run_cli("list", *options, f"--assignee={assignee}")
                    self.assert_failure(result, 1)
                    self.assertIn("筛选负责人不能为空", result.stderr)

    def test_corrupt_database_reports_error_without_traceback(self):
        self.db.parent.mkdir()
        self.db.write_bytes(b"invalid database contents")
        for options in ((), ("--json",)):
            with self.subTest(options=options):
                result = self.run_cli("list", *options)
                self.assert_failure(result, 1)
                self.assertIn("无法打开或初始化数据库", result.stderr)
                self.assertEqual(self.db.read_bytes(), b"invalid database contents")

    def test_file_in_parent_path_reports_storage_error(self):
        self.db.parent.write_text("keep", encoding="utf-8")
        result = self.run_cli("add", "任务")
        self.assert_failure(result, 1)
        self.assertIn("无法打开或初始化数据库", result.stderr)
        self.assertEqual(self.db.parent.read_text(encoding="utf-8"), "keep")
