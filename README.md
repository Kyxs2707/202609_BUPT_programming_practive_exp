# 202609_BUPT_programming_practive_exp
BUPT 2025-2026学年 大三上学期 程序设计实践——实验

## 团队任务管理器 · GitHub 双人协作 Demo

一个小型 Python 命令行项目，用于练习需求拆分、Issue、分支开发、Pull Request、交叉评审、自动测试和冲突处理。基础版本已经实现任务的增删改查与筛选；两项扩展功能留给参与者完成。

**所有 Git 命令都由你手动执行。** 助手负责项目文件和 Python 验证，Git 操作步骤见[双人协作指南](docs/collaboration.md)。也可使用两个独立克隆目录模拟两位成员。

## 快速开始

环境：Python 3.11+，从仓库根目录运行。运行和测试只使用标准库，无需 `pip install`。

```console
python --version
python -m team_tasks --help
```

下面假定首次使用空数据库，因此第一条任务的 ID 为 `1`。如果已有任务，请把命令中的 `1` 替换为 `add` 输出的实际 ID。命令适用于 PowerShell、命令提示符和常见 Unix shell。

```console
python -m team_tasks add "完善协作指南" --assignee Alice
python -m team_tasks list
python -m team_tasks show 1
python -m team_tasks update 1 --status doing
python -m team_tasks list --status doing --assignee Alice
python -m team_tasks update 1 --status done
python -m team_tasks delete 1
python -m team_tasks list
```

首次添加显示 `已创建任务 #1。`，最后一条命令显示 `暂无任务。`。`delete` 立即删除指定任务。

数据默认写入当前目录下的 `.data/tasks.db`，程序自动创建目录和表。每位成员使用自己的数据库，本地数据库及 Python 缓存已配置为忽略文件。

也可以指定独立的数据库，`--db` 必须位于子命令之前：

```console
python -m team_tasks --db .data/demo.db add "检查 CI" --assignee Bob
python -m team_tasks --db .data/demo.db list
```

## 测试

```console
python -m unittest discover -s tests -v
```

测试覆盖业务规则、SQLite 持久化以及独立进程运行的命令行行为；所有测试使用临时数据库，不改动你的任务数据。GitHub Actions 配置了 Windows / Ubuntu 与 Python 3.11 / 3.13 的四种组合；线上结果在你推送并创建 PR 后查看。

## 功能与分层

| 命令 | 用途 |
| --- | --- |
| `add TITLE [--assignee NAME]` | 创建任务，默认状态 `todo` |
| `list [--status STATUS] [--assignee NAME]` | 筛选任务，按 ID 升序显示 |
| `show ID` | 查看单条任务 |
| `update ID [--title TITLE] [--assignee NAME] [--status STATUS]` | 更新至少一个字段 |
| `delete ID` | 删除任务 |

状态可在 `todo`、`doing`、`done` 之间自由切换。负责人是普通文本，不会连接或通知 GitHub 用户。

```text
team_tasks/   命令行层 → 业务层 → SQLite 存储层，以及共享模型
tests/        命令行、业务、存储测试
docs/         需求、架构、接口、测试及协作演练文档
.github/      CI、Issue 模板、PR 模板
```

## 文档导航

| 文档 | 内容 |
| --- | --- |
| [需求与验收](docs/requirements.md) | 基础功能范围和完成标准 |
| [架构设计](docs/architecture.md) | 分层图、调用过程、数据模型和设计取舍 |
| [接口说明](docs/interfaces.md) | 命令、输出、退出码和内部接口 |
| [贡献规范](CONTRIBUTING.md) | 分工、分支、提交、评审及文档维护 |
| [双人协作指南](docs/collaboration.md) | 从首次提交到 PR 合并，以及冲突演练 |
| [练习任务卡](docs/exercises.md) | **未实现**：A 的 `list --json`、B 的 `stats` |
| [测试说明](docs/testing.md) | 测试分层、运行方法、CI 和故障定位 |

## 许可证

沿用原仓库的 [MIT License](LICENSE)。
