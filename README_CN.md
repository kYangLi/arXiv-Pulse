# arXiv Pulse - 智能 arXiv 文献追踪系统

[![Version](https://img.shields.io/pypi/v/arxiv-pulse.svg)](https://pypi.org/project/arxiv-pulse/)
![Python](https://img.shields.io/badge/python-3.12%2B-green)
![License](https://img.shields.io/badge/license-GPL--3.0-orange)

> 🌐 **语言**: [English Documentation](https://github.com/kYangLi/arXiv-Pulse/blob/main/README.md)

**arXiv Pulse** 是一个 Python 包，用于自动爬取、总结和追踪凝聚态物理、密度泛函理论 (DFT)、机器学习、力场和计算材料科学领域的最新 arXiv 论文。它提供现代化的 Web 界面，带来专业的文献管理体验。

## 📸 界面截图

![中文界面](https://github.com/kYangLi/arXiv-Pulse/blob/main/.image/interface_zh.png?raw=true)

## ✨ 主要特性

- **🌐 Web 界面**: 现代化的 FastAPI + Vue 3 + Element Plus 界面，支持实时 SSE 流
- **🚀 一键启动**: 只需 `pulse serve` 即可启动服务
- **📝 Web 配置**: 首次启动向导，所有设置存储在数据库中
- **🤖 AI 自动处理**: 自动翻译、AI 总结、图片提取
- **💬 AI 对话助手**: 基于论文内容的智能问答
- **🔍 智能搜索**: 自然语言查询，AI 解析关键词
- **📁 论文集**: 创建、编辑、删除论文集来管理重要论文
- **🛒 论文篮**: 选择多篇论文进行批量操作
- **🔒 默认安全**: 仅允许本地访问，远程访问需明确确认
- **🌍 多语言支持**: 中/英文界面，翻译支持多种语言

## 🚀 快速开始

### 安装

```bash
pip install arxiv-pulse
```

### 启动服务

```bash
# 创建数据目录
mkdir my_papers && cd my_papers

# 启动 Web 服务（默认后台运行）
pulse serve .

# 或指定端口
pulse serve . --port 3000

# 前台运行（可在终端看日志）
pulse serve . -f
```

然后访问 http://localhost:8000

### 服务管理

```bash
pulse status .          # 查看服务状态
pulse stop .            # 停止服务
pulse restart .         # 重启服务
pulse stop . --force    # 强制停止 (SIGKILL)
```

### 远程访问 (SSH 隧道)

默认情况下，服务只接受本地连接以确保安全。远程访问请使用 SSH 隧道：

```bash
# 在服务器上
pulse serve .

# 在你的电脑上
ssh -L 8000:localhost:8000 user@server

# 然后访问 http://localhost:8000
```

这提供了加密连接，不会暴露你的 API Key。

### 首次设置

1. 访问 http://localhost:8000
2. 按照设置向导操作：
   - **步骤 1**: 配置 AI API (OpenAI/DeepSeek 密钥、模型、端点)
   - **步骤 2**: 选择研究领域
   - **步骤 3**: 设置同步参数
   - **步骤 4**: 开始初始同步

## 🔒 安全设计

arXiv Pulse 注重安全：

- **默认仅本地访问**: 服务绑定 127.0.0.1，外部网络无法访问
- **无明文凭据**: API Key 存储在本地 SQLite 数据库，不会传输
- **明确的远程访问**: 开放非本地访问需要特殊标志并显示安全警告

**远程访问推荐方式**：
1. **SSH 隧道**（最简单）: `ssh -L 8000:localhost:8000 user@server`
2. **VPN**: WireGuard、OpenVPN 或 Tailscale
3. **反向代理**: Nginx/Caddy 配置 HTTPS

```bash
# 如必须开放网络访问（不推荐）
pulse serve . --host 0.0.0.0 --allow-non-localhost-access-with-plaintext-transmission-risk
```

## 📖 日常使用

### 页面功能

| 页面 | 描述 |
|------|------|
| **首页** | 统计概览，自然语言搜索 |
| **近期论文** | 最近 N 天的论文，可按领域筛选 |
| **同步** | 同步状态，领域管理，手动同步 |
| **论文集** | 将重要论文整理到论文集中 |

### 功能使用

- **搜索**: 使用自然语言，如 "电池材料的 DFT 计算"
- **筛选**: 点击"筛选领域"选择研究方向
- **AI 对话**: 点击右下角聊天图标提问
- **论文篮**: 点击卡片上的篮子图标收集论文，进行批量操作
- **设置**: 点击齿轮图标修改 API Key、语言和同步选项

## 📁 项目结构

```
arxiv_pulse/
├── core/                   # 核心基础设施 (配置、数据库、锁)
├── models/                 # SQLAlchemy ORM 模型
├── services/               # 业务逻辑 (AI、翻译、论文处理)
├── crawler/                # ArXiv API 爬虫
├── ai/                     # 论文总结器、报告生成器
├── search/                 # AI 智能搜索引擎
├── cli/                    # 命令行接口
├── web/                    # FastAPI Web 应用
│   ├── app.py             # FastAPI 应用
│   ├── api/               # API 端点
│   └── static/            # Vue 3 前端 (组件、状态管理、国际化)
└── i18n/                   # 后端翻译

数据目录/
├── data/arxiv_papers.db    # SQLite 数据库
└── web.log                 # 服务日志
```

详细架构请参阅 [DEV.md](DEV.md)。

## 🔧 API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/config` | GET/PUT | 获取/更新配置 |
| `/api/config/status` | GET | 获取初始化状态 |
| `/api/papers/search/stream` | GET (SSE) | AI 智能搜索 |
| `/api/papers/recent/update` | POST (SSE) | 更新近期论文 |
| `/api/collections` | GET/POST | 列出/创建论文集 |
| `/api/stats` | GET | 数据库统计 |
| `/api/chat/sessions/{id}/send` | POST (SSE) | 发送消息给 AI |

## 🧪 支持的研究领域

支持 20+ 个研究领域：

| 类别 | 领域 |
|------|------|
| 物理 | 凝聚态物理、量子物理、高能物理、核物理、天体物理 |
| 计算 | DFT、第一性原理、分子动力学、力场、计算物理 |
| AI/ML | 机器学习、人工智能 |
| 化学 | 量子化学、化学物理 |
| 数学 | 数学物理、数值分析、统计学 |
| 其他 | 定量生物学、电气工程 |

## 🐛 常见问题

**Q: 端口被占用？**
```bash
pulse serve . --port 3000
```

**Q: 服务显示"未运行"但端口被占用？**
```bash
pulse stop . --force
# 或删除过时的锁文件
rm .pulse.lock
```

**Q: 如何重新初始化？**
```bash
rm data/arxiv_papers.db
pulse serve .
```

**Q: AI 无响应？**
- 在设置中检查 API Key
- 检查控制台错误 (F12 → Console)
- 尝试前台运行查看日志: `pulse serve . -f`

## 📄 许可证

GPL-3.0 - 详见 [LICENSE](LICENSE)。

## 🙏 致谢

本项目由 **OpenCode** AI 编程智能体开发。

- **Yang Li** - 感谢您与我进行了 500+ 次需求迭代、设计讨论和测试反馈。没有您的耐心和愿景，就没有这个项目。
- **GLM-5** - 感谢提供驱动 OpenCode 的核心智能。本项目截至目前已消耗约 2 亿 token。
- [arXiv.org](https://arxiv.org) - 感谢开放 API
- [DeepSeek](https://www.deepseek.com) - 感谢提供论文总结的 AI 模型
- 计算材料科学社区 - 感谢灵感和使用场景

---

**arXiv Pulse** - 让 arXiv 文献追踪变得简单高效！
