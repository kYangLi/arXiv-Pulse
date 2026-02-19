"""
Figure service - 论文图片获取服务
"""

import logging
import re
import ssl
import urllib.request

from arxiv_pulse.core import Database
from arxiv_pulse.models import FigureCache

logger = logging.getLogger(__name__)

_figure_cache: dict[str, str] = {}


def get_figure_url_cached(arxiv_id: str, session) -> str | None:
    """获取缓存的图片URL"""
    figure = session.query(FigureCache).filter_by(arxiv_id=arxiv_id).first()
    return figure.figure_url if figure else None


def fetch_and_cache_figure(arxiv_id: str, use_cache: bool = True) -> str | None:
    """获取论文图片并缓存到数据库"""
    return get_first_figure_url(arxiv_id, use_cache=use_cache)


def get_first_figure_url(arxiv_id: str, use_cache: bool = True) -> str | None:
    """获取论文的第一个图片URL"""
    if use_cache and arxiv_id in _figure_cache:
        return _figure_cache[arxiv_id]

    if use_cache:
        db = Database()
        db_cached_url = db.get_figure_cache(arxiv_id)
        if db_cached_url:
            _figure_cache[arxiv_id] = db_cached_url
            return db_cached_url

    try:
        url = f"https://arxiv.org/html/{arxiv_id}"
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers={"User-Agent": "arXiv-Pulse/1.0"})
        response = urllib.request.urlopen(req, timeout=10, context=context)
        html_content = response.read().decode("utf-8", errors="ignore")

        figure_pattern = r'<figure[^>]*>.*?<img[^>]+src=["\']([^"\']+)["\'][^>]*>.*?</figure>'
        figure_matches = re.findall(figure_pattern, html_content, re.IGNORECASE | re.DOTALL)

        if figure_matches:
            first_img_src = figure_matches[0]
            result = _normalize_image_url(first_img_src, url)
            if use_cache:
                _figure_cache[arxiv_id] = result
                try:
                    db = Database()
                    db.set_figure_cache(arxiv_id, result)
                except Exception:
                    pass
            return result

        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        img_tags = re.findall(img_pattern, html_content, re.IGNORECASE)

        if not img_tags:
            return None

        image_candidates = []
        for img_tag in img_tags:
            src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag, re.IGNORECASE)
            if not src_match:
                continue

            src = src_match.group(1)
            src_lower = src.lower()

            if any(
                exclude in src_lower
                for exclude in [
                    "logo",
                    "icon",
                    "spacer",
                    "pixel",
                    "arrow",
                    "button",
                    "feed-icon",
                    "rss",
                    "twitter",
                    "facebook",
                    "youtube",
                    "header",
                    "footer",
                    "nav",
                    "menu",
                    "banner",
                ]
            ):
                continue

            if src_lower.startswith("data:image"):
                continue

            alt_match = re.search(r'alt=["\']([^"\']*)["\']', img_tag, re.IGNORECASE)
            alt = alt_match.group(1) if alt_match else ""

            width_match = re.search(r'width=["\'](\d+)["\']', img_tag, re.IGNORECASE)
            height_match = re.search(r'height=["\'](\d+)["\']', img_tag, re.IGNORECASE)
            width = int(width_match.group(1)) if width_match else 0
            height = int(height_match.group(1)) if height_match else 0

            score = 0

            alt_lower = alt.lower()
            if "figure" in alt_lower or "fig" in alt_lower:
                score += 100

            if width > 300 and height > 200:
                score += 50
            elif width > 100 and height > 100:
                score += 20

            if src_lower.endswith((".png", ".jpg", ".jpeg", ".gif")):
                score += 10

            image_candidates.append({"src": src, "alt": alt, "width": width, "height": height, "score": score})

        if not image_candidates:
            return None

        image_candidates.sort(key=lambda x: x["score"], reverse=True)
        best_image = image_candidates[0]

        result = _normalize_image_url(best_image["src"], url)
        if use_cache:
            _figure_cache[arxiv_id] = result
            try:
                db = Database()
                db.set_figure_cache(arxiv_id, result)
            except Exception:
                pass
        return result

    except Exception:
        return None


def _normalize_image_url(img_src: str, base_url: str) -> str:
    """标准化图片URL：处理相对路径"""
    if img_src.startswith("http"):
        return img_src

    arxiv_id_match = re.search(r"/html/([^/]+)$", base_url)
    arxiv_id = arxiv_id_match.group(1) if arxiv_id_match else ""

    if img_src.startswith("/"):
        if img_src.startswith("/html/"):
            path_without_html = img_src[6:]
            return f"https://arxiv.org/html/{arxiv_id}/{path_without_html}"
        return f"https://arxiv.org{img_src}"

    if img_src.startswith("./"):
        img_src = img_src[2:]

    if not base_url.endswith("/"):
        base_url = base_url + "/"

    if img_src.startswith("/"):
        img_src = img_src[1:]

    return base_url + img_src
