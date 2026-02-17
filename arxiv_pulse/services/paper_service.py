"""
Paper service - 论文数据处理和增强
"""

import json
from typing import Any

from arxiv_pulse.config import Config
from arxiv_pulse.models import CollectionPaper, FigureCache, Paper

_category_explanations = {
    "cs.AI": "人工智能 (Artificial Intelligence)",
    "cs.CL": "计算语言学 (Computation and Language)",
    "cs.CR": "密码学与安全 (Cryptography and Security)",
    "cs.CV": "计算机视觉 (Computer Vision)",
    "cs.LG": "机器学习 (Machine Learning)",
    "cs.NE": "神经网络 (Neural and Evolutionary Computing)",
    "cs.SE": "软件工程 (Software Engineering)",
    "cs.PL": "编程语言 (Programming Languages)",
    "cs.DC": "分布式计算 (Distributed, Parallel, and Cluster Computing)",
    "cs.DS": "数据结构与算法 (Data Structures and Algorithms)",
    "cs.IT": "信息论 (Information Theory)",
    "cs.SY": "系统与控制 (Systems and Control)",
    "cond-mat": "凝聚态物理 (Condensed Matter)",
    "cond-mat.mtrl-sci": "材料科学 (Materials Science)",
    "cond-mat.str-el": "强关联电子系统 (Strongly Correlated Electrons)",
    "cond-mat.supr-con": "超导 (Superconductivity)",
    "cond-mat.mes-hall": "介观系统与量子霍尔效应 (Mesoscopic Systems and Quantum Hall Effect)",
    "cond-mat.soft": "软凝聚态物质 (Soft Condensed Matter)",
    "cond-mat.dis-nn": "无序系统与神经网络 (Disordered Systems and Neural Networks)",
    "cond-mat.stat-mech": "统计力学 (Statistical Mechanics)",
    "cond-mat.quant-gas": "量子气体 (Quantum Gases)",
    "physics": "物理学 (Physics)",
    "physics.comp-ph": "计算物理 (Computational Physics)",
    "physics.chem-ph": "化学物理 (Chemical Physics)",
    "physics.data-an": "数据分析 (Data Analysis, Statistics and Probability)",
    "physics.ins-det": "仪器与探测器 (Instrumentation and Detectors)",
    "math": "数学 (Mathematics)",
    "math.NA": "数值分析 (Numerical Analysis)",
    "math.OC": "优化与控制 (Optimization and Control)",
    "math.ST": "统计 (Statistics)",
    "q-bio": "定量生物学 (Quantitative Biology)",
    "q-bio.BM": "生物分子 (Biomolecules)",
    "q-bio.QM": "定量方法 (Quantitative Methods)",
    "q-fin": "定量金融 (Quantitative Finance)",
    "stat": "统计学 (Statistics)",
    "stat.ML": "机器学习 (Machine Learning)",
    "stat.AP": "应用 (Applications)",
    "stat.CO": "计算 (Computation)",
    "stat.ME": "方法学 (Methodology)",
    "stat.OT": "其他 (Other)",
    "stat.TH": "理论 (Theory)",
}


def get_category_explanation(category_code: str) -> str:
    """获取分类代码的解释"""
    if not category_code:
        return ""
    categories = [c.strip() for c in category_code.split(",")]
    explanations = []
    for cat in categories:
        if cat in _category_explanations:
            explanations.append(_category_explanations[cat])
        else:
            main_cat = cat.split(".")[0] if "." in cat else cat
            if main_cat in _category_explanations:
                explanations.append(f"{cat} ({_category_explanations[main_cat].split('(')[0]})")
            else:
                explanations.append(cat)
    return "; ".join(explanations)


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


def get_figure_url_cached(arxiv_id: str, session) -> str | None:
    """获取缓存的图片URL"""
    figure = session.query(FigureCache).filter_by(arxiv_id=arxiv_id).first()
    return figure.figure_url if figure else None


def fetch_and_cache_figure(arxiv_id: str) -> str | None:
    """获取论文图片并缓存到数据库"""
    try:
        from arxiv_pulse.report_generator import ReportGenerator

        report_gen = ReportGenerator()
        return report_gen.get_first_figure_url(arxiv_id, use_cache=True)
    except Exception:
        return None


def summarize_and_cache_paper(paper: Paper) -> bool:
    """总结论文并保存到数据库"""
    try:
        from arxiv_pulse.summarizer import PaperSummarizer

        summarizer = PaperSummarizer()
        return summarizer.summarize_paper(paper)
    except Exception:
        return False


def enhance_paper_data(paper: Paper, session=None, translation_service=None) -> dict[str, Any]:
    """增强论文数据，添加翻译、关键发现、图片等"""
    from arxiv_pulse.services.translation_service import translate_text
    from arxiv_pulse.web.dependencies import get_db

    data = paper.to_dict()
    data["relevance_score"] = calculate_relevance_score(paper)
    data["category_explanation"] = get_category_explanation(paper.categories or "")
    data["ai_available"] = bool(Config.AI_API_KEY)

    if paper.summary:
        try:
            summary_data = json.loads(paper.summary)
            data["summary_data"] = summary_data
            data["summary_text"] = summary_data.get("summary", "") or summary_data.get("methodology", "") or ""
            data["key_findings"] = summary_data.get("key_findings", [])[:5]
            data["keywords"] = summary_data.get("keywords", [])[:10]
        except (json.JSONDecodeError, TypeError):
            data["summary_data"] = None
            data["summary_text"] = ""
            data["key_findings"] = []
            data["keywords"] = []
    else:
        data["summary_data"] = None
        data["summary_text"] = ""
        data["key_findings"] = []
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
