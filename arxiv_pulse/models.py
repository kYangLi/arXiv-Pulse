import json
from datetime import UTC, datetime, timedelta
from typing import Any

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


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True)
    arxiv_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    authors = Column(Text)  # JSON string of authors list
    abstract = Column(Text)
    categories = Column(String(500))
    primary_category = Column(String(100))
    published = Column(DateTime, nullable=False)
    updated = Column(DateTime)
    pdf_url = Column(String(500))
    doi = Column(String(200))
    journal_ref = Column(String(500))
    comment = Column(Text)

    # Search relevance
    search_query = Column(String(200))
    relevance_score = Column(Float, default=0.0)
    keywords = Column(Text)  # JSON string of extracted keywords

    # Processing status
    downloaded = Column(Boolean, default=False)
    summarized = Column(Boolean, default=False)
    summary = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": json.loads(self.authors) if self.authors else [],
            "abstract": self.abstract,
            "categories": self.categories,
            "primary_category": self.primary_category,
            "published": self.published.isoformat() if self.published else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "pdf_url": self.pdf_url,
            "doi": self.doi,
            "journal_ref": self.journal_ref,
            "comment": self.comment,
            "search_query": self.search_query,
            "relevance_score": self.relevance_score,
            "keywords": json.loads(self.keywords) if self.keywords else [],
            "downloaded": self.downloaded,
            "summarized": self.summarized,
            "summary": self.summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_arxiv_entry(cls, entry, search_query):
        """Create Paper instance from arXiv entry"""
        authors = [{"name": author.name, "affiliation": getattr(author, "affiliation", "")} for author in entry.authors]

        return cls(
            arxiv_id=entry.entry_id.split("/")[-1],
            title=entry.title,
            authors=json.dumps(authors),
            abstract=entry.summary,
            categories=", ".join(entry.categories) if hasattr(entry, "categories") else entry.primary_category,
            primary_category=entry.primary_category if hasattr(entry, "primary_category") else "",
            published=entry.published,
            updated=entry.updated if hasattr(entry, "updated") else None,
            pdf_url=(
                entry.pdf_url
                if hasattr(entry, "pdf_url")
                else f"https://arxiv.org/pdf/{entry.entry_id.split('/')[-1]}.pdf"
            ),
            doi=entry.doi if hasattr(entry, "doi") else None,
            journal_ref=entry.journal_ref if hasattr(entry, "journal_ref") else None,
            comment=entry.comment if hasattr(entry, "comment") else None,
            search_query=search_query,
            relevance_score=0.0,
        )


class TranslationCache(Base):
    """缓存翻译结果以避免重复API调用"""

    __tablename__ = "translation_cache"

    id = Column(Integer, primary_key=True)
    source_text = Column(Text, nullable=False)
    source_text_hash = Column(String(64), nullable=False, unique=True, index=True)
    translated_text = Column(Text, nullable=False)
    target_language = Column(String(10), default="zh")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    def __repr__(self):
        return f"<TranslationCache(id={self.id}, hash={self.source_text_hash[:16]}...)>"


class FigureCache(Base):
    __tablename__ = "figure_cache"

    id = Column(Integer, primary_key=True)
    arxiv_id = Column(String(50), nullable=False, unique=True, index=True)
    figure_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    def __repr__(self):
        return f"<FigureCache(id={self.id}, arxiv_id={self.arxiv_id})>"


class Collection(Base):
    """论文集"""

    __tablename__ = "collections"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    color = Column(String(7), default="#409EFF")
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Collection(id={self.id}, name={self.name})>"


class CollectionPaper(Base):
    """论文集-论文关联表"""

    __tablename__ = "collection_papers"

    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    notes = Column(Text)
    tags = Column(String(500))
    read_status = Column(String(20), default="unread")
    starred = Column(Boolean, default=False)
    added_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))

    def to_dict(self):
        return {
            "id": self.id,
            "collection_id": self.collection_id,
            "paper_id": self.paper_id,
            "notes": self.notes,
            "tags": json.loads(self.tags) if self.tags else [],
            "read_status": self.read_status,
            "starred": self.starred,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }

    def __repr__(self):
        return f"<CollectionPaper(collection_id={self.collection_id}, paper_id={self.paper_id})>"


class SyncTask(Base):
    """同步任务状态"""

    __tablename__ = "sync_tasks"

    id = Column(String(36), primary_key=True)
    task_type = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0)
    total = Column(Integer, default=0)
    message = Column(Text)
    result = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    completed_at = Column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "task_type": self.task_type,
            "status": self.status,
            "progress": self.progress,
            "total": self.total,
            "message": self.message,
            "result": json.loads(self.result) if self.result else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f"<SyncTask(id={self.id}, type={self.task_type}, status={self.status})>"


