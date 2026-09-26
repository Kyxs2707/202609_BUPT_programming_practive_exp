# 测试说明

## 运行方法

在仓库根目录执行：

```console
python -m unittest discover -s tests -v
```

运行某一层的测试：

```console
python -m unittest discover -s tests -p test_service.py -v
python -m unittest discover -s tests -p test_repository.py -v
python -m unittest discover -s tests -p test_cli.py -v
```

基础版本包含 37 个测试方法；带 `subTest` 的方法还验证多组输入。新增练习功能后，测试数量应随实际覆盖增加，不将固定数量作为通过条件。

## 测试层次

| 测试文件 | 验证内容 |
| --- | --- |
| `tests/test_service.py` | 标题、负责人、状态、ID 校验，部分更新，清除负责人，缺失记录及删除 |
| `tests/test_repository.py` | 自动建库、参数化存储、筛选排序、跨连接持久化、删除后 ID 不复用、事务回滚及存储失败 |
| `tests/test_cli.py` | 独立进程运行、完整生命周期、组合筛选、输出与退出码、帮助无副作用、中文和带空格路径、损坏数据库 |

业务和存储测试使用临时 SQLite 文件。命令行测试以 `sys.executable` 启动独立进程，工作目录和数据库都放入临时目录，借助 `PYTHONPATH` 定位源码；子进程输出统一使用 UTF-8，并设置超时。这样既能检查真实命令，也不会污染个人 `.data/`。

## 关键验收场景

1. 创建任务 → 查看 → 改为 `doing` → 组合筛选 → 改为 `done` → 删除 → 确认不存在。
2. 关闭命令进程后再次启动，仍能读取已保存的数据。
3. 更新单个字段保留其他字段，空负责人能清除分配。
4. 标题为空、非法状态、错误 ID、没有修改字段、未知参数分别得到正确错误和退出码。
5. 不存在的记录、空列表及没有匹配的筛选结果正确处理。
6. 中文、单引号及看起来像 SQL 的文本作为普通数据保存。
7. 数据库损坏、父路径被普通文件占用或驱动无法打开时，报告可读错误，不覆盖已有文件。
8. 无效写入触发回滚，原数据保留，连接仍能继续处理合法写入。

不要用“测试成功导入模块”替代行为测试，也不要为了让测试通过而删掉失败断言。练习任务需新增针对输出或业务结果的断言。

## GitHub Actions

工作流位于 `.github/workflows/tests.yml`。PR、推送到 `main`、手动触发均执行同一条测试命令，矩阵为：

| 操作系统 | Python |
| --- | --- |
| Ubuntu | 3.11、3.13 |
| Windows | 3.11、3.13 |

使用 GitHub 托管 runner，工作流权限为 `contents: read`；无需密钥、数据库服务或第三方 Python 包。一个组合失败时其他组合继续运行，便于发现平台差异。

当前本地验收使用 Windows / Python 3.13。其他组合的真实结果须在用户推送、创建 PR 后到 Actions 或 PR Checks 中确认。初始化工作流进入默认分支后，可从 Actions 页面手动运行。

配置参考：[GitHub 官方 Python CI 指南](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)。

## 排查顺序与文档验证

- 提示找不到 `team_tasks`：确认终端位于包含该文件夹的仓库根目录。
- `python` 不可用或版本过低：先执行 `python --version`，选择本机 Python 3.11+ 解释器，不需要为了本项目安装额外依赖。
- SQLite 无法打开：核对 `--db` 路径及读写权限，确认父路径不是普通文件。保留异常文件，改用新路径验证。
- 只有 CI 失败：打开失败矩阵的日志，检查 Python 版本、路径大小写及换行/编码处理。
- 文档变更：检查相对链接、Mermaid 图与实际分层，以及命令的参数位置和输出。在新的临时数据库中验证操作示例。

Git 状态、差异、提交与推送仍由你手动操作，参见[协作指南](collaboration.md)。
