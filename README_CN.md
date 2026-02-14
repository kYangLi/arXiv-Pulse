# arXiv Pulse - 智能 arXiv 文献追踪系统

[![Version](https://img.shields.io/pypi/v/arxiv-pulse.svg)](https://pypi.org/project/arxiv-pulse/)
![Python](https://img.shields.io/badge/python-3.12%2B-green)
![License](https://img.shields.io/badge/license-GPL--3.0-orange)

> 🌐 **语言**: [English](README.md)

**arXiv Pulse** 是一个 Python 包，用于自动化爬取、总结和跟踪 arXiv 在凝聚态物理、密度泛函理论（DFT）、机器学习、力场和相关计算材料科学领域的最新研究论文。提供 Web 界面，实现专业级的文献管理体验。

## ✨ 核心功能

- **🌐 Web 界面**：FastAPI + Vue 3 现代化 Web 界面，实时 SSE 流式更新
- **🚀 一键启动**：仅需 `pulse serve` 即可启动服务
- **📝 网页配置**：首次访问自动引导配置，所有设置存储在数据库
- **📁 论文集管理**：创建、编辑、删除论文集，组织管理重要论文
- **🤖 AI 自动处理**：搜索和更新时自动翻译标题摘要、AI 总结、获取论文图片
- **🔍 智能搜索**：支持自然语言查询，AI 自动解析为学术关键词
- **💾 数据库存储**：SQLite 数据库存储论文元数据和配置
- **⚙️ 系统设置**：网页端管理 AI API、研究领域、同步选项
- **🌍 多语言支持**：界面语言支持中英文，翻译语言可选中文或保留英文
- **🎯 专注科研**：专为凝聚态物理、DFT、机器学习、力场等研究领域优化

## 🆕 v1.0.0 重大更新

### 多语言支持
- **界面语言**：设置页面可切换中文/英文
- **翻译语言**：可选择将论文翻译为中文或保留原文英文
- **双语文档**：README 同时提供中英文版本

### 服务管理
- **后台运行**：默认后台执行，使用 `pulse start` 启动
- **前台运行**：使用 `-f` 参数切换到前台模式
- **服务控制**：`pulse status`、`pulse stop`、`pulse restart`

### 界面优化
- **大图标按钮**：论文卡片操作按钮更加醒目
- **浮动组件**：暂存篮、AI 聊天、返回首页按钮统一布局在右下角
- **动画优化**：平滑的过渡效果和交互反馈

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

# 前台运行
pulse serve . -f
```

### 服务管理

```bash
pulse status .          # 查看服务状态
pulse stop .            # 停止服务
pulse restart .         # 重启服务
pulse stop . --force    # 强制停止 (SIGKILL)
```

### 首次使用

1. 访问 http://localhost:8000
2. 按向导配置：
   - **步骤 1**：设置 AI API（密钥、模型、地址）
   - **步骤 2**：选择研究领域
   - **步骤 3**：设置同步参数
   - **步骤 4**：开始初始同步

### 日常使用

- **最近论文**：查看最近 N 天的论文
- **搜索**：自然语言搜索，AI 自动解析
- **论文集**：创建论文集管理重要论文
- **设置**：点击右上角齿轮图标修改配置
- **AI 聊天**：向 AI 助手提问论文相关问题

## 📁 项目结构

```
arxiv_pulse/
├── cli.py                     # CLI 入口
├── config.py                  # 配置管理（从数据库读取）
├── models.py                  # 数据库模型
├── arxiv_crawler.py           # arXiv API 交互
├── summarizer.py              # 论文总结器
├── search_engine.py           # 增强搜索引擎
├── report_generator.py        # 报告生成器
├── research_fields.py         # 研究领域定义
├── i18n/                      # 国际化
│   ├── __init__.py
│   ├── zh.py                  # 中文翻译
│   └── en.py                  # 英文翻译
└── web/
    ├── app.py                 # FastAPI 应用
    ├── static/index.html      # Vue 3 前端
    └── api/
        ├── papers.py          # 论文 API + SSE
        ├── collections.py     # 论文集 API
        ├── config.py          # 配置 API
        ├── tasks.py           # 同步任务 API
        ├── stats.py           # 统计 API
        ├── export.py          # 导出 API
        └── chat.py            # AI 聊天 API

数据目录/
├── data/
│   └── arxiv_papers.db        # SQLite 数据库（含配置）
└── web.log                    # 后台运行日志
```

## 🔧 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/config` | GET/PUT | 获取/更新配置 |
| `/api/config/status` | GET | 获取初始化状态 |
| `/api/config/init` | POST | 保存初始化配置 |
| `/api/config/init/sync` | POST (SSE) | 执行初始同步 |
| `/api/papers/search/stream` | GET (SSE) | AI 搜索 |
| `/api/papers/recent/update` | POST (SSE) | 更新最近论文 |
| `/api/collections` | GET/POST | 论文集列表/创建 |
| `/api/stats` | GET | 数据库统计 |
| `/api/chat/sessions` | GET/POST | 聊天会话列表/创建 |
| `/api/chat/sessions/{id}/send` | POST (SSE) | 发送消息给 AI |

## 🧪 支持的研究领域

系统支持 20+ 个研究领域，在 Web 初始化向导中选择：

| 领域 | 说明 |
|------|------|
| 凝聚态物理 | 超导、强关联电子、介观系统 |
| 密度泛函理论 (DFT) | 第一性原理计算、材料设计 |
| 机器学习 | ML 在物理和材料科学中的应用 |
| 力场与分子动力学 | 力场开发、MD 模拟 |
| 第一性原理计算 | ab initio 方法 |
| 量子物理 | 量子信息、量子计算 |
| 计算物理 | 数值计算方法 |
| 化学物理 | 化学过程的物理基础 |
| 分子动力学 | MD 模拟技术 |
| 计算材料科学 | 材料计算与模拟 |
| 量子化学 | 量子化学方法 |
| 天体物理 | 宇宙学、天体观测 |
| 高能物理 | 粒子物理理论与实验 |
| 核物理 | 核物理理论与实验 |
| 人工智能 | AI、神经网络 |
| 数值分析 | 数值方法与算法 |
| 统计学 | 统计理论与应用 |
| 定量生物学 | 生物信息学、系统生物学 |
| 电子工程 | 信号处理、控制系统 |
| 数学物理 | 物理问题的数学方法 |

## 🐛 故障排除

### 常见问题

**Q: 忘记 API 密钥怎么办？**
A: 点击右上角设置图标，在设置页面可以修改 API 密钥和其他配置。

**Q: 如何重新初始化？**
A: 删除 `data/arxiv_papers.db` 数据库文件，重启服务即可重新进入初始化向导。

**Q: 端口被占用怎么办？**
A: 使用 `pulse serve . --port 3000` 指定其他端口。

**Q: 服务显示未运行但端口被占用？**
A: 检查是否有残留的锁文件（`.pulse.lock`），删除它或使用 `pulse stop --force`。

### 调试

```bash
# 前台运行查看详细日志
pulse serve . -f

# 查看后台服务日志
tail -f web.log
```

## 🔧 高级使用

### 使用 Systemd 设置开机自启（Linux）

创建 `/etc/systemd/system/arxiv-pulse.service`：
```ini
[Unit]
Description=arXiv Pulse Web Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/your/papers
ExecStart=/usr/local/bin/pulse serve .
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable arxiv-pulse
sudo systemctl start arxiv-pulse
```

## 📄 许可证

本项目采用 GPL-3.0 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 仓库
2. 创建特性分支
3. 进行更改
4. 如果适用，添加测试
5. 提交 pull request

## 🙏 致谢

- [arXiv.org](https://arxiv.org) 提供 API
- [DeepSeek](https://www.deepseek.com) 提供 AI 模型
- 计算材料科学社区

## 📞 支持

如有问题或建议：
1. 查看 [GitHub Issues](https://github.com/kYangLi/ArXiv-Pulse/issues)
2. 检查数据目录中的日志文件
3. 在网页设置中检查配置

---

**arXiv Pulse** - 让 arXiv 文献追踪变得简单高效！
