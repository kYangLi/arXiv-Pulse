import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from arxiv_pulse.models import (
    DEFAULT_CONFIG,
    Base,
    FigureCache,
    Paper,
    PaperContentCache,
    TranslationCache,
)


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
        with self.get_session() as session:
            return session.query(Paper).filter_by(arxiv_id=arxiv_id).first() is not None

    def add_paper(self, paper):
        with self.get_session() as session:
            session.add(paper)
            session.commit()
            return paper.id

    def update_paper(self, arxiv_id, **kwargs):
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
        with self.get_session() as session:
            return (
                session.query(Paper)
                .filter(Paper.categories.contains(category) | Paper.primary_category.contains(category))
                .order_by(Paper.published.desc())
                .limit(limit)
                .all()
            )

    def get_papers_to_summarize(self, limit=20):
        with self.get_session() as session:
            return (
                session.query(Paper)
                .filter(Paper.summarized == False, Paper.abstract.isnot(None))
                .order_by(Paper.published.desc())
                .limit(limit)
                .all()
            )

    def get_statistics(self):
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
        import hashlib

        cache_key = f"{source_text}:{target_language}"
        text_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()

        with self.get_session() as session:
            cache_entry = session.query(TranslationCache).filter_by(source_text_hash=text_hash).first()
            if cache_entry:
                return cache_entry.translated_text
            return None

    def set_translation_cache(self, source_text: str, translated_text: str, target_language: str = "zh") -> None:
        import hashlib

        cache_key = f"{source_text}:{target_language}"
        text_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()

        with self.get_session() as session:
            existing = session.query(TranslationCache).filter_by(source_text_hash=text_hash).first()
            if existing:
                existing.translated_text = translated_text
                existing.updated_at = datetime.now(UTC).replace(tzinfo=None)
            else:
                cache_entry = TranslationCache(
                    source_text=source_text,
                    source_text_hash=text_hash,
                    translated_text=translated_text,
                    target_language=target_language,
                )
                session.add(cache_entry)
            session.commit()

    def clear_old_translation_cache(self, days_old: int = 30) -> int:
        with self.get_session() as session:
            cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_old)
            deleted_count = session.query(TranslationCache).filter(TranslationCache.updated_at < cutoff_date).delete()
            session.commit()
            return deleted_count

    def get_figure_cache(self, arxiv_id: str) -> str | None:
        with self.get_session() as session:
            cache_entry = session.query(FigureCache).filter_by(arxiv_id=arxiv_id).first()
            if cache_entry:
                return cache_entry.figure_url
            return None

    def set_figure_cache(self, arxiv_id: str, figure_url: str) -> None:
        with self.get_session() as session:
            existing = session.query(FigureCache).filter_by(arxiv_id=arxiv_id).first()
            if existing:
                existing.figure_url = figure_url
                existing.updated_at = datetime.now(UTC).replace(tzinfo=None)
            else:
                cache_entry = FigureCache(arxiv_id=arxiv_id, figure_url=figure_url)
                session.add(cache_entry)
            session.commit()

    def clear_old_figure_cache(self, days_old: int = 30) -> int:
        with self.get_session() as session:
            cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_old)
            deleted_count = session.query(FigureCache).filter(FigureCache.updated_at < cutoff_date).delete()
            session.commit()
            return deleted_count

    def clear_all_translation_cache(self) -> int:
        with self.get_session() as session:
            count = session.query(TranslationCache).delete()
            session.commit()
            return count

    def clear_all_figure_cache(self) -> int:
        with self.get_session() as session:
            count = session.query(FigureCache).delete()
            session.commit()
            return count

    def clear_all_content_cache(self) -> int:
        with self.get_session() as session:
            count = session.query(PaperContentCache).delete()
            session.commit()
            return count

    def clear_all_summaries(self) -> int:
        with self.get_session() as session:
            papers = session.query(Paper).filter(Paper.summarized == True).all()
            count = len(papers)
            for paper in papers:
                paper.summarized = False
                paper.summary = None
            session.commit()
            return count

    def get_cache_stats(self) -> dict:
        with self.get_session() as session:
            return {
                "translations": session.query(TranslationCache).count(),
                "summaries": session.query(Paper).filter(Paper.summarized == True).count(),
                "figures": session.query(FigureCache).count(),
                "contents": session.query(PaperContentCache).count(),
            }

    def get_recent_cache(self) -> dict | None:
        from arxiv_pulse.models import RecentResult

        with self.get_session() as session:
            cache = session.query(RecentResult).order_by(RecentResult.updated_at.desc()).first()
            if cache:
                return cache.to_dict()
            return None

    def set_recent_cache(self, days_back: int, paper_ids: list[int]) -> None:
        from arxiv_pulse.models import RecentResult

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
        with self.get_session() as session:
            papers = session.query(Paper).filter(Paper.id.in_(paper_ids)).all()
            return [p for p in papers]

    def get_config(self, key: str, default: str | None = None) -> str | None:
        from arxiv_pulse.models import SystemConfig

        with self.get_session() as session:
            config = session.query(SystemConfig).filter_by(key=key).first()
            if config:
                return config.value
            return default

    def set_config(self, key: str, value: str, description: str | None = None) -> None:
        from arxiv_pulse.models import SystemConfig

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
        from arxiv_pulse.models import SystemConfig

        with self.get_session() as session:
            configs = session.query(SystemConfig).all()
            return {c.key: c.value for c in configs}

    def init_default_config(self) -> None:
        for key, value in DEFAULT_CONFIG.items():
            if self.get_config(key) is None:
                self.set_config(key, value)

    def is_initialized(self) -> bool:
        return self.get_config("is_initialized") == "true"

    def set_initialized(self, initialized: bool = True) -> None:
        self.set_config("is_initialized", "true" if initialized else "false")

    def get_search_queries(self) -> list[str]:
        queries_str = self.get_config("search_queries", DEFAULT_CONFIG["search_queries"])
        return [q.strip() for q in queries_str.split(";") if q.strip()]

    def set_search_queries(self, queries: list[str]) -> None:
        self.set_config("search_queries", "; ".join(queries))

    def get_selected_fields(self) -> list[str]:
        fields_str = self.get_config("selected_fields", "[]")
        try:
            return json.loads(fields_str)
        except:
            return []

    def set_selected_fields(self, fields: list[str]) -> None:
        self.set_config("selected_fields", json.dumps(fields))
