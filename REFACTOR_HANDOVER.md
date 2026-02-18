# ArXiv-Pulse Refactor Handover

## Goal

Refactor the ArXiv-Pulse project to improve code organization, modularity, and maintainability:
- Reduce index.html from 7035 lines (monolithic Vue app) to ~2500 lines ✅
- Create modular Vue components with Pinia stores ✅
- Reorganize Python backend with clear module boundaries (进行中)
- Ensure all functionality works correctly with comprehensive tests

## Instructions

- Keep code simple and elegant
- Commit changes with `REFACTOR` prefix
- Update this file after major changes
- Run `black --check . && ruff check .` before commits
- Test using Playwright at `http://192.168.219.3:33033`

---

# Part 1: Frontend Refactoring (已完成)

## Frontend Progress

| File | Original | Current | Reduction |
|------|----------|---------|-----------|
| index.html | 7035 | 2456 | **-65%** ✅ |

## Vue Components (1070 lines)

- `js/components/PaperCard.js` (315 lines)
- `js/components/FieldSelectorDialog.js` (210 lines)
- `js/components/PaperBasketPanel.js` (115 lines)
- `js/components/SettingsDrawer.js` (115 lines)
- `js/components/CollectionDialogs.js` (270 lines)
- `js/components/ChatWidget.js` (260 lines)

## Pinia Stores (1620 lines)

- `js/stores/configStore.js` (355 lines)
- `js/stores/paperStore.js` (500 lines)
- `js/stores/collectionStore.js` (340 lines)
- `js/stores/chatStore.js` (322 lines)
- `js/stores/uiStore.js` (146 lines)

---

# Part 2: Backend Refactoring (进行中)

## Current Problems

### 1. 重复代码
| 重复项 | 文件位置 | 行数 |
|--------|----------|------|
| `category_explanations` 字典 | `report_generator.py:36` + `services/paper_service.py:11` | ~50行重复 |
| `get_category_explanation()` 函数 | 两处几乎相同的实现 | ~15行重复 |

### 2. 文件职责不清
| 文件 | 问题 |
|------|------|
| `models.py` (693行) | 混合了 ORM 模型 + Database 单例类 |
| `report_generator.py` (778行) | 图片获取、分类解释、翻译、报告生成多职责混杂 |
| `research_fields.py` (438行) | 纯数据文件，可移到 constants/ |

### 3. 根目录文件过多
当前根目录有 10 个 `.py` 文件，缺乏清晰的分层组织。

---

## Target Structure

```
arxiv_pulse/
├── core/                    # 核心基础设施
│   ├── __init__.py
│   ├── config.py           # 配置管理
│   ├── database.py         # Database 单例
│   └── lock.py             # 服务锁
│
├── models/                  # 纯 ORM 模型
│   ├── __init__.py
│   ├── base.py             # Base, engine
│   ├── paper.py            # Paper, TranslationCache, FigureCache, PaperContentCache
│   ├── chat.py             # ChatSession, ChatMessage
│   ├── collection.py       # Collection, CollectionPaper
│   └── system.py           # SyncTask, RecentResult, SystemConfig
│
├── constants/               # 常量和数据
│   ├── __init__.py
│   └── categories.py       # ARXIV_CATEGORIES, CATEGORY_EXPLANATIONS
│
├── services/                # 服务层
│   ├── __init__.py
│   ├── ai_client.py        # AI API 客户端
│   ├── paper_service.py    # 论文数据增强
│   ├── translation_service.py  # 翻译服务
│   ├── category_service.py # 分类解释服务 (合并重复代码)
│   └── figure_service.py   # 图片获取服务 (从 report_generator 分离)
│
├── crawler/                 # 爬虫模块
│   ├── __init__.py
│   └── arxiv.py            # ArXivCrawler
│
├── ai/                      # AI 功能模块
│   ├── __init__.py
│   ├── summarizer.py       # PaperSummarizer
│   └── report.py           # 简化后的 ReportGenerator
│
├── search/                  # 搜索模块
│   ├── __init__.py
│   └── engine.py           # SearchEngine, SearchFilter
│
├── cli/                     # 命令行工具
│   ├── __init__.py
│   └── service.py          # 服务管理
│
├── utils/                   # 工具函数
│   ├── __init__.py
│   ├── sse.py
│   ├── time.py
│   └── output.py           # OutputManager
│
├── web/                     # Web 应用 (保持结构)
├── i18n/                    # 国际化 (保持)
└── __init__.py             # 公共 API 导出
```

---

## Import Mapping (完全不兼容)

| 旧导入 | 新导入 |
|--------|--------|
| `from arxiv_pulse.models import Paper` | `from arxiv_pulse.models import Paper` |
| `from arxiv_pulse.models import Database` | `from arxiv_pulse.core import Database` |
| `from arxiv_pulse.config import Config` | `from arxiv_pulse.core import Config` |
| `from arxiv_pulse.lock import ServiceLock` | `from arxiv_pulse.core import ServiceLock` |
| `from arxiv_pulse.arxiv_crawler import ArXivCrawler` | `from arxiv_pulse.crawler import ArXivCrawler` |
| `from arxiv_pulse.summarizer import PaperSummarizer` | `from arxiv_pulse.ai import PaperSummarizer` |
| `from arxiv_pulse.report_generator import ReportGenerator` | `from arxiv_pulse.ai import ReportGenerator` |
| `from arxiv_pulse.search_engine import SearchEngine` | `from arxiv_pulse.search import SearchEngine` |
| `from arxiv_pulse.output_manager import output` | `from arxiv_pulse.utils import output` |
| `from arxiv_pulse.research_fields import ARXIV_CATEGORIES` | `from arxiv_pulse.constants import ARXIV_CATEGORIES` |
| `from arxiv_pulse.research_fields import get_all_categories` | `from arxiv_pulse.constants import get_all_categories` |

