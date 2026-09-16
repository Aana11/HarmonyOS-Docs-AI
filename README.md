# HarmonyOS Docs AI

面向 AI 编程助手与检索增强生成（RAG）的 HarmonyOS 开发文档离线知识库。

本仓库将华为开发者网站公开的 HarmonyOS 文档保存为结构化 Markdown，并提供目录索引、FAQ JSONL、AI Skill、MCP 检索服务和增量抓取脚本。目标是让 Codex、Claude Code、GitHub Copilot、Cursor、Gemini CLI 以及自建知识库在回答鸿蒙开发问题时，能够先查阅可追溯的官方资料，再生成代码或结论。

> [!IMPORTANT]
> 这是社区维护的非官方镜像与 AI 工具项目，不代表华为。文档内容的著作权归华为或相应权利人所有；本仓库为每篇文档保留官方来源 URL。工具代码的许可与镜像内容的版权范围不同，详见[版权与许可](#版权与许可)。

## 这个仓库为 AI 做什么

- **离线上下文**：AI 无需依赖动态网页即可读取指南、API、最佳实践、FAQ、版本说明和变更预告。
- **来源可追溯**：每篇 Markdown 的 frontmatter 包含官方 URL、标题、目录路径、抓取时间、文档更新时间和内容哈希。
- **降低幻觉**：AI 可先检索本地索引，再阅读命中文档；回答时可以引用 `url` 字段指向官方原文。
- **适配 RAG**：`faq-corpus.jsonl` 每行一篇 FAQ，包含元数据、纯文本和完整 Markdown。
- **工具调用**：`mcp/server.py` 提供文档搜索、读取、编码规则和在线兜底能力。
- **Agent Skill**：`harmonyos/SKILL.md` 可直接供支持 Skill 的 AI 编程工具使用。
- **可持续更新**：采集器直接调用华为公开的 `documentPortal` 接口，不需要浏览器逐页抓取。

## 当前内容

最新文档同步：**2026-09-16**，活动索引共 **16,817** 篇：

| 分类 | 数量 | 本地入口 |
|---|---:|---|
| 版本说明 | 1,249 | [`harmonyos-releases/INDEX.md`](harmonyos/references/harmonyos-releases/INDEX.md) |
| 指南 | 5,721 | [`harmonyos-guides/INDEX.md`](harmonyos/references/harmonyos-guides/INDEX.md) |
| API 参考 | 4,762 | [`harmonyos-references/INDEX.md`](harmonyos/references/harmonyos-references/INDEX.md) |
| 最佳实践 | 477 | [`best-practices/INDEX.md`](harmonyos/references/best-practices/INDEX.md) |
| FAQ | 4,595 | [`harmonyos-faqs/INDEX.md`](harmonyos/references/harmonyos-faqs/INDEX.md) |
| 变更预告 | 13 | [`harmonyos-roadmap/INDEX.md`](harmonyos/references/harmonyos-roadmap/INDEX.md) |

总入口：[`harmonyos/references/INDEX.md`](harmonyos/references/INDEX.md)。站点已下线但仍保留在磁盘的历史 Markdown 不进入活动索引和 JSONL。

## 快速使用

### 1. 直接让 AI 搜索 Markdown

这是依赖最少、最透明的方式：

```powershell
rg -n "自由多窗|Scroll|Tabs" harmonyos/references/harmonyos-faqs
rg -n "UIAbility 生命周期" harmonyos/references/INDEX.md
```

推荐的 AI 工作流：

1. 在总索引或分类索引中搜索关键词。
2. 阅读命中的 Markdown，而不是只根据标题作答。
3. 同时查看相关 API 参考和版本说明。
4. 回答时引用 frontmatter 的官方 `url`。

### 2. 导入 RAG 或向量数据库

`faq-corpus.jsonl` 的每一行都是一个独立 JSON 对象，主要字段如下：

```json
{
  "id": "faqs-arkui-500",
  "title": "自由多窗小页面，页面向上滑动，正文内容跳动",
  "breadcrumb": "FAQ > 应用框架开发 > UI框架 > UI界面 > ...",
  "category": "harmonyos-faqs",
  "url": "https://developer.huawei.com/consumer/cn/doc/harmonyos-faqs/faqs-arkui-500",
  "path": "harmonyos/references/harmonyos-faqs/faqs-arkui-500.md",
  "text": "用于关键词、全文或向量检索的纯文本",
  "markdown": "保留章节、列表、链接和代码块的完整正文"
}
```

建议将 `title`、`breadcrumb` 和 `text` 用作检索字段，将 `markdown` 作为送入模型的正文，将 `url` 作为回答引用来源。`catalog.jsonl` 是全量活动文档的轻量元数据目录，不重复保存正文。

### 3. 使用 MCP 服务

安装 [uv](https://docs.astral.sh/uv/) 后，在仓库根目录执行：

```powershell
uv run mcp/server.py
```

可用能力包括：

- `list_categories`：列出分类和文档数量。
- `search_docs`：按标题、路径或正文搜索。
- `read_doc`：通过相对路径或华为文档 URL 读取正文。
- `coding_rules`：读取 ArkTS / ArkUI 编码规则。
- `fetch_online`：本地缺失或过旧时，通过官方接口获取最新正文。

客户端配置示例：

```json
{
  "mcpServers": {
    "harmonyos-docs": {
      "command": "uv",
      "args": ["run", "/absolute/path/HarmonyOS-Docs-AI/mcp/server.py"]
    }
  }
}
```

### 4. 作为 AI Skill 使用

将 `harmonyos/` 链接或复制到对应工具的 Skill 目录，例如 Codex：

```powershell
New-Item -ItemType SymbolicLink `
  -Path "$env:USERPROFILE\.codex\skills\harmonyos" `
  -Target "C:\path\to\HarmonyOS-Docs-AI\harmonyos"
```

其他 AI 工具的安装方式见[上游完整说明](UPSTREAM_README.md)。

## 一键更新

Windows 用户完整克隆或下载仓库后，可以直接运行：

- `update-faq.cmd`：仅同步 FAQ，适合日常更新。
- `update-all.cmd`：同步全部六个分类。

脚本会自动准备隔离的 Python 环境、调用官方接口、增量更新 Markdown，并重建 `faq-corpus.jsonl`、`catalog.jsonl`、`manifest.json` 与内容校验值。系统需要先安装 [uv](https://docs.astral.sh/uv/)。

命令行方式：

```powershell
# 增量更新 FAQ
.\one-click-update.ps1 -Mode FAQ

# 全量更新
.\one-click-update.ps1 -Mode All

# 忽略当日缓存，强制重新检查 FAQ
.\one-click-update.ps1 -Mode FAQ -ForceRefresh
```

采集过程支持断点续传，日志位于 `scraper/data/logs/`。采集器发现目录失败或错误率过高时会返回非零退出码，避免用残缺结果覆盖索引。

## 数据结构

```text
HarmonyOS-Docs-AI/
├── harmonyos/
│   ├── SKILL.md
│   ├── rules/
│   └── references/
│       ├── INDEX.md
│       ├── harmonyos-guides/
│       ├── harmonyos-references/
│       ├── best-practices/
│       ├── harmonyos-faqs/
│       ├── harmonyos-releases/
│       └── harmonyos-roadmap/
├── faq-corpus.jsonl
├── catalog.jsonl
├── manifest.json
├── mcp/server.py
├── scraper/
├── tools/rebuild_indexes.py
├── one-click-update.ps1
├── update-faq.cmd
└── update-all.cmd
```

单篇 Markdown 的 frontmatter 示例：

```yaml
---
url: https://developer.huawei.com/consumer/cn/doc/harmonyos-faqs/faqs-arkui-500
title: 自由多窗小页面，页面向上滑动，正文内容跳动
breadcrumb: FAQ > 应用框架开发 > UI框架 > UI界面 > 自由多窗小页面，页面向上滑动，正文内容跳动
category: harmonyos-faqs
scraped_at: 2026-09-16T08:00:00+08:00
doc_updated_at: 2026-06-26
content_hash: sha256:...
---
```

## 自动化与增量策略

采集分两阶段执行：

1. 调用 `getCatalogTree` 获取每个分类的完整目录树。
2. 并发调用 `getDocumentById` 获取正文并转换为 Markdown。

正文哈希未变化时不会重写文件；manifest 每完成一批文档就会保存，可在网络中断后继续。默认不会下载图片二进制，只保留官方 CDN 地址，因为这些地址的签名可能过期且资源版权仍属于原权利人。

## 版权与许可

- `scraper/`、`mcp/`、一键更新脚本及其他工具代码沿用上游项目的 [MIT License](LICENSE)。
- `harmonyos/references/`、`faq-corpus.jsonl` 等镜像内容不是以 MIT 重新授权；其著作权归华为或相应权利人所有，应遵守原站条款。
- 每篇文档都保留官方来源 URL；请勿移除来源、冒充官方文档或将镜像内容用于违反原站条款的用途。
- 本仓库不保证镜像实时、完整或适用于特定目的。涉及版本兼容、发布审核、安全或商业决策时，请回到官方页面复核。

更完整的说明见 [NOTICE.md](NOTICE.md)。

## 数据来源与致谢

- 官方来源：[华为开发者文档中心](https://developer.huawei.com/consumer/cn/doc/)
- 上游采集与 Skill 项目：[liasica/harmonyos-skills](https://github.com/liasica/harmonyos-skills)
- 参考项目：[HarmonyOSDocs](https://gitcode.com/third-party-library-for-harmony/HarmonyOSDocs)

本仓库基于 manifest 所列的上游快照构建，并保留上游原始说明，详见 [UPSTREAM_README.md](UPSTREAM_README.md)。
