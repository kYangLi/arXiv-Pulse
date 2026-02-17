"""
Chat API Router - AI 对话助手
"""

import asyncio
import json
import os
import tempfile
from datetime import UTC, datetime

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from arxiv_pulse.config import Config
from arxiv_pulse.models import (
    ChatMessage,
    ChatSession,
    Database,
    Paper,
    PaperContentCache,
)

router = APIRouter()


def get_db():
    """Get database instance"""
    return Database()


class SendMessageRequest(BaseModel):
    content: str
    paper_ids: list[str] = []
    language: str = "zh"  # "zh" or "en"


class RenameSessionRequest(BaseModel):
    title: str


def sse_event(event_type: str, data: dict) -> str:
    """Helper to format SSE event"""
    return f"data: {json.dumps({'type': event_type, **data}, ensure_ascii=False)}\n\n"


@router.get("/sessions")
async def list_sessions():
    """获取对话会话列表"""
    with get_db().get_session() as session:
        sessions = session.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
        return [s.to_dict() for s in sessions]


@router.post("/sessions")
async def create_session():
    """创建新对话会话"""
    with get_db().get_session() as session:
        new_session = ChatSession(title="新对话")
        session.add(new_session)
        session.commit()
        session.refresh(new_session)
        return new_session.to_dict()


@router.get("/sessions/{session_id}")
async def get_session(session_id: int):
    """获取对话会话详情"""
    with get_db().get_session() as session:
        chat_session = session.query(ChatSession).filter_by(id=session_id).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")

        messages = (
            session.query(ChatMessage).filter_by(session_id=session_id).order_by(ChatMessage.created_at.asc()).all()
        )

        return {
            "session": chat_session.to_dict(),
            "messages": [m.to_dict() for m in messages],
        }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int):
    """删除对话会话"""
    with get_db().get_session() as session:
        chat_session = session.query(ChatSession).filter_by(id=session_id).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")

        session.query(ChatMessage).filter_by(session_id=session_id).delete()
        session.delete(chat_session)
        session.commit()
        return {"success": True}


@router.put("/sessions/{session_id}/rename")
async def rename_session(session_id: int, data: RenameSessionRequest):
    """重命名对话会话"""
    with get_db().get_session() as session:
        chat_session = session.query(ChatSession).filter_by(id=session_id).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")

        chat_session.title = data.title
        session.commit()
        return chat_session.to_dict()


