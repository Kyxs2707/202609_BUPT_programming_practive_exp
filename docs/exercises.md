# 双人练习任务卡

这两项功能作为基础版本之上的扩展练习：任务 A 已实现并合并至 `main`；任务 B 已实现并通过本地测试，待完成协作验收。PR 关联、CI 和交叉评审的具体记录按下方任务卡核实、补录。每个 Issue 使用对应任务卡的目标、范围和验收条件，指定一位开发人和另一位评审人。

建议两人从同一个 `main` 起点并行开发，先合并 A 的 PR，再由 B 同步 `main` 后完成集成。

## 任务 A：为任务列表增加 JSON 输出

**状态：已实现并合并至 `main`，本地测试通过。** 开发：成员 A；评审：成员 B。开发分支：`codex/list-json`。

**协作记录：** 已合并 PR 的链接待补充；关联 Issue、CI 四项结果及成员 B 的评审记录待依据该 PR 核实、补录。下方未勾选的记录项表示尚未核实，不代表 PR 尚未合并。

### 目标与接口

```console
python -m team_tasks list --json
python -m team_tasks list --json --status doing --assignee Alice
```

提供 `--json` 时，stdout 为合法 JSON 数组，不附带表头或成功说明。每个对象包含 `id`、`title`、`assignee`、`status`，ID 为整数，未分配负责人为 JSON `null`，中文直接显示。示例：

```json
[
  {
    "id": 1,
    "title": "完善协作指南",
    "assignee": "Alice",
    "status": "doing"
  }
]
```

未提供 `--json` 时保持现有文本输出。筛选条件、排序、退出码及 stderr 行为不变。

### 修改范围

- 在 `team_tasks/cli.py` 的 `list` 参数和展示分支中增加选项，使用标准库 `json`，复用现有业务查询。
- 在 `tests/test_cli.py` 中通过子进程测试，用 `json.loads` 验证数据内容，不依赖缩进格式。
- 更新 README、接口说明和本任务卡的状态；业务层、数据库表无需改变。

### 验收清单

- [x] `list --json` 输出四个字段，保留中文，未分配时为 `null`
- [x] 无数据或无匹配结果时输出 `[]`，退出码 0
- [x] 状态与负责人筛选支持组合，结果继续按 ID 升序
- [x] 不加 `--json` 时原文本行为保持一致
- [x] 错误仍写到 stderr，stdout 没有伪装成成功结果的 JSON
- [x] 任务 A 完成时，全部原有及新增测试在本地通过（Windows / Python 3.13.5，共 41 项；集成统计功能后的 53 项结果见任务 B）
- [x] README、接口说明、测试说明和任务状态已同步
- [x] PR 已合并至 `main`
- [ ] 补充已合并 PR 的链接及关联 Issue
- [ ] 核对并补录 CI 四个组合通过的记录
- [ ] 核对并补录成员 B 的评审记录

## 任务 B：增加状态统计命令

**状态：已实现，本地测试通过；待用户确认 Git 同步、PR 关联 Issue、CI 和成员 A 评审。** 开发：成员 B（填写 GitHub 用户名）；评审：成员 A（填写 GitHub 用户名）。建议分支：`codex/task-stats`。

### 目标与接口

```console
python -m team_tasks stats
python -m team_tasks --db .data/demo.db stats
```

输出固定四行，顺序为总数、待办、进行中、完成：

```text
total: 3
todo: 1
doing: 1
done: 1
```

空库四项均为 0；没有任务的某种状态也必须显示 0。统计当前数据库所有任务，不增加筛选参数；沿用全局 `--db` 和现有错误约定。

### 修改范围与层间约定

- 存储层新增 `TaskRepository.count_by_status() -> dict[str, int]`，使用 SQL `GROUP BY` 统计，返回始终包含 `todo`、`doing`、`done` 三个键的整数计数字典。
- 业务层新增 `TaskService.get_statistics() -> dict[str, int]`，在上述结果中增加 `total`，其值为三个状态数量之和。
- 命令行层注册 `stats` 子命令，按固定顺序展示结果；不在 CLI 中直接写 SQL。
- 对应补齐存储、业务、命令行测试，更新 README、架构说明、接口说明和本任务卡状态。无需改变任务模型或数据库表。

### 验收清单

- [x] 空库输出四个 0，退出码 0；某种状态没有任务时仍显示 0
- [x] 混合状态计数正确，`total = todo + doing + done`
- [x] 状态修改及删除后重新统计，结果随之变化
- [x] 默认及自定义数据库路径生效，统计不修改任务数据
- [x] 数据库初始化或查询错误只写到 stderr，退出码 1；不支持的参数退出 2
- [x] 分层职责保持清晰，新增存储层、业务层及独立进程命令行测试
- [x] 当前工作区包含 A 的 JSON 功能，原有及新增测试全部通过（Windows / Python 3.13.5，共 53 项）
- [x] README、架构说明、接口说明、测试说明、需求和任务状态已同步
- [ ] 用户确认当前分支已同步 A 合入 `main` 的提交，并在同步后重新测试
- [ ] CI 四个组合通过
- [ ] PR 关联 Issue，成员 A 已评审

本地验证命令：`python -m unittest discover -s tests -v`。助手未执行 Git 操作，也未核验线上 PR、合并记录或 CI；相应验收项由用户按实际结果更新。

## 两项练习的共同要求

两项需求都会涉及 `cli.py` 和文档，因此需要在 Issue 中确认修改范围，在合并前查看另一分支已合入的变更。遇到冲突时逐项保留双方有效功能，不能单纯选择“全部采用我的版本”。

代码、测试和说明放在同一个 PR；不要为了消除测试失败改变与当前需求无关的接口。Git 命令始终由你手动执行，完整步骤见[协作指南](collaboration.md)。
