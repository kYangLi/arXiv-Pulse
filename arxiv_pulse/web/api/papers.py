"""
Papers API Router
"""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from arxiv_pulse.config import Config
from arxiv_pulse.models import Database, FigureCache, Paper
from arxiv_pulse.summarizer import PaperSummarizer

router = APIRouter()

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


def get_db():
    """Get database instance (lazy initialization)"""
    return Database()


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


def translate_text(text: str, target_lang: str = "zh") -> str:
    """使用AI API翻译文本，优先使用缓存"""
    if not text or not text.strip():
        return ""

    if target_lang == "en":
        return ""

    db = get_db()

    cached_translation = db.get_translation_cache(text, target_lang)
    if cached_translation:
        return cached_translation

    if not Config.AI_API_KEY:
        return ""

    try:
        import openai

        from arxiv_pulse.i18n import get_translation_prompt

        client = openai.OpenAI(api_key=Config.AI_API_KEY, base_url=Config.AI_BASE_URL)
        max_chars = 3000
        text_to_translate = text[:max_chars] + "... [文本过长，已截断]" if len(text) > max_chars else text

        system_prompt = get_translation_prompt(target_lang)

        response = client.chat.completions.create(
            model=Config.AI_MODEL or "DeepSeek-V3.2",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_to_translate},
            ],
            max_tokens=min(2000, len(text_to_translate) // 2),
            temperature=0.3,
        )

        translated = response.choices[0].message.content or ""
        if translated and not translated.startswith("*"):
            db.set_translation_cache(text, translated, target_lang)
        return translated
    except Exception:
        return ""


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
        summarizer = PaperSummarizer()
        return summarizer.summarize_paper(paper)
    except Exception:
        return False


def enhance_paper_data(paper: Paper, session=None) -> dict[str, Any]:
    """增强论文数据，添加翻译、关键发现、图片等"""
    data = paper.to_dict()

    data["relevance_score"] = calculate_relevance_score(paper)
    data["category_explanation"] = get_category_explanation(paper.categories or "")

    if paper.summary:
        try:
            summary_data = json.loads(paper.summary)
            parts = []
            if summary_data.get("methodology"):
                parts.append(f"【方法】{summary_data['methodology']}")
            if summary_data.get("relevance"):
                parts.append(f"【相关领域】{summary_data['relevance']}")
            if summary_data.get("impact"):
                parts.append(f"【影响】{summary_data['impact']}")
            if summary_data.get("summary"):
                parts.insert(0, summary_data["summary"])

            data["summary_text"] = "\n\n".join(parts) if parts else ""
            data["key_findings"] = summary_data.get("key_findings", [])[:5]
            data["keywords"] = summary_data.get("keywords", [])[:10]
        except (json.JSONDecodeError, TypeError):
            data["summary_text"] = paper.summary
            data["key_findings"] = []
            data["keywords"] = []
    else:
        data["summary_text"] = ""
        data["key_findings"] = []
        data["keywords"] = []

    data["title_translation"] = translate_text(paper.title)
    if paper.abstract:
        data["abstract_translation"] = translate_text(paper.abstract)
    else:
        data["abstract_translation"] = ""

    if session:
        figure = session.query(FigureCache).filter_by(arxiv_id=paper.arxiv_id).first()
        data["figure_url"] = figure.figure_url if figure else None
    else:
        with get_db().get_session() as s:
            figure = s.query(FigureCache).filter_by(arxiv_id=paper.arxiv_id).first()
            data["figure_url"] = figure.figure_url if figure else None

    return data


@router.get("")
async def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    days: int | None = None,
):
    """List papers with pagination and filters"""
    with get_db().get_session() as session:
        query = session.query(Paper)

        if category:
            query = query.filter(Paper.categories.contains(category) | Paper.primary_category.contains(category))

        if days:
            cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)
            query = query.filter(Paper.published >= cutoff)

        total = query.count()
        papers = query.order_by(Paper.published.desc()).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "papers": [enhance_paper_data(p) for p in papers],
        }


@router.get("/recent")
async def get_recent_papers(
    days: int = Query(7, ge=1),
    limit: int = Query(64, ge=1, le=200),
):
    """Get recent papers with enhanced data (translation, relevance, key findings)"""
    with get_db().get_session() as session:
        cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)
        papers = (
            session.query(Paper).filter(Paper.published >= cutoff).order_by(Paper.published.desc()).limit(limit).all()
        )

        return {
            "days": days,
            "total": len(papers),
            "papers": [enhance_paper_data(p) for p in papers],
        }


