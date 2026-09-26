# GitHub 双人协作指南

## 约定与准备

**下文所有 Git 命令都由你手动执行，助手不会代运行。** 代码和文档文件已在当前目录准备好；尚未替你创建分支、暂存、提交或推送。每个代码块都需要在确认上一步结果后再执行。

双人演练使用两个 GitHub 账号，各自在独立工作目录操作。你也可以用两个独立克隆目录扮演 A、B，练习分支和合并，但两个目录本身不等于两个 GitHub 账号。

在 GitHub 仓库设置中，由仓库拥有者邀请另一位成员为协作者，对方接受后再推送分支。负责人名称 `Alice`、`Bob` 只是程序样例数据，与这两个账号无绑定关系。

| 阶段 | 你将练习什么 |
| --- | --- |
| 基础项目初始化 | 查看改动、建分支、暂存、提交、推送、创建第一个 PR |
| A / B 功能开发 | Issue 拆分、独立开发、交叉评审、CI 和合并 |
| 同步与冲突 | 获取远程变更、合并主分支、手工解决冲突 |
| 独立文档练习 | 稳定制造一次冲突，观察完整处理过程 |

## 1. 查看当前状态与身份

在当前项目根目录依次执行：

```console
git status --short --branch
git remote -v
git log --oneline -5
git config --get user.name
git config --get user.email
```

预期能看到当前分支、`origin`、已有提交，以及 README 修改和新建文件。`??` 表示尚未跟踪的新文件，`M` 表示已跟踪文件被修改。先确认这些都是本次项目需要的内容。

若用户名或邮箱没有配置，仅为本仓库设置实际身份：

```console
git config user.name "你的提交名字"
git config user.email "你的GitHub提交邮箱"
```

邮箱可以使用 GitHub 设置中显示的提交邮箱。配置名字不会替你完成 GitHub 登录；推送仍使用你本机的 HTTPS 或 SSH 凭据。

## 2. 提交基础 Demo

以下步骤假定当前处于初始 `main`，且没有其他无关工作。先创建初始化分支，当前尚未提交的文件会保留：

```console
git switch -c codex/collaboration-demo
python -m unittest discover -s tests -v
git add .gitignore .gitattributes .editorconfig AGENTS.md README.md CONTRIBUTING.md team_tasks tests docs .github
git diff --cached --stat
git diff --cached
git status --short
```

`git add` 只是把文件放入暂存区；`git diff --cached` 检查即将提交的内容。普通 `git diff` 不会显示还未跟踪的新文件，所以这里在暂存后检查。确认没有个人数据库或无关改动，再执行：

```console
git commit -m "feat: add two-person collaboration demo"
git push -u origin codex/collaboration-demo
```

`commit` 创建本地提交，`push` 将分支上传到 GitHub；`-u` 设置跟踪关系，后续同分支可以直接使用 `git push`。

到 GitHub 仓库页面创建 PR：base 选 `main`，compare 选 `codex/collaboration-demo`。填写目标、改动和测试结果，邀请另一位成员评审，查看四项 CI 检查。

这次是初始化 PR，模板文件尚未合入默认分支，页面可能不会自动填充模板。可手动复制 `.github/pull_request_template.md` 的内容，并按模板说明删除没有对应 Issue 的占位行。确认 CI 和评审完成后，在 GitHub 选择 **Squash and merge**。

模板文件进入默认分支后，再开始创建练习 Issue 和后续 PR。模板生效规则参见 [Issue 模板文档](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)和 [PR 模板文档](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository)。

初始化 PR 合并后，回到本地同步：

```console
git switch main
git pull --ff-only origin main
python -m unittest discover -s tests -v
```

`--ff-only` 要求直接快进；若失败，先检查本地主分支是否存在额外提交，不要用强制覆盖来绕过。

## 3. 让另一位成员准备工作目录

在另一台机器或另一个目录，复制 GitHub 页面 Code 按钮下的 HTTPS 地址进行克隆。本仓库示例：

```console
git clone https://github.com/Kyxs2707/202609_BUPT_programming_practive_exp.git demo-member-b
cd demo-member-b
python -m unittest discover -s tests -v
```

如果使用你自己 Fork 后的仓库，请替换地址。成员 B 不应直接复制成员 A 电脑上的 SSH 主机别名；独立机器使用自己的 GitHub 登录或 SSH 配置。再次按第 1 步核对提交身份。

若由一个人模拟，当前工作目录作为 A，上面的 `demo-member-b` 目录作为 B。下面每组操作都注明在哪个目录执行，避免在同一工作目录反复切换角色。

## 4. 拆分 Issue 并建立功能分支

在 GitHub Issues 页面，通过功能需求模板分别创建 [A 的 JSON 输出任务](exercises.md)和 [B 的统计任务](exercises.md)。记录各自真实 Issue 编号，不假定编号一定是 1 或 2，因为 PR 也会占用编号。

在 **A 的目录**，从最新主分支创建：

```console
git switch main
git pull --ff-only origin main
git switch -c codex/list-json
```

在 **B 的目录**，也从同一个主分支起点创建：

```console
git switch main
git pull --ff-only origin main
git switch -c codex/task-stats
```

