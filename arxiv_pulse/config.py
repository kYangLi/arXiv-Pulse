import os


class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/arxiv_papers.db")

    # Search queries - use semicolon as separator to allow commas in queries
    SEARCH_QUERIES_RAW = os.getenv(
        "SEARCH_QUERIES",
        "condensed matter physics; density functional theory; machine learning; force fields; first principles calculation; molecular dynamics; quantum chemistry; computational materials science",
    )
    SEARCH_QUERIES = [q.strip() for q in SEARCH_QUERIES_RAW.split(";") if q.strip()]

    # AI API (支持 OpenAI 格式，如 DeepSeek、Paratera AI 等)
    # 使用 AI_* 环境变量配置

    # AI API 配置变量
    AI_API_KEY = os.getenv("AI_API_KEY")  # 可以为 None
    AI_MODEL = os.getenv("AI_MODEL", "DeepSeek-V3.2-Thinking")
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://llmapi.paratera.com")

    # 模型配置：SUMMARY_MODEL 现在复用 AI_MODEL
    SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", 10000))

    # Report generation settings

    # Paths
    REPORT_DIR = os.getenv("REPORT_DIR", "reports")
    DATA_DIR = os.path.dirname(DATABASE_URL.replace("sqlite:///", ""))

    # Report generation limits
    REPORT_MAX_PAPERS = int(os.getenv("REPORT_MAX_PAPERS", "64"))

    # ArXiv API
    ARXIV_MAX_RESULTS = int(os.getenv("ARXIV_MAX_RESULTS", 10000))
    ARXIV_SORT_BY = os.getenv("ARXIV_SORT_BY", "submittedDate")
    ARXIV_SORT_ORDER = os.getenv("ARXIV_SORT_ORDER", "descending")

    # Sync configuration
    YEARS_BACK = int(os.getenv("YEARS_BACK", 5))  # Years to look back for initial sync
    IMPORTANT_PAPERS_FILE = os.getenv("IMPORTANT_PAPERS_FILE", "data/important_papers.txt")

    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.AI_API_KEY:
            print("警告: 未设置 AI_API_KEY。AI 总结和翻译功能将受限。")
            print("      请设置 AI_API_KEY 环境变量以启用 AI 功能。")
        else:
            print(f"信息: 找到 AI API 密钥 (AI_API_KEY)。AI 总结和翻译功能已启用 (模型: {cls.AI_MODEL})。")

        # Ensure directories exist
        os.makedirs(cls.REPORT_DIR, exist_ok=True)
        os.makedirs(cls.DATA_DIR, exist_ok=True)

        return True
