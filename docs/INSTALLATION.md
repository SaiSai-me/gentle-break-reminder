# 安装与使用 Gentle Break Reminder

这份指南适用于从 GitHub 安装 Gentle Break Reminder 的用户。插件不需要 API Key、付费 API 套餐或外部账号，但需要支持插件 Hooks 的 Codex 环境和可执行的 Python 3。

## 先确认使用环境

支持安装插件的界面：

- ChatGPT 桌面应用中的 Codex；
- Codex CLI。

目前不能在 Codex IDE 扩展中浏览或安装插件。安装完成后必须新建一个 Codex 任务或 CLI 会话，新的技能和 Hook 才会加载。

在终端确认 Python 3 可用：

```bash
python3 --version
```

如果提示找不到 `python3`，请先安装 Python 3，并确保 `python3` 命令可以在终端执行。Windows 用户也需要让 `python3` 成为可执行命令；仅有 `py` 或 `python` 命令还不够，因为插件 Hook 明确调用 `python3`。

## 方法一：从 GitHub Marketplace 安装（推荐）

不需要先下载 ZIP。Codex 会从 GitHub 获取 Marketplace 和插件源码。

### 第 1 步：添加 Marketplace

打开终端，运行：

```bash
codex plugin marketplace add SaiSai-me/gentle-break-reminder
```

正常情况下，Marketplace 名称是：

```text
saisai-plugins
```

可以运行下面的命令确认它已经被添加：

```bash
codex plugin marketplace list
```

### 第 2 步：安装插件

继续运行：

```bash
codex plugin add gentle-break-reminder@saisai-plugins
```

可以检查安装结果：

```bash
codex plugin list
```

列表中应当出现 `gentle-break-reminder`，并显示它来自 `saisai-plugins`。

### 第 3 步：重新打开应用并新建任务

1. 如果正在使用 ChatGPT/Codex 桌面应用，请完全退出后重新打开应用。
2. 打开 Plugins（插件）页面。
3. 在 Installed（已安装）区域确认 **Gentle Break Reminder** 已安装并启用。
4. 新建一个 Codex 任务。不要继续使用安装前已经打开的旧任务。

### 也可以通过 Codex CLI 的插件浏览器安装

先执行添加 Marketplace 的命令，然后启动 Codex：

```bash
codex
```

进入 Codex 后输入：

```text
/plugins
```

选择 `SaiSai Plugins`，打开 `Gentle Break Reminder` 并安装。安装完成后退出当前会话，再启动一个新的 Codex 会话。

## 方法二：已经下载 ZIP 时怎么安装

ZIP 文件不能通过双击直接安装。Codex 仍然需要通过 Marketplace 识别插件。

### 有 Codex CLI

即使已经下载 ZIP，最简单、最不容易出错的方式仍然是运行：

```bash
codex plugin marketplace add SaiSai-me/gentle-break-reminder
codex plugin add gentle-break-reminder@saisai-plugins
```

下载的 ZIP 可以留作源码审计或备份，不需要手动复制到 Codex 的缓存目录。

### 只有桌面应用，没有可用的 `codex` 命令

1. 在 GitHub 仓库页面选择 **Code → Download ZIP**。
2. 解压 ZIP。
3. 确认解压后的根目录中至少包含：

   ```text
   .agents/plugins/marketplace.json
   .codex-plugin/plugin.json
   hooks/hooks.json
   skills/configure-break-reminders/SKILL.md
   ```

   以 `.` 开头的目录在 macOS 和 Linux 中通常是隐藏目录，不要删除它们。

4. 把解压后的根目录作为一个项目文件夹在 ChatGPT/Codex 桌面应用中打开。
5. 完全退出并重新打开桌面应用，让它重新读取项目里的 repo Marketplace。
6. 打开 Plugins（插件）页面，选择 **SaiSai Plugins**。
7. 打开 **Gentle Break Reminder**，点击 `+` 安装。
8. 新建一个 Codex 任务再开始使用。

如果解压目录里没有 `.agents/plugins/marketplace.json`，说明下载的是较早的发布包。请改为下载仓库 `main` 分支的 ZIP，或者使用“方法一”的 Marketplace 命令。

## 验证是否安装成功

在新建的 Codex 任务中按顺序测试。

### 1. 检查插件能否被选中

在输入框键入 `@`，搜索并选择 **Gentle Break Reminder**，然后发送：

```text
查看我的休息提醒设置
```

也可以直接调用插件中的技能：

```text
$configure-break-reminders 查看我的休息提醒设置
```

成功时，Codex 会显示当前的提醒开关、触发阈值、冷却时间、每日上限和提醒通道。

### 2. 立即预览提醒

发送：

```text
测试一下休息提醒，但不要发送桌面通知
```

这只会预览当前提醒内容，不会改变活跃状态，也不会主动打开桌面通知。

### 3. 确认 Hook 正常工作

默认提醒不会在安装后立刻弹出。Hook 只会在你提交新消息时检查规则，默认需要满足以下任一条件：

- 持续活跃约 45 分钟，并且至少提交 5 条消息；
- 30 分钟内提交 10 条消息。

