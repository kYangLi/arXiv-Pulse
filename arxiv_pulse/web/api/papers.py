"""
Papers API Router
"""

import json
import re
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from arxiv_pulse.core import Config
from arxiv_pulse.models import Paper
from arxiv_pulse.services.figure_service import fetch_and_cache_figure, get_figure_url_cached
from arxiv_pulse.services.paper_service import (
    enhance_paper_data,
    summarize_and_cache_paper,
)
from arxiv_pulse.utils import sse_event, sse_response
from arxiv_pulse.web.dependencies import get_db

router = APIRouter()


def parse_arxiv_id(query: str) -> str | None:
    """Parse arXiv ID from various formats"""
    q = query.strip()
    if q.startswith("arXiv:"):
        q = q[6:]
    arxiv_pattern = r"(\d{4}\.\d{4,5})"
    match = re.search(arxiv_pattern, q)
    return match.group(1) if match else None


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
    limit: int = Query(50, ge=1, le=200),
):
    """Get recent papers with enhanced data"""
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
        return {"cached": False, "papers": [], "total": 0}

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


@router.get("/recent/cache/stream")
async def get_recent_cache_stream():
    """SSE: Get cached recent papers with progress"""

    async def event_generator():
        import asyncio

        db = get_db()
        cache = db.get_recent_cache()

        if not cache:
            yield sse_event("done", {"total": 0, "cached": False})
            return

        paper_ids = cache.get("paper_ids", [])
        total = len(paper_ids)

        if not paper_ids:
            yield sse_event("done", {"total": 0, "cached": True})
            return

        yield sse_event(
            "start", {"total": total, "days_back": cache.get("days_back", 7), "updated_at": cache.get("updated_at")}
        )
        await asyncio.sleep(0.01)

        with db.get_session() as session:
            papers = session.query(Paper).filter(Paper.id.in_(paper_ids)).all()
            id_to_paper = {p.id: p for p in papers}

            for i, pid in enumerate(paper_ids, 1):
                if pid in id_to_paper:
                    paper = id_to_paper[pid]
                    enhanced = enhance_paper_data(paper, session)
                    yield sse_event("result", {"paper": enhanced, "index": i, "total": total})
                else:
                    yield sse_event("progress", {"index": i, "total": total})
                await asyncio.sleep(0.01)

        yield sse_event("done", {"total": total, "cached": True})

    return sse_response(event_generator)


@router.get("/recent/status")
async def get_recent_cache_status():
    """Get recent papers cache status"""
    db = get_db()
    cache = db.get_recent_cache()

    if not cache:
        return {"has_cache": False, "days_back": 7, "total_count": 0, "updated_at": None}

    return {
        "has_cache": True,
        "days_back": cache.get("days_back", 7),
        "total_count": cache.get("total_count", 0),
        "updated_at": cache.get("updated_at"),
    }


