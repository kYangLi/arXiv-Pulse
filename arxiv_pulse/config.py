import os

_db_instance = None


def get_db():
    global _db_instance
    if _db_instance is None:
        from arxiv_pulse.models import Database

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

    @property
    def DATABASE_URL(cls) -> str:
        return os.getenv("DATABASE_URL", "sqlite:///data/arxiv_papers.db")

    @property
    def AI_API_KEY(cls) -> str | None:
        key = cls._get("ai_api_key", "")
        return key if key else None

    @AI_API_KEY.setter
    def AI_API_KEY(cls, value: str) -> None:
        cls._set("ai_api_key", value)

    @property
    def AI_MODEL(cls) -> str:
        return cls._get("ai_model", "DeepSeek-V3.2-Thinking")

    @AI_MODEL.setter
    def AI_MODEL(cls, value: str) -> None:
        cls._set("ai_model", value)

    @property
    def AI_BASE_URL(cls) -> str:
        return cls._get("ai_base_url", "https://llmapi.paratera.com")

    @AI_BASE_URL.setter
    def AI_BASE_URL(cls, value: str) -> None:
        cls._set("ai_base_url", value)

    @property
    def SEARCH_QUERIES(cls) -> list[str]:
        db = get_db()
        return db.get_search_queries()

    @SEARCH_QUERIES.setter
    def SEARCH_QUERIES(cls, value: list[str]) -> None:
        db = get_db()
        db.set_search_queries(value)

    @property
    def ARXIV_MAX_RESULTS(cls) -> int:
        return cls._get_int("arxiv_max_results", 10000)

    @ARXIV_MAX_RESULTS.setter
    def ARXIV_MAX_RESULTS(cls, value: int) -> None:
        cls._set("arxiv_max_results", str(value))

    @property
    def YEARS_BACK(cls) -> int:
        return cls._get_int("years_back", 5)

    @YEARS_BACK.setter
    def YEARS_BACK(cls, value: int) -> None:
        cls._set("years_back", str(value))

    @property
    def REPORT_MAX_PAPERS(cls) -> int:
        return cls._get_int("report_max_papers", 64)

    @REPORT_MAX_PAPERS.setter
    def REPORT_MAX_PAPERS(cls, value: int) -> None:
        cls._set("report_max_papers", str(value))

    @property
    def SUMMARY_MAX_TOKENS(cls) -> int:
        return int(os.getenv("SUMMARY_MAX_TOKENS", "10000"))

    @property
    def REPORT_DIR(cls) -> str:
        return os.getenv("REPORT_DIR", "reports")

    @property
    def DATA_DIR(cls) -> str:
        db_url = cls.DATABASE_URL
        return os.path.dirname(db_url.replace("sqlite:///", ""))

    @property
    def ARXIV_SORT_BY(cls) -> str:
        return os.getenv("ARXIV_SORT_BY", "submittedDate")

    @property
    def ARXIV_SORT_ORDER(cls) -> str:
        return os.getenv("ARXIV_SORT_ORDER", "descending")

    @property
    def IMPORTANT_PAPERS_FILE(cls) -> str:
        return os.getenv("IMPORTANT_PAPERS_FILE", "data/important_papers.txt")

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

        os.makedirs(cls.REPORT_DIR, exist_ok=True)
        os.makedirs(cls.DATA_DIR, exist_ok=True)

        return True
