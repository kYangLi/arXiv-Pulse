"""
SSE (Server-Sent Events) 工具函数
"""

import json
from typing import Any

from fastapi.responses import StreamingResponse

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def sse_event(event_type: str, data: dict[str, Any] | None = None, **kwargs: Any) -> str:
    """格式化 SSE 事件

    支持两种调用方式:
    - sse_event("error", {"message": "..."})
    - sse_event("error", message="...")
    """
    if data is None:
        data = kwargs
    else:
        data = {**data, **kwargs}
    return f"data: {json.dumps({'type': event_type, **data}, ensure_ascii=False)}\n\n"


def sse_log(message: str) -> str:
    """格式化 SSE 日志事件"""
    return sse_event("log", message=message)


def sse_response(generator_func) -> StreamingResponse:
    """创建 SSE 响应，接收生成器函数或生成器"""
    gen = generator_func() if callable(generator_func) else generator_func
    return StreamingResponse(gen, media_type="text/event-stream", headers=SSE_HEADERS)
