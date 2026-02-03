#!/usr/bin/env python3
"""
arXiv Pulse - 简化版命令行界面
核心功能：初始化、更新同步、智能搜索、最近论文报告
"""

import os
import sys
from pathlib import Path
import click
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta, timezone
import questionary
import wcwidth

from arxiv_pulse.config import Config
from arxiv_pulse.arxiv_crawler import ArXivCrawler
from arxiv_pulse.summarizer import PaperSummarizer
from arxiv_pulse.report_generator import ReportGenerator
from arxiv_pulse.output_manager import output
from arxiv_pulse.search_engine import SearchEngine, SearchFilter
from arxiv_pulse.__version__ import __version__


# arXiv研究领域定义（用于交互式配置和横幅生成）
RESEARCH_FIELDS = {
    # 物理学领域
    "condensed_matter": {
        "name": "凝聚态物理",
        "query": "condensed matter physics AND cat:cond-mat.*",
        "description": "包括超导、强关联电子、介观系统、材料科学等",
        "keywords": ["condensed matter physics", "cond-mat"],
    },
    "astro_physics": {
        "name": "天体物理",
        "query": "cat:astro-ph.*",
        "description": "天体物理学、宇宙学、天体观测等",
        "keywords": ["astro-ph"],
    },
    "high_energy_physics": {
        "name": "高能物理（粒子物理）",
        "query": "cat:hep-ph.* OR cat:hep-ex.* OR cat:hep-th.* OR cat:hep-lat.*",
        "description": "粒子物理、高能物理理论与实验",
        "keywords": ["hep-ph", "hep-ex", "hep-th", "hep-lat"],
    },
    "nuclear_physics": {
        "name": "核物理",
        "query": "cat:nucl-th.* OR cat:nucl-ex.*",
        "description": "核物理理论与实验",
        "keywords": ["nucl-th", "nucl-ex"],
    },
    "general_relativity": {
        "name": "广义相对论与宇宙学",
        "query": "cat:gr-qc.*",
        "description": "引力理论、宇宙学、黑洞物理",
        "keywords": ["gr-qc"],
    },
    "quantum_physics": {
        "name": "量子物理",
        "query": "cat:quant-ph.*",
        "description": "量子信息、量子计算、量子基础",
        "keywords": ["quant-ph"],
    },
    "computational_physics": {
        "name": "计算物理",
        "query": "cat:physics.comp-ph",
        "description": "数值计算方法在物理中的应用",
        "keywords": ["physics.comp-ph"],
    },
    "chemical_physics": {
        "name": "化学物理",
        "query": "cat:physics.chem-ph",
        "description": "化学过程的物理基础",
        "keywords": ["physics.chem-ph"],
    },
    "physics_other": {
        "name": "物理学（其他）",
        "query": "cat:physics:* NOT cat:physics.comp-ph NOT cat:physics.chem-ph",
        "description": "其他物理学领域",
        "keywords": ["physics:"],
    },
    "nonlinear_science": {
        "name": "非线性科学",
        "query": "cat:nlin.*",
        "description": "非线性动力学、复杂系统、混沌理论",
        "keywords": ["nlin"],
    },
    "mathematical_physics": {
        "name": "数学物理",
        "query": "cat:math-ph.*",
        "description": "物理问题的数学方法",
        "keywords": ["math-ph"],
    },
    # 计算材料科学专业领域
    "dft": {
        "name": "密度泛函理论 (DFT)",
        "query": '(ti:"density functional" OR abs:"density functional") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci OR cat:physics.chem-ph)',
        "description": "第一性原理计算、材料设计",
        "keywords": ["density functional"],
    },
    "first_principles": {
        "name": "第一性原理计算",
        "query": '(ti:"first principles" OR abs:"first principles" OR ti:"ab initio" OR abs:"ab initio") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci)',
        "description": "从头计算、量子化学方法",
        "keywords": ["first principles", "ab initio"],
    },
    "quantum_chemistry": {
        "name": "量子化学",
        "query": '(ti:"quantum chemistry" OR abs:"quantum chemistry") AND (cat:physics.chem-ph OR cat:physics.comp-ph)',
        "description": "量子化学方法与计算",
        "keywords": ["quantum chemistry"],
    },
    "force_fields": {
        "name": "力场与分子动力学",
        "query": '(ti:"force field" OR abs:"force field") AND (cat:physics.comp-ph OR cat:cond-mat.soft OR cat:physics.chem-ph)',
        "description": "力场开发、分子动力学模拟",
        "keywords": ["force field"],
    },
    "molecular_dynamics": {
        "name": "分子动力学",
        "query": '(ti:"molecular dynamics" OR abs:"molecular dynamics") AND (cat:physics.comp-ph OR cat:cond-mat.soft OR cat:physics.chem-ph)',
        "description": "分子动力学模拟技术",
        "keywords": ["molecular dynamics"],
    },
    "computational_materials": {
        "name": "计算材料科学",
        "query": 'cat:cond-mat.mtrl-sci AND (ti:"computational" OR abs:"computational" OR ti:"simulation" OR abs:"simulation")',
        "description": "材料计算与模拟",
        "keywords": ["computational materials", "materials science"],
    },
    # 数学领域
    "mathematics": {
        "name": "数学",
        "query": "cat:math.* AND NOT cat:math-ph.*",
        "description": "纯数学与应用数学",
        "keywords": ["cat:math."],
    },
    "numerical_analysis": {
        "name": "数值分析",
        "query": "cat:math.NA",
        "description": "数值计算方法与算法",
        "keywords": ["math.NA"],
    },
    "optimization_control": {
        "name": "优化与控制",
        "query": "cat:math.OC",
        "description": "数学优化、最优控制理论",
        "keywords": ["math.OC"],
    },
    "statistics_math": {
        "name": "统计学（数学）",
        "query": "cat:math.ST",
        "description": "数理统计理论",
        "keywords": ["math.ST"],
    },
    # 计算机科学领域
    "machine_learning": {
        "name": "机器学习",
        "query": '(ti:"machine learning" OR abs:"machine learning") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci OR cat:physics.chem-ph OR cat:cs.* OR cat:stat.*)',
        "description": "机器学习在物理和材料科学中的应用",
        "keywords": ["machine learning"],
    },
    "artificial_intelligence": {
        "name": "人工智能",
        "query": "cat:cs.AI OR cat:cs.LG OR cat:cs.NE",
        "description": "人工智能、机器学习、神经网络",
        "keywords": ["cs.AI", "cs.LG", "cs.NE"],
    },
    "computer_vision": {
        "name": "计算机视觉",
        "query": "cat:cs.CV",
        "description": "图像处理、计算机视觉",
        "keywords": ["cs.CV"],
    },
    "natural_language": {
        "name": "自然语言处理",
        "query": "cat:cs.CL",
        "description": "计算语言学、自然语言处理",
        "keywords": ["cs.CL"],
    },
    "computer_science_other": {
        "name": "计算机科学（其他）",
        "query": "cat:cs.* NOT cat:cs.AI NOT cat:cs.LG NOT cat:cs.NE NOT cat:cs.CV NOT cat:cs.CL",
        "description": "其他计算机科学领域",
        "keywords": ["cat:cs."],
    },
    # 统计学领域
    "statistics": {
        "name": "统计学",
        "query": "cat:stat.*",
        "description": "统计学理论与应用",
        "keywords": ["cat:stat."],
    },
    "statistical_learning": {
        "name": "统计学习",
        "query": "cat:stat.ML",
        "description": "统计学习方法与应用",
        "keywords": ["stat.ML"],
    },
    # 跨学科领域
    "quantitative_biology": {
        "name": "定量生物学",
        "query": "cat:q-bio.*",
        "description": "生物信息学、系统生物学、定量生物方法",
        "keywords": ["q-bio"],
    },
    "quantitative_finance": {
        "name": "定量金融",
        "query": "cat:q-fin.*",
        "description": "金融数学、金融工程、计量金融",
        "keywords": ["q-fin"],
    },
    "electrical_engineering": {
        "name": "电子工程与系统科学",
        "query": "cat:eess.*",
        "description": "信号处理、控制系统、电子工程",
        "keywords": ["eess"],
    },
    "economics": {
        "name": "经济学",
        "query": "cat:econ.*",
        "description": "经济学理论、计量经济学",
        "keywords": ["econ"],
    },
}


