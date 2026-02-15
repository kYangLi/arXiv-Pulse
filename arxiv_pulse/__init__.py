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
from .research_fields import DEFAULT_BANNER_FIELDS, RESEARCH_FIELDS
from .summarizer import PaperSummarizer
from .utils import get_workday_cutoff, parse_time_range

__all__ = [
    "ArXivCrawler",
    "Collection",
    "Config",
    "Database",
    "OutputManager",
    "Paper",
    "PaperSummarizer",
    "ReportGenerator",
    "TranslationCache",
    "__version__",
    "output",
    "research_fields",
    "utils",
]