@router.post("/recent/update")
async def update_recent_papers(
    days: int = Query(7, ge=1, le=30),
    need_sync: bool = Query(True),
    categories: str | None = Query(None, description="Comma-separated category codes"),
    limit: int | None = Query(None, ge=1, le=200, description="Override config limit"),
):
    """SSE endpoint: sync -> query -> cache recent papers"""

    async def event_generator():
        import asyncio
        import uuid

        from arxiv_pulse.models import SyncTask

        db = get_db()
        task_id = str(uuid.uuid4())

        category_list = [c.strip() for c in categories.split(",")] if categories else []
        query_limit = limit or Config.RECENT_PAPERS_LIMIT
        sync_years = Config.YEARS_BACK

        with db.get_session() as session:
            task = SyncTask(id=task_id, task_type="recent_update", status="pending")
            session.add(task)
            session.commit()

        yield sse_event("log", {"message": "开始更新最近论文..."})
        await asyncio.sleep(0.1)

        yield sse_event("log", {"message": f"查询范围: 最近 {days} 天"})
        await asyncio.sleep(0.1)

        if category_list:
            yield sse_event("log", {"message": f"领域过滤: {', '.join(category_list)}"})
            await asyncio.sleep(0.1)

        total_added = 0

        if need_sync:
            with db.get_session() as session:
                task = session.query(SyncTask).filter_by(id=task_id).first()
                if task:
                    task.status = "running"
                    task.message = "正在同步新论文..."
                    session.commit()

            yield sse_event("log", {"message": "正在同步新论文..."})
            await asyncio.sleep(0.1)

            try:
                from arxiv_pulse.crawler import ArXivCrawler

                crawler = ArXivCrawler()
                queries = Config.SEARCH_QUERIES

                for i, query in enumerate(queries, 1):
                    query_short = query[:50] + "..." if len(query) > 50 else query
                    yield sse_event("log", {"message": f"[{i}/{len(queries)}] 同步: {query_short}"})
                    await asyncio.sleep(0.05)

                    try:
                        result = crawler.sync_query(query=query, years_back=sync_years, force=False)
                        total_added += result.get("new_papers", 0)
                    except Exception as e:
                        yield sse_event("log", {"message": f"  同步出错: {str(e)[:80]}"})

                yield sse_event("log", {"message": f"同步完成，新增 {total_added} 篇论文"})
                await asyncio.sleep(0.1)

            except Exception as e:
                yield sse_event("log", {"message": f"同步失败: {str(e)[:100]}"})
        else:
            yield sse_event("log", {"message": "跳过同步，直接查询数据库"})
            await asyncio.sleep(0.1)

        yield sse_event("log", {"message": "正在查询最近论文..."})
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

            papers = query.order_by(Paper.published.desc()).limit(query_limit).all()
            paper_ids = [p.id for p in papers]

        yield sse_event("log", {"message": f"找到 {len(papers)} 篇最近论文"})
        await asyncio.sleep(0.1)

        db.set_recent_cache(days_back=days, paper_ids=paper_ids)
        yield sse_event("log", {"message": "缓存已更新"})
        await asyncio.sleep(0.1)

        summarized_count = 0
        figure_count = 0

        for i, paper in enumerate(papers):
            if not paper.summarized:
                yield sse_event("log", {"message": f"[{i + 1}/{len(papers)}] 总结论文 {paper.arxiv_id}..."})
                await asyncio.sleep(0.05)
                if summarize_and_cache_paper(paper):
                    summarized_count += 1
                    with db.get_session() as s:
                        refreshed = s.query(Paper).filter_by(arxiv_id=paper.arxiv_id).first()
                        if refreshed:
                            paper = refreshed

            with db.get_session() as s:
                figure_url = get_figure_url_cached(paper.arxiv_id, s)
            if not figure_url:
                yield sse_event("log", {"message": f"[{i + 1}/{len(papers)}] 获取图片 {paper.arxiv_id}..."})
                await asyncio.sleep(0.05)
                fetch_and_cache_figure(paper.arxiv_id)
                figure_count += 1

            enhanced = enhance_paper_data(paper)
            yield sse_event("result", {"paper": enhanced, "index": i + 1, "total": len(papers)})
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

        yield sse_event(
            "done",
            {"total": len(papers), "synced": total_added, "summarized": summarized_count, "figures": figure_count},
        )

    return sse_response(event_generator)


