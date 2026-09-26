"""业务层：集中校验任务规则，既不解析命令行，也不拼接 SQL。"""

from dataclasses import replace

from .errors import TaskNotFoundError, ValidationError
from .models import STATUSES, Task
from .repository import TaskRepository


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    @staticmethod
    def _title(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("标题不能为空。")
        return value.strip()

    @staticmethod
    def _assignee(value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValidationError("负责人必须是文本。")
        return value.strip() or None

    @staticmethod
    def _status(value: str) -> str:
        if value not in STATUSES:
            raise ValidationError("状态必须是 todo、doing 或 done。")
        return value

    @staticmethod
    def _task_id(value: int) -> int:
        # bool 是 int 的子类，但不能作为任务 ID；上限对应 SQLite INTEGER。
        if type(value) is not int or not 1 <= value <= 2**63 - 1:
            raise ValidationError("任务 ID 必须是 1 到 9223372036854775807 之间的整数。")
        return value

    def add_task(self, title: str, assignee: str | None = None) -> Task:
        return self._repository.create(self._title(title), self._assignee(assignee))

    def list_tasks(
        self, *, status: str | None = None, assignee: str | None = None
    ) -> list[Task]:
        if status is not None:
            status = self._status(status)
        if assignee is not None:
            assignee = self._assignee(assignee)
            if assignee is None:
                raise ValidationError("筛选负责人不能为空。")
        return self._repository.list_tasks(status=status, assignee=assignee)

    def get_task(self, task_id: int) -> Task:
        task = self._repository.get(self._task_id(task_id))
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def update_task(
        self,
        task_id: int,
        *,
        title: str | None = None,
        assignee: str | None = None,
        status: str | None = None,
    ) -> Task:
        if title is None and assignee is None and status is None:
            raise ValidationError("更新至少需要提供标题、负责人或状态中的一项。")
        current = self.get_task(task_id)
        updated = replace(
            current,
            title=current.title if title is None else self._title(title),
            assignee=current.assignee if assignee is None else self._assignee(assignee),
            status=current.status if status is None else self._status(status),
        )
        if not self._repository.update(updated):
            raise TaskNotFoundError(task_id)
        return updated

    def delete_task(self, task_id: int) -> None:
        if not self._repository.delete(self._task_id(task_id)):
            raise TaskNotFoundError(task_id)
