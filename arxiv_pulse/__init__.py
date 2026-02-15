"""
arXiv Pulse: An intelligent arXiv literature crawler and analyzer for physics research.
"""

from .__version__ import __version__

__author__ = "Yang Li, OpenCode, GLM-5"

from .arxiv_crawler import ArXivCrawler
from .config import Config
from .models import Collection, Database, Paper, TranslationCache
from .output_manager import OutputManager, output
from .report_generator import ReportGenerator
from .research_fields import ARXIV_CATEGORIES, DEFAULT_FIELDS, get_all_categories, get_queries_for_fields
from .summarizer import PaperSummarizer
from .utils import get_workday_cutoff, parse_time_range

__all__ = [
    "ArXivCrawler",
    "ARXIV_CATEGORIES",
    "Collection",
    "Config",
    "Database",
    "DEFAULT_FIELDS",
    "OutputManager",
    "Paper",
    "PaperSummarizer",
    "ReportGenerator",
    "TranslationCache",
    "__version__",
    "get_all_categories",
    "get_queries_for_fields",
    "output",
    "research_fields",
    "utils",
]