此后分别实现对应任务卡。先读接口约定，修改代码、补测试，并更新相关文档。无需等另一位成员完成才开始开发。

## 5. 提交功能并创建 PR

以下以 **A 的目录** 为例，完成 JSON 输出后执行：

```console
python -m unittest discover -s tests -v
git status --short
git diff
git add team_tasks tests docs README.md
git diff --cached
git commit -m "feat: add JSON task listing"
git push -u origin codex/list-json
```

在 GitHub 创建到 `main` 的 PR，按模板填写说明，在正文写 `Closes #实际Issue编号`，例如关联的 Issue 是 7 就写 `Closes #7`。在 Reviewers 中选择 B。B 的步骤相同，提交说明改为 `feat: add task statistics`，推送分支改为 `codex/task-stats`，邀请 A。

评审人检查需求、分层、测试与文档，在 Files changed 页面留下具体反馈，并选择 Comment、Request changes 或 Approve。开发人按反馈继续在原分支修改、测试、提交并 `git push`，原 PR 会更新，无需重建 PR。评审方式参考 [GitHub PR 评审说明](https://docs.github.com/en/pull-requests/reference/pull-request-reviews)。

按练习顺序先合并 A 的 PR；等待 CI 全部通过和 B 批准后，由你在 GitHub 选择 **Squash and merge**。正确关联的 Issue 会随默认分支合并关闭。

## 6. B 同步 A 已合并的变更

先确保 B 自己的功能改动已提交，工作区没有未保存到提交的修改。在 **B 的目录**执行：

```console
git switch codex/task-stats
git status --short
git fetch origin
git merge --no-edit origin/main
```

`fetch` 仅获取远程信息；`merge` 把远程主分支的新内容合入当前功能分支。若自动合并成功，直接运行测试并推送。若提示冲突：

1. 用 `git status` 查看冲突文件。
2. 在编辑器中处理 `<<<<<<<`、`=======`、`>>>>>>>` 标记，保留 JSON 输出和统计功能各自需要的代码与文档。
3. 保存文件后测试，再暂存实际解决的文件并完成合并提交。下面列的是这两个练习可能共同修改的范围：

```console
python -m unittest discover -s tests -v
git add team_tasks tests docs README.md
git diff --cached
git commit -m "merge: integrate JSON listing into statistics branch"
```

只有存在待完成的冲突合并时才执行上述合并提交；自动合并已完成时无需再建一个空提交。然后执行：

```console
python -m unittest discover -s tests -v
git push
```

等待 CI 重新通过，A 复查后合并 B 的 PR。最后两位成员各自在自己的目录切回 `main` 并执行 `git pull --ff-only origin main`，验证两项新功能都存在。

## 7. 在独立分支稳定制造一次文档冲突

选择任意一个工作目录，确认工作区干净。在本地练习分支上操作即可，不需要推送这些分支或合回主分支。

```console
git switch main
git pull --ff-only origin main
git status --short
git switch -c practice/conflict-base
git switch -c practice/conflict-a
```

在编辑器中打开 `docs/practice.md`，把 `演练结论：待填写。` 改成 `演练结论：成员 A 已补充操作步骤。`，然后执行：

```console
git add docs/practice.md
git commit -m "docs: add member A practice conclusion"
git switch practice/conflict-base
git switch -c practice/conflict-b
```

此时文件回到共同起点。在编辑器中把同一行改成 `演练结论：成员 B 已补充验证结果。`，然后执行：

```console
git add docs/practice.md
git commit -m "docs: add member B practice conclusion"
git switch practice/conflict-base
git merge --no-edit practice/conflict-a
git merge --no-edit practice/conflict-b
git status
```

最后一次合并应报告内容冲突。打开该文件，删除冲突标记，将冲突部分合并为一行：

```text
演练结论：成员 A 已补充操作步骤，成员 B 已补充验证结果。
```

保存后完成合并并查看历史：

```console
git add docs/practice.md
git diff --cached
git commit -m "docs: resolve practice conclusion conflict"
git status
git log --oneline --graph -8
git switch main
```

预期 `practice/conflict-base` 上留下包含双方内容的合并提交，主分支保持原有演练模板。若在解决冲突前决定取消当前合并，可由你执行 `git merge --abort`，再检查状态。

## 8. 可选的仓库规则

由拥有者在 GitHub 仓库设置中为 `main` 配置：通过 PR 合并、至少一位其他成员批准、测试检查通过、讨论解决。先让 CI 运行一次，再从实际检查列表中选择本项目的四项 `test (...)`，不要凭空填写检查名称。

是否可启用分支保护取决于仓库可见性和账号方案；以 [GitHub 分支保护说明](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)及仓库设置界面为准。此项目只交付配置文件与指南，不会代你修改线上规则。

只有一个账号时，可以练习两个目录的分支开发与冲突处理，但无法完成另一个账号的独立批准；此时不要设置自己无法满足的评审人数要求。真实双人练习再启用该约束。

## 9. 练习记录

在实验记录中保存两项 Issue 和 PR 链接、双方至少一条有效评审意见、四项 CI 结果，以及冲突原因和最终解决方式。记录基于真实操作填写，不预先编造协作结果。