def setup_environment(directory: Path):
    """设置环境并验证给定目录的配置"""
    original_cwd = os.getcwd()
    try:
        os.chdir(directory)

        # 创建必要的目录
        os.makedirs("data", exist_ok=True)
        os.makedirs("reports", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        # 加载 .env 文件（如果存在）
        env_file = directory / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        else:
            output.warn(f"在 {directory} 中未找到 .env 文件。使用默认配置。")

        # 将 DATABASE_URL 转换为绝对路径（如果是相对 SQLite 路径）
        db_url = os.getenv("DATABASE_URL", "sqlite:///data/arxiv_papers.db")
        if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
            # 相对路径，转换为绝对路径
            db_path = db_url.replace("sqlite:///", "")
            abs_db_path = os.path.abspath(db_path)
            os.environ["DATABASE_URL"] = f"sqlite:///{abs_db_path}"
            output.debug(f"Converted DATABASE_URL to absolute path: {os.environ['DATABASE_URL']}")

        # 直接更新 Config 类变量
        Config.DATABASE_URL = os.environ["DATABASE_URL"]
        # 基于新的 DATABASE_URL 更新 DATA_DIR
        Config.DATA_DIR = os.path.dirname(Config.DATABASE_URL.replace("sqlite:///", ""))
        # 如果相对，将 REPORT_DIR 转换为绝对路径
        report_dir = os.getenv("REPORT_DIR", "reports")
        if not os.path.isabs(report_dir):
            Config.REPORT_DIR = os.path.abspath(report_dir)
            output.debug(f"Converted REPORT_DIR to absolute path: {Config.REPORT_DIR}")

        # 从环境变量更新其他 Config 变量
        Config.AI_API_KEY = os.getenv("AI_API_KEY")
        Config.AI_MODEL = os.getenv("AI_MODEL", "DeepSeek-V3.2-Thinking")
        Config.AI_BASE_URL = os.getenv("AI_BASE_URL", "https://llmapi.paratera.com")
        Config.SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", "2000"))
        Config.SUMMARY_SENTENCES_LIMIT = int(os.getenv("SUMMARY_SENTENCES_LIMIT", "3"))
        Config.TOKEN_PRICE_PER_MILLION = float(os.getenv("TOKEN_PRICE_PER_MILLION", "3.0"))
        Config.MAX_RESULTS_INITIAL = int(os.getenv("MAX_RESULTS_INITIAL", "100"))
        Config.MAX_RESULTS_DAILY = int(os.getenv("MAX_RESULTS_DAILY", "20"))
        Config.YEARS_BACK = int(os.getenv("YEARS_BACK", "3"))
        Config.IMPORTANT_PAPERS_FILE = os.getenv("IMPORTANT_PAPERS_FILE", "important_papers.txt")
        Config.REPORT_MAX_PAPERS = int(os.getenv("REPORT_MAX_PAPERS", "50"))

        # 更新 SEARCH_QUERIES
        search_queries_raw = os.getenv(
            "SEARCH_QUERIES",
            "condensed matter physics; density functional theory; machine learning; force fields; first principles calculation; molecular dynamics; quantum chemistry; computational materials science",
        )
        Config.SEARCH_QUERIES_RAW = search_queries_raw
        Config.SEARCH_QUERIES = [q.strip() for q in search_queries_raw.split(";") if q.strip()]

        # 验证配置
        try:
            Config.validate()
            output.info("配置验证通过")
        except Exception as e:
            output.error(f"配置错误: {e}")
            return False

        return True
    finally:
        os.chdir(original_cwd)


def print_banner():
    """打印应用横幅"""
    print_banner_custom(["凝聚态物理", "密度泛函理论", "机器学习", "力场"])


def generate_banner_title(env_file):
    """根据配置文件生成横幅标题"""
    try:
        # 读取 .env 文件，解析 SEARCH_QUERIES
        import re
        from pathlib import Path

        env_path = Path(env_file) if isinstance(env_file, str) else env_file
        if not env_path.exists():
            return ["凝聚态物理", "密度泛函理论", "机器学习", "力场"]

        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取 SEARCH_QUERIES
        queries_match = re.search(r"SEARCH_QUERIES=(.*?)(?:\n#|\n$)", content, re.DOTALL | re.MULTILINE)
        if not queries_match:
            return ["凝聚态物理", "密度泛函理论", "机器学习", "力场"]

        queries = queries_match.group(1).strip()

        # 根据查询确定领域
        fields = []

        # 使用 RESEARCH_FIELDS 进行智能匹配
        # 首先收集所有可能的匹配
        matched_fields = []

        for field_id, field_info in RESEARCH_FIELDS.items():
            field_name = field_info["name"]
            keywords = field_info.get("keywords", [])

            # 检查每个关键词是否出现在查询中
            for keyword in keywords:
                # 对关键词进行转义，以便在正则表达式中使用
                # 简单的字符串匹配（不区分大小写）
                pattern = re.escape(keyword)
                if re.search(pattern, queries, re.IGNORECASE):
                    # 记录匹配的字段和匹配的关键词数量（用于排序）
                    matched_fields.append(
                        {
                            "id": field_id,
                            "name": field_name,
                            "match_count": 1,  # 简单计数，可以更复杂
                        }
                    )
                    break  # 找到一个匹配就足够

        # 根据匹配情况选择要显示的字段
        if matched_fields:
            # 去重（按字段名）
            seen_names = set()
            for match in matched_fields:
                if match["name"] not in seen_names:
                    fields.append(match["name"])
                    seen_names.add(match["name"])

        # 如果没有找到任何匹配，使用默认
        if not fields:
            # 尝试基于查询内容进行更宽松的匹配
            queries_lower = queries.lower()

            # 常见的arXiv分类检测
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

            # 如果还是没有匹配，使用默认
            if not fields:
                return ["凝聚态物理", "密度泛函理论", "机器学习", "力场"]

        # 限制最多显示4个领域
        return fields[:4]

    except Exception as e:
        # 出错时返回默认
        return ["凝聚态物理", "密度泛函理论", "机器学习", "力场"]


def print_banner_custom(fields):
    """打印自定义字段的应用横幅"""
    # 创建字段字符串
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

    # 横幅尺寸
    banner_width = 55
    content_width = 53

    # 辅助函数：计算字符串显示宽度
    def display_width(text):
        return wcwidth.wcswidth(text)

    # 辅助函数：截断字符串到指定显示宽度，添加省略号
    def truncate_to_width(text, max_width):
        if display_width(text) <= max_width:
            return text
        # 逐步减少字符直到宽度合适
        result = ""
        for char in text:
            if display_width(result + char) > max_width - 3:  # 为"..."留出空间
                break
            result += char
        return result + "..." if result else "..."  # 至少返回省略号

    # 创建横幅边框
    border_top = "╔" + "═" * (banner_width - 2) + "╗"
    border_bottom = "╚" + "═" * (banner_width - 2) + "╝"

    # 第一行标题
    title = "arXiv Pulse - 文献追踪系统"
    title_width = display_width(title)
    # 计算左右填充
    left_padding = (content_width - title_width) // 2
    right_padding = content_width - title_width - left_padding
    title_line = "║" + " " * left_padding + title + " " * right_padding + "║"

    # 第二行字段
    # 最大字段显示宽度（留出边距）
    max_field_width = content_width - 4
    # 截断字段字符串如果太长
    field_str = truncate_to_width(field_str, max_field_width)
    field_width = display_width(field_str)

    # 计算字段行的左右填充
    left_padding = (content_width - field_width) // 2
    right_padding = content_width - field_width - left_padding
    field_line = "║" + " " * left_padding + field_str + " " * right_padding + "║"

    banner = f"\n{border_top}\n{title_line}\n{field_line}\n{border_bottom}\n"
    click.echo(banner)


def sync_papers(years_back=1, summarize=False, force=False):
    """同步论文（内部函数）

    Args:
        years_back: 回溯的年数
        summarize: 是否总结新论文
        force: 是否强制同步（重新下载所有论文，忽略重复检查）
    """
    crawler = ArXivCrawler()
    summarizer = PaperSummarizer()

    mode_text = "强制同步" if force else "同步缺失论文"
    click.echo(f"正在{mode_text}（回溯 {years_back} 年）...")
    click.echo("=" * 50)

    # 同步所有查询
    click.echo("1. 正在同步搜索查询...")
    sync_result = crawler.sync_all_queries(years_back=years_back, force=force)
    result_text = "处理了" if force else "添加了"
    click.echo(f"   从查询{result_text} {sync_result['total_new_papers']} 篇论文")

    # 同步重要论文
    click.echo("2. 正在同步重要论文...")
    important_result = crawler.sync_important_papers()
    click.echo(f"   添加了 {important_result['added']} 篇重要论文")
    if important_result["errors"]:
        click.echo(f"   错误: {len(important_result['errors'])}")

    # 总结新论文（如果启用）
    total_new = sync_result["total_new_papers"] + important_result["added"]
    if summarize and total_new > 0:
        click.echo("3. 正在总结新论文...")
        summarize_result = summarizer.summarize_pending_papers(limit=min(50, total_new))
        click.echo(f"   已总结 {summarize_result['successful']} 篇论文")
    elif total_new > 0:
        click.echo("3. 跳过论文总结")
    else:
        click.echo("3. 没有新论文需要总结")

    # 更新数据库统计
    crawl_stats = crawler.get_crawler_stats()
    summary_stats = summarizer.get_summary_stats()

    click.echo("\n" + "=" * 50)
    click.echo("同步完成！")
    click.echo(f"总共{result_text}论文: {total_new}")
    click.echo(f"数据库现有 {crawl_stats['total_papers']} 篇论文")
    click.echo(f"已总结: {summary_stats['summarized_papers']} ({summary_stats['summarization_rate']:.1%})")

    return {
        "crawler": crawler,
        "summarizer": summarizer,
        "sync_result": sync_result,
        "important_result": important_result,
        "stats": {"crawl_stats": crawl_stats, "summary_stats": summary_stats},
        "force_mode": force,
    }


def get_workday_cutoff(days_back):
    """计算排除周末的截止日期"""
    current = datetime.now(timezone.utc).replace(tzinfo=None)
    workdays_counted = 0
    days_to_go_back = 0

    while workdays_counted < days_back:
        days_to_go_back += 1
        # 检查是否为工作日（周一至周五）
        if (current - timedelta(days=days_to_go_back)).weekday() < 5:
            workdays_counted += 1

    return current - timedelta(days=days_to_go_back)


def generate_report(paper_limit=50, days_back=2, summarize=True, max_summarize=10):
    """生成最近论文的报告（内部函数）"""
    reporter = ReportGenerator()

    # 设置报告限制
    original_limit = Config.REPORT_MAX_PAPERS
    Config.REPORT_MAX_PAPERS = paper_limit

    try:
        # 生成报告数据
        with reporter.db.get_session() as session:
            from arxiv_pulse.models import Paper

            # 获取最近N个工作日的论文（排除周末）
            cutoff = get_workday_cutoff(days_back)
            recent_papers = (
                session.query(Paper)
                .filter(Paper.published >= cutoff)
                .order_by(Paper.published.desc())
                .limit(paper_limit)
                .all()
            )

            # 总结未总结的论文（限制数量避免过多API调用）
            summarized_count = 0
            summarizer = PaperSummarizer()

            if summarize:
                for paper in recent_papers:
                    if paper.summarized is False and (max_summarize == 0 or summarized_count < max_summarize):
                        if summarizer.summarize_paper(paper):
                            summarized_count += 1
                            # 刷新论文对象以获取更新后的总结数据
                            session.refresh(paper)

                if summarized_count > 0:
                    output.info(f"已总结 {summarized_count} 篇论文用于报告")
                    # 显示累计token使用情况
                    summary_stats = summarizer.get_summary_stats()
                    token_usage = summary_stats.get("token_usage", {})
                    if token_usage:
                        output.info(
                            f"累计Token使用: 提示 {token_usage.get('total_prompt_tokens', 0)}, "
                            f"完成 {token_usage.get('total_completion_tokens', 0)}, "
                            f"总计 {token_usage.get('total_tokens', 0)}"
                        )

            # 计算热门分类
            category_counts = {}
            for paper in recent_papers:
                if paper.categories is not None:
                    # arXiv分类以空格分隔，例如 "cond-mat.mtrl-sci physics.comp-ph"
                    for cat in paper.categories.split():
                        category_counts[cat] = category_counts.get(cat, 0) + 1

            # 取前5个热门分类
            top_categories = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5])

            # 获取数据库总体统计
            crawler = ArXivCrawler()
            crawl_stats = crawler.get_crawler_stats()
            summary_stats = summarizer.get_summary_stats()

            # 创建报告数据
            report_data = {
                "stats": {
                    "total_recent": len(recent_papers),
                    "days_back": days_back,
                    "report_type": "recent",
                    "date_generated": datetime.now().isoformat(),
                    "database_stats": {
                        "total_papers": crawl_stats["total_papers"],
                        "summarized_papers": summary_stats["summarized_papers"],
                    },
                    "top_categories": top_categories,
                },
                "papers": recent_papers,
            }

        # 保存报告
        files = []

        # 保存Markdown报告
        md_file = reporter.save_markdown_report(report_data)
        if md_file:
            files.append(md_file)

        # 保存CSV报告
        csv_file = reporter.save_csv_report(report_data)
        if csv_file:
            files.append(csv_file)

        return files
    finally:
        Config.REPORT_MAX_PAPERS = original_limit


