# ArXiv-Pulse Development Guide for AI Agents

## Project Overview

Intelligent arXiv literature crawler and analyzer for physics research. Features:
- Automated paper fetching from arXiv API
- AI-powered summarization and translation (DeepSeek/OpenAI)
- FastAPI web interface with Vue 3 + Element Plus frontend
- SQLite database with SQLAlchemy ORM
- SSE (Server-Sent Events) for real-time progress streaming
- Multilingual support (Chinese/English UI, translation to multiple languages)

Target domains: condensed matter physics, DFT, machine learning, force fields, computational materials science.

## Development Setup

```bash
git clone https://github.com/kYangLi/ArXiv-Pulse.git
cd ArXiv-Pulse
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Build/Lint/Test Commands

```bash
# Build
python -m build          # Build distribution
pip install -e .         # Install locally

# Lint (Black line-length 120, Ruff, mypy)
black .                  # Format code
black --check . && ruff check . && mypy arxiv_pulse/

# Test
pytest                              # Run all tests
pytest tests/test_module.py         # Run single test file
pytest tests/test_module.py::test_name  # Run single test
pytest --cov=arxiv_pulse            # With coverage

# Playwright browser tests (run from tests/ directory)
cd tests && uv run python test_field_selector.py

# Web server
pulse serve .                        # Start web server (background)
pulse serve . -f                     # Start web server (foreground)
pulse status .                       # Check service status
pulse stop .                         # Stop service
pulse restart .                      # Restart service
```

Note: mypy may show SQLAlchemy Column type errors - these are known issues and don't affect runtime.

## Code Style Guidelines

### Import Organization
Standard library → third-party → local imports:
```python
import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from arxiv_pulse.config import Config
from arxiv_pulse.models import Database, Paper
from arxiv_pulse.i18n import t, get_translation_prompt
```

### Naming Conventions
- **Classes**: `PascalCase` (`ArXivCrawler`, `PaperSummarizer`)
- **Variables/Functions**: `snake_case` (`search_arxiv`, `paper_ids`)
- **Constants**: `UPPER_SNAKE_CASE` (`ARXIV_MAX_RESULTS`)
- **Private**: `_private_method()`
- **Database tables**: Plural `snake_case` (`papers`, `collections`)
- **API routers**: `router = APIRouter()` at module level

### Type Hints
Use type hints for all function signatures:
```python
def enhance_paper_data(paper: Paper, session=None) -> dict[str, Any]:
    """Enhance paper data with translations and metadata."""

async def update_recent_papers(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(64, ge=1, le=200),
) -> StreamingResponse:
    """SSE endpoint for updating recent papers."""
```

### Error Handling
Use try/except for operations that may fail. Use `HTTPException` in API routes:
```python
try:
    result = crawler.sync_query(query=query, years_back=years_back)
except Exception as e:
    yield f"data: {json.dumps({'type': 'log', 'message': f'同步出错: {str(e)[:80]}'}, ensure_ascii=False)}\n\n"

# In API endpoints:
if not collection:
    raise HTTPException(status_code=404, detail="Collection not found")
```

### Database Session Management
Always use context manager for sessions:
```python
with get_db().get_session() as session:
    papers = session.query(Paper).filter(Paper.id.in_(paper_ids)).all()
```

### SSE (Server-Sent Events) Pattern
```python
async def event_generator():
    yield f"data: {json.dumps({'type': 'log', 'message': '开始处理...'}, ensure_ascii=False)}\n\n"
    await asyncio.sleep(0.1)
    yield f"data: {json.dumps({'type': 'done', 'total': len(papers)}, ensure_ascii=False)}\n\n"

return StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
    headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
)
```

### Frontend (Vue 3 + Element Plus)
Located at `arxiv_pulse/web/static/index.html` - single file application:
- Use `v-for` with `:key` for lists
- Use `ref()` for reactive state
- i18n: Use `t('key.path')` for translations
- All functions must be returned in the setup() return statement
- Use `@click.stop` to prevent event propagation on nested clickable elements

### Frontend i18n Pattern
```javascript
// Translation object structure
const i18n = {
    zh: {
        collections: {
            title: '论文集',
            create: '新建论文集',
        }
    },
    en: {
        collections: {
            title: 'Collections',
            create: 'New Collection',
        }
    }
};

