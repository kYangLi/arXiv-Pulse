"""
Config API Router
"""

import json
from typing import Any

import openai
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from arxiv_pulse.config import Config
from arxiv_pulse.models import Database

router = APIRouter()


class ConfigUpdate(BaseModel):
    ai_api_key: str | None = None
    ai_model: str | None = None
    ai_base_url: str | None = None
    search_queries: list[str] | None = None
    arxiv_max_results: int | None = None
    years_back: int | None = None
    report_max_papers: int | None = None
    selected_fields: list[str] | None = None


class TestAIRequest(BaseModel):
    ai_api_key: str | None = None
    ai_base_url: str | None = None
    ai_model: str | None = None


class InitConfig(BaseModel):
    ai_api_key: str = ""
    ai_model: str = "DeepSeek-V3.2"
    ai_base_url: str = "https://llmapi.paratera.com"
    selected_fields: list[str] = []
    years_back: int = 5


def get_db():
    return Database()


@router.get("")
async def get_config():
    """获取当前配置"""
    db = get_db()
    config = db.get_all_config()

    return {
        "ai_api_key": "***" if config.get("ai_api_key") else "",
        "ai_model": config.get("ai_model", "DeepSeek-V3.2"),
        "ai_base_url": config.get("ai_base_url", "https://llmapi.paratera.com"),
        "search_queries": db.get_search_queries(),
        "arxiv_max_results": int(config.get("arxiv_max_results", 10000)),
        "years_back": int(config.get("years_back", 5)),
        "report_max_papers": int(config.get("report_max_papers", 64)),
        "selected_fields": db.get_selected_fields(),
        "is_initialized": db.is_initialized(),
    }


@router.put("")
async def update_config(config_update: ConfigUpdate):
    """更新配置"""
    from arxiv_pulse.research_fields import RESEARCH_FIELDS

    db = get_db()

    if config_update.ai_api_key is not None and config_update.ai_api_key != "***":
        db.set_config("ai_api_key", config_update.ai_api_key)
    if config_update.ai_model is not None:
        db.set_config("ai_model", config_update.ai_model)
    if config_update.ai_base_url is not None:
        db.set_config("ai_base_url", config_update.ai_base_url)
    if config_update.search_queries is not None:
        db.set_search_queries(config_update.search_queries)
    if config_update.arxiv_max_results is not None:
        db.set_config("arxiv_max_results", str(config_update.arxiv_max_results))
    if config_update.years_back is not None:
        db.set_config("years_back", str(config_update.years_back))
    if config_update.report_max_papers is not None:
        db.set_config("report_max_papers", str(config_update.report_max_papers))
    if config_update.selected_fields is not None:
        db.set_selected_fields(config_update.selected_fields)
        search_queries = []
        for field_key in config_update.selected_fields:
            if field_key in RESEARCH_FIELDS:
                search_queries.append(RESEARCH_FIELDS[field_key]["query"])
        if search_queries:
            db.set_search_queries(search_queries)

    return {"success": True, "message": "配置已更新"}


@router.get("/status")
async def get_status():
    """获取系统状态"""
    db = get_db()

    with db.get_session() as session:
        from arxiv_pulse.models import Paper

        total_papers = session.query(Paper).count()
        summarized = session.query(Paper).filter_by(summarized=True).count()

    return {
        "is_initialized": db.is_initialized(),
        "total_papers": total_papers,
        "summarized_papers": summarized,
        "has_api_key": bool(db.get_config("ai_api_key")),
    }


