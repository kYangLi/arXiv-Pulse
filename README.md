# arXiv Pulse - 智能 arXiv 文献追踪系统

[![Version](https://img.shields.io/pypi/v/arxiv-pulse.svg)](https://pypi.org/project/arxiv-pulse/)
![Python](https://img.shields.io/badge/python-3.12%2B-green)
![License](https://img.shields.io/badge/license-GPL--3.0-orange)

> 🌐 **语言说明**：本文档为中文版本。

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
- **🎯 专注科研**：专为凝聚态物理、DFT、机器学习、力场等研究领域优化

## 🆕 v0.9.0 重大更新

### 全新 Web 优先架构
- **Web 初始化向导**：首次访问自动引导配置 AI API、研究领域
- **网页设置页面**：随时修改 AI API、研究领域、同步选项
- **配置存数据库**：不再依赖 .env 文件，配置自动持久化
- **简化 CLI**：仅需 `pulse serve` 一个命令

### 改进的 Web 界面
- **初始化向导**：步骤化引导配置（API → 研究领域 → 同步设置）
- **设置抽屉**：一键打开设置面板，实时保存配置
- **研究领域选择器**：20+ 研究领域可视化选择

### 移除的功能
- 终端命令（init/sync/search/recent/stat）
- .env 配置文件依赖
- 终端交互式配置向导

## 🚀 快速开始

### 安装方式

```bash
pip install arxiv-pulse
```

### 启动服务

```bash
# 创建数据目录
mkdir my_papers && cd my_papers

# 启动 Web 服务
pulse serve .

# 或指定端口
pulse serve . --port 3000

# 后台运行
pulse serve . --detach
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

3. **随时更新数据库**
   ```bash
   pulse sync .  # 仅同步最新论文，不生成报告
   ```

4. **智能搜索论文**
   ```bash
   pulse search "机器学习在材料科学中的应用" . --years-back 1
   ```

 5. **生成最近论文报告**
    ```bash
    pulse recent . --days-back 30 --limit 20
    ```

### Web 界面（v0.8.0 新增）

启动 Web 服务器，通过浏览器管理论文：

```bash
# 启动 Web 服务器
pulse serve .

# 或使用 uvicorn
uvicorn arxiv_pulse.web.app:app --host 127.0.0.1 --port 8000 --reload
```

## 📁 项目结构

```
arxiv_pulse/
├── cli.py                     # CLI 入口（仅 serve 命令）
├── config.py                  # 配置管理（从数据库读取）
├── models.py                  # 数据库模型（含 SystemConfig）
├── arxiv_crawler.py           # arXiv API 交互
├── summarizer.py              # 论文总结器
├── search_engine.py           # 增强搜索引擎
├── report_generator.py        # 报告生成器
├── research_fields.py         # 研究领域定义
└── web/
    ├── app.py                 # FastAPI 应用
    ├── static/index.html      # Vue 3 前端
    └── api/
        ├── papers.py          # 论文 API + SSE
        ├── collections.py     # 论文集 API
        ├── config.py          # 配置 API
        ├── tasks.py           # 同步任务 API
        ├── stats.py           # 统计 API
        └── export.py          # 导出 API

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
| `/api/stats` | GET | 数据库统计 |：
- 无论是否使用 --force，都不会下载已存在的论文
- --force 模式适用于扩展数据库，而非重新下载

#### `pulse search` - 智能搜索论文
**功能**：在数据库中搜索论文，支持自然语言查询和AI解析。

```bash
pulse search "查询内容" [目录路径] --update -t 1y --limit 20
```

**参数**：
- `--update/--no-update`：搜索前是否更新数据库（默认：否，是则使用YEARS_BACK配置）
- `--time-range, -t`：搜索时间范围，如'1y'=1年、'6m'=6个月、'30d'=30天（默认：0，表示不限制）
- `--limit`：返回结果的最大数量（默认：64）
- `-c, --categories`：包含的分类（可多次使用）
- `-a, --authors`：作者姓名（可多次使用）
- `--sort-by`：排序字段（published/relevance_score/title/updated）
- `--no-cache`：禁用图片URL缓存

**自动功能**：
- 如果配置了AI API密钥，自动使用AI解析自然语言查询
- 搜索到的论文会自动尝试总结（有AI key时）
- 自动生成Markdown和CSV格式的详细报告

**搜索示例**：
```bash
# 搜索近一年的机器学习相关论文，并先更新数据库
pulse search "machine learning materials" . --update -t 1y

# 搜索特定作者在最近30天内的论文
pulse search "density functional theory" . -t 30d -a "John Doe"

# 搜索凝聚态物理分类下的论文，限制返回20篇
pulse search "superconductivity" . -c cond-mat --limit 20
```

**设计理念**：简化选项，自动化智能，让搜索更直观高效。

#### `pulse recent` - 生成最近论文报告
**功能**：生成指定时间范围内的论文报告。**如果指定天数大于 0，自动先同步数据库**。时间范围按工作日计算（排除周六和周日）。

```bash
pulse recent [目录路径] -d 7 --limit 50
```

**参数**：
- `--days-back, -d`：包含最近多少天的工作日论文（默认：2天，0 表示不更新数据库）
- `--limit`：报告中包含的最大论文数（默认：64，与REPORT_MAX_PAPERS配置一致）
- `--no-cache`：禁用图片URL缓存

**自动功能**：
- 如果 `--days-back` 大于 0，自动使用 YEARS_BACK 配置更新数据库
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

### 调试

```bash
# 查看详细日志
uvicorn arxiv_pulse.web.app:app --host 127.0.0.1 --port 8000 --log-level debug

# 后台运行日志
tail -f data/web.log
```



## 🔧 高级使用

### 自动化调度

#### 使用 Systemd（Linux）
创建 `/etc/systemd/system/arxiv-pulse.service`：
```ini
[Unit]
Description=arXiv Pulse Literature Crawler
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/your/papers
    ExecStart=/usr/local/bin/pulse sync .
Restart=always
RestartSec=10

## 🔧 高级使用

### 自动化调度

**使用 Systemd（Linux）**
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
2. 检查 `.env` 文件配置和日志文件
3. 查看 `logs/` 目录中的日志文件

---

**arXiv Pulse** - 让 arXiv 文献追踪变得简单高效！