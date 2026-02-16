---
## Goal

开发 **arXiv Pulse v1.0** - 智能学术文献追踪系统。本次会话重点优化界面配置系统，包括：

1. **配置归属重新划分**：Settings（完整配置）vs 页面配置（精简常用）
2. **研究领域选择器重构**：创建通用 FieldSelector 弹窗组件，支持可视化选择和源码模式
3. **双向同步**：可视化模式和源码模式实时同步

## Instructions

### 核心设计决策（已确认）：

1. **Settings 配置**（完整，不常改）：
   - AI 配置（API URL, Key, Model）
   - 语言设置
   - 研究领域（弹窗选择）
   - 同步设置（默认年份、每领域最大论文数、全局最大论文数）
   - 近期论文默认数量

2. **页面配置**（精简，常用）：
   - Sync：本次同步年份覆盖、强制同步开关
   - 近期论文：天数、领域过滤、同步新论文开关

3. **默认值**：
   - 每领域最大论文数：10000
   - 全局最大论文数：100000
   - 近期论文默认数量：64

4. **FieldSelector 双模式**：
   - 可视化模式：树形选择器
   - 源码模式：直接编辑 arXiv 查询语句（黑色背景代码编辑器）
   - 双向同步：选择自动生成源码，源码自动解析分类

## Discoveries

1. **el-dialog 不显示问题**：控制台日志显示 `openFieldSelector called` 和 `showFieldSelector set to true`，但对话框不渲染到 DOM
2. **Element Plus Dialog 使用 Teleport**：对话框默认渲染到 body，需要检查 `append-to-body` 属性
3. **Playwright 测试 Vue 组件**：可以通过 `page.on("console")` 监听 console.log 输出来调试 Vue 函数调用
4. **变量定义顺序重要**：`advancedQueriesLines` 必须在 `parseCodeToFields` 之前定义
5. **ref 访问方式**：在函数中访问 ref 需要用 `.value`，如 `allCategories.value[fieldId]`
6. **Vue 条件渲染影响子组件**：`el-dialog` 在 `v-else` 分支内时，如果条件不满足，对话框不会渲染

## Accomplished

✅ 后端配置新增：`ARXIV_MAX_RESULTS_PER_FIELD`, `RECENT_PAPERS_LIMIT`, 更新 `ARXIV_MAX_RESULTS`
✅ 后端 API 更新支持新配置
✅ 前端 FieldSelector 弹窗组件创建（左右双列布局）
✅ Settings 页面更新（完整配置 + 弹窗选择领域）
✅ Init 页面步骤2 更新（弹窗选择领域）
✅ 近期论文页简化配置
✅ Sync 页简化配置
✅ 双向同步逻辑实现（可视化 ↔ 源码）
✅ 源码模式黑色背景代码编辑器样式
✅ **修复 el-dialog 不渲染问题**：将 Field Selector Dialog 移到 `app-container` 外面作为全局组件

## Relevant files / directories

```
arXiv-Pulse/
├── arxiv_pulse/
│   ├── config.py                    # 新增 ARXIV_MAX_RESULTS_PER_FIELD, RECENT_PAPERS_LIMIT
│   ├── web/
│   │   ├── api/
│   │   │   ├── config.py            # 更新配置 API，新增字段支持
│   │   │   └── papers.py            # 更新 recent/update 端点参数
│   │   └── static/
│   │       └── index.html           # 主要前端文件，包含所有修改
├── tests/
│   ├── test_field_selector.py       # Playwright 测试脚本
│   └── data/                        # 测试数据库
└── pyproject.toml
```

## Key Fix

**问题**：Field Selector Dialog 在 Setup 页面点击后不显示。

**原因**：`el-dialog` 原本在 `<div v-else class="app-container">` 内部，当 `showSetup` 为 true 时，`app-container` 不会渲染，所以对话框不存在于 DOM 中。

**解决方案**：将 Field Selector Dialog 移到 `app-container` 外面，与 `setup-container` 和 `app-container` 同级，这样无论在哪个页面都可以使用。

```html
<!-- 修改前 -->
<div id="app">
    <div v-if="showSetup">...</div>
    <div v-else class="app-container">
        ...
        <el-dialog v-model="showFieldSelector">...</el-dialog>  <!-- 这里！ -->
    </div>
</div>

<!-- 修改后 -->
<div id="app">
    <div v-if="showSetup">...</div>
    <div v-else class="app-container">...</div>
    <el-dialog v-model="showFieldSelector">...</el-dialog>  <!-- 移到外面 -->
</div>
```

## Next Steps

1. 测试 Settings 页面的 Field Selector 是否正常工作
2. 测试近期论文页面的 Field Selector 是否正常工作
3. 验证双向同步功能（可视化 ↔ 源码）
4. 测试完整初始化流程

**测试命令**：
```bash
cd /mnt/OceanNAS/ActiveField/OceanBrain/2.Codes/Acadamic/arXiv-Pulse/tests
uv run python test_field_selector.py
```

**服务地址**：http://192.168.219.3:30333