@router.post("/test-ai")
async def test_ai_connection(request: TestAIRequest | None = None):
    """测试 AI API 连接"""
    db = get_db()

    if request and request.ai_api_key:
        api_key = request.ai_api_key
        base_url = request.ai_base_url or db.get_config("ai_base_url", "https://llmapi.paratera.com")
        model = request.ai_model or db.get_config("ai_model", "DeepSeek-V3.2")
    else:
        api_key = db.get_config("ai_api_key", "")
        base_url = db.get_config("ai_base_url", "https://llmapi.paratera.com")
        model = db.get_config("ai_model", "DeepSeek-V3.2")

    if not api_key:
        raise HTTPException(status_code=400, detail="未设置 API 密钥")

    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10,
        )
        return {"success": True, "message": f"连接成功，模型: {model}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"连接失败: {str(e)[:100]}")


@router.get("/models")
async def get_available_models():
    """获取可用模型列表"""
    db = get_db()
    api_key = db.get_config("ai_api_key", "")
    base_url = db.get_config("ai_base_url", "https://llmapi.paratera.com")

    if not api_key:
        return {"models": [], "error": "未设置 API 密钥"}

    try:
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        models_response = client.models.list()
        models = [model.id for model in models_response.data]
        return {"models": models}
    except Exception as e:
        return {"models": [], "error": str(e)[:100]}


@router.post("/init")
async def initialize_system(init_config: InitConfig):
    """初始化系统"""
    from arxiv_pulse.research_fields import RESEARCH_FIELDS

    db = get_db()

    if db.is_initialized():
        raise HTTPException(status_code=400, detail="系统已初始化")

    db.set_config("ai_api_key", init_config.ai_api_key)
    db.set_config("ai_model", init_config.ai_model)
    db.set_config("ai_base_url", init_config.ai_base_url)
    db.set_config("years_back", str(init_config.years_back))
    db.set_selected_fields(init_config.selected_fields)

    search_queries = []
    for field_key in init_config.selected_fields:
        if field_key in RESEARCH_FIELDS:
            search_queries.append(RESEARCH_FIELDS[field_key]["query"])

    if search_queries:
        db.set_search_queries(search_queries)

    return {"success": True, "message": "配置已保存"}


@router.post("/init/sync")
async def initial_sync():
    """执行初始同步（SSE 流）"""
    import asyncio
    import uuid

    from arxiv_pulse.arxiv_crawler import ArXivCrawler

    db = get_db()

    async def event_generator():
        task_id = str(uuid.uuid4())

        yield f"data: {json.dumps({'type': 'log', 'message': '开始初始同步...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        search_queries = db.get_search_queries()
        years_back = int(db.get_config("years_back", "5"))
        arxiv_max_results = int(db.get_config("arxiv_max_results", "10000"))

        if not search_queries:
            yield f"data: {json.dumps({'type': 'error', 'message': '未设置搜索查询'}, ensure_ascii=False)}\n\n"
            return

        yield f"data: {json.dumps({'type': 'total', 'total': len(search_queries)}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': f'回溯 {years_back} 年，{len(search_queries)} 个研究领域'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        total_added = 0
        crawler = ArXivCrawler()

        for i, query in enumerate(search_queries, 1):
            query_short = query[:50] + "..." if len(query) > 50 else query
            yield f"data: {json.dumps({'type': 'log', 'message': f'[{i}/{len(search_queries)}] {query_short}'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.05)

            try:
                result = crawler.sync_query(query=query, years_back=years_back, force=False)
                print(f"[DEBUG] sync_query result: {result.get('error', 'no error')}")
                if "error" in result:
                    error_msg = result["error"][:200] if len(result["error"]) > 200 else result["error"]
                    yield f"data: {json.dumps({'type': 'log', 'message': f'  错误: {error_msg}'}, ensure_ascii=False)}\n\n"
                else:
                    added = result.get("new_papers", 0)
                    total_added += added
                    yield f"data: {json.dumps({'type': 'progress', 'current': i, 'total': len(search_queries), 'added': added}, ensure_ascii=False)}\n\n"
            except Exception as e:
                import traceback

                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'log', 'message': f'  异常: {str(e)[:200]}'}, ensure_ascii=False)}\n\n"

        db.set_initialized(True)

        with db.get_session() as session:
            from arxiv_pulse.models import Paper

            total_papers = session.query(Paper).count()

        yield f"data: {json.dumps({'type': 'log', 'message': f'同步完成，新增 {total_added} 篇论文'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        yield f"data: {json.dumps({'type': 'done', 'total_added': total_added, 'total_papers': total_papers}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
