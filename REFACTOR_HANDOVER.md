# ArXiv-Pulse 重构 Handover 文档

## 已完成的重构（Session 1）

### 后端

| 文件 | 行数 | 作用 |
|------|------|------|
| `web/dependencies.py` | 13 | 统一数据库依赖注入，所有 API 使用 `from arxiv_pulse.web.dependencies import get_db` |
| `utils/__init__.py` | 15 | 工具模块导出 |
| `utils/sse.py` | 38 | SSE 工具函数：`sse_event()`, `sse_log()`, `sse_response()`, `SSE_HEADERS` |
| `utils/time.py` | 43 | 时间工具（原有，已迁移） |
| `services/ai_client.py` | 22 | AI client 单例：`get_ai_client()`, `get_model_name()` |

### 前端

| 文件 | 行数 | 作用 |
|------|------|------|
| `js/i18n/zh.js` | 287 | 中文翻译 |
| `js/i18n/en.js` | 287 | 英文翻译 |
| `js/utils/export.js` | 60 | 统一导出函数：`exportPapers()`, `exportCollection()`, `showMessage()` |

### 已删除的重复代码

- `get_db()` 函数：8 处 → 1 处
- SSE headers：6 处 → 1 处
- `sse_event()` 函数：2 处 → 1 处
- i18n 内联：577 行 → 独立文件
- index.html：7035 → 6460 行（-575 行）

---

## 待重构项（优先级排序）

### P0 - 高优先级

#### 1. 拆分 papers.py（1068 行 → ~200 行）

**问题**：`papers.py` 包含搜索、同步、缓存、翻译等多种职责

**建议拆分**：
```
arxiv_pulse/
├── services/
│   ├── paper_service.py      # enhance_paper_data, calculate_relevance_score
│   ├── translation_service.py # translate_text, get_translation_cache
│   └── figure_service.py      # get_figure_url_cached, fetch_and_cache_figure
└── web/api/
    ├── papers.py              # 仅路由定义
    └── search.py              # 搜索相关端点
```

**具体操作**：
1. 将 `enhance_paper_data()` 移到 `services/paper_service.py`
2. 将翻译相关函数移到 `services/translation_service.py`
3. 将图片缓存函数移到 `services/figure_service.py`
4. 将搜索端点（`/search/stream`, `/search`）移到 `api/search.py`

#### 2. 提取前端 Vue 组件

**问题**：`index.html` 仍有 6460 行，组件逻辑混杂

**建议提取的组件**：
```
web/static/
├── js/
│   └── components/
│       ├── PaperCard.js       # 论文卡片组件
│       ├── CollectionCard.js  # 收藏集卡片
│       ├── StatCard.js        # 统计卡片
│       ├── ChatWidget.js      # AI 对话组件
│       ├── FieldSelector.js   # 领域选择器
│       ├── CartPanel.js       # 暂存篮面板
│       └── EmptyState.js      # 空状态组件
└── css/
    └── main.css               # 从 index.html 提取 <style>
```

### P1 - 中优先级

#### 3. 统一前端 API 调用层

**问题**：API 调用分散在各处，有 43 处 `API_BASE` 引用

**建议**：
```javascript
// js/services/api.js
const API = {
    config: {
        get: () => fetch(`${API_BASE}/config`),
        update: (data) => fetch(`${API_BASE}/config`, { method: 'PUT', ... }),
        testAI: (data) => fetch(`${API_BASE}/config/test-ai`, { ... }),
    },
    papers: {
        recent: (params) => fetch(`${API_BASE}/papers/recent/cache/stream?${params}`),
        search: (params) => fetch(`${API_BASE}/papers/search/stream?${params}`),
        // ...
    },
    collections: {
        list: () => fetch(`${API_BASE}/collections`),
        get: (id) => fetch(`${API_BASE}/collections/${id}`),
        // ...
    }
};
```

#### 4. 提取 CSS 到独立文件

