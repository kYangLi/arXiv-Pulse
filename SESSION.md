---
## Goal

开发 **arXiv Pulse v1.0** - 智能学术文献追踪系统。本次会话重点：

1. **配置系统优化**：Init 设置、Settings 面板、配置保存逻辑
2. **FieldSelector 组件**：弹窗选择研究领域，支持可视化模式和源码模式
3. **多语言 AI 支持**：翻译和总结支持 7 种语言
4. **缓存管理功能**：新增数据管理页面，支持清理各类缓存
5. **API 状态提示**：当 AI API Key 未配置时显示提示信息
6. **论文集页面重设计**：更学术化、更优雅的卡片布局

## Instructions

### 核心设计决策：

1. **Settings 配置**（完整，不常改）：AI 配置、语言、研究领域、同步设置
2. **页面配置**（精简，常用）：Sync 页面、Recent 页面的临时配置
3. **默认值**：每领域最大论文数 10000，全局最大论文数 100000，近期论文 64，搜索结果 20
4. **AI 语言**：中文、English、Русский、Français、Deutsch、Español、العربية
5. **翻译 Prompt**：统一使用英文格式指令，指定目标语言输出

## Discoveries

1. **Vue watch 深度监听问题**：`watch(ref对象)` 时 `newVal` 和 `oldVal` 指向同一引用，需要用 getter 函数返回新对象
2. **el-dialog 在条件渲染内不显示**：`el-dialog` 如果在 `v-if/v-else` 分支内，当条件不满足时对话框不会渲染到 DOM
3. **AI 翻译 Prompt 格式**：使用目标语言写的 prompt 效果不稳定，改为英文指令 + 指定输出语言
4. **测试数据库位置**：测试都在 `tests/` 目录下进行，避免污染生产数据
5. **翻译缓存键**：包含目标语言，所以不同语言有独立缓存
6. **ECharts 图表切换消失**：页面切换时 DOM 被销毁，需要销毁旧实例再重新初始化
7. **事件冒泡**：嵌套的点击元素需要 `@click.stop` 阻止事件冒泡

## Accomplished

✅ Field Selector Dialog 修复（移到 app-container 外）
✅ FieldSelector 简化布局（左侧全部领域，右侧已选择+代码）
✅ AI 语言选项更新为 7 种语言
✅ 翻译/总结 Prompt 改为英文格式指令
✅ Settings watch 保存问题修复
✅ 缓存管理功能（数据管理页面）
✅ AI API Key 未配置提示
✅ 近期论文 AI 总结数据丢失修复
✅ 首页统计文案和图标优化
✅ 窗口调整时弹窗位置修复
✅ 图表切换消失问题修复
✅ 页面切换动画统一
✅ 导航按钮和浮动按钮尺寸优化
✅ 论文集页面重设计（搜索、卡片布局、下拉菜单）
✅ AGENTS.md 更新

## Relevant files / directories

```
arXiv-Pulse/
├── arxiv_pulse/
│   ├── config.py                    # Config 类，读取数据库配置
│   ├── models.py                    # Database 类，新增缓存清理方法
│   ├── summarizer.py                # PaperSummarizer，总结 prompt
│   ├── i18n/__init__.py             # 翻译 prompt，语言名称
│   ├── web/
│   │   ├── app.py                   # FastAPI 应用，注册 cache 路由
│   │   ├── api/
│   │   │   ├── cache.py             # 新增：缓存管理 API
│   │   │   ├── config.py            # 配置 API，Init 配置保存
│   │   │   └── papers.py            # enhance_paper_data 新增 ai_available
│   │   └── static/
│   │       └── index.html           # 主要前端文件
├── tests/
│   ├── test_field_selector.py       # Playwright 测试
│   └── data/                        # 测试数据库
├── AGENTS.md                        # 开发指南
├── SESSION.md                       # 会话记录
└── pyproject.toml
```

## Next Steps

根据用户需求继续修复 bug 或开发新功能

**测试命令**：
```bash
cd /mnt/OceanNAS/ActiveField/OceanBrain/2.Codes/Acadamic/arXiv-Pulse/tests
pulse restart .
uv run python test_field_selector.py
```

**服务地址**：http://192.168.219.3:30333