// Usage
function t(key, params = {}) {
    const keys = key.split('.');
    let value = i18n[currentLang.value];
    for (const k of keys) {
        if (value && typeof value === 'object') value = value[k];
        else return key;
    }
    if (typeof value !== 'string') return key;
    return value.replace(/\{(\w+)\}/g, (_, k) => params[k] ?? `{${k}}`);
}
```

### SSE Frontend Handling
```javascript
let buffer = '';
while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
        }
    }
}
```

## Project Structure

```
arxiv_pulse/
├── arxiv_crawler.py      # arXiv API interactions
├── cli.py                # CLI entry (pulse command)
├── config.py             # Configuration management
├── models.py             # SQLAlchemy models
├── output_manager.py     # Console output formatting
├── search_engine.py      # Enhanced search functionality
├── summarizer.py         # AI summarization
├── i18n/                 # Internationalization
│   ├── __init__.py       # t() function, get_translation_prompt()
│   ├── zh.py             # Chinese translations
│   └── en.py             # English translations
└── web/
    ├── app.py            # FastAPI application
    ├── static/index.html # Vue 3 frontend (single file)
    └── api/
        ├── papers.py     # Paper endpoints + SSE search/recent
        ├── collections.py # Collection CRUD
        ├── tasks.py      # Sync task management + SSE
        ├── stats.py      # Database statistics
        ├── cache.py      # Cache management
        ├── export.py     # Export functionality
        └── chat.py       # AI chat assistant
```

## Configuration

Configuration is stored in database, managed via Web UI settings:
- `AI_API_KEY`: OpenAI/DeepSeek API key
- `AI_MODEL`: Model name (default: DeepSeek-V3.2)
- `AI_BASE_URL`: API base URL
- `ui_language`: UI language ("zh" | "en")
- `translate_language`: Translation target
- `years_back`: Years to sync
- `arxiv_max_results`: Max results per query

## Common Pitfalls

1. **el-dialog in conditional render**: `el-dialog` inside `v-if/v-else` won't render when condition is false. Move dialogs outside conditional blocks or use `teleported` prop.

2. **Vue ref access**: Always use `.value` when accessing refs in JavaScript functions.

3. **Event propagation**: Use `@click.stop` on nested clickable elements (dropdowns inside cards).

4. **ECharts reinitialization**: After DOM changes, dispose old chart instance before creating new one. Use `initChartsWithRetry()` pattern for page switches.

5. **Translation cache key**: Includes target language, so different languages have independent caches.

6. **Stats cache**: Call `refresh_stats_cache()` after collection CRUD operations to keep homepage stats accurate.

7. **Paper cart vs selectedPaper**: When adding papers to collection, distinguish between cart (multiple papers) and single paper from card click. Clear selectedPaper on dialog close.

8. **Page transitions**: All pages should be inside the same `<transition>` wrapper for consistent animations.

9. **z-index for floating panels**: Use dynamic `ref` values for z-index to enable click-to-focus behavior.

## Notes for AI Agents

1. **Check existing patterns** before implementing new features
2. **Use HTTPException** for API errors
3. **Always use session context manager** for database operations
4. **Run lint commands** before committing: `black --check . && ruff check .`
5. **Restart server** after Python code changes
6. **Force refresh browser** (Ctrl+Shift+R) after frontend changes
7. **Use i18n** for user-facing strings: `from arxiv_pulse.i18n import t`
8. **Test database location**: Tests use `tests/data/` directory to avoid polluting production data
9. **Pagination**: Collections use pagination (20 papers/page). Update `collectionCurrentPage`, `collectionTotalCount`, `collectionTotalPages` when fetching.
10. **Page switch refresh**: Use `watch(currentPage, ...)` to refresh data when switching pages (home → fetchStats, collections → fetchCollections).

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET/PUT | Get/update configuration |
| `/api/config/test-ai` | POST | Test AI connection |
| `/api/papers/recent/cache` | GET | Get cached recent papers |
| `/api/papers/recent/update` | POST (SSE) | Update recent papers |
| `/api/papers/search/stream` | GET (SSE) | AI-powered search |
| `/api/collections` | GET/POST | List/create collections |
| `/api/collections/{id}` | GET/PUT/DELETE | Collection CRUD |
| `/api/collections/{id}/papers` | GET (paginated) | Get papers in collection |
| `/api/collections/{id}/papers` | POST | Add paper to collection |
| `/api/collections/{id}/papers/{paper_id}` | DELETE | Remove paper from collection |
| `/api/tasks/sync` | POST (SSE) | Start sync with progress |
| `/api/stats` | GET | Database statistics (cached) |
| `/api/stats/refresh` | POST | Force refresh stats cache |
| `/api/chat/sessions` | GET/POST | List/create chat sessions |
| `/api/cache/stats` | GET | Get cache statistics |
| `/api/cache/clear/{type}` | POST | Clear specific cache type |