def generate_search_report(query, search_terms, papers, paper_limit=50, summarize=True, max_summarize=10):
    """生成搜索结果的报告（内部函数）"""
    reporter = ReportGenerator()

    # 如果没有找到论文，不生成报告
    if not papers:
        output.info("未找到论文，跳过报告生成")
        return []

    # 设置报告限制
    original_limit = Config.REPORT_MAX_PAPERS
    Config.REPORT_MAX_PAPERS = paper_limit

    try:
        # 总结未总结的论文（限制数量避免过多API调用）
        summarized_count = 0
        summarizer = PaperSummarizer()

        if summarize:
            # 收集需要总结的论文ID
            papers_to_summarize = []
            for paper in papers:
                if paper.summarized is False and (max_summarize == 0 or summarized_count < max_summarize):
                    papers_to_summarize.append(paper)
                    summarized_count += 1

            # 总结论文
            for paper in papers_to_summarize:
                summarizer.summarize_paper(paper)

            if summarized_count > 0:
                output.info(f"已总结 {summarized_count} 篇论文用于报告")
                # 重新获取论文数据以确保包含最新总结
                with summarizer.db.get_session() as session:
                    from arxiv_pulse.models import Paper

                    paper_ids = [p.arxiv_id for p in papers]
                    # 按原始顺序重新查询论文
                    updated_papers = []
                    for paper_id in paper_ids:
                        paper = session.query(Paper).filter_by(arxiv_id=paper_id).first()
                        if paper:
                            updated_papers.append(paper)
                    papers = updated_papers

        # 计算热门分类
        category_counts = {}
        for paper in papers:
            if paper.categories is not None:
                # arXiv分类以空格分隔，例如 "cond-mat.mtrl-sci physics.comp-ph"
                for cat in paper.categories.split():
                    category_counts[cat] = category_counts.get(cat, 0) + 1

        # 取前5个热门分类
        top_categories = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5])

        # 获取数据库总体统计
        crawler = ArXivCrawler()
        summarizer = PaperSummarizer()
        crawl_stats = crawler.get_crawler_stats()
        summary_stats = summarizer.get_summary_stats()

        # 创建报告数据
        report_data = {
            "stats": {
                "total_found": len(papers),
                "original_query": query,
                "search_terms": search_terms,
                "report_type": "search",
                "date_generated": datetime.now().isoformat(),
                "database_stats": {
                    "total_papers": crawl_stats["total_papers"],
                    "summarized_papers": summary_stats["summarized_papers"],
                },
                "top_categories": top_categories,
            },
            "papers": papers,
        }

        # 保存报告
        files = []

        # 保存Markdown报告
        md_file = reporter.save_markdown_report(report_data)
        if md_file:
            files.append(md_file)

        # 保存CSV报告
        csv_file = reporter.save_csv_report(report_data)
        if csv_file:
            files.append(csv_file)

        return files
    finally:
        Config.REPORT_MAX_PAPERS = original_limit


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="arXiv Pulse")
def cli():
    """arXiv Pulse: 智能arXiv文献追踪和分析系统"""
    pass


