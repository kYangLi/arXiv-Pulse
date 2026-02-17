"""
Collections API Router
"""

import json
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from arxiv_pulse.models import Collection, CollectionPaper, Database, Paper

router = APIRouter()


def get_db():
    """Get database instance (lazy initialization)"""
    return Database()


def refresh_stats_cache():
    """Refresh stats cache after collection changes"""
    from arxiv_pulse.web.api.stats import update_stats_cache

    update_stats_cache()


def enhance_paper_data(paper: Paper) -> dict:
    """增强论文数据，添加翻译、关键发现、图片等"""
    from arxiv_pulse.web.api.papers import enhance_paper_data as _enhance

    return _enhance(paper)


class CollectionCreate(BaseModel):
    name: str
    description: str | None = None
    color: str = "#409EFF"
    icon: str | None = None


class CollectionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    icon: str | None = None


class AddPaperToCollection(BaseModel):
    paper_id: int
    notes: str | None = None
    tags: list[str] | None = None


class UpdateCollectionPaper(BaseModel):
    notes: str | None = None
    tags: list[str] | None = None
    read_status: str | None = None
    starred: bool | None = None


@router.get("")
async def list_collections():
    """List all collections"""
    with get_db().get_session() as session:
        collections = session.query(Collection).order_by(Collection.sort_order, Collection.created_at.desc()).all()
        result = []
        for c in collections:
            paper_count = session.query(CollectionPaper).filter_by(collection_id=c.id).count()
            data = c.to_dict()
            data["paper_count"] = paper_count
            result.append(data)
        return result


@router.post("")
async def create_collection(data: CollectionCreate):
    """Create a new collection"""
    with get_db().get_session() as session:
        existing = session.query(Collection).filter_by(name=data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="论文集名称已存在")

        collection = Collection(
            name=data.name,
            description=data.description,
            color=data.color,
            icon=data.icon,
        )
        session.add(collection)
        session.commit()
        session.refresh(collection)
        refresh_stats_cache()
        return collection.to_dict()


