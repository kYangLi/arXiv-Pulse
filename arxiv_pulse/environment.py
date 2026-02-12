"""
环境设置和配置模块
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from arxiv_pulse.config import Config
from arxiv_pulse.output_manager import output


def setup_environment(directory: Path) -> bool:
    """设置环境并验证给定目录的配置"""
    original_cwd = os.getcwd()
    try:
        os.chdir(directory)

        os.makedirs("data", exist_ok=True)
        os.makedirs("reports", exist_ok=True)

        env_file = directory / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        else:
            output.warn(f"在 {directory} 中未找到 .env 文件。使用默认配置。")

        db_url = os.getenv("DATABASE_URL", "sqlite:///data/arxiv_papers.db")
        if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
            db_path = db_url.replace("sqlite:///", "")
            abs_db_path = os.path.abspath(db_path)
            os.environ["DATABASE_URL"] = f"sqlite:///{abs_db_path}"
            output.debug(f"Converted DATABASE_URL to absolute path: {os.environ['DATABASE_URL']}")

        Config.DATABASE_URL = os.environ["DATABASE_URL"]
        Config.DATA_DIR = os.path.dirname(Config.DATABASE_URL.replace("sqlite:///", ""))
        report_dir = os.getenv("REPORT_DIR", "reports")
        if not os.path.isabs(report_dir):
            Config.REPORT_DIR = os.path.abspath(report_dir)
            output.debug(f"Converted REPORT_DIR to absolute path: {Config.REPORT_DIR}")

        Config.AI_API_KEY = os.getenv("AI_API_KEY")
        Config.AI_MODEL = os.getenv("AI_MODEL", "DeepSeek-V3.2-Thinking")
        Config.AI_BASE_URL = os.getenv("AI_BASE_URL", "https://llmapi.paratera.com")
        Config.SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", "10000"))

        Config.YEARS_BACK = int(os.getenv("YEARS_BACK", "5"))
        Config.IMPORTANT_PAPERS_FILE = os.getenv("IMPORTANT_PAPERS_FILE", "data/important_papers.txt")
        Config.ARXIV_MAX_RESULTS = int(os.getenv("ARXIV_MAX_RESULTS", "10000"))
        Config.ARXIV_SORT_BY = os.getenv("ARXIV_SORT_BY", "submittedDate")
        Config.ARXIV_SORT_ORDER = os.getenv("ARXIV_SORT_ORDER", "descending")
        Config.REPORT_MAX_PAPERS = int(os.getenv("REPORT_MAX_PAPERS", "64"))

        search_queries_raw = os.getenv(
            "SEARCH_QUERIES",
            "condensed matter physics; density functional theory; machine learning; force fields; first principles calculation; molecular dynamics; quantum chemistry; computational materials science",
        )
        Config.SEARCH_QUERIES_RAW = search_queries_raw
        Config.SEARCH_QUERIES = [q.strip() for q in search_queries_raw.split(";") if q.strip()]

        try:
            Config.validate()
            output.info("配置验证通过")
        except Exception as e:
            output.error(f"配置错误: {e}")
            return False

        return True
    finally:
        os.chdir(original_cwd)
