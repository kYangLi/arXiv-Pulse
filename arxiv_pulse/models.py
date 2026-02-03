from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Float,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import json
from typing import Optional

from arxiv_pulse.config import Config

Base = declarative_base()


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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
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
            pdf_url=entry.pdf_url
            if hasattr(entry, "pdf_url")
            else f"https://arxiv.org/pdf/{entry.entry_id.split('/')[-1]}.pdf",
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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    def __repr__(self):
        return f"<TranslationCache(id={self.id}, hash={self.source_text_hash[:16]}...)>"


class Database:
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

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
                paper.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                session.commit()
                return True
            return False

    def get_recent_papers(self, days=7, limit=100):
        """Get recent papers"""
        with self.get_session() as session:
            cutoff_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
            return (
                session.query(Paper)
                .filter(Paper.published >= cutoff_date)
                .order_by(Paper.published.desc())
                .limit(limit)
                .all()
            )

    def get_papers_by_category(self, category, limit=50):
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

    def get_translation_cache(self, source_text: str, target_language: str = "zh") -> Optional[str]:
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
                existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
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
            cutoff_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_old)
            deleted_count = session.query(TranslationCache).filter(TranslationCache.updated_at < cutoff_date).delete()
            session.commit()
            return deleted_count
