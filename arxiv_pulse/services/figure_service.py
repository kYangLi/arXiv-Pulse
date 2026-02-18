"""
Figure service - 论文图片获取服务
"""

from arxiv_pulse.models import FigureCache


def get_figure_url_cached(arxiv_id: str, session) -> str | None:
    """获取缓存的图片URL"""
    figure = session.query(FigureCache).filter_by(arxiv_id=arxiv_id).first()
    return figure.figure_url if figure else None


def fetch_and_cache_figure(arxiv_id: str) -> str | None:
    """获取论文图片并缓存到数据库"""
    try:
        from arxiv_pulse.ai import ReportGenerator

        report_gen = ReportGenerator()
        return report_gen.get_first_figure_url(arxiv_id, use_cache=True)
    except Exception:
        return None
