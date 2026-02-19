# ArXiv-Pulse Developer Documentation

## Architecture Overview

ArXiv-Pulse follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Layer (cli/)                     │
│              Command-line interface entry point          │
├─────────────────────────────────────────────────────────┤
│                    Web Layer (web/)                      │
│         FastAPI routes, SSE streaming, static files      │
├─────────────────────────────────────────────────────────┤
│                  Service Layer (services/)               │
│    Business logic: AI, translation, paper processing     │
├─────────────────────────────────────────────────────────┤
│                   Domain Layer (ai/, crawler/, search/)  │
│      Domain-specific: summarization, crawling, search    │
├─────────────────────────────────────────────────────────┤
│                    Core Layer (core/)                    │
│         Infrastructure: Config, Database, Lock           │
├─────────────────────────────────────────────────────────┤
│                   Model Layer (models/)                  │
│              ORM models, database schema                 │
└─────────────────────────────────────────────────────────┘
```

---

## Module Reference

### Core Layer (`arxiv_pulse/core/`)

#### `config.py` - Configuration Management
- **Config class**: Singleton managing all application settings
- **Storage**: Settings stored in `system_config` table (key-value pairs)
- **Key settings**: AI API key, model, base URL, language preferences, sync parameters
- **Usage**: `Config.get(key)` / `Config.set(key, value)` / `Config.get_all()`

#### `database.py` - Database Singleton
- **Database class**: Thread-safe SQLite connection manager
- **Features**: Connection pooling, session context manager, automatic table creation
- **Usage**: `with get_db().get_session() as session: ...`

#### `lock.py` - Service Lock
- **ServiceLock class**: Prevents multiple service instances on same data directory
- **Lock file**: `.pulse.lock` (JSON format with PID, host, port, timestamp)
- **Features**: Stale lock detection, process verification, auto-cleanup

---

### Model Layer (`arxiv_pulse/models/`)

#### `base.py` - Base Classes
- **Base**: SQLAlchemy declarative base
- **utcnow()**: UTC timestamp generator
- **DEFAULT_CONFIG**: Default configuration values

#### `paper.py` - Paper Models
| Model | Description |
|-------|-------------|
| **Paper** | Main paper entity: arxiv_id, title, authors, abstract, summary, etc. |
| **TranslationCache** | Cached translations by target language |
| **FigureCache** | Cached figure images from arXiv |
| **PaperContentCache** | Cached full paper content |

#### `collection.py` - Collection Models
| Model | Description |
|-------|-------------|
| **Collection** | User-created paper collections |
| **CollectionPaper** | Many-to-many relationship (papers in collections) |

#### `chat.py` - Chat Models
| Model | Description |
|-------|-------------|
| **ChatSession** | Chat conversation session with paper context |
| **ChatMessage** | Individual message in a session |

#### `system.py` - System Models
| Model | Description |
|-------|-------------|
| **SyncTask** | Sync task history and status |
| **RecentResult** | Cached recent papers query result |
| **SystemConfig** | Key-value configuration storage |

---

### Constants (`arxiv_pulse/constants/`)

#### `categories.py` - Research Field Definitions
- **ARXIV_CATEGORIES**: Dict mapping category ID to metadata (name, arXiv categories, queries)
- **DEFAULT_FIELDS**: List of default field IDs for new users
- **get_all_categories()**: Returns flattened list of all categories
- **get_queries_for_fields()**: Generates arXiv API queries for selected fields

---

### Service Layer (`arxiv_pulse/services/`)

#### `ai_client.py` - AI API Client
- **AIClient class**: Unified interface for OpenAI/DeepSeek APIs
- **Features**: Streaming responses, error handling, retry logic
- **Usage**: `client.chat(messages, stream=True)`

#### `paper_service.py` - Paper Enhancement
- **enhance_paper_data()**: Adds translations, category names, figure URLs
- **Features**: Batch processing, translation caching, parallel requests

#### `translation_service.py` - Translation
- **translate_text()**: Translates text using AI
- **Features**: Language detection, caching, batch translation

#### `category_service.py` - Category Interpretation
- **interpret_category()**: Converts arXiv categories to human-readable names
- **Features**: Hierarchical category mapping, custom field names

#### `figure_service.py` - Figure Extraction
- **get_paper_figures()**: Extracts figures from arXiv PDF
- **Features**: PyMuPDF integration, image caching, URL generation

---

### Domain Layer

#### `crawler/arxiv.py` - ArXiv Crawler
- **ArXivCrawler class**: Fetches papers from arXiv API
- **Methods**: `sync_query()`, `get_paper_by_id()`, `get_recent_papers()`
- **Features**: Rate limiting, pagination, query construction, deduplication

#### `ai/summarizer.py` - Paper Summarizer
- **PaperSummarizer class**: Generates AI summaries for papers
- **Features**: Abstract-based summarization, batch processing, streaming

#### `ai/report.py` - Report Generator
- **ReportGenerator class**: Deprecated - figure extraction moved to services/figure_service.py
- **Features**: WeasyPrint integration, markdown rendering, figure embedding

#### `search/engine.py` - Search Engine
- **SearchEngine class**: Natural language search with AI keyword extraction
- **SearchFilter class**: Field-based filtering
- **Features**: FTS5 full-text search, AI query parsing, relevance ranking

---

### Utils (`arxiv_pulse/utils/`)

#### `output.py` - Console Output
- **OutputManager class**: Formatted console output with colors
- **Features**: Progress bars, status messages, error formatting

#### `sse.py` - SSE Utilities
- **sse_event()**: Creates SSE event string
- **sse_response()**: Creates FastAPI StreamingResponse for SSE
- **Features**: Proper headers, JSON serialization, error handling

#### `time.py` - Time Utilities
- **parse_relative_time()**: Parses relative time strings ("3 days ago")
- **format_datetime()**: Formats datetime for display

---

### CLI (`arxiv_pulse/cli/`)

#### `__init__.py` - CLI Commands
| Command | Description |
|---------|-------------|
| `pulse serve .` | Start web server (background by default) |
| `pulse serve . -f` | Start in foreground mode |
| `pulse status .` | Check service status |
| `pulse stop .` | Stop service gracefully |
| `pulse restart .` | Restart service |

**Options**:
- `--port`: Custom port (default: 8000)
- `--host`: Bind address (default: 127.0.0.1)
- `--allow-non-localhost-access-with-plaintext-transmission-risk`: Enable remote access

---

### Web Layer (`arxiv_pulse/web/`)

#### `app.py` - FastAPI Application
- **create_app()**: Creates and configures FastAPI app
- **Features**: CORS, static files, exception handling, lifespan management

#### `dependencies.py` - Dependency Injection
- **get_db()**: Database session dependency for FastAPI

#### API Endpoints (`web/api/`)

| File | Endpoints |
|------|-----------|
| `papers.py` | `/api/papers/search/stream` (SSE), `/api/papers/recent/*` |
| `collections.py` | `/api/collections/*` CRUD + pagination |
| `tasks.py` | `/api/tasks/sync` (SSE), task history |
| `config.py` | `/api/config/*`, `/api/config/test-ai` |
| `chat.py` | `/api/chat/sessions/*`, `/api/chat/sessions/{id}/send` (SSE) |
| `stats.py` | `/api/stats`, `/api/stats/refresh` |
| `cache.py` | `/api/cache/stats`, `/api/cache/clear/{type}` |
| `export.py` | `/api/export/*` (PDF, JSON, CSV) |

---

### Frontend (`arxiv_pulse/web/static/`)

#### `index.html` - Main Application
- Single-file Vue 3 + Element Plus application
- 2456 lines (refactored from 7035)
- Uses Pinia stores for state management

#### Components (`js/components/`)
| Component | Lines | Description |
|-----------|-------|-------------|
| PaperCard | 315 | Paper card with actions, basket, collection |
| FieldSelectorDialog | 201 | Research field selector with search |
| PaperBasketPanel | 100 | Floating basket panel for batch operations |
| SettingsDrawer | 131 | Settings drawer with all configuration |
| CollectionDialogs | 271 | Create/Edit/Delete collection dialogs |
| ChatWidget | 246 | AI chat assistant widget |

#### Stores (`js/stores/`)
| Store | Lines | Description |
|-------|-------|-------------|
| configStore | 354 | Configuration state and API |
| paperStore | 496 | Paper search, recent, basket state |
| collectionStore | 388 | Collection management state |
| chatStore | 321 | Chat sessions and messages |
| uiStore | 146 | UI state (page, modals, z-index) |

#### Services (`js/services/`)
- `api.js`: API client with fetch wrappers, SSE handling

#### i18n (`js/i18n/`)
- `zh.js`: Chinese translations (~400 keys)
- `en.js`: English translations (~400 keys)

---

### i18n (`arxiv_pulse/i18n/`)

#### Backend Translations
- **`zh.py`**: Chinese translations for backend messages
- **`en.py`**: English translations for backend messages
- **`__init__.py`**: `t()` function, `get_translation_prompt()` for AI

---

## Data Directory Structure

When running `pulse serve .`, a data directory is created:

```
data_dir/
├── data/
│   └── arxiv_papers.db    # SQLite database
├── .pulse.lock            # Service lock file
└── web.log                # Service log
```

---

## Database Schema

### Papers Table
```sql
CREATE TABLE papers (
    id TEXT PRIMARY KEY,           -- arXiv ID
    title TEXT NOT NULL,
    authors TEXT,                  -- JSON array
    abstract TEXT,
    summary TEXT,                  -- AI-generated summary
    categories TEXT,               -- arXiv categories
    published_date DATETIME,
    updated_date DATETIME,
    pdf_url TEXT,
    source_url TEXT,
    created_at DATETIME,
    updated_at DATETIME
);
```

### Collections Table
```sql
CREATE TABLE collections (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME,
    updated_at DATETIME
);
```

### Collection Papers (Junction)
```sql
CREATE TABLE collection_papers (
    collection_id INTEGER,
    paper_id TEXT,
    added_at DATETIME,
    PRIMARY KEY (collection_id, paper_id)
);
```

---

## Configuration Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `ai_api_key` | string | - | OpenAI/DeepSeek API key |
| `ai_model` | string | DeepSeek-V3.2 | Model name |
| `ai_base_url` | string | - | API endpoint URL |
| `ui_language` | string | zh | UI language (zh/en) |
| `translate_language` | string | Chinese | Translation target language |
| `years_back` | int | 5 | Years to sync |
| `arxiv_max_results` | int | 50000 | Max total results |
| `arxiv_max_results_per_field` | int | 5000 | Max results per field |
| `selected_fields` | json | [] | Selected research field IDs |
| `search_queries` | json | [] | Custom search queries |
| `recent_papers_limit` | int | 50 | Recent papers display limit |
| `search_limit` | int | 20 | Search results limit |

---

## Testing

### Unit Tests
```bash
pytest                           # Run all tests
pytest tests/test_module.py      # Run single file
pytest --cov=arxiv_pulse         # With coverage
```

### Playwright Tests
```bash
cd tests && uv run python test_navigation.py
cd tests && uv run python test_field_selector.py
cd tests && uv run python test_ui.py
```

### Test Data Location
- Tests use `tests/data/` directory
- Isolated from production data

---

## Development Workflow

1. **Code changes**: Modify Python or JS files
2. **Lint**: `black --check . && ruff check .`
3. **Format**: `black .`
4. **Test**: `pytest && cd tests && uv run python test_*.py`
5. **Server restart**: `pulse restart .` (for Python changes)
6. **Browser refresh**: Ctrl+Shift+R (for frontend changes)

---

## Common Patterns

### SSE Endpoint Pattern
```python
async def event_generator():
    yield sse_event("log", {"message": "Starting..."})
    # ... processing ...
    yield sse_event("done", {"total": count})

return sse_response(event_generator())
```

### Database Session Pattern
```python
with get_db().get_session() as session:
    papers = session.query(Paper).filter(...).all()
    session.commit()  # If writing
```

### Vue Component Pattern
```javascript
app.component("my-component", {
    props: ["propName"],
    emits: ["update:propName"],
    setup(props, { emit }) {
        const localState = ref(null);
        return { localState };
    },
    template: `...`
});
```

### Pinia Store Pattern
```javascript
const useMyStore = defineStore("my", () => {
    const items = ref([]);
    const loading = ref(false);
    async function fetchItems() { ... }
    return { items, loading, fetchItems };
});
```
