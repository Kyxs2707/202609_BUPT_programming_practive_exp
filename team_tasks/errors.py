"""可直接向用户解释的应用错误。"""


class TaskError(Exception):
    """所有预期应用错误的基类。"""


class ValidationError(TaskError):
    """输入违反业务规则。"""


class TaskNotFoundError(TaskError):
    """指定的任务不存在。"""

    def __init__(self, task_id: int) -> None:
        super().__init__(f"任务 #{task_id} 不存在。")


class StorageError(TaskError):
    """数据库初始化、读取或写入失败。"""