def interactive_configuration():
    """交互式配置 arXiv Pulse"""
    config = {}
    import openai

    click.echo("\n" + "=" * 60)
    click.echo("arXiv Pulse 交互式配置向导")
    click.echo("=" * 60)

    # 1. AI API 配置
    click.echo("\n🔧 AI API 配置")
    click.echo("-" * 40)

    # 1.1 先询问 Base URL
    ai_base_url = click.prompt("AI API Base URL", default="https://llmapi.paratera.com", show_default=True)
    config["AI_BASE_URL"] = ai_base_url

    # 1.2 询问 API 密钥
    ai_api_key = click.prompt(
        "请输入 AI API 密钥 (留空则跳过，稍后可在 .env 文件中添加)", default="", show_default=False, hide_input=True
    )
    if ai_api_key:
        config["AI_API_KEY"] = ai_api_key
        # 使用提供的密钥查询可用模型
        available_models = []
        try:
            click.echo("正在查询可用模型...")
            client = openai.OpenAI(base_url=ai_base_url, api_key=ai_api_key)
            models_response = client.models.list()
            available_models = [model.id for model in models_response.data]
            click.echo(f"✅ 找到 {len(available_models)} 个可用模型")
        except Exception as e:
            click.echo(f"⚠️  无法查询模型列表: {e}")
            click.echo("   将使用默认模型选项")
            available_models = ["DeepSeek-V3.2-Thinking", "gpt-3.5-turbo", "gpt-4-turbo"]
    else:
        click.echo("⚠️  未提供 API 密钥，AI 总结和翻译功能将受限")
        click.echo("   您可以稍后在 .env 文件中添加 AI_API_KEY 设置")
        config["AI_API_KEY"] = "your_api_key_here"
        available_models = ["DeepSeek-V3.2-Thinking", "gpt-3.5-turbo", "gpt-4-turbo"]

    # 1.3 让用户选择模型
    if available_models:
        click.echo("\n可用模型列表:")

        # 构建questionary选择选项
        choices = []
        for model in available_models:
            choices.append(questionary.Choice(title=model, value=model))

        # 添加自定义输入选项
        choices.append(questionary.Choice(title="[自定义输入] - 输入其他模型名称", value="__custom_input__"))

        # 显示交互式选择菜单
        selected_model = questionary.select(
            "请选择AI模型（使用上下箭头导航，回车确认）:", choices=choices, instruction="(上下箭头导航，回车确认)"
        ).ask()

        if selected_model == "__custom_input__":
            # 用户选择自定义输入
            ai_model = click.prompt("请输入自定义模型名称", default="DeepSeek-V3.2-Thinking", show_default=True)
            click.echo(f"✅ 使用自定义模型: {ai_model}")
        else:
            ai_model = selected_model
            click.echo(f"✅ 已选择模型: {ai_model}")
    else:
        ai_model = click.prompt("AI 模型名称", default="DeepSeek-V3.2-Thinking", show_default=True)

    config["AI_MODEL"] = ai_model

    # 2. 爬虫配置
    click.echo("\n📊 爬虫配置")
    click.echo("-" * 40)

    max_results_initial = click.prompt("初始同步每个查询的最大论文数", default=100, type=int, show_default=True)
    config["MAX_RESULTS_INITIAL"] = str(max_results_initial)

    max_results_daily = click.prompt("每日同步每个查询的最大论文数", default=20, type=int, show_default=True)
    config["MAX_RESULTS_DAILY"] = str(max_results_daily)

    years_back = click.prompt("初始同步回溯的年数", default=5, type=int, show_default=True)
    config["YEARS_BACK"] = str(years_back)

    # 3. 研究领域选择
    click.echo("\n🎯 选择您的研究领域")
    click.echo("-" * 40)
    click.echo("请使用上下箭头导航，空格键选择/取消，回车确认（可多选）：")

    research_fields = RESEARCH_FIELDS

    # 构建questionary选项
    choices = []
    for key, field in research_fields.items():
        # 使用Choice对象，包含标题和描述
        title = f"[{field['name']}] - {field['description']}"
        choices.append(
            questionary.Choice(
                title=title,
                value=key,  # 保存字段ID用于后续查询
                checked=False,  # 默认不选中
            )
        )

    # 添加全选选项
    choices.insert(0, questionary.Choice(title="[全选] - 选择所有研究领域", value="__select_all__", checked=False))

    # 显示交互式复选框
    selected_keys = questionary.checkbox(
        "请选择您感兴趣的研究领域：",
        choices=choices,
        instruction="(空格键切换选择，回车确认)",
        validate=lambda selected: len(selected) > 0 or "请至少选择一个研究领域",
    ).ask()

    if not selected_keys:
        click.echo("❌ 未选择任何研究领域，将使用默认配置")
        selected_keys = ["condensed_matter", "dft", "machine_learning"]

    selected_queries = []
    selected_field_names = []

    # 处理选择
    if "__select_all__" in selected_keys:
        # 选择全部（排除全选标记）
        for field in research_fields.values():
            selected_queries.append(field["query"])
            selected_field_names.append(field["name"])
        click.echo("✅ 已选择全部研究领域")
    else:
        # 处理用户选择
        for key in selected_keys:
            if key in research_fields:
                field = research_fields[key]
                selected_queries.append(field["query"])
                selected_field_names.append(field["name"])
                click.echo(f"✅ 已选择: {field['name']}")
            else:
                click.echo(f"⚠️  未知的领域ID: {key}")

    # 确保至少有一个选择
    if not selected_queries:
        click.echo("⚠️  未选择任何领域，使用默认配置")
        selected_queries = [
            research_fields["condensed_matter"]["query"],
            research_fields["dft"]["query"],
            research_fields["machine_learning"]["query"],
        ]
        selected_field_names = [
            research_fields["condensed_matter"]["name"],
            research_fields["dft"]["name"],
            research_fields["machine_learning"]["name"],
        ]

    config["SEARCH_QUERIES"] = "; ".join(selected_queries)
    config["_SELECTED_FIELD_NAMES"] = selected_field_names

    # 3.5 智能建议（基于选择的领域数量）
    num_selected_fields = len(selected_field_names)
    click.echo(f"\n📊 智能建议（基于您选择的 {num_selected_fields} 个研究领域）")
    click.echo("-" * 40)

    # 根据领域数量提供建议
    recommended_initial = 100
    recommended_daily = 20

    if num_selected_fields <= 3:
        click.echo("✅ 您选择了少量领域，保持默认配置即可。")
    elif num_selected_fields <= 6:
        recommended_initial = 70
        recommended_daily = 15
        click.echo(f"⚠️  您选择了中等数量领域，建议调整爬虫配置以避免过多论文：")
        click.echo(f"   - 初始同步每个查询最大论文数: {recommended_initial} (原默认: 100)")
        click.echo(f"   - 每日同步每个查询最大论文数: {recommended_daily} (原默认: 20)")
    else:
        recommended_initial = 50
        recommended_daily = 10
        click.echo(f"⚠️  您选择了大量领域 ({num_selected_fields}个)，强烈建议调整爬虫配置：")
        click.echo(f"   - 初始同步每个查询最大论文数: {recommended_initial} (原默认: 100)")
        click.echo(f"   - 每日同步每个查询最大论文数: {recommended_daily} (原默认: 20)")
        click.echo(f"   - 注意：同步大量领域可能需要较长时间和更多存储空间。")

    # 询问用户是否应用建议
    if num_selected_fields > 3:
        if click.confirm("\n💡 是否应用上述建议调整爬虫配置？", default=True):
            config["MAX_RESULTS_INITIAL"] = str(recommended_initial)
            config["MAX_RESULTS_DAILY"] = str(recommended_daily)
            click.echo(
                f"✅ 已应用建议配置：MAX_RESULTS_INITIAL={recommended_initial}, MAX_RESULTS_DAILY={recommended_daily}"
            )
        else:
            click.echo("ℹ️  保持您原有的爬虫配置。")

    # 4. 报告配置
    click.echo("\n📄 报告配置")
    click.echo("-" * 40)

    report_max_papers = click.prompt("每份报告显示的最大论文数", default=50, type=int, show_default=True)
    config["REPORT_MAX_PAPERS"] = str(report_max_papers)

    summary_sentences_limit = click.prompt("摘要句子数限制", default=3, type=int, show_default=True)
    config["SUMMARY_SENTENCES_LIMIT"] = str(summary_sentences_limit)

    click.echo("\n✅ 配置完成！")
    return config, int(years_back)


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--years-back", type=int, default=None, help="初始同步回溯的年数（默认：交互式配置）")
def init(directory, years_back):
    """初始化目录并同步历史论文"""
    directory = Path(directory).resolve()

    # 创建目录结构
    (directory / "data").mkdir(exist_ok=True)
    (directory / "reports").mkdir(exist_ok=True)
    (directory / "logs").mkdir(exist_ok=True)

    # 创建 .env 文件（如果不存在）
    env_file = directory / ".env"
    custom_banner_fields = None  # 用于存储自定义横幅字段

    if not env_file.exists():
        # 交互式配置
        config, interactive_years_back = interactive_configuration()

        # 保存自定义横幅字段
        custom_banner_fields = config.get("_SELECTED_FIELD_NAMES", [])

        # 如果命令行参数没有指定 years_back，使用交互式配置的值
        if years_back is None:
            years_back = interactive_years_back

        # 生成 .env 文件内容
        env_content = f"""# arXiv Pulse 配置文件
# 由交互式配置向导于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} 生成

# ========================
# AI API 配置 (支持 OpenAI 格式)
# ========================
AI_API_KEY={config.get("AI_API_KEY", "your_api_key_here")}
AI_MODEL={config.get("AI_MODEL", "DeepSeek-V3.2-Thinking")}
AI_BASE_URL={config.get("AI_BASE_URL", "https://llmapi.paratera.com")}

# ========================
# 数据库配置
# ========================
DATABASE_URL=sqlite:///data/arxiv_papers.db

# ========================
# 爬虫配置
# ========================
MAX_RESULTS_INITIAL={config.get("MAX_RESULTS_INITIAL", "100")}    # init命令每个查询的论文数
MAX_RESULTS_DAILY={config.get("MAX_RESULTS_DAILY", "20")}        # sync命令每个查询的论文数

# ========================
# 搜索查询配置
# ========================
# 分号分隔，允许查询中包含逗号
# 根据您的选择生成的研究领域查询
SEARCH_QUERIES={config.get("SEARCH_QUERIES", 'condensed matter physics AND cat:cond-mat.*; (ti:"density functional" OR abs:"density functional") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci OR cat:physics.chem-ph); (ti:"machine learning" OR abs:"machine learning") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci OR cat:physics.chem-ph)')}

# ========================
# 报告配置
# ========================
REPORT_DIR=reports
SUMMARY_MAX_TOKENS=2000          # 总结和翻译的最大token数
SUMMARY_SENTENCES_LIMIT={config.get("SUMMARY_SENTENCES_LIMIT", "3")}
TOKEN_PRICE_PER_MILLION=3.0
REPORT_MAX_PAPERS={config.get("REPORT_MAX_PAPERS", "50")}

# ========================
# 同步配置
# ========================
YEARS_BACK={config.get("YEARS_BACK", "3")}               # 同步回溯的年数
IMPORTANT_PAPERS_FILE=important_papers.txt

# ========================
# 可选配置
# ========================
# 日志级别: DEBUG, INFO, WARNING, ERROR (默认: INFO)
LOG_LEVEL=INFO

# 爬虫延迟（秒，避免频繁请求 arXiv API）
CRAWL_DELAY=1.0
"""

        env_file.write_text(env_content)
        click.echo(f"\n✅ 已在 {directory} 创建 .env 配置文件")

    else:
        click.echo(f".env 文件已存在于 {directory}")
        if years_back is None:
            years_back = 5  # 默认值

    # 创建 important_papers.txt（如果不存在）
    important_file = directory / "important_papers.txt"
    if not important_file.exists():
        important_file.write_text("# 在此添加重要论文的arXiv ID，每行一个\n")
        click.echo(f"✅ 已在 {directory} 创建 important_papers.txt 文件")

    # 设置环境并验证配置
    if not setup_environment(directory):
        click.echo("❌ 配置验证失败，请检查 .env 文件")
        sys.exit(1)

    # 确认同步
    click.echo("\n" + "=" * 60)
    click.echo("准备同步数据库")
    click.echo("=" * 60)
    click.echo(f"即将开始初始同步，回溯 {years_back} 年历史论文...")
    click.echo(f"这可能会花费一些时间，具体取决于您选择的领域数量。")
    click.echo(f"您可以在任何时候按 Ctrl+C 中断同步。")

    if not click.confirm("\n🚀 确认开始同步数据库吗？", default=True):
        click.echo("❌ 已取消同步")
        sys.exit(0)

    click.echo(f"\n⏳ 开始初始同步，回溯 {years_back} 年历史论文...")
    sync_result = sync_papers(years_back=years_back, summarize=False)

    # 生成横幅标题
    if custom_banner_fields:
        banner_title = custom_banner_fields[:4]  # 限制最多4个字段
    else:
        banner_title = generate_banner_title(env_file)
    print_banner_custom(banner_title)

    click.echo(f"\n🎉 arXiv Pulse 初始化完成！")
    click.echo(f"\n📁 文件位置：")
    click.echo(f"  配置文件: {env_file}")
    click.echo(f"  数据库: {directory}/data/arxiv_papers.db")
    click.echo(f"  报告目录: {directory}/reports/")
    click.echo(f"\n🚀 下一步：")
    click.echo(f"  1. 运行 'pulse sync {directory}' 更新最新论文")
    click.echo(f"  2. 运行 'pulse search \"关键词\" {directory}' 搜索论文")
    click.echo(f"  3. 运行 'pulse recent {directory}' 查看最近论文报告")
    click.echo(f"  4. 编辑 {important_file} 添加重要论文")


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--years-back", type=int, default=None, help="同步回溯的年数（默认：强制模式5年，普通模式1年）")
@click.option("--summarize/--no-summarize", default=False, help="是否总结新论文（默认：否）")
@click.option("--force", is_flag=True, default=False, help="强制同步：重新下载最近N年的所有论文，忽略重复检查")
def sync(directory, years_back, summarize, force):
    """同步最新论文到数据库

    强制模式(--force): 重新下载最近N年的所有论文，忽略重复检查，默认回溯5年。
    普通模式: 只下载缺失的新论文，默认回溯1年。
    """
    directory = Path(directory).resolve()
    click.echo(f"正在同步 arXiv Pulse 于 {directory}")

    if not setup_environment(directory):
        sys.exit(1)

    print_banner()

    # 设置默认years_back值
    if years_back is None:
        years_back = 5 if force else 1
        click.echo(f"使用默认回溯年数: {years_back} 年")

    # 同步论文
    sync_result = sync_papers(years_back=years_back, summarize=summarize, force=force)

    click.echo("\n" + "=" * 50)
    click.echo("同步完成！数据库已更新。")


