"""
Export API Router
"""

import json
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from arxiv_pulse.config import Config
from arxiv_pulse.models import Collection, CollectionPaper, Database, Paper

router = APIRouter()


def get_db():
    """Get database instance (lazy initialization)"""
    return Database()


class ExportRequest(BaseModel):
    paper_ids: list[int]
    format: str = "markdown"
    include_summary: bool = True


class CollectionExportRequest(BaseModel):
    collection_id: int
    format: str = "markdown"
    include_summary: bool = True


@router.post("/papers")
async def export_papers(data: ExportRequest):
    """Export selected papers"""
    with get_db().get_session() as session:
        papers = session.query(Paper).filter(Paper.id.in_(data.paper_ids)).all()
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found")

        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = f"papers_export_{timestamp}"

        if data.format == "markdown":
            content = generate_markdown(papers, data.include_summary)
            return PlainTextResponse(
                content=content,
                media_type="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="{filename}.md"'},
            )
        elif data.format == "csv":
            content = generate_csv(papers)
            return PlainTextResponse(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
            )
        elif data.format == "bibtex":
            content = generate_bibtex(papers)
            return PlainTextResponse(
                content=content,
                media_type="text/plain",
                headers={"Content-Disposition": f'attachment; filename="{filename}.bib"'},
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")


@router.post("/collection")
async def export_collection(data: CollectionExportRequest):
    """Export a collection"""
    with get_db().get_session() as session:
        collection = session.query(Collection).filter_by(id=data.collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        collection_papers = session.query(CollectionPaper).filter_by(collection_id=data.collection_id).all()

        papers = []
        for cp in collection_papers:
            paper = session.query(Paper).filter_by(id=cp.paper_id).first()
            if paper:
                papers.append(paper)

        if not papers:
            raise HTTPException(status_code=404, detail="No papers in collection")

        timestamp = datetime.now().strftime("%Y-%m-%d")
        safe_name = collection.name.replace(" ", "_").replace("/", "_")
        filename = f"collection_{safe_name}_{timestamp}"

        if data.format == "markdown":
            content = generate_markdown(papers, data.include_summary, collection_name=collection.name)
            return PlainTextResponse(
                content=content,
                media_type="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="{filename}.md"'},
            )
        elif data.format == "csv":
            content = generate_csv(papers)
            return PlainTextResponse(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
            )
        elif data.format == "bibtex":
            content = generate_bibtex(papers)
            return PlainTextResponse(
                content=content,
                media_type="text/plain",
                headers={"Content-Disposition": f'attachment; filename="{filename}.bib"'},
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")


def generate_markdown(papers: list[Paper], include_summary: bool, collection_name: str | None = None) -> str:
    """Generate Markdown content from papers"""
    lines = []

    title = f"# {collection_name}" if collection_name else "# 论文导出"
    lines.append(title)
    lines.append(f"\n导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"论文数量: {len(papers)}\n")
    lines.append("---\n")

    for i, paper in enumerate(papers, 1):
        lines.append(f"## {i}. {paper.title}\n")

        authors = json.loads(paper.authors) if paper.authors else []
        author_names = [a.get("name", "") for a in authors]
        lines.append(f"**作者**: {', '.join(author_names)}\n")

        lines.append(f"**arXiv ID**: {paper.arxiv_id}")
        lines.append(f"**发布日期**: {paper.published.strftime('%Y-%m-%d') if paper.published else 'N/A'}")
        lines.append(f"**分类**: {paper.categories or 'N/A'}")
        lines.append(f"**PDF**: {paper.pdf_url}\n")

        if paper.abstract:
            lines.append("### 摘要\n")
            lines.append(paper.abstract + "\n")

        if include_summary and paper.summary:
            lines.append("### AI 总结\n")
            try:
                summary_data = json.loads(paper.summary)
                if "summary" in summary_data:
                    lines.append(summary_data["summary"] + "\n")
                if "keywords" in summary_data:
                    lines.append(f"**关键词**: {', '.join(summary_data['keywords'])}\n")
            except:
                lines.append(paper.summary + "\n")

        lines.append("---\n")

    return "\n".join(lines)


def generate_csv(papers: list[Paper]) -> str:
    """Generate CSV content from papers"""
    lines = ["Title,Authors,arXiv ID,Published,PDF URL,Categories"]

    for paper in papers:
        authors = json.loads(paper.authors) if paper.authors else []
        author_names = "; ".join([a.get("name", "") for a in authors])

        title = paper.title.replace('"', '""')
        categories = (paper.categories or "").replace('"', '""')

        line = f'"{title}","{author_names}",{paper.arxiv_id},{paper.published.strftime("%Y-%m-%d") if paper.published else ""},{paper.pdf_url},"{categories}"'
        lines.append(line)

    return "\n".join(lines)


def generate_bibtex(papers: list[Paper]) -> str:
    """Generate BibTeX content from papers"""
    lines = []

    for paper in papers:
        authors = json.loads(paper.authors) if paper.authors else []
        author_names = " and ".join([a.get("name", "") for a in authors])

        year = paper.published.year if paper.published else ""
        cite_key = f"{paper.arxiv_id.replace(':', '_')}_{year}"

        lines.append(f"@article{{{cite_key},")
        lines.append(f"  title = {{{paper.title}}},")
        lines.append(f"  author = {{{author_names}}},")
        lines.append(f"  journal = {{arXiv preprint arXiv:{paper.arxiv_id}}},")
        if paper.published:
            lines.append(f"  year = {{{year}}},")
        lines.append(f"  url = {{https://arxiv.org/abs/{paper.arxiv_id}}}")
        lines.append("}\n")

    return "\n".join(lines)
