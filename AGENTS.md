# ArXiv-Pulse Development Guide for AI Agents

## Project Overview

Intelligent arXiv literature crawler and analyzer for physics research. Automated paper fetching, AI-powered summarization, and database management for condensed matter physics, DFT, machine learning, force fields, and computational materials science.

## Development Setup

```bash
git clone https://github.com/kYangLi/ArXiv-Pulse.git
cd ArXiv-Pulse
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Build Commands

```bash
python -m build          # Build distribution
pip install -e .         # Install locally
python -m pip show arxiv-pulse  # Check metadata
```

## Lint and Format Commands

**Black** (line-length 120), **Ruff**, **mypy**.

```bash
black .                  # Format code
black --check .          # Check formatting
ruff check .             # Run linter
ruff check --fix .       # Fix auto-fixable issues
mypy arxiv_pulse/        # Type checking
# All checks:
black --check . && ruff check . && mypy arxiv_pulse/
```

## Test Commands

No test suite yet. When added: `pytest`, `pytest tests/test_module.py`, `pytest --cov=arxiv_pulse`.

## Code Style Guidelines

### Import Organization
Standard library → third-party → local imports. Example:
```python
import os
from datetime import datetime
from typing import Optional
import arxiv
from arxiv_pulse.config import Config
```

### Naming Conventions
- **Classes**: `PascalCase` (`ArXivCrawler`)
- **Variables/Functions**: `snake_case` (`search_arxiv`)
- **Constants**: `UPPER_SNAKE_CASE` (`MAX_RESULTS_INITIAL`)
- **Private**: `_private_method()`
- **Database tables**: Plural `snake_case` (`papers`)

### Type Hints
Use type hints for all function signatures:
```python
def search_arxiv(query: str, max_results: int = 100) -> List[arxiv.Result]:
    """Search arXiv for papers."""
```

### Error Handling
Try/except for operations that may fail. Log with `output.error()`:
```python
try:
    paper_obj = Paper.from_arxiv_entry(paper, search_query)
except Exception as e:
    output.error("保存论文失败", details={"exception": str(e)})
```

### Docstrings
Triple-quoted with **Args**, **Returns**, **Raises**:
```python
def sync_papers(query: str, years_back: int = 1) -> Dict[str, Any]:
    """Synchronize papers from arXiv."""
```

### Logging and Output
Use `OutputManager` from `arxiv_pulse.output_manager`:
```python
from arxiv_pulse.output_manager import output
output.do("开始初始爬取")
output.info(f"搜索: {query}")
```

### Database Models
SQLAlchemy declarative base. Table names plural. Include timestamps:
```python
class Paper(Base):
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
```

## Project Structure

```
arxiv_pulse/
├── arxiv_crawler.py    # arXiv API
├── cli.py              # CLI entry (pulse command)
├── config.py           # Configuration
├── models.py           # Database models
├── output_manager.py   # Console output
├── report_generator.py # Report generation
├── search_engine.py    # Enhanced search
├── summarizer.py       # AI summarization
└── .ENV.TEMPLATE       # Environment template
```

## Git Workflow

- **Branch naming**: `feature/description`, `fix/issue`, `docs/topic`
- **Commit messages**: Conventional commits
- **Version tagging**: Semantic versioning (v0.7.0)

## Configuration

- Environment via `.env` (copy from `.ENV.TEMPLATE`)
- AI API: `AI_API_KEY`, `AI_MODEL`, `AI_BASE_URL`
- Search: `SEARCH_QUERIES` (semicolon-separated)
- Database: `DATABASE_URL` (default SQLite)

## Notes for AI Agents

1. **Check existing patterns** before new features
2. **Use output manager** for console output
3. **Follow type hints** and run mypy
4. **Test with actual arXiv queries** when modifying crawler
5. **Preserve backward compatibility** in config changes
6. **Document new features** in README.md when appropriate