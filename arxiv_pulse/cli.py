#!/usr/bin/env python3
"""
arXiv Pulse - 简化版命令行界面
核心功能：初始化、更新同步、智能搜索、最近论文报告
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import click
import openai
import questionary

from arxiv_pulse.__version__ import __version__
from arxiv_pulse.arxiv_crawler import ArXivCrawler
from arxiv_pulse.banner import generate_banner_title, print_banner, print_banner_custom
from arxiv_pulse.config import Config
from arxiv_pulse.environment import setup_environment
from arxiv_pulse.output_manager import OutputLevel, output
from arxiv_pulse.report_generator import ReportGenerator
from arxiv_pulse.research_fields import DEFAULT_BANNER_FIELDS, RESEARCH_FIELDS
from arxiv_pulse.search_engine import SearchEngine, SearchFilter
from arxiv_pulse.summarizer import PaperSummarizer
from arxiv_pulse.utils import get_workday_cutoff, parse_time_range


def sync_papers(years_back=1, summarize=False, force=False, arxiv_max_results=None):
    """同步论文（内部函数）"""
    crawler = ArXivCrawler()
    summarizer = PaperSummarizer()

    if arxiv_max_results is None:
        arxiv_max_results = Config.ARXIV_MAX_RESULTS

    sync_description = crawler.get_sync_description(years_back, force)

    mode_text = "强制同步" if force else "同步缺失论文"
    click.echo(f"正在{mode_text}（{sync_description}，最大 {arxiv_max_results} 篇）...")
    click.echo("=" * 50)

    click.echo("1. 正在同步搜索查询...")
    sync_result = crawler.sync_all_queries(years_back=years_back, force=force, arxiv_max_results=arxiv_max_results)
    result_text = "处理了" if force else "添加了"
    click.echo(f"   从查询{result_text} {sync_result['total_new_papers']} 篇论文")

    click.echo("2. 正在同步重要论文...")
    important_result = crawler.sync_important_papers()
    click.echo(f"   添加了 {important_result['added']} 篇重要论文")
    if important_result["errors"]:
        click.echo(f"   错误: {len(important_result['errors'])}")

    total_new = sync_result["total_new_papers"] + important_result["added"]
    if summarize and total_new > 0:
        click.echo("3. 正在总结新论文...")
        summarize_result = summarizer.summarize_pending_papers(limit=min(64, total_new))
        click.echo(f"   已总结 {summarize_result['successful']} 篇论文")
    elif total_new > 0:
        click.echo("3. 跳过论文总结")
    else:
        click.echo("3. 没有新论文需要总结")

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


def generate_report(paper_limit=64, days_back=2, summarize=True, max_summarize=10, cache=True):
    """生成最近论文的报告（内部函数）"""
    reporter = ReportGenerator()
    reporter.use_cache = cache

    original_limit = Config.REPORT_MAX_PAPERS
    Config.REPORT_MAX_PAPERS = paper_limit

    try:
        with reporter.db.get_session() as session:
            from arxiv_pulse.models import Paper

            cutoff = get_workday_cutoff(days_back)
            recent_papers = (
                session.query(Paper)
                .filter(Paper.published >= cutoff)
                .order_by(Paper.published.desc())
                .limit(paper_limit)
                .all()
            )

            summarizer = PaperSummarizer()

            category_counts = {}
            for paper in recent_papers:
                if paper.categories is not None:
                    for cat in paper.categories.split():
                        category_counts[cat] = category_counts.get(cat, 0) + 1

            top_categories = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5])

            crawler = ArXivCrawler()
            crawl_stats = crawler.get_crawler_stats()
            summary_stats = summarizer.get_summary_stats()

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
                    "summarize": summarize,
                    "max_summarize": max_summarize,
                },
                "papers": recent_papers,
            }

        files = []
        md_file = reporter.save_markdown_report(report_data)
        if md_file:
            files.append(md_file)

        csv_file = reporter.save_csv_report(report_data)
        if csv_file:
            files.append(csv_file)

        return files
    finally:
        Config.REPORT_MAX_PAPERS = original_limit


def generate_search_report(query, search_terms, papers, paper_limit=64, summarize=True, max_summarize=10, cache=True):
    """生成搜索结果的报告（内部函数）"""
    reporter = ReportGenerator()
    reporter.use_cache = cache

    if not papers:
        output.info("未找到论文，跳过报告生成")
        return []

    original_limit = Config.REPORT_MAX_PAPERS
    Config.REPORT_MAX_PAPERS = paper_limit

    try:
        summarizer = PaperSummarizer()

        category_counts = {}
        for paper in papers:
            if paper.categories is not None:
                for cat in paper.categories.split():
                    category_counts[cat] = category_counts.get(cat, 0) + 1

        top_categories = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5])

        crawler = ArXivCrawler()
        crawl_stats = crawler.get_crawler_stats()
        summary_stats = summarizer.get_summary_stats()

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
                "summarize": summarize,
                "max_summarize": max_summarize,
            },
            "papers": papers,
        }

        files = []
        md_file = reporter.save_markdown_report(report_data)
        if md_file:
            files.append(md_file)

        csv_file = reporter.save_csv_report(report_data)
        if csv_file:
            files.append(csv_file)

        return files
    finally:
        Config.REPORT_MAX_PAPERS = original_limit


def interactive_configuration():
    """交互式配置 arXiv Pulse"""
    config = {}

    click.echo("\n" + "=" * 60)
    click.echo("arXiv Pulse 交互式配置向导")
    click.echo("=" * 60)

    click.echo("\n🔧 AI API 配置")
    click.echo("-" * 40)

    ai_base_url = click.prompt("AI API Base URL", default="https://llmapi.paratera.com", show_default=True)
    config["AI_BASE_URL"] = ai_base_url

    ai_api_key = click.prompt(
        "请输入 AI API 密钥 (留空则跳过，稍后可在 .env 文件中添加)", default="", show_default=False, hide_input=True
    )
    if ai_api_key:
        config["AI_API_KEY"] = ai_api_key
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

    if available_models:
        click.echo("\n可用模型列表:")

        choices = []
        for model in available_models:
            choices.append(questionary.Choice(title=model, value=model))

        choices.append(questionary.Choice(title="[自定义输入] - 输入其他模型名称", value="__custom_input__"))

        selected_model = questionary.select(
            "请选择AI模型（使用上下箭头导航，回车确认）:", choices=choices, instruction="(上下箭头导航，回车确认)"
        ).ask()

        if selected_model == "__custom_input__":
            ai_model = click.prompt("请输入自定义模型名称", default="DeepSeek-V3.2-Thinking", show_default=True)
            click.echo(f"✅ 使用自定义模型: {ai_model}")
        else:
            ai_model = selected_model
            click.echo(f"✅ 已选择模型: {ai_model}")
    else:
        ai_model = click.prompt("AI 模型名称", default="DeepSeek-V3.2-Thinking", show_default=True)

    config["AI_MODEL"] = ai_model

    click.echo("\n📊 爬虫配置")
    click.echo("-" * 40)

    arxiv_max_results = click.prompt("arXiv API 最大返回论文数", default=10000, type=int, show_default=True)
    config["ARXIV_MAX_RESULTS"] = str(arxiv_max_results)

    years_back = click.prompt("初始同步回溯的年数", default=5, type=int, show_default=True)
    config["YEARS_BACK"] = str(years_back)

    click.echo("\n🎯 选择您的研究领域")
    click.echo("-" * 40)
    click.echo("请使用上下箭头导航，空格键选择/取消，回车确认（可多选）：")

    research_fields = RESEARCH_FIELDS

    choices = []
    for key, field in research_fields.items():
        title = f"[{field['name']}] - {field['description']}"
        choices.append(
            questionary.Choice(
                title=title,
                value=key,
                checked=False,
            )
        )

    choices.insert(0, questionary.Choice(title="[全选] - 选择所有研究领域", value="__select_all__", checked=False))

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

    if "__select_all__" in selected_keys:
        for field in research_fields.values():
            selected_queries.append(field["query"])
            selected_field_names.append(field["name"])
        click.echo("✅ 已选择全部研究领域")
    else:
        for key in selected_keys:
            if key in research_fields:
                field = research_fields[key]
                selected_queries.append(field["query"])
                selected_field_names.append(field["name"])
                click.echo(f"✅ 已选择: {field['name']}")
            else:
                click.echo(f"⚠️  未知的领域ID: {key}")

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

    num_selected_fields = len(selected_field_names)
    click.echo(f"\n📊 智能建议（基于您选择的 {num_selected_fields} 个研究领域）")
    click.echo("-" * 40)

    recommended_max_results = 0
    if num_selected_fields <= 6:
        click.echo("✅ 您选择了少量领域，保持默认配置即可。")
        recommended_max_results = 10000
    elif num_selected_fields <= 10:
        recommended_max_results = 4000
        click.echo("⚠️  您选择了中等数量领域，建议调整 ARXIV_MAX_RESULTS：")
        click.echo(f"   - arXiv API 最大返回论文数: {recommended_max_results}")
    else:
        recommended_max_results = 1000
        click.echo(f"⚠️  您选择了大量领域 ({num_selected_fields}个)，强烈建议调整 ARXIV_MAX_RESULTS：")
        click.echo(f"   - arXiv API 最大返回论文数: {recommended_max_results}")
        click.echo("   - 注意：同步大量领域可能需要较长时间和更多存储空间。")

    if num_selected_fields > 6:
        if click.confirm("\n💡 是否应用上述建议调整 ARXIV_MAX_RESULTS？", default=True):
            config["ARXIV_MAX_RESULTS"] = str(recommended_max_results)
            click.echo(f"✅ 已应用建议配置：ARXIV_MAX_RESULTS={recommended_max_results}")
        else:
            click.echo("ℹ️  保持您原有的 ARXIV_MAX_RESULTS 配置。")

    click.echo("\n📄 报告配置")
    click.echo("-" * 40)

    report_max_papers = click.prompt("每份报告显示的最大论文数", default=64, type=int, show_default=True)
    config["REPORT_MAX_PAPERS"] = str(report_max_papers)

    click.echo("\n✅ 配置完成！")
    return config, int(years_back)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--verbose", "-v", is_flag=True, help="显示详细输出（包括调试信息）")
@click.version_option(version=__version__, prog_name="arXiv Pulse")
def cli(verbose):
    """arXiv Pulse: 智能arXiv文献追踪和分析系统"""
    if verbose:
        output.set_min_level(OutputLevel.DEBUG)


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
def init(directory):
    """初始化目录并同步历史论文"""
    directory = Path(directory).resolve()

    (directory / "data").mkdir(exist_ok=True)
    (directory / "reports").mkdir(exist_ok=True)

    env_file = directory / ".env"
    custom_banner_fields = None

    if not env_file.exists():
        config, years_back = interactive_configuration()

        custom_banner_fields = config.get("_SELECTED_FIELD_NAMES", [])

        template_file = Path(__file__).parent / ".ENV.TEMPLATE"
        if not template_file.exists():
            click.echo(f"❌ 找不到模板文件: {template_file}")
            click.echo("请确保 .ENV.TEMPLATE 文件存在于 arxiv_pulse 目录中")
            return

        env_content = template_file.read_text(encoding="utf-8")

        timestamp_comment = f"# 由交互式配置向导于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 生成\n"
        lines = env_content.split("\n")
        if lines and lines[0].startswith("#"):
            lines.insert(1, timestamp_comment)
        else:
            lines.insert(0, timestamp_comment)
        env_content = "\n".join(lines)

        lines = env_content.split("\n")

        for i, line in enumerate(lines):
            if line.strip().startswith("AI_API_KEY="):
                lines[i] = f"AI_API_KEY={config.get('AI_API_KEY', 'your_api_key_here')}"
                break

        for i, line in enumerate(lines):
            if line.strip().startswith("AI_MODEL="):
                lines[i] = f"AI_MODEL={config.get('AI_MODEL', 'DeepSeek-V3.2-Thinking')}"
                break

        for i, line in enumerate(lines):
            if line.strip().startswith("AI_BASE_URL="):
                lines[i] = f"AI_BASE_URL={config.get('AI_BASE_URL', 'https://llmapi.paratera.com')}"
                break

        for i, line in enumerate(lines):
            if line.strip().startswith("ARXIV_MAX_RESULTS="):
                lines[i] = f"ARXIV_MAX_RESULTS={config.get('ARXIV_MAX_RESULTS', '10000')}"
                break

        default_search_queries = 'condensed matter physics AND cat:cond-mat.*; (ti:"density functional" OR abs:"density functional") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci OR cat:physics.chem-ph); (ti:"machine learning" OR abs:"machine learning") AND (cat:physics.comp-ph OR cat:cond-mat.mtrl-sci OR cat:physics.chem-ph)'
        for i, line in enumerate(lines):
            if line.strip().startswith("SEARCH_QUERIES="):
                lines[i] = f"SEARCH_QUERIES={config.get('SEARCH_QUERIES', default_search_queries)}"
                break

        for i, line in enumerate(lines):
            if line.strip().startswith("REPORT_MAX_PAPERS="):
                lines[i] = f"REPORT_MAX_PAPERS={config.get('REPORT_MAX_PAPERS', '64')}"
                break

        for i, line in enumerate(lines):
            if line.strip().startswith("YEARS_BACK="):
                lines[i] = f"YEARS_BACK={config.get('YEARS_BACK', '5')}"
                break

        env_content = "\n".join(lines)

        env_file.write_text(env_content)
        click.echo(f"\n✅ 已在 {directory} 创建 .env 配置文件")

    else:
        click.echo(f".env 文件已存在于 {directory}")
        years_back = Config.YEARS_BACK

    important_file = directory / Config.IMPORTANT_PAPERS_FILE
    important_file.parent.mkdir(parents=True, exist_ok=True)
    if not important_file.exists():
        important_file.write_text("# 在此添加重要论文的arXiv ID，每行一个\n")
        click.echo(f"✅ 已创建重要论文文件: {important_file}")

    if not setup_environment(directory):
        click.echo("❌ 配置验证失败，请检查 .env 文件")
        sys.exit(1)

    click.echo("\n" + "=" * 60)
    click.echo("准备同步数据库")
    click.echo("=" * 60)
    click.echo(f"即将开始初始同步，回溯 {years_back} 年历史论文...")
    click.echo("这可能会花费一些时间，具体取决于您选择的领域数量。")
    click.echo("您可以在任何时候按 Ctrl+C 中断同步。")

    if not click.confirm("\n🚀 确认开始同步数据库吗？", default=True):
        click.echo("❌ 已取消同步")
        sys.exit(0)

    click.echo(f"\n⏳ 开始初始同步，回溯 {years_back} 年历史论文...")
    sync_result = sync_papers(years_back=years_back, summarize=False)

    if custom_banner_fields:
        banner_title = custom_banner_fields[:4]
    else:
        banner_title = generate_banner_title(env_file)
    print_banner_custom(banner_title)

    click.echo("\n🎉 arXiv Pulse 初始化完成！")
    click.echo("\n📁 文件位置：")
    click.echo(f"  配置文件: {env_file}")
    click.echo(f"  数据库: {directory}/data/arxiv_papers.db")
    click.echo(f"  报告目录: {directory}/reports/")
    click.echo("\n🚀 下一步：")
    click.echo(f"  1. 运行 'pulse sync {directory}' 更新最新论文")
    click.echo(f"  2. 运行 'pulse search \"关键词\" {directory}' 搜索论文")
    click.echo(f"  3. 运行 'pulse recent {directory}' 查看最近论文报告")
    click.echo(f"  4. 编辑 {important_file} 添加重要论文")


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--years-back", type=int, default=None, help="同步回溯的年数（默认：5年）")
@click.option("--force", is_flag=True, default=False, help="强制同步：继续查询，跳过已存在的论文")
@click.option(
    "--arxiv-max-results", type=int, default=None, help="arXiv API 最大返回论文数（默认：ARXIV_MAX_RESULTS配置）"
)
def sync(directory, years_back, force, arxiv_max_results):
    """同步最新论文到数据库

    普通模式（无 --force）: 按时间从近到早同步，遇到已存在的论文立即停止。
    强制模式（--force）: 继续查询，跳过已存在的论文，用于扩展数据库。

    注意: 无论是否使用 --force，都不会下载已存在的论文。
    """
    directory = Path(directory).resolve()
    click.echo(f"正在同步 arXiv Pulse 于 {directory}")

    if not setup_environment(directory):
        sys.exit(1)

    print_banner()

    if years_back is None:
        years_back = Config.YEARS_BACK
        click.echo(f"使用默认回溯年数: {years_back} 年")

    if arxiv_max_results is None:
        arxiv_max_results = Config.ARXIV_MAX_RESULTS
        click.echo(f"使用 ARXIV_MAX_RESULTS 配置: {arxiv_max_results}")

    sync_result = sync_papers(years_back=years_back, summarize=False, force=force, arxiv_max_results=arxiv_max_results)

    click.echo("\n" + "=" * 50)
    click.echo("同步完成！数据库已更新。")


@cli.command()
@click.argument("query")
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--limit", default=64, help="返回结果的最大数量（默认：64）")
@click.option("--update/--no-update", default=False, help="搜索前是否更新数据库（默认：否，是则使用YEARS_BACK配置）")
@click.option(
    "--time-range", "-t", default="0", help="搜索时间范围，如'1y'=1年、'6m'=6个月、'30d'=30天（默认：0，表示不限制）"
)
@click.option("--categories", "-c", multiple=True, help="包含的分类（可多次使用）")
@click.option("--authors", "-a", multiple=True, help="作者姓名（可多次使用）")
@click.option(
    "--sort-by",
    type=click.Choice(["published", "relevance_score", "title", "updated"]),
    default="published",
    help="排序字段",
)
@click.option("--no-cache", is_flag=True, default=False, help="禁用图片URL缓存")
def search(
    query,
    directory,
    limit,
    update,
    time_range,
    categories,
    authors,
    sort_by,
    no_cache,
):
    """智能搜索论文（支持自然语言查询和基本过滤）"""
    directory = Path(directory).resolve()

    if not setup_environment(directory):
        sys.exit(1)

    print_banner()

    crawler = ArXivCrawler()

    if update:
        years_back = Config.YEARS_BACK
        sync_result = sync_papers(years_back=years_back, summarize=False, force=False)

    click.echo(f"\n正在搜索: '{query}'")
    click.echo("=" * 50)

    search_terms = [query]

    if Config.AI_API_KEY:
        try:
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
                if ai_response:
                    search_terms = json.loads(ai_response)
                    if isinstance(search_terms, list) and len(search_terms) > 0:
                        click.echo(f"AI解析的搜索词: {', '.join(search_terms[:3])}")
                        if len(search_terms) > 3:
                            click.echo(f"  以及 {len(search_terms) - 3} 个其他关键词")
            except:
                pass

        except Exception as e:
            click.echo(f"AI解析失败，使用原始查询: {e}")

    with crawler.db.get_session() as session:
        search_engine = SearchEngine(session)

        days_back = parse_time_range(time_range)
        if days_back > 0:
            click.echo(f"搜索时间范围: 最近 {days_back} 天")

        phrases = []
        if len(search_terms) == 1 and "," in search_terms[0]:
            phrases = [phrase.strip() for phrase in search_terms[0].split(",") if phrase.strip()]
        else:
            phrases = search_terms

        if len(phrases) == 1:
            combined_query = phrases[0]
            filter_config = SearchFilter(
                query=combined_query,
                search_fields=["title", "abstract"],
                categories=list(categories) if categories else None,
                authors=list(authors) if authors else None,
                author_match="contains",
                days_back=days_back,
                limit=limit * min(len(phrases), 2),
                sort_by=sort_by,
                sort_order="desc",
                match_all=True,
            )
            papers_to_show = search_engine.search_papers(filter_config)
        else:
            all_papers = []
            for phrase in phrases:
                filter_config = SearchFilter(
                    query=phrase,
                    search_fields=["title", "abstract"],
                    categories=list(categories) if categories else None,
                    authors=list(authors) if authors else None,
                    author_match="contains",
                    days_back=days_back,
                    limit=limit * 2,
                    sort_by=sort_by,
                    sort_order="desc",
                    match_all=True,
                )
                phrase_papers = search_engine.search_papers(filter_config)
                all_papers.extend(phrase_papers)

            seen_ids = set()
            papers_to_show = []
            for paper in all_papers:
                if paper.arxiv_id not in seen_ids:
                    seen_ids.add(paper.arxiv_id)
                    papers_to_show.append(paper)

            papers_to_show.sort(key=lambda p: p.published if p.published else datetime.min, reverse=True)

        papers_to_show = papers_to_show[:limit]

        click.echo(f"找到 {len(papers_to_show)} 篇论文:")

        click.echo("正在生成搜索报告...")
        files = generate_search_report(
            query,
            search_terms,
            papers_to_show,
            paper_limit=limit,
            summarize=Config.AI_API_KEY is not None,
            max_summarize=0,
            cache=not no_cache,
        )

        for i, paper in enumerate(papers_to_show[:5], 1):
            authors_list = json.loads(paper.authors) if paper.authors is not None else []
            author_names = [a.get("name", "") for a in authors_list[:2]]
            if len(authors_list) > 2:
                author_names.append("等")

            click.echo(f"\n{i}. {paper.title}")
            click.echo(f"   作者: {', '.join(author_names)}")
            click.echo(f"   arXiv ID: {paper.arxiv_id}")
            click.echo(f"   发布日期: {paper.published.strftime('%Y-%m-%d') if paper.published is not None else 'N/A'}")

        if len(papers_to_show) > 5:
            click.echo(f"\n... 以及 {len(papers_to_show) - 5} 篇更多论文")

        click.echo(f"\n报告生成完成：")
        for f in files:
            click.echo(f"  - {f}")
        click.echo(f"\n详细论文信息、中文翻译和PDF链接请查看生成的Markdown报告。")


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--limit", default=64, help="报告中包含的最大论文数（默认：64，与REPORT_MAX_PAPERS配置一致）")
@click.option(
    "--days-back", "-d", type=int, default=2, help="包含最近多少天的工作日论文（默认：2天，0表示不更新数据库）"
)
@click.option("--no-cache", is_flag=True, default=False, help="禁用图片URL缓存")
def recent(directory, limit, days_back, no_cache):
    """生成最近论文的报告（先同步最新论文）"""
    directory = Path(directory).resolve()

    if not setup_environment(directory):
        sys.exit(1)

    print_banner()

    if days_back > 0:
        years_back = Config.YEARS_BACK
        sync_papers(years_back=years_back, summarize=False, force=False)

    click.echo("\n" + "=" * 50)
    click.echo(f"正在生成最近 {days_back} 天论文报告...")

    files = generate_report(
        paper_limit=limit,
        days_back=days_back,
        summarize=Config.AI_API_KEY is not None,
        max_summarize=0,
        cache=not no_cache,
    )

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

    crawl_stats = crawler.get_crawler_stats()
    summary_stats = summarizer.get_summary_stats()

    click.echo(f"\n📊 基本统计:")
    click.echo(f"   总论文数: {crawl_stats['total_papers']}")
    click.echo(f"   今日论文: {crawl_stats['papers_today']}")
    click.echo(f"   已总结论文: {summary_stats['summarized_papers']}")
    click.echo(f"   总结率: {summary_stats['summarization_rate']:.1%}")

    click.echo(f"\n🔍 按搜索查询分布:")
    for query, count in crawl_stats["papers_by_query"].items():
        percentage = count / crawl_stats["total_papers"] * 100 if crawl_stats["total_papers"] > 0 else 0
        click.echo(f"   {query}: {count} 篇 ({percentage:.1f}%)")

    click.echo(f"\n📁 分类统计:")
    with crawler.db.get_session() as session:
        from arxiv_pulse.models import Paper

        papers = session.query(Paper).all()
        category_counts = {}

        for paper in papers:
            if paper.categories is not None and paper.categories:
                categories = [cat.strip().rstrip(",") for cat in paper.categories.split(",")]
                unique_cats = set(cat for cat in categories if cat)
                for cat in unique_cats:
                    category_counts[cat] = category_counts.get(cat, 0) + 1

        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        for category, count in sorted_categories[:10]:
            percentage = count / crawl_stats["total_papers"] * 100 if crawl_stats["total_papers"] > 0 else 0
            click.echo(f"   {category}: {count} 篇 ({percentage:.1f}%)")

        if len(sorted_categories) > 10:
            click.echo(f"   ... 以及 {len(sorted_categories) - 10} 个其他分类")

    click.echo(f"\n📅 时间分布:")
    with crawler.db.get_session() as session:
        year_stats = {}
        for paper in papers:
            if paper.published is not None:
                year = paper.published.year
                year_stats[year] = year_stats.get(year, 0) + 1

        sorted_years = sorted(year_stats.items())
        for year, count in sorted_years[-5:]:
            percentage = count / crawl_stats["total_papers"] * 100 if crawl_stats["total_papers"] > 0 else 0
            click.echo(f"   {year}年: {count} 篇 ({percentage:.1f}%)")

    pending_papers = crawl_stats["total_papers"] - summary_stats["summarized_papers"]
    click.echo(f"\n🤖 AI总结统计:")
    click.echo(f"   已总结: {summary_stats['summarized_papers']} 篇")
    click.echo(f"   待总结: {pending_papers} 篇")
    click.echo(f"   总结率: {summary_stats['summarization_rate']:.1%}")

    click.echo("\n" + "=" * 50)
    click.echo("统计完成 ✅")


if __name__ == "__main__":
    cli()
