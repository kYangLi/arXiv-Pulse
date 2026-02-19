import os


class classproperty:
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


_db_instance = None


def get_db():
    global _db_instance
    if _db_instance is None:
        from arxiv_pulse.core.database import Database

        db_url = os.getenv("DATABASE_URL", "sqlite:///data/arxiv_papers.db")
        _db_instance = Database(db_url)
        _db_instance.init_default_config()
    return _db_instance


class Config:
    @classmethod
    def _get(cls, key: str, default: str = "") -> str:
        db = get_db()
        value = db.get_config(key)
        return value if value is not None else default

    @classmethod
    def _get_int(cls, key: str, default: int = 0) -> int:
        try:
            return int(cls._get(key, str(default)))
        except:
            return default

    @classmethod
    def _set(cls, key: str, value: str) -> None:
        db = get_db()
        db.set_config(key, value)

    @classproperty
    def DATABASE_URL(cls) -> str:
        return os.getenv("DATABASE_URL", "sqlite:///data/arxiv_papers.db")

    @classproperty
    def AI_API_KEY(cls) -> str | None:
        key = cls._get("ai_api_key", "")
        return key if key else None

    @classproperty
    def AI_MODEL(cls) -> str:
        return cls._get("ai_model", "DeepSeek-V3.2")

    @classproperty
    def AI_BASE_URL(cls) -> str:
        return cls._get("ai_base_url", "https://llmapi.paratera.com")

    @classproperty
    def SEARCH_QUERIES(cls) -> list[str]:
        db = get_db()
        return db.get_search_queries()

    @classproperty
    def ARXIV_MAX_RESULTS(cls) -> int:
        return cls._get_int("arxiv_max_results", 100000)

    @classproperty
    def ARXIV_MAX_RESULTS_PER_FIELD(cls) -> int:
        return cls._get_int("arxiv_max_results_per_field", 10000)

    @classproperty
    def RECENT_PAPERS_LIMIT(cls) -> int:
        return cls._get_int("recent_papers_limit", 50)

    @classproperty
    def SEARCH_LIMIT(cls) -> int:
        return cls._get_int("search_limit", 20)

    @classproperty
    def YEARS_BACK(cls) -> int:
        return cls._get_int("years_back", 5)

    @classproperty
    def SUMMARY_MAX_TOKENS(cls) -> int:
        return int(os.getenv("SUMMARY_MAX_TOKENS", "10000"))

    @classproperty
    def DATA_DIR(cls) -> str:
        db_url = cls.DATABASE_URL
        return os.path.dirname(db_url.replace("sqlite:///", ""))

    @classproperty
    def ARXIV_SORT_BY(cls) -> str:
        return os.getenv("ARXIV_SORT_BY", "submittedDate")

    @classproperty
    def ARXIV_SORT_ORDER(cls) -> str:
        return os.getenv("ARXIV_SORT_ORDER", "descending")

    @classproperty
    def UI_LANGUAGE(cls) -> str:
        return cls._get("ui_language", "zh")

    @classproperty
    def TRANSLATE_LANGUAGE(cls) -> str:
        return cls._get("translate_language", "zh")

    @classmethod
    def is_initialized(cls) -> bool:
        db = get_db()
        return db.is_initialized()

    @classmethod
    def set_initialized(cls, initialized: bool = True) -> None:
        db = get_db()
        db.set_initialized(initialized)

    @classmethod
    def get_all_config(cls) -> dict[str, str]:
        db = get_db()
        return db.get_all_config()

    @classmethod
    def update_config(cls, config_dict: dict[str, str]) -> None:
        for key, value in config_dict.items():
            cls._set(key, value)

    @classmethod
    def validate(cls) -> bool:
        if not cls.AI_API_KEY:
            print("警告: 未设置 AI_API_KEY。AI 总结和翻译功能将受限。")
        else:
            print(f"信息: 找到 AI API 密钥。模型: {cls.AI_MODEL}")
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        return True