@router.post("/sessions/{session_id}/send")
async def send_message(session_id: int, data: SendMessageRequest):
    """发送消息，SSE 流式返回 AI 回复"""

    lang = data.language

    msgs = {
        "zh": {
            "start": f"开始处理 {len(data.paper_ids)} 篇论文...",
            "paper_start": lambda i, t, a: f"处理论文 {i}/{t}: {a}",
            "cached": lambda a, l: f"从缓存加载: {a} ({l} 字符)",
            "downloading": lambda a: f"正在下载 PDF: {a}",
            "downloaded": lambda s: f"下载完成 ({s:.1f} KB)",
            "parsing": "正在解析 PDF...",
            "parsing_progress": lambda i, t: f"解析中... ({i}/{t} 页)",
            "parsed": lambda l, p: f"解析完成: {l} 字符, {p} 页",
            "download_failed": lambda s: f"下载失败: HTTP {s}",
            "process_failed": lambda e: f"处理失败: {e[:50]}",
            "papers_ready": "论文内容已准备就绪，开始 AI 分析...",
            "ai_thinking": "AI 正在分析...",
            "papers_content_prefix": "\n\n以下是用户选中的论文内容：",
        },
        "en": {
            "start": f"Processing {len(data.paper_ids)} papers...",
            "paper_start": lambda i, t, a: f"Processing paper {i}/{t}: {a}",
            "cached": lambda a, l: f"Loaded from cache: {a} ({l} chars)",
            "downloading": lambda a: f"Downloading PDF: {a}",
            "downloaded": lambda s: f"Download complete ({s:.1f} KB)",
            "parsing": "Parsing PDF...",
            "parsing_progress": lambda i, t: f"Parsing... ({i}/{t} pages)",
            "parsed": lambda l, p: f"Parse complete: {l} chars, {p} pages",
            "download_failed": lambda s: f"Download failed: HTTP {s}",
            "process_failed": lambda e: f"Processing failed: {e[:50]}",
            "papers_ready": "Paper content ready, starting AI analysis...",
            "ai_thinking": "AI is analyzing...",
            "papers_content_prefix": "\n\nThe following is the paper content selected by the user:",
        },
    }

    m = msgs.get(lang, msgs["zh"])

    async def event_generator():
        with get_db().get_session() as session:
            chat_session = session.query(ChatSession).filter_by(id=session_id).first()
            if not chat_session:
                yield sse_event("error", {"message": "Session not found"})
                return

            is_first_message = session.query(ChatMessage).filter_by(session_id=session_id).count() == 0

            user_message = ChatMessage(
                session_id=session_id,
                role="user",
                content=data.content,
                paper_ids=json.dumps(data.paper_ids) if data.paper_ids else None,
            )
            session.add(user_message)

            if is_first_message:
                title = data.content[:30]
                if len(data.content) > 30:
                    title += "..."
                chat_session.title = title

            session.commit()

        papers_content = ""
        if data.paper_ids:
            yield sse_event(
                "progress",
                {
                    "stage": "start",
                    "message": m["start"],
                    "total_papers": len(data.paper_ids),
                },
            )
            await asyncio.sleep(0.3)

            for idx, arxiv_id in enumerate(data.paper_ids):
                yield sse_event(
                    "progress",
                    {
                        "stage": "paper_start",
                        "arxiv_id": arxiv_id,
                        "message": m["paper_start"](idx + 1, len(data.paper_ids), arxiv_id),
                    },
                )
                await asyncio.sleep(0.2)

                content = None
                text_length = 0

                with get_db().get_session() as session:
                    cache = session.query(PaperContentCache).filter_by(arxiv_id=arxiv_id).first()
                    if cache and cache.full_text:
                        content = cache.full_text if isinstance(cache.full_text, str) else str(cache.full_text)
                        text_length = len(content)
                        yield sse_event(
                            "progress",
                            {
                                "stage": "cached",
                                "arxiv_id": arxiv_id,
                                "message": m["cached"](arxiv_id, text_length),
                            },
                        )
                        await asyncio.sleep(0.2)

                if not content:
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                    try:
                        yield sse_event(
                            "progress",
                            {"stage": "downloading", "arxiv_id": arxiv_id, "message": m["downloading"](arxiv_id)},
                        )
                        await asyncio.sleep(0.1)

                        response = requests.get(pdf_url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
                        if response.status_code == 200:
                            file_size = len(response.content)
                            yield sse_event(
                                "progress",
                                {
                                    "stage": "downloaded",
                                    "arxiv_id": arxiv_id,
                                    "message": m["downloaded"](file_size / 1024),
                                },
                            )
                            await asyncio.sleep(0.2)

                            yield sse_event(
                                "progress", {"stage": "parsing", "arxiv_id": arxiv_id, "message": m["parsing"]}
                            )
                            await asyncio.sleep(0.1)

                            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                                tmp_file.write(response.content)
                                tmp_path = tmp_file.name

                            try:
                                import fitz

                                doc = fitz.open(tmp_path)
                                page_count = len(doc)
                                full_text = ""
                                for i, page in enumerate(doc):
                                    full_text += page.get_text()
                                    if i % 5 == 0:
                                        yield sse_event(
                                            "progress",
                                            {
                                                "stage": "parsing",
                                                "arxiv_id": arxiv_id,
                                                "message": m["parsing_progress"](i + 1, page_count),
                                                "progress": int((i + 1) / page_count * 100),
                                            },
                                        )
                                        await asyncio.sleep(0.05)
                                doc.close()

                                content = full_text.strip()
                                text_length = len(content)
                                yield sse_event(
                                    "progress",
                                    {
                                        "stage": "parsed",
                                        "arxiv_id": arxiv_id,
                                        "message": m["parsed"](text_length, page_count),
                                        "text_length": text_length,
                                        "page_count": page_count,
                                    },
                                )
                                await asyncio.sleep(0.2)

                                with get_db().get_session() as session:
                                    cache = PaperContentCache(arxiv_id=arxiv_id, full_text=content)
                                    session.add(cache)
                                    session.commit()
                            finally:
                                if os.path.exists(tmp_path):
                                    os.unlink(tmp_path)
                        else:
                            yield sse_event(
                                "progress",
                                {
                                    "stage": "error",
                                    "arxiv_id": arxiv_id,
                                    "message": m["download_failed"](response.status_code),
                                },
                            )
                    except Exception as e:
                        yield sse_event(
                            "progress", {"stage": "error", "arxiv_id": arxiv_id, "message": m["process_failed"](str(e))}
                        )

                if content:
                    with get_db().get_session() as session:
                        paper = session.query(Paper).filter_by(arxiv_id=arxiv_id).first()
                        title = paper.title if paper else arxiv_id
                    paper_header = (
                        f"\n\n---\n### 论文: {title}\n### arXiv ID: {arxiv_id}\n\n"
                        if lang == "zh"
                        else f"\n\n---\n### Paper: {title}\n### arXiv ID: {arxiv_id}\n\n"
                    )
                    papers_content += f"{paper_header}{content[:10000]}"

            if papers_content:
                yield sse_event("progress", {"stage": "papers_ready", "message": m["papers_ready"]})
                await asyncio.sleep(0.3)

        history_messages = []
        with get_db().get_session() as session:
            messages = (
                session.query(ChatMessage).filter_by(session_id=session_id).order_by(ChatMessage.created_at.asc()).all()
            )
            for msg in messages:
                history_messages.append({"role": msg.role, "content": msg.content})

        if data.language == "en":
            system_prompt = """You are a professional academic research assistant specializing in physics, materials science, and computational science.

You can:
1. Answer academic questions
2. Analyze paper content, methodology, and contributions
3. Explain complex concepts and formulas
4. Compare viewpoints and methods across different papers
5. Provide research suggestions and literature recommendations

Please respond in clear, professional yet accessible language. If the user has provided paper content, analyze based on that content.
Format your response using Markdown, including headers, lists, code blocks, etc.

IMPORTANT: Always respond in English."""
        else:
            system_prompt = """你是一个专业的学术研究助手，专门帮助用户分析物理学、材料科学和计算科学领域的学术论文。

你可以：
1. 解答学术问题
2. 分析论文内容、方法论、贡献
3. 解释复杂的概念和公式
4. 比较不同论文的观点和方法
5. 提供研究建议和文献推荐

请用清晰、专业但易懂的语言回答问题。如果用户提供了论文内容，请基于论文内容进行分析。
回复请使用 Markdown 格式，包括标题、列表、代码块等。

重要：请始终使用中文回复。"""

        if papers_content:
            system_prompt += f"{m['papers_content_prefix']}{papers_content}"

        messages_for_api = [{"role": "system", "content": system_prompt}] + history_messages

        if not Config.AI_API_KEY:
            err_msg = "AI API 未配置" if lang == "zh" else "AI API not configured"
            yield sse_event("error", {"message": err_msg})
            return

        try:
            import openai

            client = openai.OpenAI(api_key=Config.AI_API_KEY, base_url=Config.AI_BASE_URL)

            yield sse_event("progress", {"stage": "ai_thinking", "message": m["ai_thinking"]})
            await asyncio.sleep(0.3)

            response = client.chat.completions.create(
                model=Config.AI_MODEL or "DeepSeek-V3.2",
                messages=messages_for_api,
                max_tokens=4096,
                temperature=0.7,
                stream=True,
            )

            full_response = ""
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield sse_event("chunk", {"content": content})
                    await asyncio.sleep(0.01)

            with get_db().get_session() as session:
                assistant_message = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                )
                session.add(assistant_message)
                session.commit()

            yield sse_event("done", {})

        except Exception as e:
            err_msg = f"AI 响应失败: {str(e)[:100]}" if lang == "zh" else f"AI response failed: {str(e)[:100]}"
            yield sse_event("error", {"message": err_msg})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/papers/{arxiv_id}/content")
async def get_paper_content_api(arxiv_id: str):
    """获取论文 PDF 内容"""
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    try:
        response = requests.get(pdf_url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Failed to download PDF")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name

        try:
            import fitz

            doc = fitz.open(tmp_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()

            content = full_text.strip()

            with get_db().get_session() as session:
                cache = PaperContentCache(arxiv_id=arxiv_id, full_text=content)
                session.add(cache)
                session.commit()

            return {
                "arxiv_id": arxiv_id,
                "content": content[:5000] + "..." if len(content) > 5000 else content,
                "full_length": len(content),
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
