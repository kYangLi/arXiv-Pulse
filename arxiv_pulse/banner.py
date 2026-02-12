"""
横幅打印功能模块
"""

import re
from pathlib import Path

import click
import wcwidth

from arxiv_pulse.research_fields import DEFAULT_BANNER_FIELDS, RESEARCH_FIELDS


def print_banner():
    """打印应用横幅"""
    print_banner_custom(DEFAULT_BANNER_FIELDS)


def generate_banner_title(env_file) -> list[str]:
    """根据配置文件生成横幅标题"""
    try:
        env_path = Path(env_file) if isinstance(env_file, str) else env_file
        if not env_path.exists():
            return DEFAULT_BANNER_FIELDS

        with open(env_path, encoding="utf-8") as f:
            content = f.read()

        queries_match = re.search(r"SEARCH_QUERIES=(.*?)(?:\n#|\n$)", content, re.DOTALL | re.MULTILINE)
        if not queries_match:
            return DEFAULT_BANNER_FIELDS

        queries = queries_match.group(1).strip()
        fields = []
        matched_fields = []

        for field_id, field_info in RESEARCH_FIELDS.items():
            field_name = field_info["name"]
            keywords = field_info.get("keywords", [])

            for keyword in keywords:
                pattern = re.escape(keyword)
                if re.search(pattern, queries, re.IGNORECASE):
                    matched_fields.append(
                        {
                            "id": field_id,
                            "name": field_name,
                            "match_count": 1,
                        }
                    )
                    break

        if matched_fields:
            seen_names = set()
            for match in matched_fields:
                if match["name"] not in seen_names:
                    fields.append(match["name"])
                    seen_names.add(match["name"])

        if not fields:
            queries_lower = queries.lower()

            if "cond-mat" in queries_lower or "condensed matter" in queries_lower:
                fields.append("凝聚态物理")
            if "astro-ph" in queries_lower:
                fields.append("天体物理")
            if "hep-" in queries_lower:
                fields.append("高能物理")
            if "quant-ph" in queries_lower:
                fields.append("量子物理")
            if "physics.comp-ph" in queries_lower:
                fields.append("计算物理")
            if "math." in queries_lower:
                fields.append("数学")
            if "cs." in queries_lower:
                fields.append("计算机科学")
            if "stat." in queries_lower:
                fields.append("统计学")

            if not fields:
                return DEFAULT_BANNER_FIELDS

        return fields[:4]

    except Exception:
        return DEFAULT_BANNER_FIELDS


def print_banner_custom(fields):
    """打印自定义字段的应用横幅"""
    if len(fields) == 0:
        field_str = "凝聚态物理 • 密度泛函理论 • 机器学习 • 力场"
    elif len(fields) == 1:
        field_str = fields[0]
    elif len(fields) == 2:
        field_str = f"{fields[0]} • {fields[1]}"
    elif len(fields) == 3:
        field_str = f"{fields[0]} • {fields[1]} • {fields[2]}"
    else:
        field_str = f"{fields[0]} • {fields[1]} • {fields[2]} • {fields[3]}"

    banner_width = 55
    content_width = 53

    def display_width(text):
        return wcwidth.wcswidth(text)

    def truncate_to_width(text, max_width):
        if display_width(text) <= max_width:
            return text
        result = ""
        for char in text:
            if display_width(result + char) > max_width - 3:
                break
            result += char
        return result + "..." if result else "..."

    border_top = "╔" + "═" * (banner_width - 2) + "╗"
    border_bottom = "╚" + "═" * (banner_width - 2) + "╝"

    title = "arXiv Pulse - 文献追踪系统"
    title_width = display_width(title)
    left_padding = (content_width - title_width) // 2
    right_padding = content_width - title_width - left_padding
    title_line = "║" + " " * left_padding + title + " " * right_padding + "║"

    max_field_width = content_width - 4
    field_str = truncate_to_width(field_str, max_field_width)
    field_width = display_width(field_str)

    left_padding = (content_width - field_width) // 2
    right_padding = content_width - field_width - left_padding
    field_line = "║" + " " * left_padding + field_str + " " * right_padding + "║"

    banner = f"\n{border_top}\n{title_line}\n{field_line}\n{border_bottom}\n"
    click.echo(banner)
