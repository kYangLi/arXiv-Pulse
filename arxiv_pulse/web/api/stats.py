"""
Stats API Router
"""

import json
from collections import Counter
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter

from arxiv_pulse.config import Config
from arxiv_pulse.models import Collection, CollectionPaper, Database, Paper
from arxiv_pulse.research_fields import ARXIV_CATEGORIES, get_all_categories

router = APIRouter()


def get_db():
    """Get database instance (lazy initialization)"""
    return Database()


def update_stats_cache():
    """更新统计数据缓存"""
    with get_db().get_session() as session:
        total_papers = session.query(Paper).count()
        summarized_papers = session.query(Paper).filter_by(summarized=True).count()

        now = datetime.now(UTC).replace(tzinfo=None)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)

        today_count = session.query(Paper).filter(Paper.published >= today_start).count()
        week_count = session.query(Paper).filter(Paper.published >= week_start).count()
        month_count = session.query(Paper).filter(Paper.published >= month_start).count()

        papers = session.query(Paper).all()
        category_counter = Counter()
        for paper in papers:
            if paper.categories:
                for cat in paper.categories.split(", "):
                    if cat:
                        category_counter[cat] += 1

        top_categories = category_counter.most_common(10)

        year_counter = Counter()
        for paper in papers:
            if paper.published:
                year_counter[paper.published.year] += 1

        year_distribution = dict(sorted(year_counter.items()))

        total_collections = session.query(Collection).count()
        total_collection_papers = session.query(CollectionPaper).count()

        cache_data = {
            "updated_at": datetime.now(UTC).isoformat(),
            "papers": {
                "total": total_papers,
                "summarized": summarized_papers,
                "summarization_rate": summarized_papers / total_papers if total_papers > 0 else 0,
                "today": today_count,
                "this_week": week_count,
                "this_month": month_count,
            },
            "categories": {
                "total": len(category_counter),
                "top": [{"name": cat, "count": count} for cat, count in top_categories],
            },
            "years": year_distribution,
            "collections": {
                "total": total_collections,
                "total_papers": total_collection_papers,
            },
        }

        db = get_db()
        db.set_config("stats_cache", json.dumps(cache_data, ensure_ascii=False))
        return cache_data


@router.get("")
async def get_stats():
    """Get database statistics (from cache if available)"""
    db = get_db()
    cached = db.get_config("stats_cache")

    if cached:
        try:
            return json.loads(cached)
        except:
            pass

    return update_stats_cache()


@router.post("/refresh")
async def refresh_stats():
    """Force refresh stats cache"""
    return update_stats_cache()


@router.get("/fields")
async def get_field_stats():
    """Get research field statistics with paper counts"""
    db = get_db()

    selected_fields = db.get_selected_fields()
    all_cats = get_all_categories()

    with db.get_session() as session:
        papers = session.query(Paper).all()
        category_counter = Counter()
        for paper in papers:
            if paper.categories:
                for cat in paper.categories.split(", "):
                    if cat:
                        category_counter[cat] += 1

    fields_data = []
    for field_id, field_info in all_cats.items():
        count = category_counter.get(field_id, 0)
        fields_data.append(
            {
                "key": field_id,
                "name": field_info.get("name", field_id),
                "name_en": field_info.get("name_en", field_id),
                "paper_count": count,
                "is_selected": field_id in selected_fields,
                "recommended": field_info.get("recommended", False),
            }
        )

    return {
        "fields": fields_data,
        "selected_fields": selected_fields,
    }
