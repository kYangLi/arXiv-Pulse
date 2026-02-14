# arXiv Pulse v0.9.9 - AI Chat Assistant 开发进度

## Goal

开发 **arXiv Pulse v0.9.9** - 完善 AI Chat Assistant 和用户体验优化：
- 普通 AI 对话，进行学术讨论
- 选择论文进行分析（下载 PDF，解析内容，发送给 AI）
- 全局记忆 - 对话历史跨会话持久化
- 多会话管理 - 创建/切换/删除对话
- 浮动小部件 UI（类似客服聊天）
- 使用 pymupdf 完整解析 PDF
- 支持 @提及论文和预选论文两种方式

## Instructions

- **UI 设计**: 浮动小部件（右下角，类似客服），非侧边栏抽屉
- **PDF 解析**: 使用 pymupdf 完整解析文本，不只是摘要/结论
- **论文关联**: 支持两种方式 - 消息中 @提及 和 预选论文
- **标题生成**: 首条消息自动生成（截断至30字符）
- **Web 优先架构**: 所有功能通过 web 界面实现
- **数据库配置**: SystemConfig 表存储所有设置
- **学术 UI 风格**: 深蓝 (#1e3a5f) + 金色 (#c9a227) 配色

## Discoveries

- `@property` 装饰器不能用于类级别属性；创建了 `classproperty` 描述符
- Element Plus 需要显式导入 CSS
- 前端发送 `***` 表示掩码的 API key；后端需要使用存储的值
- 摘要 JSON 结构包含 `methodology`, `relevance`, `impact`, `key_findings`, `keywords` - 不只是 `summary`
- weasyprint 中文 PDF 渲染需要正确的 CJK 字体列表
- Canvas API 可用于客户端 PNG 生成，无需外部库
- pymupdf (fitz) 推荐用于 PDF 解析 - 快速且可靠

## Accomplished

### Phase 1: Database Models + Dependencies ✅
- [x] 添加 `pymupdf>=1.24.0` 到 pyproject.toml
- [x] 添加 `ChatSession` 模型
- [x] 添加 `ChatMessage` 模型 (session_id, role, content, paper_ids, created_at)
- [x] 添加 `PaperContentCache` 模型 (arxiv_id, full_text, created_at)

### Phase 2: Backend API ✅
- [x] 创建 `arxiv_pulse/web/api/chat.py` 包含端点：
  - `GET /api/chat/sessions` - 列出会话
  - `POST /api/chat/sessions` - 创建会话
  - `GET /api/chat/sessions/{id}` - 获取会话及消息
  - `DELETE /api/chat/sessions/{id}` - 删除会话
  - `PUT /api/chat/sessions/{id}/rename` - 重命名会话
  - `POST /api/chat/sessions/{id}/send` - 发送消息 (SSE 流式)
  - `GET /api/chat/papers/{arxiv_id}/content` - 获取 PDF 内容
- [x] 在 `app.py` 中注册 chat router

### Phase 3: PDF Download & Parsing ✅
- [x] `download_and_parse_pdf()` - 从 arXiv 下载 PDF，使用 pymupdf 解析
- [x] `get_paper_content()` - 优先检查缓存，需要时下载
- [x] 在 `PaperContentCache` 表缓存解析后的文本

### Phase 4: Frontend UI ✅
- [x] 添加聊天小部件 HTML 结构：
  - 折叠状态：带徽章的浮动按钮
  - 展开状态：带头部、侧边栏、消息区、输入框的聊天窗口
  - 论文选择弹出框
- [x] 添加所有聊天组件的 CSS 样式
- [x] 添加 JavaScript/Vue 逻辑：
  - `chatExpanded`, `chatSessions`, `currentChatSession`, `chatMessages`
  - `chatInput`, `selectedChatPapers`, `chatTyping`, `paperSearchQuery`
  - `toggleChat()`, `createNewChat()`, `selectChatSession()`
  - `sendChatMessage()` - SSE 流式
  - `formatChatMessage()`, `formatChatTime()`
  - `togglePaperSelection()`, `removeSelectedChatPaper()`

### Phase 5: Paper Association ✅
- [x] 在 paper-card 组件添加"分析"按钮
- [x] 点击时打开聊天并预选论文
- [x] 事件监听器 `analyze-paper` 处理

### Phase 6: Final Updates ✅
- [x] 版本更新至 0.9.5
- [x] 更新 AGENTS.md 文档
- [x] Lint 检查通过

## Relevant files / directories

```
arXiv-Pulse/
├── pyproject.toml                  # 添加了 pymupdf 依赖，版本 0.9.5
├── arxiv_pulse/
│   ├── models.py                   # 添加了 ChatSession, ChatMessage, PaperContentCache
│   ├── web/
│   │   ├── app.py                  # 注册了 chat router
│   │   ├── api/
│   │   │   └── chat.py             # 所有聊天 API 端点
│   │   └── static/
│   │       └── index.html          # 聊天小部件 HTML + CSS + JS
```

## Next Steps

1. **Integration Testing**: 手动测试完整聊天功能
2. **Optional Enhancements**:
   - 添加会话重命名功能到 UI
   - 添加删除会话按钮
   - 支持多论文同时分析

## Recent Fixes

- **AI 头像**: 显示 "AI" 文字 + 深蓝背景，替代空图标
- **聊天按钮图标**: 改为聊天气泡 SVG 图标
- **Markdown 渲染**: 添加 marked.js，支持标题/列表/代码块/引用等完整语法，减少间距
- **流式输出**: AI 回复实时显示，不再是等待完成后才显示
  - 支持 Markdown 流式渲染
  - 自动处理未闭合的代码块
- **进度显示**: 实时显示论文处理进度，增加延迟让用户有时间看到
  - 检查缓存 → 下载 PDF → 解析页面 → AI 分析
  - 显示文件大小、字符数、页数等信息
  - 带进度条动画
- **聊天按钮样式**: 渐变背景，hover 放大效果，更明显
- **窗口可调整大小**: 支持拖拽调整聊天窗口大小
- **消息自动换行**: 长内容自动换行适应窗口宽度
- **删除对话**: 对话历史中添加删除按钮，hover 显示，确认后删除
- **滚动行为**: AI 输出时可自由滚动查看历史消息
  - 用户向上滚动时暂停自动滚动
  - 用户在底部时恢复自动滚动
- **简化输入区域**: 移除无效的论文搜索功能，保留已选论文显示
- **论文暂存篮**: 新增暂存篮功能，类似收藏夹体验
  - 右下角浮动按钮（金色，显示数量徽章）
  - 支持多来源论文加入暂存篮
  - 批量导出（Markdown/CSV/BibTeX）
  - 批量加入论文集
  - 批量 AI 分析
  - 一键清空
  - 移除旧的导出条和选择框
  - 按钮始终可见，空篮子也可打开
- **返回首页按钮**: 非 homepage 页面显示浮动返回按钮（左下角）
  - 淡入动画效果
  - hover 放大效果
- **加入论文集动画**: 点击加入论文集时显示飞入动画
  - 卡片缩小上升消失效果
- **页面切换动画**: 返回首页时圆圈扩展过渡动画
- **PDF 原文批量下载**: 导出支持 PDF（原文）选项，批量下载 arXiv 原始 PDF
- **复制链接功能**: 暂存篮新增复制所有论文链接功能
- **stop 命令增强**: 支持 --force 强制停止，更友好的输出信息
