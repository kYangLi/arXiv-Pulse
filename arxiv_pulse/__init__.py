"""
arXiv Pulse: An intelligent arXiv literature crawler and analyzer for physics research.
"""

from .__version__ import __version__

__author__ = "Yang Li, OpenCode, GLM-5"

from arxiv_pulse.ai import PaperSummarizer
from arxiv_pulse.constants import ARXIV_CATEGORIES, DEFAULT_FIELDS, get_all_categories, get_queries_for_fields
from arxiv_pulse.core import Config, Database
from arxiv_pulse.crawler import ArXivCrawler
from arxiv_pulse.models import Collection, Paper, TranslationCache
from arxiv_pulse.utils import OutputManager, output

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
    "TranslationCache",
    "__version__",
    "get_all_categories",
    "get_queries_for_fields",
    "output",
]