@router.get("/recent/cache")
async def get_recent_cache():
    """Get cached recent papers (instant load)"""
    db = get_db()
    cache = db.get_recent_cache()

    if not cache:
        return {
            "cached": False,
            "papers": [],
            "total": 0,
        }

    paper_ids = cache.get("paper_ids", [])
    if not paper_ids:
        return {
            "cached": True,
            "papers": [],
            "total": 0,
            "days_back": cache.get("days_back", 7),
            "updated_at": cache.get("updated_at"),
        }

    with db.get_session() as session:
        papers = session.query(Paper).filter(Paper.id.in_(paper_ids)).all()
        id_to_paper = {p.id: p for p in papers}
        ordered_papers = [id_to_paper[pid] for pid in paper_ids if pid in id_to_paper]

        result = [enhance_paper_data(p, session) for p in ordered_papers]

    return {
        "cached": True,
        "papers": result,
        "total": len(ordered_papers),
        "days_back": cache.get("days_back", 7),
        "updated_at": cache.get("updated_at"),
    }


@router.get("/recent/status")
async def get_recent_cache_status():
    """Get recent papers cache status"""
    db = get_db()
    cache = db.get_recent_cache()

    if not cache:
        return {
            "has_cache": False,
            "days_back": 7,
            "total_count": 0,
            "updated_at": None,
        }

    return {
        "has_cache": True,
        "days_back": cache.get("days_back", 7),
        "total_count": cache.get("total_count", 0),
        "updated_at": cache.get("updated_at"),
    }


