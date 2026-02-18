"""
FastAPI dependencies - 共享依赖注入
"""

from functools import lru_cache

from arxiv_pulse.core import Database


@lru_cache
def get_db() -> Database:
    """获取数据库单例"""
    return Database()