@router.get("/quick")
async def quick_fetch(q: str = Query(..., min_length=1)):
    """SSE endpoint for quick paper fetch by arXiv ID or fuzzy search"""

    async def event_generator():
        import asyncio

        from arxiv_pulse.crawler import ArXivCrawler

        db = get_db()
        arxiv_id = parse_arxiv_id(q)

        if arxiv_id:
            yield sse_event("log", {"message": f"识别为 arXiv ID: {arxiv_id}"})
            await asyncio.sleep(0.1)

            with db.get_session() as session:
                paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()

            if paper:
                yield sse_event("log", {"message": "在数据库中找到论文"})
                await asyncio.sleep(0.1)

                if not paper.summarized:
                    yield sse_event("log", {"message": "正在生成 AI 总结..."})
                    await asyncio.sleep(0.1)
                    if summarize_and_cache_paper(paper):
                        with db.get_session() as s:
                            s.query(Paper).filter_by(id=paper.id).update({"summarized": True})
                            paper = s.query(Paper).filter_by(arxiv_id=arxiv_id).first()

                with db.get_session() as s:
                    figure_url = get_figure_url_cached(arxiv_id, s)
                    paper = s.query(Paper).filter_by(arxiv_id=arxiv_id).first() or paper
                if not figure_url:
                    yield sse_event("log", {"message": "正在获取论文图片..."})
                    await asyncio.sleep(0.1)
                    fetch_and_cache_figure(arxiv_id)

                enhanced = enhance_paper_data(paper)
                yield sse_event("result", {"paper": enhanced, "match_type": "exact"})
                await asyncio.sleep(0.1)
                yield sse_event("done", {"total": 1})
                return

            yield sse_event("log", {"message": "数据库中无此论文，正在从 arXiv 获取..."})
            await asyncio.sleep(0.1)

            import arxiv as arxiv_lib

            try:
                crawler = ArXivCrawler()
                paper = crawler.fetch_paper_by_id(arxiv_id)

                if paper:
                    yield sse_event("log", {"message": "成功获取论文"})
                    await asyncio.sleep(0.1)

                    yield sse_event("log", {"message": "正在生成 AI 总结..."})
                    await asyncio.sleep(0.1)
                    summarize_and_cache_paper(paper)

                    yield sse_event("log", {"message": "正在获取论文图片..."})
                    await asyncio.sleep(0.1)
                    fetch_and_cache_figure(arxiv_id)

                    with db.get_session() as session:
                        paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
                    enhanced = enhance_paper_data(paper)
                    yield sse_event("result", {"paper": enhanced, "match_type": "exact"})
                    await asyncio.sleep(0.1)
                    yield sse_event("done", {"total": 1})
                    return
                else:
                    yield sse_event(
                        "error", {"message": f"未找到论文: {arxiv_id}（可能是 arXiv API 暂时不可用，请稍后重试）"}
                    )
                    return

            except arxiv_lib.HTTPError as e:
                yield sse_event("error", {"message": f"arXiv API 请求失败 (HTTP {e.status}): 请稍后重试"})
                return
            except Exception as e:
                yield sse_event("error", {"message": f"获取失败: {str(e)[:100]}"})
                return

        yield sse_event("log", {"message": f"正在进行模糊搜索: {q}"})
        await asyncio.sleep(0.1)

        main_query = q
        alternative_queries = []
        keywords = []

        if Config.AI_API_KEY:
            try:
                import openai

                yield sse_event("log", {"message": "正在使用 AI 解析搜索词..."})
                await asyncio.sleep(0.1)

                client = openai.OpenAI(api_key=Config.AI_API_KEY, base_url=Config.AI_BASE_URL)

                ai_prompt = f"""用户搜索 arXiv 论文，查询是: "{q}"

请分析查询意图并生成最优搜索策略：

1. 识别专有名词/缩写/特定术语（如 DeepH, NequIP, MACE, DFT 等），保持原样
2. 对于中文查询，翻译为英文
3. 使用 arXiv 高级搜索语法：
   - AND 表示必须包含
   - OR 表示任一包含  
   - 引号 "" 表示精确短语匹配
4. 生成主查询和备选查询
5. 提取用于相关性计算的关键词

返回 JSON 格式：
{{
  "main_query": "精确的组合搜索词（使用 AND/OR/引号）",
  "alternative_queries": ["备选查询1", "备选查询2"],
  "keywords": ["关键词1", "关键词2"]
}}

示例：
输入: "使用深度学习哈密顿量方法预测力场"
输出: {{"main_query": "deep learning AND Hamiltonian AND force field", "alternative_queries": ["DeepH", "machine learning interatomic potentials"], "keywords": ["deep learning", "Hamiltonian", "force field"]}}

输入: "DeepH"
输出: {{"main_query": "DeepH", "alternative_queries": ["deep learning Hamiltonian"], "keywords": ["DeepH", "deep learning", "Hamiltonian"]}}

只返回 JSON，不要其他文本。"""

                response = client.chat.completions.create(
                    model=Config.AI_MODEL or "DeepSeek-V3.2",
                    messages=[
                        {
                            "role": "system",
                            "content": "你是 arXiv 论文搜索助手，擅长识别专业术语并将自然语言查询转换为最优的学术搜索关键词。返回纯 JSON，不要 markdown 代码块。",
                        },
                        {"role": "user", "content": ai_prompt},
                    ],
                    max_tokens=300,
                    temperature=0.2,
                )

                ai_response = response.choices[0].message.content
                if ai_response:
                    ai_response = ai_response.strip()
                    if ai_response.startswith("```"):
                        ai_response = re.sub(r"^```(?:json)?\s*", "", ai_response)
                        ai_response = re.sub(r"\s*```$", "", ai_response)
                    try:
                        parsed = json.loads(ai_response)
                        if isinstance(parsed, dict):
                            main_query = parsed.get("main_query", q)
                            alternative_queries = parsed.get("alternative_queries", [])
                            keywords = parsed.get("keywords", [])
                            log_msg = f"AI 解析: 主查询={main_query}"
                            if alternative_queries:
                                log_msg += f", 备选={len(alternative_queries)}个"
                            yield sse_event("log", {"message": log_msg})
                            await asyncio.sleep(0.1)
                    except json.JSONDecodeError:
                        pass

            except Exception as e:
                yield sse_event("log", {"message": f"AI 解析失败，使用原始搜索词: {str(e)[:50]}"})
                await asyncio.sleep(0.1)

        if not keywords:
            keywords = [kw.strip() for kw in re.split(r"[^\w]+", q.lower()) if len(kw.strip()) > 2]

        import arxiv as arxiv_lib

        from arxiv_pulse.search import SearchEngine, SearchFilter

        all_papers = []
        remote_total = 0
        remote_new = 0

        yield sse_event("log", {"message": "正在从 arXiv 远程搜索..."})
        await asyncio.sleep(0.1)

        queries_to_search = [main_query] + alternative_queries[:2]
        searched_queries = set()

        try:
            crawler = ArXivCrawler()
            for query in queries_to_search:
                if query.lower() in searched_queries:
                    continue
                searched_queries.add(query.lower())

                yield sse_event("log", {"message": f"远程搜索: {query}"})
                await asyncio.sleep(0.05)

                papers, total, new_count = crawler.search_and_save(query, max_results=15)
                remote_total += total
                remote_new += new_count

                if papers:
                    all_papers.extend(papers)
                    if new_count > 0:
                        yield sse_event("log", {"message": f"找到 {total} 篇，其中 {new_count} 篇为新论文"})
                    else:
                        yield sse_event("log", {"message": f"找到 {total} 篇论文（均已收录）"})
                else:
                    yield sse_event("log", {"message": "未找到相关论文"})
                await asyncio.sleep(0.1)

                if len(all_papers) >= 30:
                    break

        except arxiv_lib.HTTPError:
            yield sse_event("log", {"message": "arXiv API 暂时不可用，仅使用本地搜索"})
            await asyncio.sleep(0.1)
        except Exception as e:
            yield sse_event("log", {"message": f"远程搜索失败: {str(e)[:50]}"})
            await asyncio.sleep(0.1)

        yield sse_event("log", {"message": "正在搜索本地数据库..."})
        await asyncio.sleep(0.1)

        with db.get_session() as session:
            search_engine = SearchEngine(session)
            for query in queries_to_search[:2]:
                filter_config = SearchFilter(
                    query=query,
                    search_fields=["title", "abstract"],
                    days_back=0,
                    limit=Config.SEARCH_LIMIT,
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

        with db.get_session() as session:
            search_engine = SearchEngine(session)
            scored_papers = search_engine.sort_papers_by_relevance(unique_papers, keywords, q)
            papers_with_scores = [(p, score) for p, score in scored_papers[:30] if score > 0]
            if not papers_with_scores:
                papers_with_scores = scored_papers[:25]

        if not papers_with_scores:
            yield sse_event("log", {"message": "未找到匹配论文"})
            await asyncio.sleep(0.1)
            yield sse_event("done", {"total": 0})
            return

        summary_msg = f"合并结果：共 {len(papers_with_scores)} 篇论文（已按相关性排序）"
        if remote_new > 0:
            summary_msg += f"，远程新增 {remote_new} 篇"
        yield sse_event("log", {"message": summary_msg})
        await asyncio.sleep(0.1)

        for i, (paper, relevance_score) in enumerate(papers_with_scores):
            with db.get_session() as s:
                fresh_paper = s.query(Paper).filter_by(arxiv_id=paper.arxiv_id).first()
                if fresh_paper:
                    paper = fresh_paper

            if not paper.summarized:
                yield sse_event("log", {"message": f"[{i + 1}/{len(papers_with_scores)}] 正在总结..."})
                await asyncio.sleep(0.05)
                if summarize_and_cache_paper(paper):
                    with db.get_session() as s:
                        paper = s.query(Paper).filter_by(arxiv_id=paper.arxiv_id).first() or paper

            with db.get_session() as s:
                figure_url = get_figure_url_cached(paper.arxiv_id, s)
            if not figure_url:
                yield sse_event("log", {"message": f"[{i + 1}/{len(papers_with_scores)}] 获取图片..."})
                await asyncio.sleep(0.05)
                fetch_and_cache_figure(paper.arxiv_id)

            enhanced = enhance_paper_data(paper)
            enhanced["search_relevance_score"] = round(relevance_score, 1)
            yield sse_event(
                "result", {"paper": enhanced, "index": i + 1, "total": len(papers_with_scores), "match_type": "fuzzy"}
            )
            await asyncio.sleep(0.03)

        yield sse_event("done", {"total": len(papers_with_scores)})

    return sse_response(event_generator)


@router.get("/search")
async def search_papers(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    days: int | None = None,
):
    """Search papers by query (basic search without AI parsing)"""
    from arxiv_pulse.search import SearchEngine, SearchFilter

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

        yield sse_event("log", {"message": f"正在搜索: '{q}'"})
        await asyncio.sleep(0.1)

        search_terms = [q]

        if Config.AI_API_KEY:
            try:
                import openai

                yield sse_event("log", {"message": "正在使用 AI 解析搜索词..."})
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
                            yield sse_event("ai_parsed", {"terms": search_terms})
                            await asyncio.sleep(0.1)
                    except:
                        pass

            except Exception as e:
                yield sse_event("log", {"message": f"AI 解析失败: {str(e)[:100]}"})
                await asyncio.sleep(0.1)

        yield sse_event("log", {"message": f"搜索词: {', '.join(search_terms)}"})
        await asyncio.sleep(0.1)

        yield sse_event("log", {"message": "正在数据库中搜索..."})
        await asyncio.sleep(0.1)

        from arxiv_pulse.search import SearchEngine, SearchFilter

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

        yield sse_event("log", {"message": f"找到 {len(unique_papers)} 篇论文"})
        await asyncio.sleep(0.1)

        db = get_db()
        summarized_count = 0
        figure_count = 0

        for i, paper in enumerate(unique_papers):
            with db.get_session() as s:
                fresh_paper = s.query(Paper).filter_by(arxiv_id=paper.arxiv_id).first()
                if fresh_paper:
                    paper = fresh_paper

            if not paper.summarized:
                yield sse_event("log", {"message": f"[{i + 1}/{len(unique_papers)}] 总结论文 {paper.arxiv_id}..."})
                await asyncio.sleep(0.05)
                if summarize_and_cache_paper(paper):
                    summarized_count += 1
                    with db.get_session() as s:
                        refreshed = s.query(Paper).filter_by(arxiv_id=paper.arxiv_id).first()
                        if refreshed:
                            paper = refreshed

            with db.get_session() as s:
                figure_url = get_figure_url_cached(paper.arxiv_id, s)
            if not figure_url:
                yield sse_event("log", {"message": f"[{i + 1}/{len(unique_papers)}] 获取图片 {paper.arxiv_id}..."})
                await asyncio.sleep(0.05)
                fetch_and_cache_figure(paper.arxiv_id)
                figure_count += 1

            enhanced = enhance_paper_data(paper)
            yield sse_event("result", {"paper": enhanced, "index": i + 1, "total": len(unique_papers)})
            await asyncio.sleep(0.05)

        yield sse_event("done", {"total": len(unique_papers), "summarized": summarized_count, "figures": figure_count})

    return sse_response(event_generator)


class AIFilterPapersRequest(BaseModel):
    query: str
    paper_ids: list[int]


@router.post("/ai-filter")
async def ai_filter_papers(data: AIFilterPapersRequest):
    """AI-powered filter papers from a given list by query"""
    if not data.paper_ids:
        return {"papers": [], "total_found": 0}

    with get_db().get_session() as session:
        papers = session.query(Paper).filter(Paper.id.in_(data.paper_ids)).all()

        if not papers:
            return {"papers": [], "total_found": 0}

        papers_info = []
        for idx, paper in enumerate(papers):
            papers_info.append(
                {
                    "index": idx,
                    "id": paper.id,
                    "title": paper.title or "",
                    "arxiv_id": paper.arxiv_id,
                }
            )

        titles_text = "\n".join([f"{p['index']}. {p['title']}" for p in papers_info])

        prompt = f"""用户描述：{data.query}

以下是论文列表的标题（每行一个）：
{titles_text}

请找出与用户描述最相关的论文，返回编号列表（JSON数组格式），如：[1, 3, 5]

如果没有相关论文，返回空列表 []
只返回JSON数组，不要其他文字。"""

        try:
            import openai

            client = openai.OpenAI(api_key=Config.AI_API_KEY, base_url=Config.AI_BASE_URL)

            response = client.chat.completions.create(
                model=Config.AI_MODEL or "DeepSeek-V3.2",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3,
            )

            result_text = response.choices[0].message.content.strip()

            import re

            match = re.search(r"\[.*?\]", result_text)
            if match:
                indices = json.loads(match.group())
            else:
                indices = []

            matched_papers = []
            for p in papers_info:
                if p["index"] in indices:
                    paper = session.query(Paper).filter_by(id=p["id"]).first()
                    if paper:
                        paper_data = enhance_paper_data(paper)
                        paper_data["_originalIndex"] = p["index"]
                        matched_papers.append(paper_data)

            return {"papers": matched_papers, "total_found": len(matched_papers)}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI filter failed: {str(e)[:100]}")


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
    from arxiv_pulse.services.translation_service import translate_text

    with get_db().get_session() as session:
        paper = session.query(Paper).filter_by(id=paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        return {
            "id": paper.id,
            "arxiv_id": paper.arxiv_id,
            "title": paper.title,
            "title_translation": translate_text(paper.title, Config.TRANSLATE_LANGUAGE),
            "abstract": paper.abstract,
            "abstract_translation": translate_text(paper.abstract, Config.TRANSLATE_LANGUAGE) if paper.abstract else "",
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