@cli.command()
@click.argument("query")
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--limit", default=20, help="返回结果的最大数量（默认：20）")
@click.option("--years-back", type=int, default=0, help="搜索前同步回溯的年数（默认：0，不更新）")
@click.option("--use-ai/--no-ai", default=True, help="是否使用AI理解自然语言查询（默认：是）")
@click.option("--summarize/--no-summarize", default=True, help="是否自动总结未总结的论文（默认：是）")
@click.option("--max-summarize", type=int, default=0, help="最大总结论文数（默认：0表示无限制）")
@click.option("--categories", "-c", multiple=True, help="包含的分类（可多次使用）")
@click.option("--days-back", type=int, help="回溯天数（例如：30表示最近30天）")
@click.option("--authors", "-a", multiple=True, help="作者姓名（可多次使用）")
@click.option(
    "--sort-by",
    type=click.Choice(["published", "relevance_score", "title", "updated"]),
    default="published",
    help="排序字段",
)
def search(
    query, directory, limit, years_back, use_ai, summarize, max_summarize, categories, days_back, authors, sort_by
):
    """智能搜索论文（支持自然语言查询和基本过滤）"""
    directory = Path(directory).resolve()

    if not setup_environment(directory):
        sys.exit(1)

    print_banner()

    # 如果需要，先同步最新论文
    crawler = ArXivCrawler()
    if years_back > 0:
        click.echo(f"搜索前先同步最近 {years_back} 年论文...")
        sync_result = sync_papers(years_back=years_back, summarize=False, force=False)
        crawler = sync_result["crawler"]

    click.echo(f"\n正在搜索: '{query}'")
    click.echo("=" * 50)

    search_terms = [query]

    # 如果启用AI且配置了AI API密钥，尝试解析自然语言查询
    if use_ai and Config.AI_API_KEY:
        try:
            import openai

            client = openai.OpenAI(api_key=Config.AI_API_KEY, base_url=Config.AI_BASE_URL)

            ai_prompt = f"""
            用户正在搜索arXiv物理/计算材料科学论文，查询是: "{query}"
            
            请将自然语言查询转换为适合arXiv搜索的关键词或短语。
            
            重要规则：
            1. 如果查询已经是明确的搜索词（如"DeepH"、"deep learning Hamiltonian"、"DFT计算"），直接使用它，不要添加同义词
            2. 如果查询包含专业术语、缩写或专有名词，保持原样作为主要搜索词
            3. 仅当查询非常模糊或一般性时（如"机器学习在材料科学中的应用"），才生成1-2个相关关键词
            4. 优先保持查询的原始意图，不要添加不相关的关键词
            5. 对于英文查询，保持原样；对于中文查询，翻译为英文关键词
            考虑以下领域：凝聚态物理、密度泛函理论(DFT)、机器学习、力场、分子动力学、量子化学、计算材料科学。
            
            返回格式：JSON数组，包含1-2个搜索关键词/短语。
            示例：
            - 查询"DeepH": ["DeepH"]
            - 查询"deep learning Hamiltonian": ["deep learning Hamiltonian"]
            - 查询"DFT计算": ["DFT"]
            - 查询"分子动力学模拟": ["molecular dynamics simulation"]
            - 查询"机器学习在材料科学中的应用": ["machine learning materials science"]
            
            只返回JSON数组，不要其他文本。
            """

            response = client.chat.completions.create(
                model=Config.AI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是arXiv论文搜索助手，擅长识别专业术语并将自然语言查询转换为学术搜索关键词。",
                    },
                    {"role": "user", "content": ai_prompt},
                ],
                max_tokens=200,
                temperature=0.3,
            )

            ai_response = response.choices[0].message.content
            try:
                search_terms = json.loads(ai_response)
                if isinstance(search_terms, list) and len(search_terms) > 0:
                    click.echo(f"AI解析的搜索词: {', '.join(search_terms[:3])}")
                    if len(search_terms) > 3:
                        click.echo(f"  以及 {len(search_terms) - 3} 个其他关键词")
            except:
                # 如果AI响应不是有效JSON，使用原始查询
                pass

        except Exception as e:
            click.echo(f"AI解析失败，使用原始查询: {e}")

    # 在数据库中搜索
    with crawler.db.get_session() as session:
        from arxiv_pulse.models import Paper

        # 使用增强搜索引擎进行模糊搜索
        search_engine = SearchEngine(session)

        # 将搜索词合并为一个查询（搜索引擎会处理单词拆分和同义词扩展）
        combined_query = " ".join(search_terms)

        filter_config = SearchFilter(
            query=combined_query,
            search_fields=["title", "abstract"],
            categories=list(categories) if categories else None,
            authors=list(authors) if authors else None,
            author_match="contains",  # 默认使用包含匹配
            days_back=days_back,
            limit=limit * min(len(search_terms), 2),  # 扩大限制但最多2倍，避免过多结果
            sort_by=sort_by,
            sort_order="desc",
            match_all=True,  # AND逻辑：匹配所有搜索词
        )

        # 执行搜索
        papers_to_show = search_engine.search_papers(filter_config)

        # 确保不超过限制
        papers_to_show = papers_to_show[:limit]

        click.echo(f"找到 {len(papers_to_show)} 篇论文:")

        # 生成搜索报告
        click.echo("正在生成搜索报告...")
        files = generate_search_report(
            query,
            search_terms,
            papers_to_show,
            paper_limit=limit,
            summarize=summarize,
            max_summarize=max_summarize,
        )

        # 输出简要结果和报告文件
        for i, paper in enumerate(papers_to_show[:5], 1):  # 只显示前5篇作为预览
            authors = json.loads(paper.authors) if paper.authors else []
            author_names = [a.get("name", "") for a in authors[:2]]
            if len(authors) > 2:
                author_names.append("等")

            click.echo(f"\n{i}. {paper.title}")
            click.echo(f"   作者: {', '.join(author_names)}")
            click.echo(f"   arXiv ID: {paper.arxiv_id}")
            click.echo(f"   发布日期: {paper.published.strftime('%Y-%m-%d') if paper.published else 'N/A'}")

        if len(papers_to_show) > 5:
            click.echo(f"\n... 以及 {len(papers_to_show) - 5} 篇更多论文")

        click.echo(f"\n报告生成完成：")
        for f in files:
            click.echo(f"  - {f}")
        click.echo(f"\n详细论文信息、中文翻译和PDF链接请查看生成的Markdown报告。")


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--limit", default=50, help="报告中包含的最大论文数（默认：50）")
@click.option("--days-back", type=int, default=2, help="包含最近多少天的论文（默认：2天）")
@click.option("--years-back", type=int, default=1, help="报告前同步回溯的年数（默认：1年）")
@click.option("--summarize/--no-summarize", default=True, help="是否自动总结未总结的论文（默认：是）")
@click.option("--max-summarize", type=int, default=0, help="最大总结论文数（默认：0表示无限制）")
def recent(directory, limit, days_back, years_back, summarize, max_summarize):
    """生成最近论文的报告（先同步最新论文）"""
    directory = Path(directory).resolve()

    if not setup_environment(directory):
        sys.exit(1)

    print_banner()

    # 先同步论文
    if years_back > 0:
        click.echo(f"报告前先同步最近 {years_back} 年论文...")
        sync_papers(years_back=years_back, summarize=False, force=False)

    # 生成报告
    click.echo("\n" + "=" * 50)
    click.echo(f"正在生成最近 {days_back} 天论文报告...")

    files = generate_report(paper_limit=limit, days_back=days_back, summarize=summarize, max_summarize=max_summarize)

    click.echo(f"报告生成完成：")
    for f in files:
        click.echo(f"  - {f}")


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
def stat(directory):
    """显示数据库统计信息"""
    directory = Path(directory).resolve()

    if not setup_environment(directory):
        sys.exit(1)

    print_banner()

    crawler = ArXivCrawler()
    summarizer = PaperSummarizer()
    report_generator = ReportGenerator()

    click.echo("\n" + "=" * 50)
    click.echo("arXiv Pulse 数据库统计")
    click.echo("=" * 50)

    # 获取统计信息
    crawl_stats = crawler.get_crawler_stats()
    summary_stats = summarizer.get_summary_stats()

    # 显示基本统计
    click.echo(f"\n📊 基本统计:")
    click.echo(f"   总论文数: {crawl_stats['total_papers']}")
    click.echo(f"   今日论文: {crawl_stats['papers_today']}")
    click.echo(f"   已总结论文: {summary_stats['summarized_papers']}")
    click.echo(f"   总结率: {summary_stats['summarization_rate']:.1%}")

    # 按搜索查询统计
    click.echo(f"\n🔍 按搜索查询分布:")
    for query, count in crawl_stats["papers_by_query"].items():
        percentage = count / crawl_stats["total_papers"] * 100 if crawl_stats["total_papers"] > 0 else 0
        click.echo(f"   {query}: {count} 篇 ({percentage:.1f}%)")

    # 分类统计
    click.echo(f"\n📁 分类统计:")
    with crawler.db.get_session() as session:
        from arxiv_pulse.models import Paper
        import json

        papers = session.query(Paper).all()
        category_counts = {}

        for paper in papers:
            if paper.categories:
                for cat in paper.categories.split():
                    category_counts[cat] = category_counts.get(cat, 0) + 1

        # 按数量排序
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories[:10]:  # 显示前10个
            percentage = count / crawl_stats["total_papers"] * 100 if crawl_stats["total_papers"] > 0 else 0
            click.echo(f"   {category}: {count} 篇 ({percentage:.1f}%)")

        if len(sorted_categories) > 10:
            click.echo(f"   ... 以及 {len(sorted_categories) - 10} 个其他分类")

    # 时间分布
    click.echo(f"\n📅 时间分布:")
    with crawler.db.get_session() as session:
        # 按年统计
        year_stats = {}
        for paper in papers:
            if paper.published:
                year = paper.published.year
                year_stats[year] = year_stats.get(year, 0) + 1

        sorted_years = sorted(year_stats.items())
        for year, count in sorted_years[-5:]:  # 显示最近5年
            percentage = count / crawl_stats["total_papers"] * 100 if crawl_stats["total_papers"] > 0 else 0
            click.echo(f"   {year}年: {count} 篇 ({percentage:.1f}%)")

    # 总结统计
    pending_papers = crawl_stats["total_papers"] - summary_stats["summarized_papers"]
    click.echo(f"\n🤖 AI总结统计:")
    click.echo(f"   已总结: {summary_stats['summarized_papers']} 篇")
    click.echo(f"   待总结: {pending_papers} 篇")
    click.echo(f"   总结率: {summary_stats['summarization_rate']:.1%}")

    click.echo("\n" + "=" * 50)
    click.echo("统计完成 ✅")


if __name__ == "__main__":
    cli()
