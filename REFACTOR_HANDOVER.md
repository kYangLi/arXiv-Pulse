# ArXiv-Pulse 重构 Handover 文档

## 已完成的重构

### Session 1-4 (已完成)

详见之前 commit 历史。

**关键指标**：
- index.html: 7035 → 3696 行 (**-47%**)
- papers.py: 1069 → 812 行 (**-24%**)

### Session 5 (Pinia Stores 创建)

**创建的 Stores** (1455 行):

| Store | 行数 | 职责 |
|-------|------|------|
| configStore.js | 327 | 配置、设置、分类、i18n |
| paperStore.js | 359 | 论文、购物车、搜索、导出 |
| collectionStore.js | 302 | 收藏集、收藏集论文 |
| chatStore.js | 321 | 聊天会话、消息 |
| uiStore.js | 146 | 导航、同步、缓存 |

**添加的依赖**：
- Pinia v2.3.1 (Vue 3 状态管理库)

---

## 待完成：集成 Stores 到 index.html

### 需要做的修改

#### 1. 添加脚本标签

```html
<!-- 在其他脚本后添加 -->
<script src="libs/pinia/pinia.iife.prod.js"></script>
<script src="js/stores/configStore.js"></script>
<script src="js/stores/paperStore.js"></script>
<script src="js/stores/collectionStore.js"></script>
<script src="js/stores/chatStore.js"></script>
<script src="js/stores/uiStore.js"></script>
```

#### 2. 初始化 Pinia

```javascript
const app = createApp({ ... });
const pinia = createPinia();
app.use(pinia);
```

#### 3. 替换 ref() 为 store

**之前**:
```javascript
const recentPapers = ref([]);
const loadingRecent = ref(true);
```

**之后**:
```javascript
const paperStore = usePaperStore();
// 使用 paperStore.recentPapers, paperStore.loadingRecent
```

#### 4. 更新模板绑定

**之前**:
```html
<div v-for="paper in recentPapers">
```

**之后**:
```html
<div v-for="paper in paperStore.recentPapers">
```

### 迁移策略

建议按模块逐步迁移，避免一次性大改动：

1. **阶段 1**: configStore (最独立)
   - 设置页面
   - 分类选择器

2. **阶段 2**: uiStore
   - 导航
   - 同步页面

3. **阶段 3**: paperStore
   - 主页
   - 搜索
   - 购物车

4. **阶段 4**: collectionStore
   - 收藏集页面

5. **阶段 5**: chatStore
   - AI 聊天

---

## 当前项目结构

```
arxiv_pulse/
├── services/               # ✅ 服务层
│   ├── ai_client.py
│   ├── paper_service.py
│   └── translation_service.py
├── utils/                  # ✅ 工具层
│   ├── sse.py
│   └── time.py
├── web/
│   ├── dependencies.py
│   ├── api/
│   │   └── papers.py       # 已瘦身 (812 行)
│   └── static/
│       ├── css/
│       │   └── main.css
│       ├── js/
│       │   ├── components/
│       │   │   └── PaperCard.js
│       │   ├── i18n/
│       │   ├── services/
│       │   │   └── api.js
│       │   ├── stores/     # ✅ 新增 Pinia stores
│       │   │   ├── configStore.js
│       │   │   ├── paperStore.js
│       │   │   ├── collectionStore.js
│       │   │   ├── chatStore.js
│       │   │   └── uiStore.js
│       │   └── utils/
│       ├── libs/
│       │   └── pinia/      # ✅ 新增 Pinia 库
│       └── index.html      # 待迁移 (3696 行)
```

---

## 测试命令

```bash
# 代码检查
black --check . && ruff check .

# 启动服务
pulse serve .
```

---

## 下一步

1. **集成 stores 到 index.html** - 按阶段逐步迁移
2. **提取更多 Vue 组件** - 使用 stores 后组件提取会更容易
3. **考虑 Vite 构建** - 支持 Vue SFC
