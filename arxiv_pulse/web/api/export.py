"""
Export API Router
"""

import base64
import io
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel

from arxiv_pulse.config import Config
from arxiv_pulse.models import Collection, CollectionPaper, Database, FigureCache, Paper

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
        elif data.format == "pdf":
            pdf_bytes = generate_pdf(papers, data.include_summary, session)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
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
        elif data.format == "pdf":
            pdf_bytes = generate_pdf(papers, data.include_summary, session, collection_name=collection.name)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")


def get_figure_data(arxiv_id: str, session) -> dict[str, Any] | None:
    """Get figure URL and base64 data for a paper"""
    figure = session.query(FigureCache).filter_by(arxiv_id=arxiv_id).first()
    if not figure or not figure.figure_url:
        return None

    result = {"url": figure.figure_url}

    try:
        import requests

        response = requests.get(figure.figure_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "image/png")
            b64_data = base64.b64encode(response.content).decode("utf-8")
            result["base64"] = f"data:{content_type};base64,{b64_data}"
    except Exception:
        pass

    return result


def get_translation(paper: Paper) -> dict[str, str]:
    """Get translations for paper title and abstract"""
    from arxiv_pulse.web.api.papers import translate_text

    return {
        "title_translation": translate_text(paper.title) if paper.title else "",
        "abstract_translation": translate_text(paper.abstract) if paper.abstract else "",
    }


def get_paper_summary_data(paper: Paper) -> dict[str, Any]:
    """Parse and return summary data"""
    if not paper.summary:
        return {}

    try:
        data = json.loads(paper.summary)
        result = {}
        if "summary" in data:
            result["summary"] = data["summary"]
        if "keywords" in data:
            result["keywords"] = data["keywords"]
        if "key_findings" in data:
            result["key_findings"] = data["key_findings"]
        return result
    except Exception:
        return {"summary": paper.summary}


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
            summary_data = get_paper_summary_data(paper)
            if "summary" in summary_data:
                lines.append(summary_data["summary"] + "\n")
            if "keywords" in summary_data:
                lines.append(f"**关键词**: {', '.join(summary_data['keywords'])}\n")

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


