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

# Part 1: Frontend Refactoring (已完成) ✅

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

## Progress Summary

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Create directory structure | ✅ |
| 2 | Separate ORM models into models/ | ✅ |
| 3 | Move core modules (Config, Database, ServiceLock) | ✅ |
| 4 | Move research_fields to constants/categories.py | ✅ |
| 5 | Extract category_service and figure_service | ✅ |
| 6 | Move ArXivCrawler to crawler/arxiv.py | ✅ |
| 7 | Move PaperSummarizer and ReportGenerator to ai/ | ✅ |
| 8 | Move SearchEngine to search/engine.py | ✅ |
| 9 | Move CLI tools to cli/ | ⏳ |
| 10 | Move OutputManager to utils/ | ⏳ |
| 11 | Update all API imports | ⏳ |
| 12 | Delete old files and update root `__init__.py` | ⏳ |
| 13 | Test and final commit | ⏳ |

## New Structure Created

```
arxiv_pulse/
├── core/                    # ✅ 核心基础设施
│   ├── __init__.py          # Config, Database, ServiceLock exports
│   ├── config.py            # 配置管理
│   ├── database.py          # Database 单例
│   └── lock.py              # 服务锁
│
├── models/                  # ✅ 纯 ORM 模型
│   ├── __init__.py          # All model exports
│   ├── base.py              # Base, DEFAULT_CONFIG, utcnow
│   ├── paper.py             # Paper, TranslationCache, FigureCache, PaperContentCache
│   ├── chat.py              # ChatSession, ChatMessage
│   ├── collection.py        # Collection, CollectionPaper
│   └── system.py            # SyncTask, RecentResult, SystemConfig
│
├── constants/               # ✅ 常量和数据
│   ├── __init__.py          # ARXIV_CATEGORIES exports
│   └── categories.py        # ARXIV_CATEGORIES, DEFAULT_FIELDS, get_all_categories()
│
├── services/                # ✅ 服务层
│   ├── ai_client.py         # AI API 客户端
│   ├── paper_service.py     # 论文数据增强
│   ├── translation_service.py  # 翻译服务
│   ├── category_service.py  # 分类解释服务
│   └── figure_service.py    # 图片获取服务
│
├── crawler/                 # ✅ 爬虫模块
│   ├── __init__.py          # ArXivCrawler export
│   └── arxiv.py             # ArXivCrawler
│
├── ai/                      # ✅ AI 功能模块
│   ├── __init__.py          # PaperSummarizer, ReportGenerator exports
│   ├── summarizer.py        # PaperSummarizer
│   └── report.py            # ReportGenerator
│
├── search/                  # ✅ 搜索模块
│   ├── __init__.py          # SearchEngine, SearchFilter exports
│   └── engine.py            # SearchEngine, SearchFilter
│
├── cli/                     # ⏳ 命令行工具
│   └── __init__.py          # (needs CLI tools)
│
├── utils/                   # ⏳ 工具函数
│   ├── __init__.py          # sse_event, sse_response exports
│   └── sse.py               # SSE utilities
│
├── web/                     # Web 应用 (保持结构)
├── i18n/                    # 国际化 (保持)
└── __init__.py              # 公共 API 导出
```

---

## Import Mapping (已完成 ✅)

| 旧导入 | 新导入 | 状态 |
|--------|--------|------|
| `from arxiv_pulse.models import Paper` | `from arxiv_pulse.models import Paper` | ✅ |
| `from arxiv_pulse.models import Database` | `from arxiv_pulse.core import Database` | ✅ |
| `from arxiv_pulse.config import Config` | `from arxiv_pulse.core import Config` | ✅ |
| `from arxiv_pulse.lock import ServiceLock` | `from arxiv_pulse.core import ServiceLock` | ✅ |
| `from arxiv_pulse.arxiv_crawler import ArXivCrawler` | `from arxiv_pulse.crawler import ArXivCrawler` | ✅ |
| `from arxiv_pulse.summarizer import PaperSummarizer` | `from arxiv_pulse.ai import PaperSummarizer` | ✅ |
| `from arxiv_pulse.report_generator import ReportGenerator` | `from arxiv_pulse.ai import ReportGenerator` | ✅ |
| `from arxiv_pulse.search_engine import SearchEngine` | `from arxiv_pulse.search import SearchEngine` | ✅ |
| `from arxiv_pulse.research_fields import ARXIV_CATEGORIES` | `from arxiv_pulse.constants import ARXIV_CATEGORIES` | ✅ |
| `from arxiv_pulse.research_fields import get_all_categories` | `from arxiv_pulse.constants import get_all_categories` | ✅ |
| `from arxiv_pulse.output_manager import output` | `from arxiv_pulse.utils import output` | ⏳ |

---

## Files to Delete (Phase 12)

| Old File | New Location | Status |
|----------|--------------|--------|
| `arxiv_pulse/arxiv_crawler.py` | `crawler/arxiv.py` | ✅ created |
| `arxiv_pulse/config.py` | `core/config.py` | ✅ created |
| `arxiv_pulse/lock.py` | `core/lock.py` | ✅ created |
| `arxiv_pulse/models.py` | `models/*.py` | ✅ created |
| `arxiv_pulse/output_manager.py` | `utils/output.py` | ⏳ |
| `arxiv_pulse/report_generator.py` | `ai/report.py` | ✅ created |
| `arxiv_pulse/research_fields.py` | `constants/categories.py` | ✅ created |
| `arxiv_pulse/search_engine.py` | `search/engine.py` | ✅ created |
| `arxiv_pulse/summarizer.py` | `ai/summarizer.py` | ✅ created |
| `arxiv_pulse/cli.py` | `cli/__init__.py` | ⏳ |

---

## Discoveries

- **LSP errors are false positives**: SQLAlchemy Column type errors in Python files don't affect runtime
- **Pinia storeToRefs()**: Essential for destructuring store properties while maintaining reactivity
- **Self-closing Vue component tags**: HTML5 browsers don't recognize self-closing tags for custom elements
- **Config circular dependency**: Uses lazy import `from arxiv_pulse.models import Database` inside `get_db()` to avoid circular imports
- **Database singleton**: `_instance` and `_engine` are class variables requiring careful handling during move

---

## Commit Message Format

```
REFACTOR(phase): Brief description
```

---

## Next Steps

1. Phase 9: Move CLI tools to cli/
2. Phase 10: Move OutputManager to utils/output.py
3. Phase 11: Update remaining API imports in web/api/
4. Phase 12: Delete old files and update root `__init__.py`
5. Phase 13: Test and final commit
