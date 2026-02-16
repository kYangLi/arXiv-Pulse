# ArXiv-Pulse Handover Document

## 项目状态

**版本**: v1.0 开发中
**最后更新**: 2026-02-16

### 已完成功能

1. **核心功能**
   - arXiv 论文爬取和同步
   - AI 摘要和翻译（支持 7 种语言）
   - SQLite 数据库 + SQLAlchemy ORM
   - FastAPI 后端 + Vue 3 + Element Plus 前端

2. **界面功能**
   - 初始化设置向导
   - 首页搜索（AI 解析搜索词）
   - 近期论文（支持领域过滤、同步选项）
   - 数据管理（统计图表、缓存管理）
   - 论文集（重设计的卡片布局、分页）
   - AI 对话助手
   - 暂存篮（导出、添加到论文集）
   - 多语言支持（中/英）

3. **本次 Session 完成的修复**
   - 论文集页面重设计（搜索、卡片布局、下拉菜单）
   - 论文集分页（每页 20 篇）
   - ESC 键关闭浮动窗口（按层级顺序）
   - 浮动窗口点击聚焦（z-index 切换）
   - 暂存篮添加论文集逻辑修复
   - 统计缓存自动刷新
   - 页面切换自动刷新数据
   - 图表切换消失问题修复
   - 页面切换动画统一

### 当前代码状态

- **后端**: 稳定，无已知 bug
- **前端**: 稳定，无已知 bug
- **测试**: Playwright 测试在 tests/ 目录

### 文件结构要点

```
arxiv_pulse/
├── config.py          # 配置类，从数据库读取
├── models.py          # 数据库模型
├── i18n/              # 国际化
└── web/
    ├── app.py         # FastAPI 应用入口
    ├── api/           # API 路由
    │   ├── collections.py  # 论文集 CRUD（已添加分页和缓存刷新）
    │   ├── papers.py       # 论文相关 API
    │   └── stats.py        # 统计 API
    └── static/
        └── index.html      # Vue 3 单文件应用（约 6100 行）
```

## 待办事项 / 已知问题

暂无已知 bug。用户可根据需求继续开发新功能。

## 开发环境

```bash
# 启动服务
pulse serve .

# 测试服务地址
http://192.168.219.3:30333

# 测试目录
tests/
tests/data/           # 测试数据库（独立于生产数据）

# Lint 命令
black --check . && ruff check . && mypy arxiv_pulse/
```

## 给下一个 Session 的建议

1. **前端修改后**：重启服务器 + 强制刷新浏览器（Ctrl+Shift+R）
2. **后端修改后**：重启服务器
3. **添加新功能前**：先查看现有代码模式
4. **国际化**：新增用户可见文字需添加到 i18n（中/英）
5. **API 错误**：使用 HTTPException
6. **数据库操作**：使用 `with get_db().get_session() as session:`
