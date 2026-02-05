# arXiv Pulse - 智能 arXiv 文献追踪系统

[![Version](https://img.shields.io/pypi/v/arxiv-pulse.svg)](https://pypi.org/project/arxiv-pulse/)
![Python](https://img.shields.io/badge/python-3.12%2B-green)
![License](https://img.shields.io/badge/license-GPL--3.0-orange)

> 🌐 **语言说明**：本文档为中文版本。

**arXiv Pulse** 是一个 Python 包，用于自动化爬取、总结和跟踪 arXiv 在凝聚态物理、密度泛函理论（DFT）、机器学习、力场和相关计算材料科学领域的最新研究论文。提供简化的命令行界面，通过 **5 个核心命令** 提供专业级的文献管理体验。

## ✨ 核心功能

- **📦 极简设计**：**5 个核心命令**覆盖完整文献管理流程
- **🔍 智能搜索**：支持自然语言查询，AI 自动解析为学术关键词
- **🤖 AI 总结**：使用 OpenAI 兼容 API（如 DeepSeek、Paratera AI 等）生成简洁摘要和中文翻译
- **💾 数据库存储**：SQLite 数据库存储完整论文元数据
- **📊 智能报告**：自动同步最新论文后生成报告，确保数据时效性
- **🔄 自动同步**：搜索和报告前自动更新数据库，保持数据最新
- **💰 成本透明**：准确跟踪 API 使用费用，优化成本控制
- **🎯 专注科研**：专为凝聚态物理、DFT、机器学习、力场等研究领域优化
- **🎛️ 交互式配置**：引导式配置向导，支持 30+ 研究领域选择
- **🧠 智能建议**：基于选择领域数量自动推荐优化配置
- **🌐 通用 AI API**：支持所有 OpenAI 兼容服务（DeepSeek、Paratera AI 等）

## 🚀 快速开始

### 安装方式

**方式一：从 PyPI 安装**
```bash
pip install arxiv-pulse
```

**方式二：从源码安装（开发模式）**
```bash
git clone https://github.com/kYangLi/ArXiv-Pulse.git
cd ArXiv-Pulse
pip install -e .
```

### 基本使用流程

1. **初始化工作目录并同步历史论文**
   ```bash
   mkdir my_papers && cd my_papers
   pulse init .  # 自动创建目录并同步5年历史论文
   ```

   首次初始化时，配置向导将引导您完成：
   - 🔧 **AI API 配置**：设置 API 密钥、模型和 Base URL（支持所有 OpenAI 兼容服务）
   - 📊 **爬虫配置**：调整初始/每日最大论文数、回溯年数
   - 🎯 **研究领域选择**：从 30+ 专业领域中选择您关注的领域
   - 📈 **智能建议**：基于选择领域数量自动推荐优化配置
   - 📄 **报告配置**：设置报告最大论文数和摘要句子限制
   
   **重新配置**：如果需要修改配置，可以删除 `.env` 文件后重新运行 `pulse init .`。

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

## 📋 核心命令参考

### 全局选项

所有命令都支持以下全局选项：

- `-v, --verbose`：显示详细输出（包括调试信息）
- `--version`：显示版本信息
- `-h, --help`：显示命令帮助信息

**日志级别控制**：
- 默认输出级别为 `INFO`，隐藏调试信息
- 使用 `--verbose` 选项显示所有调试信息
- 通过环境变量 `LOG_LEVEL` 设置默认级别：`DEBUG`、`INFO`、`WARNING`、`ERROR`

### 5个核心命令

| 命令 | 说明 | 关键特性 |
|------|------|----------|
| **`pulse init`** | 初始化目录并自动同步历史论文 | ✅ 一键创建目录结构<br>✅ 自动同步5年历史论文<br>✅ 创建 `.env` 配置模板 |
| **`pulse sync`** | 同步最新论文到数据库 | ✅ 专注于数据更新<br>✅ 普通模式和强制模式<br>✅ 不自动生成报告 |
| **`pulse search`** | 智能搜索论文（支持自然语言查询） | ✅ AI解析自然语言查询（有AI key时）<br>✅ 灵活的时间范围过滤<br>✅ 自动总结搜索结果（有AI key时）<br>✅ 生成详细Markdown/CSV报告<br>✅ 包含中文翻译和PDF链接 |
| **`pulse recent`** | 生成最近论文报告 | ✅ 指定天数自动更新数据库<br>✅ 按工作日计算时间范围<br>✅ 自动总结未总结论文<br>✅ 生成Markdown和CSV格式报告 |
| **`pulse stat`** | 显示数据库统计信息 | ✅ 查看论文总数和总结率<br>✅ 分析论文分类和领域分布<br>✅ 查看时间分布和趋势 |

### 命令详细说明

#### `pulse init` - 初始化目录并同步历史论文
**功能**：创建必要的目录结构、配置模板，并通过交互式向导配置系统，然后自动同步历史论文。

```bash
pulse init [目录路径]
```

**交互式配置**：
首次运行时会引导您完成以下配置：
- 🔧 **AI API 配置**：设置 API 密钥、模型和 Base URL
- 📊 **爬虫配置**：调整初始/每日最大论文数、回溯年数
- 🎯 **研究领域选择**：从 30+ 专业领域中选择您关注的领域
- 📈 **智能建议**：基于选择领域数量自动推荐优化配置
- 📄 **报告配置**：设置报告最大论文数

**注意**：
- 如果 `.env` 文件已存在，将直接使用现有配置，不再进行交互式配置
- 回溯年数在交互式配置中设置，或者在 `.env` 文件中的 `YEARS_BACK` 配置

**创建的文件结构**：
```
[工作目录]/
├── data/                    # 数据库存储目录
│   └── important_papers.txt # 重要论文列表（在data目录内）
├── reports/                 # 报告输出目录  
└── .env                     # 环境配置文件（由.ENV.TEMPLATE生成）
```

**设计理念**：一键完成所有初始化工作，无需额外步骤。

#### `pulse sync` - 同步最新论文
**功能**：同步最新论文到数据库，不生成报告。支持普通模式和强制模式。

```bash
# 普通模式：只下载缺失的新论文，默认回溯1年
pulse sync [目录路径] --years-back 1 --no-summarize

# 强制模式：重新下载最近N年的所有论文，忽略重复检查，默认回溯5年
pulse sync [目录路径] --force --years-back 5 --no-summarize
```

**参数**：
- `--years-back`：同步回溯的年数（默认：强制模式5年，普通模式1年）
- `--summarize/--no-summarize`：是否总结新论文（默认：否）
- `--force`：强制同步：重新下载最近N年的所有论文，忽略重复检查，默认回溯5年

**使用场景**：
- **普通模式**：日常更新，只获取最新发布的论文
- **强制模式**：初始化新数据库、修复数据缺失、更新配置后重新获取历史论文

**设计理念**：专注于数据更新，提供灵活的同步策略，让用户根据需求选择普通更新或完全重新同步。

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
- 如果配置了AI API密钥，自动总结未总结的论文
- 自动生成包含中文翻译的Markdown和CSV报告

**工作日计算**：由于 arXiv 在周末（周六和周日）不发布新论文，系统会自动排除周末，仅计算工作日。例如，`-d 7` 会返回最近 7 个工作日（约 9-10 个日历天）的论文。

**使用示例**：
```bash
# 生成最近7个工作日的报告，并自动更新数据库
pulse recent . -d 7

# 生成最近30个工作日的报告，不限制返回数量
pulse recent . -d 30 --limit 100

# 只生成报告，不更新数据库
pulse recent . -d 0
```

**设计理念**：简化选项，自动化处理，天数 > 0 时自动更新数据库。

#### `pulse stat` - 显示数据库统计信息
**功能**：查看arXiv Pulse数据库的详细统计信息，包括论文数量、分类分布、时间趋势和总结进度。

```bash
pulse stat [目录路径]
```

**显示的统计信息**：
1. **基本统计**：总论文数、今日论文数、已总结论文数、总结率
2. **搜索查询分布**：按不同搜索查询的论文分布情况
3. **分类统计**：前10个热门分类的论文数量
4. **时间分布**：最近5年的论文数量趋势
5. **AI总结统计**：已总结、待总结论文数量和总结率

**设计理念**：提供全面的数据库洞察，帮助用户了解文献分布和研究趋势。

## ⚙️ 配置说明

### 环境变量（`.env` 文件）

初始化目录时会自动创建 `.env` 配置文件，或首次运行 `pulse init .` 时通过交互式配置生成。所有配置项均支持通过环境变量覆盖。

**主要配置类别：**

1. **AI API 配置** - 支持所有 OpenAI 兼容服务（DeepSeek、Paratera AI、OpenAI 等）
2. **数据库配置** - SQLite 数据库连接设置
3. **爬虫配置** - 论文获取限制、排序方式、API 参数
4. **搜索查询配置** - 分号分隔的研究领域查询列表
5. **报告配置** - 报告生成、AI 总结、费用估算设置
6. **同步配置** - 回溯年数、重要论文追踪
7. **日志配置** - 输出级别、爬虫延迟

**详细配置说明请参考 `arxiv_pulse/.ENV.TEMPLATE` 文件，其中包含完整的配置项列表、默认值和详细注释。**

**使用建议：**
- 首次使用建议运行 `pulse init .` 通过交互式配置向导自动生成优化配置
- 如需手动配置，将 `.ENV.TEMPLATE` 复制为 `.env` 并根据需要修改
- 交互式配置向导支持 30+ 个专业研究领域选择，并基于选择数量提供智能参数建议

### 研究领域

系统支持 30+ 个专业研究领域，通过交互式配置向导选择：

#### 🧪 物理学领域
- **凝聚态物理**：电子结构、超导、磁性、强关联系统
- **天体物理**：宇宙学、恒星物理、星系形成
- **高能物理**：粒子物理、量子场论、标准模型
- **核物理**：核结构、核反应、重离子碰撞
- **广义相对论**：引力波、黑洞、宇宙学
- **量子物理**：量子信息、量子计算、量子光学
- **统计物理**：相变、临界现象、非平衡统计
- **软凝聚态物理**：生物物理、胶体、聚合物
- **材料物理**：电子材料、光学材料、磁性材料
- **光学物理**：非线性光学、量子光学、光子学

#### 💻 计算材料科学
- **密度泛函理论（DFT）**：第一性原理计算、电子结构
- **第一性原理计算**：ab initio 方法、从头计算
- **量子化学**：电子结构方法、波函数理论
- **分子动力学**：经典分子动力学、反应力场
- **力场开发**：原子间势、反应力场、机器学习力场
- **多尺度建模**：从原子到宏观的跨尺度模拟
- **计算化学**：化学反应、催化、分子设计
- **计算生物物理**：蛋白质折叠、分子对接、药物设计

#### 🧮 数学与计算机科学
- **数学物理**：数学方法在物理中的应用
- **数值分析**：数值方法、计算算法
- **人工智能**：机器学习、深度学习、强化学习
- **计算机视觉**：图像处理、模式识别
- **自然语言处理**：文本分析、语言模型
- **数据科学**：数据分析、可视化、统计学习
- **计算机科学**：算法、系统、网络

#### 🌐 跨学科领域
- **定量生物学**：系统生物学、计算生物学
- **定量金融**：金融建模、风险管理
- **电子工程**：半导体、微电子、光电子
- **经济学**：计量经济学、经济建模

通过首次运行 `pulse init .` 交互式选择您关注的领域，系统会自动生成优化的搜索查询和配置建议。

## 📁 项目结构

```
arxiv_pulse/                    # Python 包源码
├── __init__.py                # 包初始化
├── arxiv_crawler.py           # arXiv API 交互
├── cli.py                     # 命令行接口（主入口点）
├── config.py                  # 配置管理
├── models.py                  # 数据库模型
├── output_manager.py          # 统一输出管理
├── report_generator.py        # 报告生成器
├── search_engine.py           # 增强搜索引擎
├── summarizer.py              # 论文总结器
└── .ENV.TEMPLATE              # 环境配置模板文件

 项目根目录/
├── pyproject.toml             # 包配置和依赖
├── README.md                  # 本文档
├── LICENSE                    # GPL-3.0 许可证
└── .gitignore                 # Git 忽略文件

工作目录（用户使用）/
├── .env                       # 环境配置文件（由.ENV.TEMPLATE生成）
├── data/                      # 数据库存储
│   ├── arxiv_papers.db        # SQLite数据库文件
│   └── important_papers.txt   # 重要论文列表
└── reports/                   # 生成的报告目录
```

## 🗂️ 输出文件

### 数据库
- 位置：`data/arxiv_papers.db` (SQLite)
- 包含：论文元数据、摘要、AI 总结、处理状态

### 报告文件
- **搜索结果报告**：`reports/search_YYYYMMDD_HHMMSS.md` 和 `.csv` (通过 `pulse search` 生成)
- **最近论文报告**：`reports/recent_YYYYMMDD_HHMMSS.md` 和 `.csv` (通过 `pulse recent` 生成)
- **报告内容**：论文详情、AI总结、中文翻译、相关度评级、费用统计、PDF链接



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

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable arxiv-pulse
sudo systemctl start arxiv-pulse
```

#### 使用 Cron
添加到 crontab（`crontab -e`）：
```
0 8 * * * cd /path/to/your/papers && pulse sync .
```

### 自定义搜索查询

编辑 `.env` 文件中的 `SEARCH_QUERIES` 变量：
- 使用分号（`;`）分隔多个查询
- 查询中可以包含逗号
- 支持标准的 arXiv 搜索语法

示例：
```bash
SEARCH_QUERIES=condensed matter physics AND cat:cond-mat.*; quantum computing AND cat:quant-ph; machine learning AND cat:cs.LG
```

### 重要论文追踪

在 `important_papers.txt` 文件中添加 arXiv ID（每行一个）：
```
# 重要论文列表
2401.12345v1
2402.67890v2
cond-mat/24030001
```

系统会自动跟踪这些论文的更新和引用。

## 🐛 故障排除

### 常见问题

#### 数据库连接错误
```bash
# 检查数据库文件
ls -la data/
sqlite3 data/arxiv_papers.db ".tables"
```

#### AI API 错误
1. 确认 `.env` 文件中设置了 `AI_API_KEY`
2. 检查 API 密钥是否有效且有余额
3. 检查 `.env` 文件中的配置是否正确（Base URL、模型名称等）
4. 确认 API 服务支持 OpenAI 格式的调用

#### 路径问题
如果遇到文件未找到错误，确保：
1. 在工作目录中运行命令（或指定完整路径）
2. 已运行 `pulse init .` 初始化目录
3. 数据库路径为绝对路径（自动处理）

#### arXiv 周末无更新
**现象**：周末运行 `pulse recent` 或 `pulse sync` 时可能找不到新论文。
**原因**：arXiv 在周末（周六和周日）不发布新论文。
**解决方案**：
- 这是正常现象，不是系统错误
- 工作日计算功能会自动排除周末
- 建议在工作日（周一至周五）使用系统获取最新论文

### 调试和验证

#### 验证基本功能
```bash
# 初始化一个新目录测试基本功能
mkdir test_pulse && cd test_pulse
pulse init . --years-back 0
```

#### 查看日志文件
```bash
# 查看最近的操作日志
ls -la logs/
tail -f logs/summarizer.log
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