@router.get("/{collection_id}")
async def get_collection(
    collection_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    sort_by: str = Query("published"),
    sort_order: str = Query("desc"),
):
    """Get collection by ID with papers (paginated, searchable, sortable)"""
    with get_db().get_session() as session:
        collection = session.query(Collection).filter_by(id=collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        # Base query
        query = session.query(CollectionPaper).filter_by(collection_id=collection_id)

        # Get all collection papers first for search
        all_cp = query.all()

        # Filter by search keyword
        if search:
            search_lower = search.lower()
            filtered_cp = []
            for cp in all_cp:
                paper = session.query(Paper).filter_by(id=cp.paper_id).first()
                if paper:
                    title = (paper.title or "").lower()
                    authors = (paper.authors or "").lower()
                    summary = (paper.summary or "").lower()
                    if search_lower in title or search_lower in authors or search_lower in summary:
                        filtered_cp.append(cp)
            all_cp = filtered_cp

        # Sort
        def get_sort_key(cp):
            paper = session.query(Paper).filter_by(id=cp.paper_id).first()
            if sort_by == "published":
                return paper.published if paper and paper.published else datetime.min.replace(tzinfo=None)
            else:
                return cp.added_at or datetime.min.replace(tzinfo=None)

        all_cp.sort(key=get_sort_key, reverse=(sort_order == "desc"))

        # Get total count
        total_count = len(all_cp)

        # Paginate
        offset = (page - 1) * page_size
        paginated_cp = all_cp[offset : offset + page_size]

        papers = []
        for cp in paginated_cp:
            paper = session.query(Paper).filter_by(id=cp.paper_id).first()
            if paper:
                paper_data = enhance_paper_data(paper)
                paper_data["collection_info"] = cp.to_dict()
                papers.append(paper_data)

        result = collection.to_dict()
        result["papers"] = papers
        result["total_count"] = total_count
        result["page"] = page
        result["page_size"] = page_size
        result["total_pages"] = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        return result


@router.put("/{collection_id}")
async def update_collection(collection_id: int, data: CollectionUpdate):
    """Update collection"""
    with get_db().get_session() as session:
        collection = session.query(Collection).filter_by(id=collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        if data.name is not None:
            existing = (
                session.query(Collection).filter(Collection.name == data.name, Collection.id != collection_id).first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="论文集名称已存在")
            collection.name = data.name
        if data.description is not None:
            collection.description = data.description
        if data.color is not None:
            collection.color = data.color
        if data.icon is not None:
            collection.icon = data.icon

        collection.updated_at = datetime.now(UTC).replace(tzinfo=None)
        session.commit()
        session.refresh(collection)
        return collection.to_dict()


@router.delete("/{collection_id}")
async def delete_collection(collection_id: int):
    """Delete collection"""
    with get_db().get_session() as session:
        collection = session.query(Collection).filter_by(id=collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        session.query(CollectionPaper).filter_by(collection_id=collection_id).delete()
        session.delete(collection)
        session.commit()
        refresh_stats_cache()
        return {"message": "Collection deleted"}


@router.get("/{collection_id}/papers")
async def get_collection_papers(
    collection_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    sort_by: str = Query("published"),
    sort_order: str = Query("desc"),
):
    """Get papers in a collection (paginated, searchable, sortable)"""
    with get_db().get_session() as session:
        collection = session.query(Collection).filter_by(id=collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        # Base query
        query = session.query(CollectionPaper).filter_by(collection_id=collection_id)

        # Get all collection papers first for search
        all_cp = query.all()

        # Filter by search keyword
        if search:
            search_lower = search.lower()
            filtered_cp = []
            for cp in all_cp:
                paper = session.query(Paper).filter_by(id=cp.paper_id).first()
                if paper:
                    title = (paper.title or "").lower()
                    authors = (paper.authors or "").lower()
                    summary = (paper.summary or "").lower()
                    if search_lower in title or search_lower in authors or search_lower in summary:
                        filtered_cp.append(cp)
            all_cp = filtered_cp

        # Sort
        def get_sort_key(cp):
            paper = session.query(Paper).filter_by(id=cp.paper_id).first()
            if sort_by == "published":
                return paper.published if paper and paper.published else datetime.min.replace(tzinfo=None)
            else:
                return cp.added_at or datetime.min.replace(tzinfo=None)

        all_cp.sort(key=get_sort_key, reverse=(sort_order == "desc"))

        # Get total count
        total_count = len(all_cp)

        # Paginate
        offset = (page - 1) * page_size
        paginated_cp = all_cp[offset : offset + page_size]

        papers = []
        for cp in paginated_cp:
            paper = session.query(Paper).filter_by(id=cp.paper_id).first()
            if paper:
                paper_data = enhance_paper_data(paper)
                paper_data["collection_info"] = cp.to_dict()
                papers.append(paper_data)

        return {
            "papers": papers,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size if total_count > 0 else 1,
        }


@router.post("/{collection_id}/papers")
async def add_paper_to_collection(collection_id: int, data: AddPaperToCollection):
    """Add paper to collection"""
    with get_db().get_session() as session:
        collection = session.query(Collection).filter_by(id=collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        paper = session.query(Paper).filter_by(id=data.paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        existing = session.query(CollectionPaper).filter_by(collection_id=collection_id, paper_id=data.paper_id).first()
        if existing:
            return {"message": "Paper already in collection", "already_exists": True}

        cp = CollectionPaper(
            collection_id=collection_id,
            paper_id=data.paper_id,
            notes=data.notes,
            tags=json.dumps(data.tags) if data.tags else None,
        )
        session.add(cp)
        collection.updated_at = datetime.now(UTC).replace(tzinfo=None)
        session.commit()
        refresh_stats_cache()
        return {"message": "Paper added to collection"}


@router.delete("/{collection_id}/papers/{paper_id}")
async def remove_paper_from_collection(collection_id: int, paper_id: int):
    """Remove paper from collection"""
    with get_db().get_session() as session:
        cp = session.query(CollectionPaper).filter_by(collection_id=collection_id, paper_id=paper_id).first()
        if not cp:
            raise HTTPException(status_code=404, detail="Paper not in collection")

        session.delete(cp)
        collection = session.query(Collection).filter_by(id=collection_id).first()
        if collection:
            collection.updated_at = datetime.now(UTC).replace(tzinfo=None)
        session.commit()
        refresh_stats_cache()
        return {"message": "Paper removed from collection"}


@router.put("/{collection_id}/papers/{paper_id}")
async def update_collection_paper(collection_id: int, paper_id: int, data: UpdateCollectionPaper):
    """Update paper in collection (notes, tags, status)"""
    with get_db().get_session() as session:
        cp = session.query(CollectionPaper).filter_by(collection_id=collection_id, paper_id=paper_id).first()
        if not cp:
            raise HTTPException(status_code=404, detail="Paper not in collection")

        if data.notes is not None:
            cp.notes = data.notes
        if data.tags is not None:
            cp.tags = json.dumps(data.tags)
        if data.read_status is not None:
            cp.read_status = data.read_status
        if data.starred is not None:
            cp.starred = data.starred

        collection = session.query(Collection).filter_by(id=collection_id).first()
        if collection:
            collection.updated_at = datetime.now(UTC).replace(tzinfo=None)
        session.commit()
        return cp.to_dict()


class AISearchRequest(BaseModel):
    query: str


@router.post("/{collection_id}/ai-search")
async def ai_search_papers(collection_id: int, data: AISearchRequest):
    """AI-powered search in collection papers (searches titles only)"""
    from arxiv_pulse.config import Config

    with get_db().get_session() as session:
        collection = session.query(Collection).filter_by(id=collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        # Get all papers in collection
        collection_papers = session.query(CollectionPaper).filter_by(collection_id=collection_id).all()

        if not collection_papers:
            return {"papers": [], "message": "No papers in collection"}

        # Build paper list with titles
        papers_info = []
        for idx, cp in enumerate(collection_papers, 1):
            paper = session.query(Paper).filter_by(id=cp.paper_id).first()
            if paper:
                papers_info.append(
                    {
                        "index": idx,
                        "id": paper.id,
                        "title": paper.title or "",
                        "arxiv_id": paper.arxiv_id,
                    }
                )

        if not papers_info:
            return {"papers": [], "message": "No papers found"}

        # Build prompt for AI
        titles_text = "\n".join([f"{p['index']}. {p['title']}" for p in papers_info])

        prompt = f"""用户描述：{data.query}

以下是论文集中的所有论文标题（每行一个）：
{titles_text}

请找出与用户描述最相关的论文，返回编号列表（JSON数组格式），如：[1, 3, 5]

如果没有相关论文，返回空列表 []
只返回JSON数组，不要其他文字。"""

        # Call AI
        if not Config.AI_API_KEY:
            raise HTTPException(status_code=400, detail="AI API not configured")

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

            # Parse JSON result
            import re

            match = re.search(r"\[.*?\]", result_text)
            if match:
                indices = json.loads(match.group())
            else:
                indices = []

            # Get matched papers
            matched_papers = []
            for p in papers_info:
                if p["index"] in indices:
                    paper = session.query(Paper).filter_by(id=p["id"]).first()
                    if paper:
                        paper_data = enhance_paper_data(paper)
                        cp = (
                            session.query(CollectionPaper)
                            .filter_by(collection_id=collection_id, paper_id=p["id"])
                            .first()
                        )
                        if cp:
                            paper_data["collection_info"] = cp.to_dict()
                        matched_papers.append(paper_data)

            return {"papers": matched_papers, "total_found": len(matched_papers)}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI search failed: {str(e)[:100]}")