def generate_pdf(papers: list[Paper], include_summary: bool, session, collection_name: str | None = None) -> bytes:
    """Generate PDF content from papers with images"""
    from weasyprint import CSS, HTML

    title = collection_name if collection_name else "论文导出"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        '<meta charset="UTF-8">',
        "<style>",
        """
        @page {
            size: A4;
            margin: 2cm;
            @bottom-center {
                content: counter(page) " / " counter(pages);
                font-size: 10pt;
                color: #666;
            }
        }
        body {
            font-family: "Noto Sans CJK SC", "Noto Serif CJK SC", "Source Han Sans CN", 
                         "Source Han Serif CN", "WenQuanYi Micro Hei", "WenQuanYi Zen Hei",
                         "Microsoft YaHei", "SimHei", "SimSun", sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            color: #1e3a5f;
            font-size: 24pt;
            text-align: center;
            margin-bottom: 8pt;
            padding-bottom: 8pt;
            border-bottom: 2px solid #c9a227;
        }
        .meta {
            text-align: center;
            color: #666;
            font-size: 10pt;
            margin-bottom: 20pt;
        }
        .paper {
            margin-bottom: 24pt;
            padding-bottom: 16pt;
            border-bottom: 1px solid #ddd;
            page-break-inside: avoid;
        }
        .paper:last-child {
            border-bottom: none;
        }
        .paper-title {
            font-size: 14pt;
            color: #1e3a5f;
            font-weight: bold;
            margin-bottom: 8pt;
        }
        .paper-meta {
            font-size: 9pt;
            color: #666;
            margin-bottom: 8pt;
        }
        .paper-meta span {
            margin-right: 12pt;
        }
        .section-title {
            font-size: 11pt;
            font-weight: bold;
            color: #1e3a5f;
            margin-top: 10pt;
            margin-bottom: 4pt;
        }
        .abstract {
            font-size: 10pt;
            text-align: justify;
            color: #444;
        }
        .translation {
            font-size: 10pt;
            color: #555;
            font-style: italic;
            margin-top: 4pt;
            padding-left: 8pt;
            border-left: 2px solid #c9a227;
        }
        .summary {
            font-size: 10pt;
            background: #f9f7f3;
            padding: 8pt;
            border-radius: 4pt;
            margin-top: 6pt;
        }
        .keywords {
            font-size: 9pt;
            color: #c9a227;
            margin-top: 4pt;
        }
        .key-findings {
            margin-top: 6pt;
            padding-left: 12pt;
        }
        .key-findings li {
            font-size: 9pt;
            margin-bottom: 2pt;
        }
        .figure {
            text-align: center;
            margin: 12pt 0;
        }
        .figure img {
            max-width: 100%;
            max-height: 300pt;
        }
        .figure-caption {
            font-size: 8pt;
            color: #888;
            margin-top: 4pt;
        }
        .links {
            font-size: 9pt;
            margin-top: 8pt;
        }
        .links a {
            color: #1e3a5f;
            text-decoration: none;
        }
        """,
        "</style>",
        "</head>",
        "<body>",
        f"<h1>{title}</h1>",
        f'<div class="meta">导出时间: {timestamp} | 论文数量: {len(papers)}</div>',
    ]

    for i, paper in enumerate(papers, 1):
        authors = json.loads(paper.authors) if paper.authors else []
        author_names = ", ".join([a.get("name", "") for a in authors])
        pub_date = paper.published.strftime("%Y-%m-%d") if paper.published else "N/A"

        html_parts.append('<div class="paper">')
        html_parts.append(f'<div class="paper-title">{i}. {paper.title}</div>')
        html_parts.append(f'<div class="paper-meta">')
        html_parts.append(f"<span>作者: {author_names}</span>")
        html_parts.append(f"<span>arXiv: {paper.arxiv_id}</span>")
        html_parts.append(f"<span>日期: {pub_date}</span>")
        html_parts.append("</div>")

        if paper.abstract:
            html_parts.append('<div class="section-title">摘要</div>')
            abstract_escaped = paper.abstract.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_parts.append(f'<div class="abstract">{abstract_escaped}</div>')

            translations = get_translation(paper)
            if translations.get("abstract_translation"):
                trans_escaped = (
                    translations["abstract_translation"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                )
                html_parts.append(f'<div class="translation">{trans_escaped}</div>')

        if include_summary and paper.summary:
            summary_data = get_paper_summary_data(paper)
            if summary_data.get("summary"):
                html_parts.append('<div class="section-title">AI 总结</div>')
                summary_escaped = (
                    summary_data["summary"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                )
                html_parts.append(f'<div class="summary">{summary_escaped}</div>')

            if summary_data.get("keywords"):
                keywords_str = ", ".join(summary_data["keywords"])
                html_parts.append(f'<div class="keywords">关键词: {keywords_str}</div>')

            if summary_data.get("key_findings"):
                html_parts.append('<div class="section-title">关键发现</div>')
                html_parts.append('<ul class="key-findings">')
                for finding in summary_data["key_findings"][:5]:
                    finding_escaped = finding.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    html_parts.append(f"<li>{finding_escaped}</li>")
                html_parts.append("</ul>")

        figure_data = get_figure_data(paper.arxiv_id, session)
        if figure_data and figure_data.get("base64"):
            html_parts.append('<div class="figure">')
            html_parts.append(f'<img src="{figure_data["base64"]}" alt="Figure">')
            html_parts.append('<div class="figure-caption">论文图片</div>')
            html_parts.append("</div>")

        html_parts.append('<div class="links">')
        html_parts.append(f'<a href="https://arxiv.org/abs/{paper.arxiv_id}">arXiv 链接</a> | ')
        html_parts.append(f'<a href="{paper.pdf_url}">PDF 下载</a>')
        html_parts.append("</div>")

        html_parts.append("</div>")

    html_parts.append("</body>")
    html_parts.append("</html>")

    html_content = "\n".join(html_parts)

    pdf_buffer = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    return pdf_buffer.read()
