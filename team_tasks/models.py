"""各层共享的任务模型，不依赖命令行或数据库。"""

from dataclasses import dataclass


STATUSES = ("todo", "doing", "done")


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    assignee: str | None
    status: str
