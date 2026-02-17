"""
Tasks API Router - Async task management
"""

import asyncio
import json
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from arxiv_pulse.config import Config
from arxiv_pulse.models import Paper, RecentResult, SyncTask
from arxiv_pulse.utils import sse_event, sse_response
from arxiv_pulse.web.dependencies import get_db

router = APIRouter()


class SyncTaskCreate(BaseModel):
    task_type: str
    years_back: int = 5
    force: bool = False


@router.get("/status")
async def get_sync_status():
    """Get database sync status and statistics"""
    with get_db().get_session() as session:
        total_papers = session.query(Paper).count()

        earliest_paper = session.query(Paper).order_by(Paper.created_at.asc()).first()
        latest_paper = session.query(Paper).order_by(Paper.published.desc()).first()

        last_completed_task = (
            session.query(SyncTask)
            .filter(SyncTask.status.in_(["completed", "failed"]))
            .order_by(SyncTask.completed_at.desc())
            .first()
        )

        running_task = (
            session.query(SyncTask)
            .filter(SyncTask.status.in_(["pending", "running"]))
            .order_by(SyncTask.created_at.desc())
            .first()
        )

        last_sync = None
        if last_completed_task:
            result_data = None
            if last_completed_task.result:
                try:
                    result_data = json.loads(last_completed_task.result)
                except:
                    pass

            last_sync = {
                "time": last_completed_task.completed_at.isoformat() if last_completed_task.completed_at else None,
                "status": last_completed_task.status,
                "message": last_completed_task.message,
                "papers_added": result_data.get("total_new_papers", 0) if result_data else 0,
            }

        current_task = None
        if running_task:
            current_task = {
                "id": running_task.id,
                "status": running_task.status,
                "progress": running_task.progress,
                "total": running_task.total,
                "message": running_task.message,
                "created_at": running_task.created_at.isoformat() if running_task.created_at else None,
            }

        return {
            "last_sync": last_sync,
            "database": {
                "created_at": (
                    earliest_paper.created_at.isoformat() if earliest_paper and earliest_paper.created_at else None
                ),
                "latest_paper": (
                    latest_paper.published.strftime("%Y-%m-%d") if latest_paper and latest_paper.published else None
                ),
                "total_papers": total_papers,
            },
            "current_task": current_task,
        }


