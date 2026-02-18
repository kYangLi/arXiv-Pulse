# ArXiv-Pulse 系统测试

基于 Playwright 的端到端系统测试套件，模拟用户真实使用场景。

## 测试环境要求

- Python 3.12+
- Playwright (`pip install playwright && playwright install chromium`)
- 已配置 AI API Key 的测试数据库

## 测试文件结构

```
tests/
├── README.md               # 本文档
├── conftest.py             # pytest 配置、fixtures、通用工具
├── test_01_init.py         # 首次运行设置向导测试
├── test_02_navigation.py   # 页面导航测试
├── test_03_home.py         # 首页功能测试
├── test_04_recent.py       # 近期论文测试
├── test_05_collections.py  # 论文集管理测试
├── test_06_chat.py         # AI 对话测试
├── test_07_settings.py     # 设置功能测试
├── test_08_export.py       # 导出功能测试
├── run_all.py              # 运行所有测试的入口
├── data/                   # 测试数据库目录
│   └── arxiv_papers.db     # 已初始化的测试数据库
└── init_data/              # init 测试临时数据目录
```

## 测试用例概览

### test_01_init.py - 首次运行设置向导

**前置条件:** 临时启动新的服务实例（独立端口、独立数据库）

| 测试用例 | 描述 |
|---------|------|
| `test_init_page_visible` | 首次访问显示设置向导 |
| `test_init_step1_elements` | 步骤1：AI 配置页面元素检查 |
| `test_init_step1_test_connection` | 步骤1：测试 AI 连接功能 |
| `test_init_step2_field_selector` | 步骤2：领域选择器功能 |
| `test_init_step3_sync_settings` | 步骤3：同步参数设置 |
| `test_init_step4_start_sync` | 步骤4：开始同步按钮 |
| `test_init_navigation_blocked` | 初始化前导航被阻止 |

### test_02_navigation.py - 页面导航

**前置条件:** 应用已初始化

| 测试用例 | 描述 |
|---------|------|
| `test_bottom_nav_expand` | 底部导航栏悬停展开 |
| `test_navigate_to_recent` | 导航到近期论文页 |
| `test_navigate_to_sync` | 导航到同步页 |
| `test_navigate_to_collections` | 导航到论文集页 |
| `test_navigate_to_home` | 导航回首页 |
| `test_no_console_errors` | 导航时无 JS 错误 |

### test_03_home.py - 首页功能

| 测试用例 | 描述 |
|---------|------|
| `test_stats_display` | 统计卡片显示 |
| `test_search_input_visible` | 搜索框显示 |
| `test_ai_search` | AI 搜索功能（真实 API） |
| `test_search_results_display` | 搜索结果展示 |
| `test_field_filter_button` | 领域筛选按钮 |

### test_04_recent.py - 近期论文

| 测试用例 | 描述 |
|---------|------|
| `test_recent_papers_load` | 近期论文列表加载 |
| `test_recent_papers_count` | 论文数量显示 |
| `test_paper_card_expand` | 论文卡片展开/收起 |
| `test_paper_card_arxiv_link` | arXiv 链接 |
| `test_paper_card_pdf_link` | PDF 下载链接 |

### test_05_collections.py - 论文集管理

| 测试用例 | 描述 |
|---------|------|
| `test_collections_list_load` | 论文集列表加载 |
| `test_create_collection` | 创建新论文集 |
| `test_edit_collection_name` | 编辑论文集名称 |
| `test_add_paper_to_collection` | 添加论文到论文集 |
| `test_view_collection_papers` | 查看论文集内论文 |
| `test_remove_paper_from_collection` | 从论文集移除论文 |
| `test_delete_collection` | 删除论文集 |

### test_06_chat.py - AI 对话

| 测试用例 | 描述 |
|---------|------|
| `test_chat_fab_visible` | 聊天 FAB 按钮显示 |
| `test_chat_open_from_fab` | FAB 打开聊天窗口 |
| `test_chat_create_new_session` | 创建新对话 |
| `test_chat_send_message` | 发送消息（真实 API） |
| `test_chat_from_paper_card` | 从论文卡片分析打开 |
| `test_chat_close` | 关闭聊天窗口 |

### test_07_settings.py - 设置功能

| 测试用例 | 描述 |
|---------|------|
| `test_settings_open` | 打开设置抽屉 |
| `test_settings_language_toggle` | 切换界面语言 |
| `test_settings_field_selector` | 从设置打开领域选择器 |
| `test_settings_ai_test_connection` | AI 连接测试 |
| `test_settings_close` | 关闭设置抽屉 |

### test_08_export.py - 导出功能

| 测试用例 | 描述 |
|---------|------|
| `test_export_collection_json` | 导出论文集 JSON |
| `test_export_collection_csv` | 导出论文集 CSV |
| `test_export_paper_card_image` | 导出论文卡片图片 |

## 运行测试

### 运行所有测试

```bash
cd tests
uv run python run_all.py
```

### 运行单个测试文件

```bash
cd tests
uv run python test_02_navigation.py
uv run python test_03_home.py
# ...
```

### 使用 pytest 运行

```bash
cd tests
uv run pytest test_02_navigation.py -v
uv run pytest test_03_home.py -v
# ...
```

## 配置

### 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `BASE_URL` | `http://192.168.219.3:33033` | 已初始化服务地址 |
| `INIT_PORT` | `33034` | init 测试临时服务端口 |

### API 配置

测试从 `tests/data/arxiv_papers.db` 数据库读取 AI API 配置：
- `ai_api_key` - API 密钥
- `ai_model` - 模型名称
- `ai_base_url` - API 基础 URL

## 测试输出

### 截图

测试截图保存到 `/tmp/` 目录：
- `/tmp/init_page.png` - init 页面截图
- `/tmp/navigation_*.png` - 导航测试截图
- `/tmp/test_*.png` - 各测试截图

### 导出文件

导出测试文件保存到 `/tmp/` 目录：
- `/tmp/collection_export_*.json` - 论文集 JSON 导出
- `/tmp/collection_export_*.csv` - 论文集 CSV 导出
- `/tmp/paper_card_*.png` - 论文卡片图片

## 测试流程

```
┌─────────────────────────────────────────────────────────────┐
│                     test_01_init.py                         │
│  临时启动服务 → 测试设置向导 → 关闭服务                       │
│  (独立端口 33034, 独立数据库 init_data/)                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              test_02 ~ test_08 (主测试套件)                  │
│  连接已初始化服务 (BASE_URL, tests/data/arxiv_papers.db)     │
│  顺序执行各功能模块测试                                       │
└─────────────────────────────────────────────────────────────┘
```

## 注意事项

1. **init 测试隔离**: `test_01_init.py` 启动独立服务实例，不影响主测试数据库
2. **真实 AI API**: 部分测试（搜索、聊天）使用真实 AI API 调用
3. **顺序执行**: 测试按编号顺序执行，后续测试依赖前面测试状态
4. **控制台监控**: 所有测试监控 JavaScript 控制台错误
5. **超时设置**: 页面加载超时 30s，SSE 流超时 120s
