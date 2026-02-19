"""
Paper service - 论文数据处理和增强
"""

import json
from typing import Any

from arxiv_pulse.core import Config
from arxiv_pulse.models import CollectionPaper, FigureCache, Paper
from arxiv_pulse.services.category_service import get_category_explanations
from arxiv_pulse.services.figure_service import get_figure_url_cached


def calculate_relevance_score(paper) -> int:
    """计算论文相关度评级 (1-5星)"""
    query = (paper.search_query or "").lower()
    categories = (paper.categories or "").lower()

    core_domains = [
        "condensed matter physics",
        "density functional theory",
        "first principles calculation",
        "force fields",
        "molecular dynamics",
        "computational materials science",
        "quantum chemistry",
    ]
    related_domains = ["machine learning"]
    target_categories = ["cond-mat", "physics.comp-ph", "physics.chem-ph", "quant-ph"]
    related_categories = ["cs.LG", "cs.AI", "cs.NE", "stat.ML"]
    unrelated_categories = ["cs.CR", "cs.SE", "cs.PL", "cs.DC", "q-fin"]

    score = 3
    for domain in core_domains:
        if domain in query:
            score += 2
            break
    for domain in related_domains:
        if domain in query:
            score += 1
            break
    if any(cat in categories for cat in target_categories):
        score += 2
    elif any(cat in categories for cat in related_categories):
        score += 1
    if any(cat in categories for cat in unrelated_categories):
        score -= 1
    if "computational materials science" in query and any(cat in categories for cat in unrelated_categories):
        score = max(2, score - 1)
    return max(1, min(5, score))


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
    data["relevance_score"] = calculate_relevance_score(paper)

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