@router.post("/sync")
async def start_sync_stream(
    years_back: int = Query(5, ge=1, le=20),
    force: bool = Query(False),
):
    """Start sync task with SSE stream for real-time progress"""

    async def event_generator():
        task_id = str(uuid.uuid4())

        with get_db().get_session() as session:
            task = SyncTask(
                id=task_id,
                task_type="sync",
                status="pending",
            )
            session.add(task)
            session.commit()

        yield f"data: {json.dumps({'type': 'log', 'message': '开始同步任务...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        with get_db().get_session() as session:
            task = session.query(SyncTask).filter_by(id=task_id).first()
            if task:
                task.status = "running"
                task.message = "正在初始化..."
                session.commit()

        yield f"data: {json.dumps({'type': 'log', 'message': f'回溯年数: {years_back} 年'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        mode_text = "强制同步" if force else "增量同步"
        yield f"data: {json.dumps({'type': 'log', 'message': f'同步模式: {mode_text}'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        try:
            from arxiv_pulse.arxiv_crawler import ArXivCrawler

            crawler = ArXivCrawler()

            yield f"data: {json.dumps({'type': 'log', 'message': '正在连接 arXiv API...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

            queries = Config.SEARCH_QUERIES
            total_queries = len(queries)
            total_added = 0

            for i, query in enumerate(queries, 1):
                query_short = query[:50] + "..." if len(query) > 50 else query
                yield f"data: {json.dumps({'type': 'log', 'message': f'[{i}/{total_queries}] 搜索查询: {query_short}'}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)

                yield f"data: {json.dumps({'type': 'progress', 'current': i, 'total': total_queries}, ensure_ascii=False)}\n\n"

                try:
                    result = crawler.sync_query(
                        query=query,
                        years_back=years_back,
                        force=force,
                    )
                    added = result.get("new_papers", 0)
                    total_added += added
                    yield f"data: {json.dumps({'type': 'log', 'message': f'  添加了 {added} 篇新论文'}, ensure_ascii=False)}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'  查询出错: {str(e)[:100]}'}, ensure_ascii=False)}\n\n"

                await asyncio.sleep(0.1)

            yield f"data: {json.dumps({'type': 'log', 'message': '正在刷新最近论文缓存...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)

            try:
                db = get_db()
                with db.get_session() as session:
                    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=7)
                    recent_papers = (
                        session.query(Paper)
                        .filter(Paper.published >= cutoff)
                        .order_by(Paper.published.desc())
                        .limit(64)
                        .all()
                    )
                    paper_ids = [p.id for p in recent_papers]
                db.set_recent_cache(days_back=7, paper_ids=paper_ids)
                yield f"data: {json.dumps({'type': 'log', 'message': f'缓存已更新: {len(paper_ids)} 篇论文'}, ensure_ascii=False)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'log', 'message': f'更新缓存失败: {str(e)[:80]}'}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'log', 'message': '正在更新统计缓存...'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)
            try:
                from arxiv_pulse.web.api.stats import update_stats_cache

                update_stats_cache()
                yield f"data: {json.dumps({'type': 'log', 'message': '统计缓存已更新'}, ensure_ascii=False)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'log', 'message': f'更新统计缓存失败: {str(e)[:80]}'}, ensure_ascii=False)}\n\n"

            with get_db().get_session() as session:
                task = session.query(SyncTask).filter_by(id=task_id).first()
                if task:
                    task.status = "completed"
                    task.progress = 100
                    task.message = "同步完成"
                    task.result = json.dumps({"total_new_papers": total_added})
                    task.completed_at = datetime.now(UTC).replace(tzinfo=None)
                    session.commit()

            yield f"data: {json.dumps({'type': 'done', 'papers_added': total_added}, ensure_ascii=False)}\n\n"

        except Exception as e:
            with get_db().get_session() as session:
                task = session.query(SyncTask).filter_by(id=task_id).first()
                if task:
                    task.status = "failed"
                    task.message = str(e)
                    task.completed_at = datetime.now(UTC).replace(tzinfo=None)
                    session.commit()

            yield sse_event("error", message=f"同步失败: {str(e)}")

    return sse_response(event_generator)


@router.post("")
async def create_task(data: SyncTaskCreate):
    """Create a new sync task (legacy endpoint)"""
    task_id = str(uuid.uuid4())

    with get_db().get_session() as session:
        task = SyncTask(
            id=task_id,
            task_type=data.task_type,
            status="pending",
        )
        session.add(task)
        session.commit()

    asyncio.create_task(run_sync_task(task_id, data))

    return {"task_id": task_id, "status": "pending"}


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get task status"""
    with get_db().get_session() as session:
        task = session.query(SyncTask).filter_by(id=task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task.to_dict()


async def run_sync_task(task_id: str, data: SyncTaskCreate):
    """Background task for syncing papers"""
    from arxiv_pulse.arxiv_crawler import ArXivCrawler

    with get_db().get_session() as session:
        task = session.query(SyncTask).filter_by(id=task_id).first()
        if not task:
            return
        task.status = "running"
        task.message = "Starting sync..."
        session.commit()

    try:
        crawler = ArXivCrawler()

        update_task(task_id, progress=10, message="Syncing papers from arXiv...")

        result = crawler.sync_all_queries(
            years_back=data.years_back,
            force=data.force,
        )

        update_task(task_id, progress=80, total=result.get("total_processed", 0), message="Sync completed")

        with get_db().get_session() as session:
            task = session.query(SyncTask).filter_by(id=task_id).first()
            if task:
                task.status = "completed"
                task.progress = 100
                task.message = "Sync completed successfully"
                task.result = json.dumps(result)
                task.completed_at = datetime.now(UTC).replace(tzinfo=None)
                session.commit()

    except Exception as e:
        with get_db().get_session() as session:
            task = session.query(SyncTask).filter_by(id=task_id).first()
            if task:
                task.status = "failed"
                task.message = str(e)
                task.completed_at = datetime.now(UTC).replace(tzinfo=None)
                session.commit()


def update_task(task_id: str, progress: int = 0, total: int = 0, message: str = ""):
    """Update task progress"""
    with get_db().get_session() as session:
        task = session.query(SyncTask).filter_by(id=task_id).first()
        if task:
            task.progress = progress
            task.total = total
            task.message = message
            session.commit()
