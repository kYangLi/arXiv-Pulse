"""
Paper service - 论文数据处理和增强
"""

import json
from typing import Any

from arxiv_pulse.core import Config
from arxiv_pulse.models import CollectionPaper, FigureCache, Paper
from arxiv_pulse.services.category_service import get_category_explanations
from arxiv_pulse.services.figure_service import get_figure_url_cached


def extract_key_findings(summary: str | None) -> list[str]:
    """从summary JSON中提取关键发现"""
    if not summary:
        return []
    try:
        data = json.loads(summary)
        return data.get("key_findings", [])[:5]
    except:
        return []


def summarize_and_cache_paper(paper: Paper) -> bool:
    """总结论文并保存到数据库"""
    try:
        from arxiv_pulse.ai import PaperSummarizer

        summarizer = PaperSummarizer()
        return summarizer.summarize_paper(paper)
    except Exception:
        return False


def enhance_paper_data(paper: Paper, session=None, translation_service=None, lang: str | None = None) -> dict[str, Any]:
    """增强论文数据，添加翻译、关键发现、图片等"""
    from arxiv_pulse.services.translation_service import translate_text
    from arxiv_pulse.web.dependencies import get_db

    data = paper.to_dict()

    # Get category explanations for both languages
    cat_explanations = get_category_explanations(paper.categories or "")
    data["category_explanation_zh"] = cat_explanations["zh"]
    data["category_explanation_en"] = cat_explanations["en"]

    data["ai_available"] = bool(Config.AI_API_KEY)

    if paper.summary:
        try:
            summary_data = json.loads(paper.summary)
            data["summary_data"] = summary_data
            data["key_findings"] = summary_data.get("key_findings", [])[:5]
            data["methodology"] = summary_data.get("methodology", "")
            data["keywords"] = summary_data.get("keywords", [])[:10]
        except (json.JSONDecodeError, TypeError):
            data["summary_data"] = None
            data["key_findings"] = []
            data["methodology"] = ""
            data["keywords"] = []
    else:
        data["summary_data"] = None
        data["key_findings"] = []
        data["methodology"] = ""
        data["keywords"] = []

    data["title_translation"] = translate_text(paper.title, Config.TRANSLATE_LANGUAGE)
    data["abstract_translation"] = translate_text(paper.abstract, Config.TRANSLATE_LANGUAGE) if paper.abstract else ""

    if session:
        figure = session.query(FigureCache).filter_by(arxiv_id=paper.arxiv_id).first()
        data["figure_url"] = figure.figure_url if figure else None
        collection_ids = [cp.collection_id for cp in session.query(CollectionPaper).filter_by(paper_id=paper.id).all()]
        data["collection_ids"] = collection_ids
    else:
        with get_db().get_session() as s:
            figure = s.query(FigureCache).filter_by(arxiv_id=paper.arxiv_id).first()
            data["figure_url"] = figure.figure_url if figure else None
            collection_ids = [cp.collection_id for cp in s.query(CollectionPaper).filter_by(paper_id=paper.id).all()]
            data["collection_ids"] = collection_ids

    return data