class RecentResult(Base):
    """最近论文查询结果缓存"""

    __tablename__ = "recent_results"

    id = Column(Integer, primary_key=True)
    days_back = Column(Integer, default=7)
    paper_ids = Column(Text)
    total_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "days_back": self.days_back,
            "paper_ids": json.loads(self.paper_ids) if self.paper_ids else [],
            "total_count": self.total_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<RecentResult(id={self.id}, days_back={self.days_back}, count={self.total_count})>"


class SystemConfig(Base):
    """系统配置表"""

    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    description = Column(String(500))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<SystemConfig(key={self.key}, value={self.value[:20] if self.value else None}...)>"


class Database:
    _instance = None
    _engine = None

    def __new__(cls, db_url: str | None = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._engine = create_engine(db_url or "sqlite:///data/arxiv_papers.db")
            Base.metadata.create_all(cls._engine)
        return cls._instance

    def __init__(self, db_url: str | None = None):
        self.Session = sessionmaker(bind=self._engine)

    def get_session(self):
        return self.Session()

    def paper_exists(self, arxiv_id):
        """Check if paper already exists"""
        with self.get_session() as session:
            return session.query(Paper).filter_by(arxiv_id=arxiv_id).first() is not None

    def add_paper(self, paper):
        """Add paper to database"""
        with self.get_session() as session:
            session.add(paper)
            session.commit()
            return paper.id

    def update_paper(self, arxiv_id, **kwargs):
        """Update paper fields"""
        with self.get_session() as session:
            paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
            if paper:
                for key, value in kwargs.items():
                    setattr(paper, key, value)
                paper.updated_at = datetime.now(UTC).replace(tzinfo=None)
                session.commit()
                return True
            return False

    def get_recent_papers(self, days=7, limit=100):
        """Get recent papers"""
        with self.get_session() as session:
            cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)
            return (
                session.query(Paper)
                .filter(Paper.published >= cutoff_date)
                .order_by(Paper.published.desc())
                .limit(limit)
                .all()
            )

    def get_papers_by_category(self, category, limit=64):
        """Get papers by category"""
        with self.get_session() as session:
            return (
                session.query(Paper)
                .filter(Paper.categories.contains(category) | Paper.primary_category.contains(category))
                .order_by(Paper.published.desc())
                .limit(limit)
                .all()
            )

    def get_papers_to_summarize(self, limit=20):
        """Get papers that need summarization"""
        with self.get_session() as session:
            return (
                session.query(Paper)
                .filter(Paper.summarized == False, Paper.abstract.isnot(None))
                .order_by(Paper.published.desc())
                .limit(limit)
                .all()
            )

    def get_statistics(self):
        """Get database statistics"""
        with self.get_session() as session:
            total = session.query(Paper).count()
            summarized = session.query(Paper).filter_by(summarized=True).count()
            categories = {}
            papers = session.query(Paper).all()
            for paper in papers:
                for cat in paper.categories.split(", "):
                    categories[cat] = categories.get(cat, 0) + 1

            return {
                "total_papers": total,
                "summarized_papers": summarized,
                "categories_distribution": categories,
            }

    def get_translation_cache(self, source_text: str, target_language: str = "zh") -> str | None:
        """获取缓存的翻译结果"""
        import hashlib

        # 计算文本哈希作为缓存键（包含目标语言）
        cache_key = f"{source_text}:{target_language}"
        text_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()

        with self.get_session() as session:
            cache_entry = session.query(TranslationCache).filter_by(source_text_hash=text_hash).first()

            if cache_entry:
                return cache_entry.translated_text
            return None

    def set_translation_cache(self, source_text: str, translated_text: str, target_language: str = "zh") -> None:
        """缓存翻译结果"""
        import hashlib

        # 计算文本哈希作为缓存键（包含目标语言）
        cache_key = f"{source_text}:{target_language}"
        text_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()

        with self.get_session() as session:
            # 检查是否已存在缓存
            existing = session.query(TranslationCache).filter_by(source_text_hash=text_hash).first()

            if existing:
                # 更新现有缓存
                existing.translated_text = translated_text
                existing.updated_at = datetime.now(UTC).replace(tzinfo=None)
            else:
                # 创建新缓存
                cache_entry = TranslationCache(
                    source_text=source_text,
                    source_text_hash=text_hash,
                    translated_text=translated_text,
                    target_language=target_language,
                )
                session.add(cache_entry)

            session.commit()

    def clear_old_translation_cache(self, days_old: int = 30) -> int:
        """清理旧的翻译缓存"""
        with self.get_session() as session:
            cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_old)
            deleted_count = session.query(TranslationCache).filter(TranslationCache.updated_at < cutoff_date).delete()
            session.commit()
            return deleted_count

    def get_figure_cache(self, arxiv_id: str) -> str | None:
        """获取缓存的图片URL"""
        with self.get_session() as session:
            cache_entry = session.query(FigureCache).filter_by(arxiv_id=arxiv_id).first()
            if cache_entry:
                return cache_entry.figure_url
            return None

    def set_figure_cache(self, arxiv_id: str, figure_url: str) -> None:
        """缓存图片URL"""
        with self.get_session() as session:
            # 检查是否已存在缓存
            existing = session.query(FigureCache).filter_by(arxiv_id=arxiv_id).first()
            if existing:
                # 更新现有缓存
                existing.figure_url = figure_url
                existing.updated_at = datetime.now(UTC).replace(tzinfo=None)
            else:
                # 创建新缓存
                cache_entry = FigureCache(
                    arxiv_id=arxiv_id,
                    figure_url=figure_url,
                )
                session.add(cache_entry)
            session.commit()

    def clear_old_figure_cache(self, days_old: int = 30) -> int:
        """清理旧的图片缓存"""
        with self.get_session() as session:
            cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_old)
            deleted_count = session.query(FigureCache).filter(FigureCache.updated_at < cutoff_date).delete()
            session.commit()
            return deleted_count

    def get_recent_cache(self) -> dict | None:
        """获取最近论文缓存"""
        with self.get_session() as session:
            cache = session.query(RecentResult).order_by(RecentResult.updated_at.desc()).first()
            if cache:
                return cache.to_dict()
            return None

    def set_recent_cache(self, days_back: int, paper_ids: list[int]) -> None:
        """保存最近论文缓存"""
        with self.get_session() as session:
            existing = session.query(RecentResult).first()
            if existing:
                existing.days_back = days_back
                existing.paper_ids = json.dumps(paper_ids)
                existing.total_count = len(paper_ids)
                existing.updated_at = datetime.now(UTC).replace(tzinfo=None)
            else:
                cache = RecentResult(
                    days_back=days_back,
                    paper_ids=json.dumps(paper_ids),
                    total_count=len(paper_ids),
                )
                session.add(cache)
            session.commit()

    def get_papers_by_ids(self, paper_ids: list[int]) -> list[Paper]:
        """根据 ID 列表获取论文"""
        with self.get_session() as session:
            papers = session.query(Paper).filter(Paper.id.in_(paper_ids)).all()
            return [p for p in papers]

    def get_config(self, key: str, default: str | None = None) -> str | None:
        """获取配置项"""
        with self.get_session() as session:
            config = session.query(SystemConfig).filter_by(key=key).first()
            if config:
                return config.value
            return default

    def set_config(self, key: str, value: str, description: str | None = None) -> None:
        """设置配置项"""
        with self.get_session() as session:
            config = session.query(SystemConfig).filter_by(key=key).first()
            if config:
                config.value = value
                if description:
                    config.description = description
            else:
                config = SystemConfig(key=key, value=value, description=description)
                session.add(config)
            session.commit()

    def get_all_config(self) -> dict[str, str]:
        """获取所有配置"""
        with self.get_session() as session:
            configs = session.query(SystemConfig).all()
            return {c.key: c.value for c in configs}

    def init_default_config(self) -> None:
        """初始化默认配置"""
        for key, value in DEFAULT_CONFIG.items():
            if self.get_config(key) is None:
                self.set_config(key, value)

    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self.get_config("is_initialized") == "true"

    def set_initialized(self, initialized: bool = True) -> None:
        """设置初始化状态"""
        self.set_config("is_initialized", "true" if initialized else "false")

    def get_search_queries(self) -> list[str]:
        """获取搜索查询列表"""
        queries_str = self.get_config("search_queries", DEFAULT_CONFIG["search_queries"])
        return [q.strip() for q in queries_str.split(";") if q.strip()]

    def set_search_queries(self, queries: list[str]) -> None:
        """设置搜索查询列表"""
        self.set_config("search_queries", "; ".join(queries))

    def get_selected_fields(self) -> list[str]:
        """获取选中的研究领域"""
        fields_str = self.get_config("selected_fields", "[]")
        try:
            return json.loads(fields_str)
        except:
            return []

    def set_selected_fields(self, fields: list[str]) -> None:
        """设置选中的研究领域"""
        self.set_config("selected_fields", json.dumps(fields))