**问题**：index.html 内联约 2400 行 CSS

**建议**：
```html
<link rel="stylesheet" href="css/main.css">
```

### P2 - 低优先级

#### 5. 引入 Pinia 状态管理

**问题**：114 个 `ref()` 状态分散在 setup() 中

**建议**：
```javascript
// js/stores/paperStore.js
import { defineStore } from 'pinia';
export const usePaperStore = defineStore('paper', {
    state: () => ({
        papers: [],
        selectedIds: [],
        // ...
    }),
    actions: {
        async fetchRecent() { ... }
    }
});
```

#### 6. 后端 Repository 模式

**问题**：数据库查询逻辑直接在 API 中

**建议**：
```python
# repositories/paper_repository.py
class PaperRepository:
    def __init__(self, session):
        self.session = session
    
    def get_by_id(self, paper_id: int) -> Paper | None:
        return self.session.query(Paper).filter_by(id=paper_id).first()
    
    def get_recent(self, days: int, limit: int) -> list[Paper]:
        # ...
```

---

## 当前项目结构

```
arxiv_pulse/
├── __init__.py
├── __version__.py
├── arxiv_crawler.py      # arXiv API 交互
├── cli.py                # CLI 入口
├── config.py             # 配置管理
├── i18n/                 # Python i18n（后端）
│   ├── __init__.py
│   ├── zh.py
│   └── en.py
├── lock.py
├── models.py             # SQLAlchemy 模型
├── output_manager.py
├── report_generator.py
├── research_fields.py    # 研究领域定义
├── search_engine.py      # 搜索引擎
├── summarizer.py         # AI 总结
├── services/             # ✅ 新增
│   └── ai_client.py
├── utils/                # ✅ 新增
│   ├── __init__.py
│   ├── sse.py
│   └── time.py
└── web/
    ├── app.py
    ├── dependencies.py   # ✅ 新增
    ├── api/
    │   ├── __init__.py
    │   ├── cache.py
    │   ├── chat.py
    │   ├── collections.py
    │   ├── config.py
    │   ├── export.py
    │   ├── papers.py     # ⚠️ 需要拆分
    │   ├── stats.py
    │   └── tasks.py
    └── static/
        ├── index.html    # ⚠️ 需要继续拆分
        ├── libs/
        └── js/           # ✅ 新增
            ├── i18n/
            │   ├── zh.js
            │   └── en.js
            └── utils/
                └── export.js
```

---

## 代码规范（来自 AGENTS.md）

### 后端
- Import 顺序：标准库 → 第三方 → 本地
- 命名：类 PascalCase，函数/变量 snake_case
- 数据库 session：使用 `with get_db().get_session() as session:`
- SSE：使用 `from arxiv_pulse.utils import sse_event, sse_response`
- 错误处理：API 中使用 `HTTPException`

### 前端
- Vue 3 Composition API
- Element Plus 组件库
- i18n：使用 `t('key.path')` 函数
- 事件冒泡：使用 `@click.stop`

---

## 测试命令

```bash
# 后端测试
python -c "from arxiv_pulse.web.api import papers, collections, chat, tasks, stats, export, cache, config; print('OK')"
python -c "from arxiv_pulse.utils import sse_event, sse_response; print('OK')"
python -c "from arxiv_pulse.services.ai_client import get_ai_client; print('OK')"

# 代码检查
black --check . && ruff check .

# 启动服务
pulse serve .
```

---

## 下一步建议

1. **从 P0 开始**：先拆分 `papers.py`，这是最大的技术债务
2. **小步提交**：每完成一个模块就提交，避免大改动
3. **保持向后兼容**：API 端点不变，只是内部重构
4. **测试验证**：每次改动后运行 `pulse serve .` 验证功能

---

## 联系信息

- 项目仓库：https://github.com/kYangLi/ArXiv-Pulse
- 重构日期：2025-02-17
