"""
AI Client 单例服务
"""

from functools import lru_cache

from arxiv_pulse.config import Config


@lru_cache
def get_ai_client():
    """获取 OpenAI 客户端单例"""
    if not Config.AI_API_KEY:
        return None
    import openai

    return openai.OpenAI(api_key=Config.AI_API_KEY, base_url=Config.AI_BASE_URL)


def get_model_name() -> str:
    """获取模型名称"""
    return Config.AI_MODEL or "DeepSeek-V3.2"
