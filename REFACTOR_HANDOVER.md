# ArXiv-Pulse 重构 Handover 文档

## 已完成的重构

### Session 1-4 (已完成)

详见之前 commit 历史。

**关键指标**：
- index.html: 7035 → 3696 行 (**-47%**)
- papers.py: 1069 → 812 行 (**-24%**)

### Session 5 (Pinia Stores 创建与初始化)

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

**已完成的集成**：
- 添加 Pinia 和 store 脚本标签
- 创建 Pinia 实例并添加到 app
- 在 setup() 中初始化所有 5 个 store

---

## 待完成：全面迁移到 Stores

### 当前状态

index.html 中 setup() 函数仍有 ~2400 行代码，包含 ~100 个 ref() 声明。需要逐步替换为 store 引用。

### 迁移步骤

#### 示例：迁移 configStore

**之前** (setup 函数内):
```javascript
const showSetup = ref(false);
const setupConfig = ref({ ... });
const currentLang = ref('zh');
```

**之后** (使用 store):
```javascript
// 删除上述 ref() 声明
// 使用 configStore.showSetup, configStore.setupConfig, configStore.currentLang
```

**模板更新**:
```html
<!-- 之前 -->
<div v-if="showSetup">

<!-- 之后 -->
<div v-if="configStore.showSetup">
```

### 建议的迁移顺序

1. **configStore** - 最独立，优先迁移
   - 设置页面、分类选择器、i18n

2. **uiStore** - 导航和同步
   - 底部导航、同步页面

3. **paperStore** - 核心业务
   - 主页、搜索、购物车

4. **collectionStore** - 收藏集
   - 收藏集页面

5. **chatStore** - AI 聊天
   - 聊天组件

---

## 当前项目结构

```
arxiv_pulse/web/static/
├── css/
│   └── main.css
├── js/
│   ├── components/
│   │   └── PaperCard.js
│   ├── i18n/
│   ├── services/
│   │   └── api.js
│   ├── stores/             # ✅ Pinia stores
│   │   ├── configStore.js
│   │   ├── paperStore.js
│   │   ├── collectionStore.js
│   │   ├── chatStore.js
│   │   └── uiStore.js
│   └── utils/
├── libs/
│   └── pinia/              # ✅ Pinia 库
└── index.html              # 待迁移 (3711 行)
```

---

## 测试命令

```bash
black --check . && ruff check .
pulse serve .
```

---

## 下一步

1. **迁移 configStore** - 替换设置相关的 ref()
2. **迁移 uiStore** - 替换导航相关的 ref()
3. **逐步迁移其他 stores**
4. **提取更多 Vue 组件** - 使用 stores 后组件提取会更容易