@router.post("/recent/update")
async def update_recent_papers(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(64, ge=1, le=200),
    need_sync: bool = Query(True),
    sync_years: int = Query(5, ge=1, le=20),
    categories: str | None = Query(None, description="Comma-separated category codes"),
):
    """SSE endpoint: sync -> query -> cache recent papers"""

    async def event_generator():
        import asyncio
        import uuid

        from arxiv_pulse.models import SyncTask

        db = get_db()
        task_id = str(uuid.uuid4())

        category_list = [c.strip() for c in categories.split(",")] if categories else []

        with db.get_session() as session:
            task = SyncTask(
                id=task_id,
                task_type="recent_update",
                status="pending",
            )
            session.add(task)
            session.commit()

        yield f"data: {json.dumps({'type': 'log', 'message': '开始更新最近论文...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        yield f"data: {json.dumps({'type': 'log', 'message': f'查询范围: 最近 {days} 天'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        if category_list:
            yield f"data: {json.dumps({'type': 'log', 'message': f'领域过滤: {", ".join(category_list)}'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

        total_added = 0

        if need_sync:
            with db.get_session() as session:
                task = session.query(SyncTask).filter_by(id=task_id).first()
                if task:
                    task.status = "running"
                    task.message = "正在同步新论文..."
                    session.commit()

            yield f"data: {json.dumps({'type': 'log', 'message': '正在同步新论文...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

            try:
                from arxiv_pulse.arxiv_crawler import ArXivCrawler

                crawler = ArXivCrawler()
                queries = Config.SEARCH_QUERIES

                for i, query in enumerate(queries, 1):
                    query_short = query[:50] + "..." if len(query) > 50 else query
                    yield f"data: {json.dumps({'type': 'log', 'message': f'[{i}/{len(queries)}] 同步: {query_short}'}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.05)

                    try:
                        result = crawler.sync_query(query=query, years_back=sync_years, force=False)
                        added = result.get("new_papers", 0)
                        total_added += added
                    except Exception as e:
                        yield f"data: {json.dumps({'type': 'log', 'message': f'  同步出错: {str(e)[:80]}'}, ensure_ascii=False)}\n\n"

                yield f"data: {json.dumps({'type': 'log', 'message': f'同步完成，新增 {total_added} 篇论文'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

            except Exception as e:
                yield f"data: {json.dumps({'type': 'log', 'message': f'同步失败: {str(e)[:100]}'}, ensure_ascii=False)}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'log', 'message': '跳过同步，直接查询数据库'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

        yield f"data: {json.dumps({'type': 'log', 'message': '正在查询最近论文...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        with db.get_session() as session:
            cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)
            query = session.query(Paper).filter(Paper.published >= cutoff)

            if category_list:
                from sqlalchemy import or_

                conditions = []
                for cat in category_list:
                    conditions.append(Paper.categories.contains(cat))
                    conditions.append(Paper.primary_category.contains(cat))
                query = query.filter(or_(*conditions))

            papers = query.order_by(Paper.published.desc()).limit(limit).all()
            paper_ids = [p.id for p in papers]

        yield f"data: {json.dumps({'type': 'log', 'message': f'找到 {len(papers)} 篇最近论文'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        db.set_recent_cache(days_back=days, paper_ids=paper_ids)
        yield f"data: {json.dumps({'type': 'log', 'message': '缓存已更新'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        summarized_count = 0
        figure_count = 0

        for i, paper in enumerate(papers):
            if not paper.summarized:
                yield f"data: {json.dumps({'type': 'log', 'message': f'[{i + 1}/{len(papers)}] 总结论文 {paper.arxiv_id}...'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.05)
                if summarize_and_cache_paper(paper):
                    summarized_count += 1
                    paper.summarized = True

            with db.get_session() as s:
                figure_url = get_figure_url_cached(paper.arxiv_id, s)
            if not figure_url:
                yield f"data: {json.dumps({'type': 'log', 'message': f'[{i + 1}/{len(papers)}] 获取图片 {paper.arxiv_id}...'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.05)
                fetch_and_cache_figure(paper.arxiv_id)
                figure_count += 1

            enhanced = enhance_paper_data(paper)
            yield f"data: {json.dumps({'type': 'result', 'paper': enhanced, 'index': i + 1, 'total': len(papers)}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.03)

        with db.get_session() as session:
            task = session.query(SyncTask).filter_by(id=task_id).first()
            if task:
                task.status = "completed"
                task.progress = 100
                task.message = "更新完成"
                task.result = json.dumps({"total_papers": len(papers), "new_synced": total_added})
                task.completed_at = datetime.now(UTC).replace(tzinfo=None)
                session.commit()

        yield f"data: {json.dumps({'type': 'done', 'total': len(papers), 'synced': total_added, 'summarized': summarized_count, 'figures': figure_count}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


import re


def parse_arxiv_id(query: str) -> str | None:
    """Parse arXiv ID from various formats

    Supports:
    - arXiv:2602.09790
    - https://arxiv.org/abs/2602.09790v1
    - https://arxiv.org/pdf/2602.09790v1.pdf
    - 2602.09790
    - 2602.09790v1

    Returns cleaned arXiv ID without version, or None if not an arXiv ID
    """
    q = query.strip()

    if q.startswith("arXiv:"):
        q = q[6:]

    arxiv_pattern = r"(\d{4}\.\d{4,5})"
    match = re.search(arxiv_pattern, q)
    if match:
        return match.group(1)

    return None


@router.get("/quick")
async def quick_fetch(q: str = Query(..., min_length=1)):
    """SSE endpoint for quick paper fetch by arXiv ID or fuzzy search"""

    async def event_generator():
        import asyncio

        from arxiv_pulse.arxiv_crawler import ArXivCrawler

        db = get_db()
        arxiv_id = parse_arxiv_id(q)

        if arxiv_id:
            yield f"data: {json.dumps({'type': 'log', 'message': f'识别为 arXiv ID: {arxiv_id}'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

            with db.get_session() as session:
                paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()

            if paper:
                yield f"data: {json.dumps({'type': 'log', 'message': '在数据库中找到论文'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

                if not paper.summarized:
                    yield f"data: {json.dumps({'type': 'log', 'message': '正在生成 AI 总结...'}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.1)
                    if summarize_and_cache_paper(paper):
                        with db.get_session() as s:
                            s.query(Paper).filter_by(id=paper.id).update({"summarized": True})

                with db.get_session() as s:
                    figure_url = get_figure_url_cached(arxiv_id, s)
                if not figure_url:
                    yield f"data: {json.dumps({'type': 'log', 'message': '正在获取论文图片...'}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.1)
                    fetch_and_cache_figure(arxiv_id)

                enhanced = enhance_paper_data(paper)
                yield f"data: {json.dumps({'type': 'result', 'paper': enhanced, 'match_type': 'exact'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)
                yield f"data: {json.dumps({'type': 'done', 'total': 1}, ensure_ascii=False)}\n\n"
                return

            yield f"data: {json.dumps({'type': 'log', 'message': '数据库中无此论文，正在从 arXiv 获取...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

            import arxiv as arxiv_lib

            try:
                crawler = ArXivCrawler()
                paper = crawler.fetch_paper_by_id(arxiv_id)

                if paper:
                    yield f"data: {json.dumps({'type': 'log', 'message': '成功获取论文'}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.1)

                    yield f"data: {json.dumps({'type': 'log', 'message': '正在生成 AI 总结...'}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.1)
                    summarize_and_cache_paper(paper)

                    yield f"data: {json.dumps({'type': 'log', 'message': '正在获取论文图片...'}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.1)
                    fetch_and_cache_figure(arxiv_id)

                    with db.get_session() as session:
                        paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
                    enhanced = enhance_paper_data(paper)
                    yield f"data: {json.dumps({'type': 'result', 'paper': enhanced, 'match_type': 'exact'}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.1)
                    yield f"data: {json.dumps({'type': 'done', 'total': 1}, ensure_ascii=False)}\n\n"
                    return
                else:
                    yield f"data: {json.dumps({'type': 'error', 'message': f'未找到论文: {arxiv_id}（可能是 arXiv API 暂时不可用，请稍后重试）'}, ensure_ascii=False)}\n\n"
                    return

            except arxiv_lib.HTTPError as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'arXiv API 请求失败 (HTTP {e.status}): 请稍后重试'}, ensure_ascii=False)}\n\n"
                return
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'获取失败: {str(e)[:100]}'}, ensure_ascii=False)}\n\n"
                return

        yield f"data: {json.dumps({'type': 'log', 'message': f'正在进行模糊搜索: {q}'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        search_terms = [q]

        if Config.AI_API_KEY:
            try:
                import openai

                yield f"data: {json.dumps({'type': 'log', 'message': '正在使用 AI 解析搜索词...'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

                client = openai.OpenAI(api_key=Config.AI_API_KEY, base_url=Config.AI_BASE_URL)

                ai_prompt = f"""
用户正在搜索arXiv物理/计算材料科学论文，查询是: "{q}"

请将自然语言查询转换为适合arXiv搜索的关键词或短语。

重要规则：
1. 如果查询已经是明确的搜索词（如"DeepH"、"deep learning Hamiltonian"、"DFT计算"），直接使用它，不要添加同义词
2. 如果查询包含专业术语、缩写或专有名词，保持原样作为主要搜索词
3. 仅当查询非常模糊或一般性时，才生成1-2个相关关键词
4. 优先保持查询的原始意图，不要添加不相关的关键词
5. 对于英文查询，保持原样；对于中文查询，翻译为英文关键词

返回格式：JSON数组，包含1-2个搜索关键词/短语。
只返回JSON数组，不要其他文本。
"""

                response = client.chat.completions.create(
                    model=Config.AI_MODEL or "DeepSeek-V3.2",
                    messages=[
                        {
                            "role": "system",
                            "content": "你是arXiv论文搜索助手，擅长识别专业术语并将自然语言查询转换为学术搜索关键词。",
                        },
                        {"role": "user", "content": ai_prompt},
                    ],
                    max_tokens=200,
                    temperature=0.3,
                )

                ai_response = response.choices[0].message.content
                if ai_response:
                    try:
                        parsed = json.loads(ai_response)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            search_terms = parsed
                            yield f"data: {json.dumps({'type': 'log', 'message': f'AI 解析结果: {", ".join(search_terms)}'}, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0.1)
                    except:
                        pass

            except Exception as e:
                yield f"data: {json.dumps({'type': 'log', 'message': f'AI 解析失败，使用原始搜索词'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

        from arxiv_pulse.search_engine import SearchEngine, SearchFilter

        import arxiv as arxiv_lib

        all_papers = []
        remote_total = 0
        remote_new = 0

        yield f"data: {json.dumps({'type': 'log', 'message': '正在从 arXiv 远程搜索...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        try:
            crawler = ArXivCrawler()
            for term in search_terms:
                yield f"data: {json.dumps({'type': 'log', 'message': f'远程搜索: {term}'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.05)

                papers, total, new_count = crawler.search_and_save(term, max_results=15)
                remote_total += total
                remote_new += new_count

                if papers:
                    all_papers.extend(papers)
                    if new_count > 0:
                        yield f"data: {json.dumps({'type': 'log', 'message': f'找到 {total} 篇，其中 {new_count} 篇为新论文'}, ensure_ascii=False)}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'log', 'message': f'找到 {total} 篇论文（均已收录）'}, ensure_ascii=False)}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'未找到相关论文'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

        except arxiv_lib.HTTPError as e:
            yield f"data: {json.dumps({'type': 'log', 'message': f'arXiv API 暂时不可用，仅使用本地搜索'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'log', 'message': f'远程搜索失败: {str(e)[:50]}'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

        yield f"data: {json.dumps({'type': 'log', 'message': '正在搜索本地数据库...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        with db.get_session() as session:
            search_engine = SearchEngine(session)
            for term in search_terms:
                filter_config = SearchFilter(
                    query=term,
                    search_fields=["title", "abstract"],
                    days_back=0,
                    limit=20,
                    sort_by="published",
                    sort_order="desc",
                )
                local_papers = search_engine.search_papers(filter_config)
                for p in local_papers:
                    all_papers.append(p)

        seen_ids = set()
        unique_papers = []
        for p in all_papers:
            if p.arxiv_id not in seen_ids:
                seen_ids.add(p.arxiv_id)
                unique_papers.append(p)

        unique_papers.sort(key=lambda p: p.published if p.published else datetime.min, reverse=True)
        papers = unique_papers[:25]

        if not papers:
            yield f"data: {json.dumps({'type': 'log', 'message': '未找到匹配论文'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)
            yield f"data: {json.dumps({'type': 'done', 'total': 0}, ensure_ascii=False)}\n\n"
            return

        summary_msg = f"合并结果：共 {len(papers)} 篇论文"
        if remote_new > 0:
            summary_msg += f"（远程新增 {remote_new} 篇）"
        yield f"data: {json.dumps({'type': 'log', 'message': summary_msg}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        for i, paper in enumerate(papers):
            if not paper.summarized:
                yield f"data: {json.dumps({'type': 'log', 'message': f'[{i + 1}/{len(papers)}] 正在总结...'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.05)
                if summarize_and_cache_paper(paper):
                    paper.summarized = True

            with db.get_session() as s:
                figure_url = get_figure_url_cached(paper.arxiv_id, s)
            if not figure_url:
                yield f"data: {json.dumps({'type': 'log', 'message': f'[{i + 1}/{len(papers)}] 获取图片...'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.05)
                fetch_and_cache_figure(paper.arxiv_id)

            enhanced = enhance_paper_data(paper)
            yield f"data: {json.dumps({'type': 'result', 'paper': enhanced, 'index': i + 1, 'total': len(papers), 'match_type': 'fuzzy'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.03)

        yield f"data: {json.dumps({'type': 'done', 'total': len(papers)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/search")
