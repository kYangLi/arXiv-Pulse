import json
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

DEFAULT_CONFIG = {
    "ai_api_key": "",
    "ai_model": "DeepSeek-V3.2",
    "ai_base_url": "https://llmapi.paratera.com",
    "search_queries": 'condensed matter physics AND cat:cond-mat.*; (ti:"density functional" OR abs:"density functional") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci OR cat:physics.chem-ph); (ti:"machine learning" OR abs:"machine learning") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci OR cat:physics.chem-ph)',
    "arxiv_max_results": "10000",
    "years_back": "5",
    "report_max_papers": "64",
    "is_initialized": "false",
    "selected_fields": "[]",
}


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