因此，“安装后没有马上提醒”通常不是故障。先用上面的预览命令验证安装，再让插件按正常阈值运行。

## 日常使用

安装完成后，默认提醒已经开启。你可以直接用自然语言配置：

```text
把提醒语改成“站起来走两分钟，再回来继续。”

连续活跃 50 分钟、至少 6 条消息后再提醒我

把对话强度规则改成 30 分钟内 12 条消息

两次提醒至少间隔 90 分钟，每天最多提醒 2 次

把提醒通道切换为桌面通知

关闭休息提醒
```

macOS 桌面通知只有在用户明确要求切换时才会启用。Windows 和 Linux 用户应继续使用默认的 Codex 内系统消息。

## 更新插件

先刷新 GitHub Marketplace：

```bash
codex plugin marketplace upgrade saisai-plugins
```

然后重新安装插件：

```bash
codex plugin add gentle-break-reminder@saisai-plugins
```

更新后重新打开桌面应用，并新建一个 Codex 任务。

## 卸载插件

卸载插件：

```bash
codex plugin remove gentle-break-reminder@saisai-plugins
```

如果以后也不再使用 SaiSai 的 Marketplace，可以继续移除 Marketplace：

```bash
codex plugin marketplace remove saisai-plugins
```

也可以在桌面应用或 `/plugins` 浏览器中打开插件，然后选择 **Uninstall plugin**。

卸载插件不会自动删除插件以前保存在本机的配置和活动计数。如需连同本地数据一起删除，请在卸载前先发送：

```text
$configure-break-reminders 恢复默认设置并清空状态
```

然后根据操作系统手动删除对应的数据目录：

- macOS：`~/Library/Application Support/gentle-break-reminder`
- Windows：`%LOCALAPPDATA%/gentle-break-reminder`
- Linux：`$XDG_STATE_HOME/gentle-break-reminder`；未设置时为 `~/.local/state/gentle-break-reminder`

## 常见问题

### 添加 Marketplace 后看不到插件

依次检查：

1. 运行 `codex plugin marketplace list`，确认存在 `saisai-plugins`。
2. 运行 `codex plugin marketplace upgrade saisai-plugins`。
3. 完全退出并重新打开桌面应用。
4. 在 Plugins 页面切换到 **SaiSai Plugins**。
5. 确认当前使用的是桌面应用或 Codex CLI，而不是 IDE 扩展。

### 插件已安装，但新消息没有触发 Hook

依次检查：

1. 是否在安装后新建了任务；旧任务不会自动加载新插件。
2. `python3 --version` 是否能正常运行。
3. 插件是否仍处于启用状态。
4. 是否误以为默认提醒会立即出现；默认阈值需要时间和消息数量共同满足。
5. 先执行“查看我的休息提醒设置”和“测试一下休息提醒”来区分安装问题与阈值尚未满足。

### `python3: command not found`

安装 Python 3，并确保终端能够直接执行 `python3`。安装后完全退出并重新打开桌面应用，再新建一个任务。

### Marketplace 已经存在

如果 `codex plugin marketplace add` 提示 Marketplace 已存在，不需要重复添加。运行：

```bash
codex plugin marketplace upgrade saisai-plugins
codex plugin add gentle-break-reminder@saisai-plugins
```

### 安全方面应该检查什么

本插件包含 `UserPromptSubmit` Hook。安装第三方 Hook 前，建议先查看：

- `hooks/hooks.json`：确认运行的命令；
- `scripts/codex_hook.py`：确认 Hook 适配逻辑；
- `scripts/activity_engine.py`：确认本地状态和提醒规则；
- `PRIVACY.md`：确认数据处理边界。

插件不需要 API Key，不调用外部网络服务，也不会打开对话 transcript。Hook 会收到 Codex 提交的事件 JSON，但后续逻辑不分析、传输或持久化提示词正文。

## 获取帮助

- 问题反馈：[GitHub Issues](https://github.com/SaiSai-me/gentle-break-reminder/issues)
- 最新版本：[GitHub Releases](https://github.com/SaiSai-me/gentle-break-reminder/releases)
- 隐私说明：[PRIVACY.md](../PRIVACY.md)
- 安全说明：[SECURITY.md](../SECURITY.md)

提交问题时，请附上操作系统、Codex 使用界面（桌面应用或 CLI）、`codex --version`、`python3 --version` 和完整错误信息，但不要上传私人对话内容或本地状态文件。

## English quick install

Requirements: a Codex surface that supports plugins and Hooks, plus an executable `python3` command. Plugins are not currently available in the Codex IDE extension.

```bash
codex plugin marketplace add SaiSai-me/gentle-break-reminder
codex plugin add gentle-break-reminder@saisai-plugins
```

Restart the desktop app or CLI, start a new Codex session, type `@`, select **Gentle Break Reminder**, and ask:

```text
Show my current break reminder settings.
```

To update:

```bash
codex plugin marketplace upgrade saisai-plugins
codex plugin add gentle-break-reminder@saisai-plugins
```

To uninstall:

```bash
codex plugin remove gentle-break-reminder@saisai-plugins
```