---

## Execution Phases

### Phase 1: 创建目录结构
**操作**: 创建新目录和空 `__init__.py`
```
arxiv_pulse/core/__init__.py
arxiv_pulse/models/__init__.py
arxiv_pulse/constants/__init__.py
arxiv_pulse/crawler/__init__.py
arxiv_pulse/ai/__init__.py
arxiv_pulse/search/__init__.py
arxiv_pulse/cli/__init__.py
```

### Phase 2: 分离 ORM 模型
**操作**: 拆分 `models.py` (693行)
- `models/base.py` - Base 定义
- `models/paper.py` - Paper, TranslationCache, FigureCache, PaperContentCache
- `models/chat.py` - ChatSession, ChatMessage
- `models/collection.py` - Collection, CollectionPaper
- `models/system.py` - SyncTask, RecentResult, SystemConfig

**注意**: Database 类在 Phase 3 处理

### Phase 3: 分离 core/ 模块
**操作**:
- 创建 `core/database.py` - Database 单例类
- 创建 `core/config.py` - 从根目录移动
- 创建 `core/lock.py` - 从根目录移动

### Phase 4: 创建 constants/ 模块
**操作**:
- 创建 `constants/categories.py`
- 移入 `ARXIV_CATEGORIES` (从 `research_fields.py`)
- 移入 `DEFAULT_FIELDS`, `get_all_categories()`, `get_queries_for_fields()`
- 新增 `CATEGORY_EXPLANATIONS` (合并重复数据)
- 新增 `get_category_explanation()` (统一实现)

### Phase 5: 扩充 services/ 模块
**操作**:
- 创建 `services/category_service.py` - 分类解释服务
- 创建 `services/figure_service.py` - 图片获取服务
- 更新 `services/paper_service.py` - 移除重复代码，添加 `calculate_relevance_score()`

### Phase 6: 移动 crawler/ 模块
**操作**:
- 创建 `crawler/arxiv.py` - 移入 ArXivCrawler

### Phase 7: 移动 ai/ 模块
**操作**:
- 创建 `ai/summarizer.py` - 移入 PaperSummarizer
- 创建 `ai/report.py` - 移入简化后的 ReportGenerator

### Phase 8: 移动 search/ 模块
**操作**:
- 创建 `search/engine.py` - 移入 SearchEngine, SearchFilter

### Phase 9: 移动 cli/ 模块
**操作**:
- 创建 `cli/service.py` - 服务管理逻辑
- 更新 `cli/__init__.py` - CLI 入口

### Phase 10: 移动 utils/ 模块
**操作**:
- 创建 `utils/output.py` - 移入 OutputManager

### Phase 11: 更新 API 导入
**操作**: 更新 `web/api/` 下所有文件的导入

### Phase 12: 更新根 `__init__.py` 和清理
**操作**:
- 更新 `arxiv_pulse/__init__.py`
- 删除旧文件: `arxiv_crawler.py`, `config.py`, `lock.py`, `models.py`, `output_manager.py`, `report_generator.py`, `research_fields.py`, `search_engine.py`, `summarizer.py`, `cli.py`

### Phase 13: 测试和提交
**操作**:
- 运行 `black --check . && ruff check .`
- 运行 Playwright 测试
- 最终提交

---

## Files to Delete (Phase 12)

- `arxiv_pulse/arxiv_crawler.py` → `crawler/arxiv.py`
- `arxiv_pulse/config.py` → `core/config.py`
- `arxiv_pulse/lock.py` → `core/lock.py`
- `arxiv_pulse/models.py` → `models/*.py`
- `arxiv_pulse/output_manager.py` → `utils/output.py`
- `arxiv_pulse/report_generator.py` → `ai/report.py`
- `arxiv_pulse/research_fields.py` → `constants/categories.py`
- `arxiv_pulse/search_engine.py` → `search/engine.py`
- `arxiv_pulse/summarizer.py` → `ai/summarizer.py`
- `arxiv_pulse/cli.py` → `cli/__init__.py`

---

## pyproject.toml Updates

入口点保持不变：
```toml
[project.scripts]
pulse = "arxiv_pulse.cli:cli"
```

---

## Testing

使用 Playwright 端到端测试：
```bash
# Start server
pulse serve . -f

# Run tests
cd tests && ../.venv/bin/python test_navigation.py
```

---

## Discoveries

- **Pinia storeToRefs()**: Essential for destructuring store properties while maintaining reactivity.
- **Self-closing tags**: HTML5 browsers don't recognize self-closing tags for custom Vue components.
- **config.py circular dependency**: Uses lazy import `from arxiv_pulse.models import Database` inside `get_db()` to avoid circular imports.
- **Database singleton**: `_instance` and `_engine` are class variables, needs careful handling when moving.

---

## Commit Message Format

```
REFACTOR(phase): Brief description

- Detailed changes
- Files affected
- Import path changes
```
