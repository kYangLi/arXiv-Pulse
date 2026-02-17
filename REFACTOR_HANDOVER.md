# ArXiv-Pulse 重构 Handover 文档

## 已完成的重构

### Session 1

**后端**:
- `web/dependencies.py` - 统一数据库依赖注入
- `utils/sse.py` - SSE 工具函数
- `services/ai_client.py` - AI client 单例
- `js/i18n/zh.js`, `js/i18n/en.js` - i18n 提取

**前端**:
- index.html: 7035 → 6460 行

### Session 2

**后端服务层**:

| 文件 | 行数 | 作用 |
|------|------|------|
| `services/paper_service.py` | 195 | enhance_paper_data, calculate_relevance_score, get_category_explanation, summarize_and_cache_paper |
| `services/translation_service.py` | 52 | translate_text with caching |

**papers.py 瘦身**: 1069 → 812 行 (-24%)

**前端**:

| 文件 | 行数 | 作用 |
|------|------|------|
| `css/main.css` | 2377 | 所有样式 |

**index.html 瘦身**: 6460 → 4082 行 (-37%)

### Session 3

**前端 API 统一层**:

| 文件 | 行数 | 作用 |
|------|------|------|
| `js/services/api.js` | 121 | 统一 API 调用层，封装 43 处 fetch 调用 |

**修改**:
- 更新 `js/utils/export.js` - 移除重复的 API_BASE 定义
- 更新 `index.html` - 所有 API 调用改用 API 对象

**index.html 瘦身**: 4082 → 3999 行 (-2%)

### Session 4

**前端 Vue 组件提取**:

| 文件 | 行数 | 作用 |
|------|------|------|
| `js/components/PaperCard.js` | 312 | 论文卡片组件 (template + setup) |

**index.html 瘦身**: 3999 → 3696 行 (-8%)

### 累计成果

| 指标 | 变化 |
|------|------|
| index.html | 7035 → 3696 行 (**-47%**) |
| papers.py | 1069 → 812 行 (**-24%**) |
| 新增服务层 | 4 个文件，321 行 |
| 新增前端模块 | api.js (121 行), PaperCard.js (312 行) |

---

## 待重构项

### P1 - 中优先级

#### 1. 继续提取 Vue 组件

**问题**：`index.html` 仍有 3696 行

**可提取的组件**：
- `ChatWidget.js` - AI 对话组件 (~190 行模板)
- `CollectionCard.js` - 收藏集卡片 (~70 行)
- `FieldSelector.js` - 领域选择器 (~150 行)

**注意**：这些组件与主 app 状态耦合较深，提取需要传递大量 props

### P2 - 低优先级

#### 1. 引入 Pinia 状态管理

**问题**：100+ 个 `ref()` 状态分散在 setup() 中

#### 2. 后端 Repository 模式

**问题**：数据库查询逻辑直接在 API 中

---

## 当前项目结构

```
arxiv_pulse/
├── services/               # ✅ 新增服务层
│   ├── ai_client.py        # AI client 单例
│   ├── paper_service.py    # 论文数据处理
│   └── translation_service.py # 翻译服务
├── utils/                  # ✅ 新增工具层
│   ├── __init__.py
│   ├── sse.py              # SSE 工具
│   └── time.py             # 时间工具
├── web/
│   ├── dependencies.py     # ✅ 新增依赖注入
│   ├── api/
│   │   ├── papers.py       # 已瘦身 (812 行)
│   │   └── ...
│   └── static/
│       ├── css/
│       │   └── main.css    # ✅ 新增样式文件
│       ├── js/
│       │   ├── components/ # ✅ 新增 Vue 组件
│       │   │   └── PaperCard.js
│       │   ├── i18n/       # ✅ 新增 i18n 模块
│       │   ├── services/   # ✅ 新增 API 层
│       │   │   └── api.js  # 统一 API 调用
│       │   └── utils/      # ✅ 新增工具模块
│       └── index.html      # 已瘦身 (3696 行)
```

---

## 测试命令

```bash
# 后端测试
python -c "from arxiv_pulse.web.api import papers, collections; print('OK')"
python -c "from arxiv_pulse.services import paper_service; print('OK')"

# 代码检查
black --check . && ruff check .

# 启动服务
pulse serve .
```

---

## 下一步建议

1. **继续提取组件** - ChatWidget, CollectionCard 等
2. **考虑 Vite 构建** - 支持 Vue SFC 和模块化
3. **状态管理** - 引入 Pinia 减少组件间耦合
