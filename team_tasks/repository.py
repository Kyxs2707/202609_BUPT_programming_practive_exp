"""SQLite 存储：负责 SQL、事务、连接生命周期和存储错误转换。"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .errors import StorageError
from .models import Task


class TaskRepository:
    def __init__(self, db_path: str | Path) -> None:
        path = Path(db_path).expanduser()
        connection = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(path)
            connection.row_factory = sqlite3.Row
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL CHECK (length(trim(title)) > 0),
                        assignee TEXT,
                        status TEXT NOT NULL DEFAULT 'todo'
                            CHECK (status IN ('todo', 'doing', 'done'))
                    )
                    """
                )
        except (OSError, sqlite3.Error) as exc:
            if connection is not None:
                connection.close()
            raise StorageError(f"无法打开或初始化数据库 {path}：{exc}") from exc
        self._connection = connection

    def __enter__(self) -> "TaskRepository":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        self._connection.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            with self._connection:
                yield self._connection
        except sqlite3.Error as exc:
            raise StorageError(f"数据库操作失败：{exc}") from exc

    @staticmethod
    def _to_task(row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            assignee=row["assignee"],
            status=row["status"],
        )

    def create(self, title: str, assignee: str | None) -> Task:
        with self._transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO tasks (title, assignee, status) VALUES (?, ?, ?)",
                (title, assignee, "todo"),
            )
            task_id = cursor.lastrowid
        return Task(id=task_id, title=title, assignee=assignee, status="todo")

    def list_tasks(
        self, *, status: str | None = None, assignee: str | None = None
    ) -> list[Task]:
        clauses = []
        parameters = []
        if status is not None:
            clauses.append("status = ?")
            parameters.append(status)
        if assignee is not None:
            clauses.append("assignee = ?")
            parameters.append(assignee)
        query = "SELECT id, title, assignee, status FROM tasks"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id ASC"
        with self._transaction() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._to_task(row) for row in rows]

    def get(self, task_id: int) -> Task | None:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT id, title, assignee, status FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
        return None if row is None else self._to_task(row)

    def update(self, task: Task) -> bool:
        with self._transaction() as connection:
            cursor = connection.execute(
                "UPDATE tasks SET title = ?, assignee = ?, status = ? WHERE id = ?",
                (task.title, task.assignee, task.status, task.id),
            )
        return cursor.rowcount > 0

    def delete(self, task_id: int) -> bool:
        with self._transaction() as connection:
            cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0
