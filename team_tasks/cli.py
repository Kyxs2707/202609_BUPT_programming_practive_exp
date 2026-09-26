"""命令行适配层：参数、展示和退出码。"""

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .errors import TaskError
from .models import STATUSES, Task
from .repository import TaskRepository
from .service import TaskService


def _positive_id(value: str) -> int:
    try:
        task_id = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("任务 ID 必须是整数。") from None
    if not 1 <= task_id <= 2**63 - 1:
        raise argparse.ArgumentTypeError("任务 ID 必须是 1 到 9223372036854775807 之间的整数。")
    return task_id


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m team_tasks", description="团队任务管理器：GitHub 双人协作 Demo"
    )
    parser.add_argument(
        "--db", type=Path, default=Path(".data/tasks.db"),
        help="SQLite 数据库路径，默认 .data/tasks.db；放在子命令之前",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="新建任务")
    add.add_argument("title", help="任务标题")
    add.add_argument("--assignee", help="负责人；省略时为未分配")

    listing = commands.add_parser("list", help="查看或筛选任务")
    listing.add_argument("--status", choices=STATUSES, help="按状态筛选")
    listing.add_argument("--assignee", help="按负责人精确筛选")
    listing.add_argument("--json", action="store_true", help="以 JSON 数组输出任务列表")

    commands.add_parser("stats", help="统计任务总数及各状态数量")

    show = commands.add_parser("show", help="查看单个任务")
    show.add_argument("task_id", type=_positive_id, metavar="ID")

    update = commands.add_parser("update", help="修改任务，至少指定一个字段")
    update.add_argument("task_id", type=_positive_id, metavar="ID")
    update.add_argument("--title", help="新标题")
    update.add_argument("--assignee", help="新负责人；--assignee= 清除负责人")
    update.add_argument("--status", choices=STATUSES, help="新状态")

    delete = commands.add_parser("delete", help="删除任务（立即生效）")
    delete.add_argument("task_id", type=_positive_id, metavar="ID")
    return parser


def _show_task(task: Task) -> None:
    print(f"ID: {task.id}")
    print(f"标题: {task.title}")
    print(f"负责人: {task.assignee or '未分配'}")
    print(f"状态: {task.status}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "update" and all(
        getattr(args, field) is None for field in ("title", "assignee", "status")
    ):
        parser.error("update 至少需要 --title、--assignee 或 --status 中的一项。")

    try:
        with TaskRepository(args.db) as repository:
            service = TaskService(repository)
            if args.command == "add":
                task = service.add_task(args.title, args.assignee)
                print(f"已创建任务 #{task.id}。")
            elif args.command == "list":
                tasks = service.list_tasks(status=args.status, assignee=args.assignee)
                if args.json:
                    print(json.dumps([
                        {
                            "id": task.id,
                            "title": task.title,
                            "assignee": task.assignee,
                            "status": task.status,
                        }
                        for task in tasks
                    ], ensure_ascii=False))
                elif tasks:
                    print("ID\t标题\t负责人\t状态")
                    for task in tasks:
                        print(f"{task.id}\t{task.title}\t{task.assignee or '未分配'}\t{task.status}")
                else:
                    print("暂无任务。")
            elif args.command == "stats":
                statistics = service.get_statistics()
                for key in ("total", *STATUSES):
                    print(f"{key}: {statistics[key]}")
            elif args.command == "show":
                _show_task(service.get_task(args.task_id))
            elif args.command == "update":
                task = service.update_task(
                    args.task_id, title=args.title,
                    assignee=args.assignee, status=args.status,
                )
                print(f"已更新任务 #{task.id}。")
            elif args.command == "delete":
                service.delete_task(args.task_id)
                print(f"已删除任务 #{args.task_id}。")
    except TaskError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    return 0
