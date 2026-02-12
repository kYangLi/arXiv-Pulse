"""
arXiv Pulse: An intelligent arXiv literature crawler and analyzer for physics research.
"""

from .__version__ import __version__

__author__ = "arXiv Pulse Team"

from .arxiv_crawler import ArXivCrawler
from .banner import generate_banner_title, print_banner, print_banner_custom
from .config import Config
from .environment import setup_environment
from .models import Database, Paper, TranslationCache
from .output_manager import OutputManager, output
from .report_generator import ReportGenerator
from .research_fields import DEFAULT_BANNER_FIELDS, RESEARCH_FIELDS
from .summarizer import PaperSummarizer
from .utils import get_workday_cutoff, parse_time_range

__all__ = [
    "ArXivCrawler",
    "Config",
    "Database",
    "OutputManager",
    "Paper",
    "PaperSummarizer",
    "ReportGenerator",
    "TranslationCache",
    "__version__",
    "output",
    "banner",
    "environment",
    "research_fields",
    "utils",
]