async def search_papers(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    days: int | None = None,
):
    """Search papers by query (basic search without AI parsing)"""
    from arxiv_pulse.search_engine import SearchEngine, SearchFilter

    with get_db().get_session() as session:
        search_engine = SearchEngine(session)
        days_back = days if days else 0

        filter_config = SearchFilter(
            query=q,
            search_fields=["title", "abstract"],
            days_back=days_back,
            limit=page_size * 2,
            sort_by="published",
            sort_order="desc",
        )

        papers = search_engine.search_papers(filter_config)

        return {
            "query": q,
            "total": len(papers),
            "page": page,
            "page_size": page_size,
            "papers": [enhance_paper_data(p) for p in papers[:page_size]],
        }


@router.get("/search/stream")
async def search_papers_stream(
    q: str = Query(..., min_length=1),
    days: int | None = None,
    limit: int = Query(20, ge=1, le=100),
):
    """SSE endpoint for real-time search with AI parsing and logs"""

    async def event_generator():
        import asyncio

        yield f"data: {json.dumps({'type': 'log', 'message': f"正在搜索: '{q}'"}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        search_terms = [q]

        if Config.AI_API_KEY:
            try:
                import openai

                yield f"data: {json.dumps({'type': 'log', 'message': '正在使用 AI 解析搜索词...'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

                client = openai.OpenAI(api_key=Config.AI_API_KEY, base_url=Config.AI_BASE_URL)

                ai_prompt = f"""
用户正在搜索arXiv物理/计算材料科学论文，查询是: "{q}"

请将自然语言查询转换为适合arXiv搜索的关键词或短语。

重要规则：
1. 如果查询已经是明确的搜索词（如"DeepH"、"deep learning Hamiltonian"、"DFT计算"），直接使用它，不要添加同义词
2. 如果查询包含专业术语、缩写或专有名词，保持原样作为主要搜索词
3. 仅当查询非常模糊或一般性时，才生成1-2个相关关键词
4. 优先保持查询的原始意图，不要添加不相关的关键词
5. 对于英文查询，保持原样；对于中文查询，翻译为英文关键词

返回格式：JSON数组，包含1-2个搜索关键词/短语。
只返回JSON数组，不要其他文本。
"""

                response = client.chat.completions.create(
                    model=Config.AI_MODEL or "DeepSeek-V3.2",
                    messages=[
                        {
                            "role": "system",
                            "content": "你是arXiv论文搜索助手，擅长识别专业术语并将自然语言查询转换为学术搜索关键词。",
                        },
                        {"role": "user", "content": ai_prompt},
                    ],
                    max_tokens=200,
                    temperature=0.3,
                )

                ai_response = response.choices[0].message.content
                if ai_response:
                    try:
                        parsed = json.loads(ai_response)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            search_terms = parsed
                            yield f"data: {json.dumps({'type': 'ai_parsed', 'terms': search_terms}, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0.1)
                    except:
                        pass

            except Exception as e:
                yield f"data: {json.dumps({'type': 'log', 'message': f'AI 解析失败: {str(e)[:100]}'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

        yield f"data: {json.dumps({'type': 'log', 'message': f'搜索词: {", ".join(search_terms)}'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        yield f"data: {json.dumps({'type': 'log', 'message': '正在数据库中搜索...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        from arxiv_pulse.search_engine import SearchEngine, SearchFilter

        with get_db().get_session() as session:
            search_engine = SearchEngine(session)
            days_back = days if days else 0

            all_papers = []
            for term in search_terms:
                filter_config = SearchFilter(
                    query=term,
                    search_fields=["title", "abstract"],
                    days_back=days_back,
                    limit=limit * 2,
                    sort_by="published",
                    sort_order="desc",
                )
                papers = search_engine.search_papers(filter_config)
                all_papers.extend(papers)

            seen_ids = set()
            unique_papers = []
            for p in all_papers:
                if p.arxiv_id not in seen_ids:
                    seen_ids.add(p.arxiv_id)
                    unique_papers.append(p)

            unique_papers.sort(key=lambda p: p.published if p.published else datetime.min, reverse=True)
            unique_papers = unique_papers[:limit]

        yield f"data: {json.dumps({'type': 'log', 'message': f'找到 {len(unique_papers)} 篇论文'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        db = get_db()
        summarized_count = 0
        figure_count = 0

        for i, paper in enumerate(unique_papers):
            if not paper.summarized:
                yield f"data: {json.dumps({'type': 'log', 'message': f'[{i + 1}/{len(unique_papers)}] 总结论文 {paper.arxiv_id}...'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.05)
                if summarize_and_cache_paper(paper):
                    summarized_count += 1
                    paper.summarized = True

            with db.get_session() as s:
                figure_url = get_figure_url_cached(paper.arxiv_id, s)
            if not figure_url:
                yield f"data: {json.dumps({'type': 'log', 'message': f'[{i + 1}/{len(unique_papers)}] 获取图片 {paper.arxiv_id}...'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.05)
                fetch_and_cache_figure(paper.arxiv_id)
                figure_count += 1

            enhanced = enhance_paper_data(paper)
            yield f"data: {json.dumps({'type': 'result', 'paper': enhanced, 'index': i + 1, 'total': len(unique_papers)}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.05)

        yield f"data: {json.dumps({'type': 'done', 'total': len(unique_papers), 'summarized': summarized_count, 'figures': figure_count}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{paper_id}")
async def get_paper(paper_id: int):
    """Get paper by ID with enhanced data"""
    with get_db().get_session() as session:
        paper = session.query(Paper).filter_by(id=paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return enhance_paper_data(paper)


@router.get("/{paper_id}/translate")
async def get_paper_translation(paper_id: int):
    """Get paper translation (title and abstract)"""
    with get_db().get_session() as session:
        paper = session.query(Paper).filter_by(id=paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        return {
            "id": paper.id,
            "arxiv_id": paper.arxiv_id,
            "title": paper.title,
            "title_translation": translate_text(paper.title),
            "abstract": paper.abstract,
            "abstract_translation": translate_text(paper.abstract) if paper.abstract else "",
        }


@router.get("/arxiv/{arxiv_id}")
async def get_paper_by_arxiv_id(arxiv_id: str):
    """Get paper by arXiv ID with enhanced data"""
    with get_db().get_session() as session:
        paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return enhance_paper_data(paper)


@router.get("/pdf/{arxiv_id}")
async def download_pdf(arxiv_id: str):
    """Download PDF from arXiv (proxy to avoid CORS)"""
    import requests
    from fastapi.responses import Response

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    try:
        response = requests.get(pdf_url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            return Response(
                content=response.content,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{arxiv_id}.pdf"'},
            )
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to download PDF from arXiv")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to download PDF: {str(e)}")
