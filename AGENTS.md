# ArXiv-Pulse Development Guide for AI Agents

## Project Overview

Intelligent arXiv literature crawler and analyzer for physics research. Features:
- Automated paper fetching from arXiv API
- AI-powered summarization and translation (DeepSeek/OpenAI)
- FastAPI web interface with Vue 3 + Element Plus frontend
- SQLite database with SQLAlchemy ORM
- SSE (Server-Sent Events) for real-time progress streaming

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

# Web server
pulse serve .                        # Start web server
uvicorn arxiv_pulse.web.app:app --host 127.0.0.1 --port 8000 --reload
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
Located at `arxiv_pulse/web/static/index.html`:
- Use `v-for` with `:key` for lists
- Use `ref()` for reactive state
- SSE handling with buffer for incomplete lines:
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
└── web/
    ├── app.py            # FastAPI application
    ├── static/index.html # Vue 3 frontend
    └── api/
        ├── papers.py     # Paper endpoints + SSE search/recent
        ├── collections.py # Collection CRUD
        ├── tasks.py      # Sync task management + SSE
        ├── stats.py      # Database statistics
        ├── export.py     # Export functionality
        └── chat.py       # AI chat assistant
```

## Configuration

Environment variables (`.env` from `.ENV.TEMPLATE`):
- `AI_API_KEY`: OpenAI/DeepSeek API key
- `AI_MODEL`: Model name (default: DeepSeek-V3.2)
- `AI_BASE_URL`: API base URL
- `SEARCH_QUERIES`: Semicolon-separated search queries
- `DATABASE_URL`: Database URL (default: SQLite)
- `ARXIV_MAX_RESULTS`: Max results per query

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/papers/recent/cache` | GET | Get cached recent papers |
| `/api/papers/recent/update` | POST (SSE) | Update recent papers |
| `/api/papers/search/stream` | GET (SSE) | AI-powered search |
| `/api/collections` | GET/POST | List/create collections |
| `/api/collections/{id}` | GET/PUT/DELETE | Collection CRUD |
| `/api/tasks/sync` | POST (SSE) | Start sync with progress |
| `/api/stats` | GET | Database statistics |
| `/api/chat/sessions` | GET/POST | List/create chat sessions |
| `/api/chat/sessions/{id}` | GET/DELETE | Get/delete chat session |
| `/api/chat/sessions/{id}/send` | POST (SSE) | Send message to AI |
| `/api/chat/papers/{arxiv_id}/content` | GET | Get paper PDF content |

## Notes for AI Agents

1. **Check existing patterns** before implementing new features
2. **Use HTTPException** for API errors
3. **Always use session context manager** for database operations
4. **Run lint commands** before committing: `black --check . && ruff check .`
5. **Restart server** after Python code changes
6. **Force refresh browser** (Ctrl+Shift+R) after frontend changes
