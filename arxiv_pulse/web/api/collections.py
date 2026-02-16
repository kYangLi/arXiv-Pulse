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
):
    """Get collection by ID with papers (paginated)"""
    with get_db().get_session() as session:
        collection = session.query(Collection).filter_by(id=collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        # Get total count
        total_count = session.query(CollectionPaper).filter_by(collection_id=collection_id).count()

        # Get paginated papers
        offset = (page - 1) * page_size
        collection_papers = (
            session.query(CollectionPaper)
            .filter_by(collection_id=collection_id)
            .order_by(CollectionPaper.added_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        papers = []
        for cp in collection_papers:
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
        result["total_pages"] = (total_count + page_size - 1) // page_size
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
):
    """Get papers in a collection (paginated)"""
    with get_db().get_session() as session:
        collection = session.query(Collection).filter_by(id=collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        # Get total count
        total_count = session.query(CollectionPaper).filter_by(collection_id=collection_id).count()

        # Get paginated papers
        offset = (page - 1) * page_size
        collection_papers = (
            session.query(CollectionPaper)
            .filter_by(collection_id=collection_id)
            .order_by(CollectionPaper.added_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        papers = []
        for cp in collection_papers:
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
            "total_pages": (total_count + page_size - 1) // page_size,
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
