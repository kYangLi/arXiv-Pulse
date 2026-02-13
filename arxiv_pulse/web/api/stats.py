"""
Stats API Router
"""

import json
from collections import Counter

from fastapi import APIRouter

from arxiv_pulse.models import Collection, CollectionPaper, Database, Paper
from arxiv_pulse.research_fields import RESEARCH_FIELDS

router = APIRouter()


def get_db():
    """Get database instance (lazy initialization)"""
    return Database()


@router.get("")
async def get_stats():
    """Get database statistics"""
    with get_db().get_session() as session:
        total_papers = session.query(Paper).count()
        summarized_papers = session.query(Paper).filter_by(summarized=True).count()

        today_count = 0
        week_count = 0
        month_count = 0

        from datetime import UTC, datetime, timedelta

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

        return {
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


@router.get("/fields")
async def get_field_stats():
    """Get research field statistics with paper counts"""
    db = get_db()

    selected_fields = db.get_selected_fields()

    with db.get_session() as session:
        query_counts = {}
        papers = session.query(Paper).all()

        for field_key, field_info in RESEARCH_FIELDS.items():
            count = 0
            query = field_info.get("query", "")
            for paper in papers:
                if paper.search_query and query in paper.search_query:
                    count += 1
                elif not paper.search_query:
                    pass
            if count > 0:
                query_counts[field_key] = count

    fields_data = []
    for field_key, field_info in RESEARCH_FIELDS.items():
        fields_data.append(
            {
                "key": field_key,
                "name": field_info["name"],
                "description": field_info["description"],
                "paper_count": query_counts.get(field_key, 0),
                "is_selected": field_key in selected_fields,
            }
        )

    return {
        "fields": fields_data,
        "selected_fields": selected_fields,
    }
