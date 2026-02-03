# arXiv Pulse - 智能 arXiv 文献追踪系统

[![Version](https://img.shields.io/pypi/v/arxiv-pulse.svg)](https://pypi.org/project/arxiv-pulse/)
![Python](https://img.shields.io/badge/python-3.12%2B-green)
![License](https://img.shields.io/badge/license-GPL--3.0-orange)

> 🌐 **语言说明**：本文档为中文版本。

**arXiv Pulse** 是一个 Python 包，用于自动化爬取、总结和跟踪 arXiv 在凝聚态物理、密度泛函理论（DFT）、机器学习、力场和相关计算材料科学领域的最新研究论文。提供简化的命令行界面，通过 **8 个核心命令** 提供专业级的文献管理体验。

## ✨ 核心功能

- **📦 极简设计**：**4 个核心命令**覆盖完整文献管理流程
- **🔍 智能搜索**：支持自然语言查询，AI 自动解析为学术关键词
- **🔬 高级搜索**：多字段精细过滤（分类、作者、时间范围等）
- **🔗 相似推荐**：基于分类重叠查找相似论文，拓展研究视野
- **📋 搜索历史**：记录和重用成功搜索，提高检索效率
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

### 8个核心命令

| 命令 | 说明 | 关键特性 |
|------|------|----------|
| **`pulse init`** | 初始化目录并自动同步历史论文 | ✅ 一键创建目录结构<br>✅ 自动同步5年历史论文<br>✅ 创建 `.env` 配置模板 |
| **`pulse sync`** | 同步最新论文到数据库 | ✅ 专注于数据更新<br>✅ 可选择是否总结新论文<br>✅ 不自动生成报告 |
| **`pulse search`** | 智能搜索论文（支持自然语言查询） | ✅ AI解析自然语言查询<br>✅ 自动前置同步确保数据最新<br>✅ 生成详细Markdown/CSV报告<br>✅ 包含中文翻译和PDF链接 |
| **`pulse search-advanced`** | 高级搜索论文（支持多字段过滤） | ✅ AI解析自然语言查询<br>✅ 多字段精细过滤（分类、作者、时间等）<br>✅ 多种排序选项和匹配逻辑<br>✅ 生成详细报告 |
| **`pulse similar`** | 查找与指定论文相似的论文 | ✅ 基于分类重叠计算相似度<br>✅ 可调节相似度阈值<br>✅ 发现相关研究方向<br>✅ 生成详细报告 |
| **`pulse search-history`** | 显示搜索历史（按使用频率排序） | ✅ 查看最常用的搜索查询<br>✅ 统计使用频率和最后使用时间<br>✅ 快速重用成功搜索 |
| **`pulse recent`** | 生成最近论文报告 | ✅ 先同步再报告，数据时效性强<br>✅ 自定义报告时间范围和论文数量<br>✅ 生成Markdown和CSV格式报告 |
| **`pulse stat`** | 显示数据库统计信息 | ✅ 查看论文总数和总结率<br>✅ 分析论文分类和领域分布<br>✅ 查看时间分布和趋势 |

### 命令详细说明

#### `pulse init` - 初始化目录并同步历史论文
**功能**：创建必要的目录结构、配置模板，并自动同步指定年数的历史论文。

```bash
pulse init [目录路径] --years-back 5
```

**参数**：
- `--years-back`：初始同步回溯的年数（默认：5年）

**创建的文件结构**：
```
[工作目录]/
├── data/                    # 数据库存储目录
├── reports/                 # 报告输出目录  
├── logs/                    # 日志目录
├── .env                     # 环境配置文件模板
└── important_papers.txt     # 重要论文列表
```

**设计理念**：一键完成所有初始化工作，无需额外步骤。

#### `pulse sync` - 同步最新论文
**功能**：仅同步最新论文到数据库，不生成报告。

```bash
pulse sync [目录路径] --years-back 1 --no-summarize
```

**参数**：
- `--years-back`：同步回溯的年数（默认：1年）
- `--summarize/--no-summarize`：是否总结新论文（默认：否）

**设计理念**：专注于数据更新，让用户控制是否总结论文。

#### `pulse search` - 智能搜索论文
**功能**：在数据库中搜索论文，支持自然语言查询和AI解析。

```bash
pulse search "查询内容" [目录路径] --years-back 1 --use-ai --limit 20
```

**参数**：
- `--years-back`：搜索前同步回溯的年数（默认：1年，0表示不更新）
- `--use-ai/--no-ai`：是否使用AI理解自然语言查询（默认：是）
- `--limit`：返回结果的最大数量（默认：20）

**AI搜索示例**：
```bash
# AI会将自然语言查询解析为学术关键词
pulse search "我想找关于机器学习在材料科学中的应用" . --use-ai
# 可能解析为：["machine learning materials science", "AI for materials", "computational materials design"]
```

**设计理念**：搜索前自动同步确保数据最新，AI增强提高搜索精度。

#### `pulse recent` - 生成最近论文报告
**功能**：先同步最新论文，然后生成指定时间范围内的报告。**从 v0.5.0 开始，时间范围按工作日计算（排除周六和周日）**。

```bash
pulse recent [目录路径] --days-back 7 --limit 50 --years-back 1
```

**参数**：
- `--days-back`：包含最近多少天的论文（默认：7天，按工作日计算）
- `--limit`：报告中包含的最大论文数（默认：50）
- `--years-back`：报告前同步回溯的年数（默认：1年）

**工作日计算**：由于 arXiv 在周末（周六和周日）不发布新论文，系统会自动排除周末，仅计算工作日。例如，`--days-back 7` 会返回最近 7 个工作日（约 9-10 个日历天）的论文。

**设计理念**：先同步再报告，确保报告基于最新数据，避免滞后。工作日计算更符合 arXiv 的实际发布周期。

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

#### `pulse search-advanced` - 高级搜索论文
**功能**：支持多字段精细过滤的高级搜索，满足复杂文献检索需求。

```bash
pulse search-advanced "查询内容" [目录路径] --categories 分类1 --categories 分类2 --date-from 2026-01-01 --summarized-only
```

**参数**：
- `--categories, -c`：包含的分类（可多次使用）
- `--exclude-categories, -ec`：排除的分类（可多次使用）
- `--primary-category, -pc`：主要分类
- `--authors, -a`：作者姓名（可多次使用）
- `--author-match`：作者匹配方式（contains/exact/any，默认：contains）
- `--date-from`：起始日期（格式：YYYY-MM-DD）
- `--date-to`：结束日期（格式：YYYY-MM-DD）
- `--days-back`：回溯天数（例如：30表示最近30天）
- `--summarized-only/--no-summarized-only`：仅显示已总结的论文
- `--downloaded-only/--no-downloaded-only`：仅显示已下载的论文
- `--sort-by`：排序字段（published/relevance_score/title/updated/created_at，默认：published）
- `--sort-order`：排序顺序（asc/desc，默认：desc）
- `--match-all/--match-any`：匹配所有条件（AND逻辑）或任一条件（OR逻辑）

**设计理念**：为科研工作者提供专业级的文献检索工具，支持复杂查询和精细过滤。

#### `pulse similar` - 查找相似论文
**功能**：基于分类重叠查找与指定论文相似的论文，帮助发现相关研究。

```bash
pulse similar [arXiv ID] [目录路径] --threshold 0.5 --limit 10
```

**参数**：
- `--threshold`：相似度阈值（0.0-1.0，默认：0.5）
- `--limit`：返回结果的最大数量（默认：10）
- `--years-back`：搜索前同步回溯的年数（默认：0，不更新）

**算法**：计算分类重叠相似度 = 共同分类数 / 总分类数，返回相似度≥阈值的论文。

**设计理念**：帮助研究者拓展文献视野，发现相关研究方向，避免信息孤岛。

#### `pulse search-history` - 显示搜索历史
**功能**：显示最常用的搜索查询及其使用频率，便于快速重用成功搜索。

```bash
pulse search-history [目录路径] --limit 10
```

**参数**：
- `--limit`：显示的搜索查询数量（默认：10）

**显示信息**：
1. **搜索查询**：查询内容
2. **使用次数**：该查询的使用频率统计
3. **最后使用**：最近一次使用该查询的时间
4. **最后论文ID**：最近一次使用该查询找到的论文ID

**设计理念**：提高搜索效率，通过历史记录快速重用成功搜索，避免重复构建复杂查询。

## ⚙️ 配置说明

### 环境变量（`.env` 文件）

初始化目录时会自动创建 `.env` 模板文件，或首次运行 `pulse init .` 时通过交互式配置生成：

```bash
# AI API 配置 (支持所有 OpenAI 兼容服务，如 DeepSeek、Paratera AI、OpenAI 等)
AI_API_KEY=your_api_key_here
AI_MODEL=DeepSeek-V3.2-Thinking
AI_BASE_URL=https://llmapi.paratera.com

# 数据库配置
DATABASE_URL=sqlite:///data/arxiv_papers.db

# 爬虫配置
MAX_RESULTS_INITIAL=100    # init命令每个查询的论文数
MAX_RESULTS_DAILY=20       # sync命令每个查询的论文数

# 搜索查询（分号分隔，允许查询中包含逗号）
# 通过交互式配置选择研究领域后自动生成
SEARCH_QUERIES=condensed matter physics AND cat:cond-mat.*; (ti:"density functional" OR abs:"density functional") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci OR cat:physics.chem-ph); (ti:"machine learning" OR abs:"machine learning") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci OR cat:physics.chem-ph); (ti:"force field" OR abs:"force field") AND (cat:physics.comp-ph OR cat:cond-mat.soft OR cat:physics.chem-ph); (ti:"first principles" OR abs:"first principles" OR ti:"ab initio" OR abs:"ab initio") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci); (ti:"molecular dynamics" OR abs:"molecular dynamics") AND (cat:physics.comp-ph OR cat:cond-mat.soft OR cat:physics.chem-ph); (ti:"quantum chemistry" OR abs:"quantum chemistry") AND (cat:physics.chem-ph OR cat:physics.comp-ph); cat:cond-mat.mtrl-sci AND (ti:"computational" OR abs:"computational" OR ti:"simulation" OR abs:"simulation")

# 报告配置
REPORT_DIR=reports
SUMMARY_MAX_TOKENS=2000    # 总结和翻译的最大token数
SUMMARY_SENTENCES_LIMIT=3
TOKEN_PRICE_PER_MILLION=3.0
REPORT_MAX_PAPERS=50

# 同步配置
YEARS_BACK=3               # 同步回溯的年数
IMPORTANT_PAPERS_FILE=important_papers.txt
```

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
└── summarizer.py              # 论文总结器

项目根目录/
├── pyproject.toml             # 包配置和依赖
├── README.md                  # 本文档
├── LICENSE                    # GPL-3.0 许可证

└── .gitignore                 # Git 忽略文件

工作目录（用户使用）/
├── .env                       # 环境配置
├── data/                      # 数据库存储
├── reports/                   # 生成的报告
├── logs/                      # 应用日志
└── important_papers.txt       # 重要论文列表
```

## 🗂️ 输出文件

### 数据库
- 位置：`data/arxiv_papers.db` (SQLite)
- 包含：论文元数据、摘要、AI 总结、处理状态

### 报告文件
- **搜索结果报告**：`reports/search_YYYYMMDD_HHMMSS.md` 和 `.csv` (通过 `pulse search` 生成)
- **最近论文报告**：`reports/recent_YYYYMMDD_HHMMSS.md` 和 `.csv` (通过 `pulse recent` 生成)
- **报告内容**：论文详情、AI总结、中文翻译、相关度评级、费用统计、PDF链接

### 日志
- `logs/arxiv_pulse.log` - 主要应用日志
- `logs/summarizer.log` - 总结器日志

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

## 📋 更新日志

### v0.5.3 (2026-02-03)

**重要修复和改进：**

1. **弃用警告修复**：
   - 修复 Python 3.12+ 中 `datetime.utcnow()` 弃用问题
   - 替换为 `datetime.now(timezone.utc).replace(tzinfo=None)`
   - 更新所有相关文件：`search_engine.py`, `cli.py`, `report_generator.py`, `models.py`

2. **横幅显示优化**：
   - 使用 `wcwidth` 库精确计算中文字符显示宽度
   - 实现智能截断功能，长字段自动添加省略号
   - 确保边框完美对齐，提升视觉体验

3. **搜索算法改进**：
   - 简化三层匹配策略：短语匹配 → 顺序匹配 → 单词AND匹配
   - 修复多单词查询逻辑错误（OR改为AND逻辑）
   - 限制搜索字段为 `["title", "abstract"]`，提高准确性

4. **代码质量提升**：
   - 修复 `cli.py` 中的缩进错误
   - 更新版本信息元数据
   - 重新安装包确保一致性

### v0.5.0 (2025-02-03)

- 交互式配置向导，支持 30+ 研究领域选择
- 智能建议：基于选择领域数量自动推荐优化配置
- 工作日计算：时间范围排除周六和周日
- 通用 AI API：支持所有 OpenAI 兼容服务（DeepSeek、Paratera AI 等）

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