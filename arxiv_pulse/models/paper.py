import json

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from arxiv_pulse.models.base import Base, utcnow


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True)
    arxiv_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    authors = Column(Text)
    abstract = Column(Text)
    categories = Column(String(500))
    primary_category = Column(String(100))
    published = Column(DateTime, nullable=False)
    updated = Column(DateTime)
    pdf_url = Column(String(500))
    doi = Column(String(200))
    journal_ref = Column(String(500))
    comment = Column(Text)
    search_query = Column(String(200))
    relevance_score = Column(Float, default=0.0)
    keywords = Column(Text)
    downloaded = Column(Boolean, default=False)
    summarized = Column(Boolean, default=False)
    summary = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self):
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
        authors = [{"name": author.name, "affiliation": getattr(author, "affiliation", "")} for author in entry.authors]
        arxiv_id = entry.entry_id.split("/")[-1]
        if "v" in arxiv_id:
            arxiv_id = arxiv_id.split("v")[0]
        return cls(
            arxiv_id=arxiv_id,
            title=entry.title,
            authors=json.dumps(authors),
            abstract=entry.summary,
            categories=", ".join(entry.categories) if hasattr(entry, "categories") else entry.primary_category,
            primary_category=entry.primary_category if hasattr(entry, "primary_category") else "",
            published=entry.published,
            updated=entry.updated if hasattr(entry, "updated") else None,
            pdf_url=(entry.pdf_url if hasattr(entry, "pdf_url") else f"https://arxiv.org/pdf/{arxiv_id}.pdf"),
            doi=entry.doi if hasattr(entry, "doi") else None,
            journal_ref=entry.journal_ref if hasattr(entry, "journal_ref") else None,
            comment=entry.comment if hasattr(entry, "comment") else None,
            search_query=search_query,
            relevance_score=0.0,
        )


class TranslationCache(Base):
    __tablename__ = "translation_cache"

    id = Column(Integer, primary_key=True)
    source_text = Column(Text, nullable=False)
    source_text_hash = Column(String(64), nullable=False, unique=True, index=True)
    translated_text = Column(Text, nullable=False)
    target_language = Column(String(10), default="zh")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def __repr__(self):
        return f"<TranslationCache(id={self.id}, hash={self.source_text_hash[:16]}...)>"


class FigureCache(Base):
    __tablename__ = "figure_cache"

    id = Column(Integer, primary_key=True)
    arxiv_id = Column(String(50), nullable=False, unique=True, index=True)
    figure_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def __repr__(self):
        return f"<FigureCache(id={self.id}, arxiv_id={self.arxiv_id})>"


class PaperContentCache(Base):
    __tablename__ = "paper_content_cache"

    id = Column(Integer, primary_key=True)
    arxiv_id = Column(String(50), nullable=False, unique=True, index=True)
    full_text = Column(Text)
    created_at = Column(DateTime, default=utcnow)

    def __repr__(self):
        return f"<PaperContentCache(id={self.id}, arxiv_id={self.arxiv_id})>"
