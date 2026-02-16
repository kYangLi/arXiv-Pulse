"""
Cache API Router
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal

from arxiv_pulse.models import Database

router = APIRouter(prefix="/cache", tags=["cache"])


def get_db():
    return Database()


class ClearCacheRequest(BaseModel):
    cache_type: Literal["translations", "summaries", "figures", "contents", "all"]


@router.get("/stats")
async def get_cache_stats():
    """获取缓存统计"""
    db = get_db()
    return db.get_cache_stats()


@router.post("/clear")
async def clear_cache(request: ClearCacheRequest):
    """清理缓存"""
    db = get_db()
    results = {}

    if request.cache_type == "translations" or request.cache_type == "all":
        results["translations"] = db.clear_all_translation_cache()

    if request.cache_type == "summaries" or request.cache_type == "all":
        results["summaries"] = db.clear_all_summaries()

    if request.cache_type == "figures" or request.cache_type == "all":
        results["figures"] = db.clear_all_figure_cache()

    if request.cache_type == "contents" or request.cache_type == "all":
        results["contents"] = db.clear_all_content_cache()

    return {"success": True, "cleared": results}
