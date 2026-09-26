# 接口说明

## 通用约定

```text
python -m team_tasks [--db PATH] <command> [arguments]
```

- 从仓库根目录运行；默认数据库是**当前工作目录**下的 `.data/tasks.db`。
- 全局 `--db PATH` 放在子命令前，支持相对路径和绝对路径；路径包含空格时使用引号。
- 用 `python -m team_tasks --help` 查看总帮助，用 `python -m team_tasks update --help` 查看子命令帮助。
- 正常结果写到 stdout，错误说明写到 stderr。
- 标题及负责人去除首尾空白；状态严格区分大小写。
- `ID` 为 1 到 `9223372036854775807` 的整数。删除后 ID 不复用。

## 命令

### add

```console
python -m team_tasks add "完善协作指南" --assignee Alice
```

`TITLE` 必填，不能为空或全为空白。`--assignee` 可省略，省略或空文本表示未分配。成功返回新任务的 ID：

```text
已创建任务 #1。
```

新任务状态固定为 `todo`。上面的 ID 仅为在新库上的示例。

### list

```console
python -m team_tasks list
python -m team_tasks list --status doing
python -m team_tasks list --assignee Alice
python -m team_tasks list --status doing --assignee Alice
python -m team_tasks list --json
python -m team_tasks list --json --status doing --assignee Alice
```

`--status` 可取 `todo`、`doing`、`done`。负责人按去除首尾空白后的文本精确匹配，区分大小写；同时提供两个条件时取交集。空负责人筛选报业务错误。

结果按 ID 升序。不加 `--json` 时，用制表符分隔列；示例如下，视觉列宽取决于终端：

```text
ID	标题	负责人	状态
1	完善协作指南	Alice	doing
```

文本模式下，未分配负责人显示 `未分配`。无结果时只输出 `暂无任务。`，退出码仍为 0。

提供 `--json` 时，成功结果的 stdout 仅包含合法 JSON 数组，不附带表头或成功说明。示例（排版仅用于展示，不保证缩进或空格格式）：

```json
[
  {"id": 1, "title": "完善协作指南", "assignee": "Alice", "status": "doing"},
  {"id": 2, "title": "补充测试", "assignee": null, "status": "todo"}
]
```

每个对象包含以下四个字段：

| 字段 | JSON 类型 | 说明 |
| --- | --- | --- |
| `id` | 整数 | 任务 ID，数组按 ID 升序排列 |
| `title` | 字符串 | 任务标题 |
| `assignee` | 字符串或 `null` | 未分配负责人为 `null` |
| `status` | 字符串 | `todo`、`doing`、`done` 之一 |

中文直接显示，双引号、反斜杠、换行等按 JSON 规则转义。无任务或无匹配结果时输出 `[]`，退出码为 0。`--json` 可与任意已有筛选条件组合，筛选规则不变。

错误仍仅输出到 stderr，stdout 为空，不输出 JSON 错误对象或 `[]`。例如 `list --json --status invalid` 退出 2，`list --json --assignee=` 或数据库损坏退出 1。

### show

```console
python -m team_tasks show 1
```

```text
ID: 1
标题: 完善协作指南
负责人: Alice
状态: doing
```

ID 不存在时输出 `错误：任务 #1 不存在。`，退出码 1。

### update

```console
python -m team_tasks update 1 --status doing
python -m team_tasks update 1 --title "检查协作指南" --assignee Bob --status done
python -m team_tasks update 1 --assignee=
```

至少提供 `--title`、`--assignee`、`--status` 中的一项；未提供的字段保持原值。状态允许任意合法转换。`--assignee=` 用于清除负责人，避免不同 shell 对空引号参数的处理差异。

成功输出 `已更新任务 #1。`。标题为空会失败且保持原数据。未提供任何更新字段属于参数错误，退出码 2；不存在的 ID 属于业务错误，退出码 1。

### delete

```console
python -m team_tasks delete 1
```

立即删除并输出 `已删除任务 #1。`。再次删除同一个 ID 会报任务不存在。

## 退出码与失败示例

| 退出码 | 含义 | 例子 |
| --- | --- | --- |
| 0 | 成功，包含空列表和帮助 | `list`、`--help` |
| 1 | 业务或存储错误 | 空标题、任务不存在、数据库文件损坏 |
| 2 | 命令行参数错误 | 未知命令、无效状态、非法 ID、缺少更新字段 |

```console
python -m team_tasks add "   "
python -m team_tasks show 999999
python -m team_tasks list --status invalid
python -m team_tasks update 1
```

以上分别演示空标题、记录不存在（假设该 ID 未创建）、非法状态和未提供修改字段。数据库错误文本带有路径与底层原因，具体措辞可能因系统不同而变化；不会显示预期错误的 Python 调用栈。

PowerShell 用 `$LASTEXITCODE`、命令提示符用 `echo %ERRORLEVEL%`、bash 用 `echo $?` 查看上一条命令的退出码。

## Python 内部接口

### 数据与错误类型

```python
Task(id: int, title: str, assignee: str | None, status: str)
STATUSES = ("todo", "doing", "done")
```

`Task` 是不可变 dataclass。`ValidationError`、`TaskNotFoundError`、`StorageError` 均继承 `TaskError`。

### 业务接口

通过 `TaskService(repository)` 创建服务，不直接解析命令行或操作文件。

| 方法 | 返回值 | 约定 |
| --- | --- | --- |
| `add_task(title, assignee=None)` | `Task` | 校验后创建 |
| `list_tasks(*, status=None, assignee=None)` | `list[Task]` | `None` 表示不筛选，空列表合法 |
| `get_task(task_id)` | `Task` | 不存在抛出 `TaskNotFoundError` |
| `update_task(task_id, *, title=None, assignee=None, status=None)` | `Task` | `None` 表示保留，负责人传 `""` 表示清空 |
| `delete_task(task_id)` | `None` | 不存在抛出 `TaskNotFoundError` |

直接调用业务接口时，无效状态或 ID 抛出 `ValidationError`；CLI 会提前将部分此类输入判为参数错误。更新方法直接调用时若没有修改字段，也抛出 `ValidationError`。

### 存储接口

通过 `TaskRepository(db_path)` 打开或初始化数据库，支持 `with`，也可以显式 `close()`。

| 方法 | 返回值 | 约定 |
| --- | --- | --- |
| `create(title, assignee)` | `Task` | 保存已校验值，生成 ID，状态为 `todo` |
| `list_tasks(*, status=None, assignee=None)` | `list[Task]` | AND 筛选、ID 升序 |
| `get(task_id)` | `Task \| None` | 不存在时返回 `None` |
| `update(task)` | `bool` | 保存对象全部可变字段；不存在返回 `False` |
| `delete(task_id)` | `bool` | 有记录被删除返回 `True` |

存储层负责 SQL、事务与错误转换，不负责用户文本的清理。调用方应先经过业务层。

## 扩展练习的接口状态

`list --json` 已实现，接口见上文；`stats` **未实现**。验收进度及统计命令的预定行为见[练习任务卡](exercises.md)。
