# Gentle Break Reminder

![Gentle Break Reminder 图标](./assets/icon.png)

[![Version](https://img.shields.io/badge/version-0.1.2-71C2FF)](https://github.com/847426577/gentle-break-reminder/releases/tag/v0.1.2)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

**把休息提醒放进 Agent 对话流里。**

Gentle Break Reminder 是一个面向 Codex 的本地插件。它通过 `UserPromptSubmit` Hook 感知用户与 Agent 的交互节奏，根据持续活跃度和短时间对话强度，在合适的时机给出低打扰的休息提醒。

它不是固定闹钟，也不限于提醒喝水。提醒内容、触发频率、每日上限和投递方式都可以用自然语言修改。

> ⏸️ 轻轻休息一下：喝口水、看看远处或活动肩颈，再舒服地继续吧。

## English overview

Gentle Break Reminder is a privacy-conscious Codex plugin that turns local prompt-submit timing and message counts into low-interruption break reminders. It supports sustained-activity and conversation-burst rules, cooldowns, daily limits, customizable reminder text, one-shot Codex system messages, and optional macOS desktop notifications. It requires no account, cloud service, API key, or external network request.

## 核心特点

- **对话流内部触发**：提醒跟随 Codex 交互发生，不需要额外打开计时器应用。
- **双重活跃度判断**：同时识别长时间持续交互和短时间高强度对话。
- **低打扰**：冷却时间、每日上限和空闲重置共同抑制重复提醒。
- **自由定制**：提醒内容可以是喝水、护眼、拉伸、站立、呼吸或任何自定义提示。
- **隐私优先**：不分析或保存提示词正文，不读取 Agent 回复，不打开对话 transcript，也不访问项目文件。
- **极简配置**：安装后即可运行，也可以直接用自然语言调整设置。

## Hook 如何工作

每当用户向 Codex 提交一条消息，`UserPromptSubmit` Hook 会记录一次本地活动事件：

```text
用户提交消息
    ↓
Hook 记录哈希会话 ID、时间和次数
    ↓
判断持续活跃度或对话强度
    ↓
检查冷却时间与每日上限
    ↓
在当前对话或桌面通知中显示自定义提醒
```

运行时判断由本地 Python 规则引擎完成，不需要调用额外的语言模型。

Codex 会把完整的 `UserPromptSubmit` 事件 JSON 交给 Hook。适配器会在本地反序列化这个事件，但后续逻辑只访问事件类型和会话标识，并以本机收到事件的时间进行计数；它不查询、分析、记录或持久化 `prompt` 字段，也不会打开 `transcript_path` 指向的文件。因为事件需要先反序列化，如果载荷中包含提示词正文，正文可能短暂存在于 Hook 进程内存中，进程结束后即被丢弃。

## 默认触发规则

满足任意一组条件即可进入提醒判断：

| 规则 | 默认条件 | 用途 |
| --- | --- | --- |
| 持续活跃 | 约 45 分钟，并且至少提交 5 条消息 | 识别长时间连续协作 |
| 对话强度 | 30 分钟内提交 10 条消息 | 识别短时间高密度协作 |

默认防打扰限制：

- 两次提醒至少间隔 60 分钟；
- 每天最多提醒 3 次；
- 空闲达到 20 分钟后重新计算当前活跃段；
- 只有不超过 15 分钟的相邻交互间隔才计入估算活跃时长。

插件不是后台计时器。它只在用户再次提交消息时检查规则，因此不会保证在第 45 分钟整点弹出提醒。

## 快速使用

安装并启用插件后，新建一个 Codex 任务。默认提醒已开启，无需额外配置。

直接告诉 Codex 你想怎样调整：

```text
查看我的休息提醒设置

把提醒语改成“站起来走两分钟，再回来继续。”

连续活跃 50 分钟、至少 6 条消息后再提醒我

把对话强度规则改成 30 分钟内 12 条消息

两次提醒至少间隔 90 分钟，每天最多提醒 2 次

把提醒通道切换为桌面通知

关闭休息提醒
```

也可以调用 `$configure-break-reminders` 明确进入配置流程。

## 可以自定义什么

| 设置 | 作用 |
| --- | --- |
| 提醒内容 | 自定义不超过 240 个字符的单行提示 |
| 持续活跃阈值 | 调整活跃分钟数和最低消息数 |
| 对话强度阈值 | 调整统计窗口和窗口内消息数 |
| 连续性与空闲重置 | 控制哪些相邻交互计入同一活跃段 |
| 冷却时间 | 控制两次提醒之间的最短间隔 |
| 每日上限 | 控制一天最多提醒几次 |
| 投递方式 | 选择 Codex 内系统消息或 macOS 桌面通知 |

所有配置都保存在本地。关闭插件会清空当前活跃状态，但保留其他设置；恢复默认配置时可以同时清空状态。

## 提醒方式

### Codex 内系统消息

默认方式。提醒以一次性系统消息显示在当前对话中，不要求模型重新生成提醒内容，也不会把固定提醒指令持续注入后续上下文。

### macOS 桌面通知

可选方式。插件通过本地 `osascript` 发送系统通知；发送失败时自动回退为 Codex 内系统消息。

桌面通知目前只支持 macOS。插件不会在用户没有明确要求时主动切换到桌面通知或投递测试通知。

## 隐私设计

插件在本地保存：

- 截短后的 SHA-256 会话标识；
- 消息提交时间戳和计数；
- 估算的活跃时长；
- 上次提醒时间和当天提醒次数；
- 用户主动修改的配置。

插件不会分析、返回、传输或持久化：

- 用户提示词正文；
- Agent 回复正文；
- 对话 transcript 内容或路径（插件不会打开 transcript 文件）；
- 项目代码、文件内容或文件名；
- 键盘、鼠标、摄像头或屏幕内容；
- 对情绪、疲劳、健康或饮水状态的语义推断；
- 原始会话 ID。

活动数据不会发送到外部服务。超过 7 天没有活动的会话状态会自动清理。

默认数据目录：

- macOS：`~/Library/Application Support/gentle-break-reminder`
- Windows：`%LOCALAPPDATA%/gentle-break-reminder`
- Linux：`$XDG_STATE_HOME/gentle-break-reminder`，未设置时使用 `~/.local/state/gentle-break-reminder`

哈希化是数据最小化措施，不等同于完全匿名化。本地状态仍应被视为私人数据。

完整披露请参阅[隐私政策](./PRIVACY.md)。使用插件即表示你同意[服务条款](./TERMS.md)。

## 设计边界

Gentle Break Reminder 只能根据消息事件的时间和次数估算交互节奏。它不能测量真实屏幕使用时间、打字时间、工作时长、疲劳程度或身体状态，也不能替代医学或健康建议。

插件的目标不是“猜出你累了”，而是在透明、可控、低频的规则下，为持续的人机协作提供一个自然的暂停点。

## 兼容性

- 需要支持插件 Hook 的 Codex 环境；
- 本地运行需要 Python 3；
- 支持 Codex 内系统消息；
- 支持 macOS 桌面通知；
- Windows 和 Linux 可继续使用 Codex 内系统消息；
- 不需要外部账号、云服务或 API Key。

## 开发与验证

运行测试：

```bash
python3 -m unittest discover -s tests -v
```

当前测试覆盖持续活跃、对话强度、冷却、每日上限、空闲重置、跨任务全局限制、自定义提醒、状态迁移、隐私约束和通知回退。

## 发布与支持

- 最新版本与安装包：[GitHub Releases](https://github.com/847426577/gentle-break-reminder/releases)
- 问题与功能建议：[GitHub Issues](https://github.com/847426577/gentle-break-reminder/issues)
- 安全问题：[安全政策](./SECURITY.md)
- 参与贡献：[贡献指南](./CONTRIBUTING.md)

公开 Codex 插件目录版本需要通过 OpenAI 审核；GitHub Release 是可审计的源代码发布渠道，不代表 OpenAI 已审核或认可本插件。
