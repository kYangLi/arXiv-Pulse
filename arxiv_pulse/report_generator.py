import json
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import logging
import os

from arxiv_pulse.models import Database, Paper
from arxiv_pulse.config import Config
from arxiv_pulse.output_manager import output

# 使用根日志记录器的配置（保留用于向后兼容）
logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self):
        self.db = Database()
        self.config = Config
        self.total_tokens_used = 0  # 总token使用量
        self.total_cost = 0.0  # 总费用（元）
        self.token_price_per_million = Config.TOKEN_PRICE_PER_MILLION  # 每百万token价格，可从配置覆盖
        self.summary_sentences_limit = Config.SUMMARY_SENTENCES_LIMIT  # 摘要句子数限制

        # 抑制第三方库的详细日志
        import logging

        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        # arXiv分类解释映射
        self.category_explanations = {
            # Computer Science
            "cs.AI": "人工智能 (Artificial Intelligence)",
            "cs.CL": "计算语言学 (Computation and Language)",
            "cs.CR": "密码学与安全 (Cryptography and Security)",
            "cs.CV": "计算机视觉 (Computer Vision)",
            "cs.LG": "机器学习 (Machine Learning)",
            "cs.NE": "神经网络 (Neural and Evolutionary Computing)",
            "cs.SE": "软件工程 (Software Engineering)",
            "cs.PL": "编程语言 (Programming Languages)",
            "cs.DC": "分布式计算 (Distributed, Parallel, and Cluster Computing)",
            "cs.DS": "数据结构与算法 (Data Structures and Algorithms)",
            "cs.IT": "信息论 (Information Theory)",
            "cs.SY": "系统与控制 (Systems and Control)",
            # Physics
            "cond-mat": "凝聚态物理 (Condensed Matter)",
            "cond-mat.mtrl-sci": "材料科学 (Materials Science)",
            "cond-mat.str-el": "强关联电子系统 (Strongly Correlated Electrons)",
            "cond-mat.supr-con": "超导 (Superconductivity)",
            "cond-mat.mes-hall": "介观系统与量子霍尔效应 (Mesoscopic Systems and Quantum Hall Effect)",
            "cond-mat.soft": "软凝聚态物质 (Soft Condensed Matter)",
            "cond-mat.dis-nn": "无序系统与神经网络 (Disordered Systems and Neural Networks)",
            "cond-mat.stat-mech": "统计力学 (Statistical Mechanics)",
            "cond-mat.quant-gas": "量子气体 (Quantum Gases)",
            # Physics other
            "physics": "物理学 (Physics)",
            "physics.comp-ph": "计算物理 (Computational Physics)",
            "physics.chem-ph": "化学物理 (Chemical Physics)",
            "physics.data-an": "数据分析 (Data Analysis, Statistics and Probability)",
            "physics.ins-det": "仪器与探测器 (Instrumentation and Detectors)",
            # Mathematics
            "math": "数学 (Mathematics)",
            "math.NA": "数值分析 (Numerical Analysis)",
            "math.OC": "优化与控制 (Optimization and Control)",
            "math.ST": "统计 (Statistics)",
            # Quantitative Biology
            "q-bio": "定量生物学 (Quantitative Biology)",
            "q-bio.BM": "生物分子 (Biomolecules)",
            "q-bio.QM": "定量方法 (Quantitative Methods)",
            # Quantitative Finance
            "q-fin": "定量金融 (Quantitative Finance)",
            # Statistics
            "stat": "统计学 (Statistics)",
            "stat.ML": "机器学习 (Machine Learning)",
            "stat.AP": "应用 (Applications)",
            "stat.CO": "计算 (Computation)",
            "stat.ME": "方法学 (Methodology)",
            "stat.OT": "其他 (Other)",
            "stat.TH": "理论 (Theory)",
        }

    def get_category_explanation(self, category_code: str) -> str:
        """获取分类代码的解释"""
        # 处理可能的多个分类
        categories = [c.strip() for c in category_code.split(",")]
        explanations = []

        for cat in categories:
            # 处理主分类，如cond-mat.mtrl-sci
            if cat in self.category_explanations:
                explanations.append(self.category_explanations[cat])
            else:
                # 尝试匹配主分类前缀
                main_cat = cat.split(".")[0] if "." in cat else cat
                if main_cat in self.category_explanations:
                    explanations.append(f"{cat} ({self.category_explanations[main_cat].split('(')[0]})")
                else:
                    explanations.append(cat)

        return "; ".join(explanations)

    def clean_json_response(self, text):
        """清理AI响应中的JSON代码块标记"""
        import re

        if not text:
            return text
        # 移除 ```json 和 ``` 标记
        text = text.strip()
        # 匹配 ```json ... ``` 模式
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        # 匹配 ``` ... ``` 模式（没有json标签）
        code_match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        # 如果以 ```json 开头但没有闭合
        if text.startswith("```json"):
            text = text[7:].strip()
        if text.startswith("```"):
            text = text[3:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        return text

    def calculate_relevance_score(self, paper) -> int:
        """计算论文相关度评级 (1-5星)"""
        # 基于搜索查询和分类的评分
        query = paper.search_query or ""
        categories = paper.categories or ""

        # 核心研究领域 (凝聚态物理、DFT、力场等)
        core_domains = [
            "condensed matter physics",
            "density functional theory",
            "first principles calculation",
            "force fields",
            "molecular dynamics",
            "computational materials science",
            "quantum chemistry",
        ]

        # 相关领域 (机器学习等)
        related_domains = ["machine learning"]

        # 目标分类 (凝聚态物理、计算物理等)
        target_categories = [
            "cond-mat",  # 凝聚态物理
            "physics.comp-ph",  # 计算物理
            "physics.chem-ph",  # 化学物理
            "quant-ph",  # 量子物理
        ]

        # 相关分类 (机器学习、人工智能)
        related_categories = [
            "cs.ai",
            "cs.lg",
            "stat.ml",
            "cs.ne",  # 机器学习
            "physics.data-an",  # 数据分析
        ]

        # 不相关分类 (网络安全、其他CS领域)
        unrelated_categories = [
            "cs.cr",  # 密码学与安全
            "cs.pl",  # 编程语言
            "cs.se",  # 软件工程
            "cs.cv",  # 计算机视觉 (除非明确相关)
            "cs.cl",  # 计算语言学
        ]

        query_lower = query.lower()
        categories_lower = categories.lower()

        # 评分逻辑
        score = 3  # 默认3星

        # 1. 检查搜索查询
        for domain in core_domains:
            if domain in query_lower:
                score += 2  # 核心领域加分
                break

        for domain in related_domains:
            if domain in query_lower:
                score += 1  # 相关领域加分
                break

        # 2. 检查分类匹配
        # 如果分类与目标领域匹配
        if any(cat in categories_lower for cat in target_categories):
            score += 2

        # 如果分类与相关领域匹配
        elif any(cat in categories_lower for cat in related_categories):
            score += 1

        # 如果分类明显不相关
        if any(cat in categories_lower for cat in unrelated_categories):
            score -= 1

        # 3. 特殊情况：搜索查询是计算材料科学但分类是CS领域
        if "computational materials science" in query_lower and any(
            cat in categories_lower for cat in unrelated_categories
        ):
            score = max(2, score - 1)  # 降低评分

        # 确保分数在1-5之间
        return max(1, min(5, score))

    def _truncate_to_sentences(self, text: str, max_sentences: Optional[int] = None) -> str:
        """将文本截断为指定数量的句子（支持中英文）"""
        if not text:
            return ""

        if max_sentences is None:
            max_sentences = self.summary_sentences_limit

        import re

        # 支持中英文句子分隔符：句号、问号、感叹号、分号、省略号
        # 英文: . ? ! ; ... 中文: 。！？；…
        pattern = r"([。！？；…\.\?!;]+|\.{3,})"
        parts = re.split(pattern, text)

        sentences = []
        current = ""
        for i, part in enumerate(parts):
            current += part
            if i % 2 == 1:  # 分隔符部分
                sentences.append(current)
                current = ""

        # 如果最后还有未结束的句子
        if current:
            sentences.append(current)

        # 如果分割失败，按长度简单截断
        if len(sentences) == 0:
            return text[:200] + "..." if len(text) > 200 else text

        # 取前max_sentences句
        result = "".join(sentences[:max_sentences])

        # 如果截断后比原文本短很多，添加省略号
        if len(result) < len(text) * 0.8:
            # 移除末尾的句子分隔符，添加省略号
            result = result.rstrip("。！？；….?!;") + "…"

        return result

    def translate_text(self, text: str, target_lang: str = "zh") -> str:
        """使用DeepSeek或OpenAI API翻译文本，优先使用缓存"""
        if not text or not text.strip():
            return ""

        try:
            import openai

            # 1. 检查缓存
            cached_translation = self.db.get_translation_cache(text, target_lang)
            if cached_translation:
                output.info(f"✓ 缓存命中 ({len(text)} 字符)")
                return cached_translation

            # 2. 使用DeepSeek
            if Config.AI_API_KEY:
                translated = self._translate_with_deepseek(text, target_lang)
                # 3. 存储到缓存
                if translated and not translated.startswith("*"):
                    self.db.set_translation_cache(text, translated, target_lang)
                return translated
            else:
                return "*翻译需要配置DeepSeek API密钥*"

        except ImportError:
            return "*需要安装openai库*"
        except Exception as e:
            output.error("翻译文本失败", details={"exception": str(e)})
            return f"*翻译出错: {str(e)[:100]}*"

    def _translate_with_deepseek(self, text: str, target_lang: str = "zh") -> str:
        """使用DeepSeek API翻译文本"""
        import openai

        # 配置DeepSeek (openai 2.x版本)
        client = openai.OpenAI(api_key=Config.AI_API_KEY, base_url=Config.AI_BASE_URL)

        # 如果文本太长，截断（API有token限制）
        max_chars = 3000
        if len(text) > max_chars:
            text_to_translate = text[:max_chars] + "... [文本过长，已截断]"
        else:
            text_to_translate = text

        # 准备翻译提示
        if target_lang == "zh":
            system_prompt = "你是一个专业的翻译助手。将以下英文文本翻译成中文，保持专业术语准确，语言流畅。"
        else:
            system_prompt = f"你是一个专业的翻译助手。将以下文本翻译成{target_lang}，保持专业术语准确，语言流畅。"

        try:
            response = client.chat.completions.create(
                model=Config.AI_MODEL or "DeepSeek-V3.2-Thinking",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_to_translate},
                ],
                max_tokens=min(2000, len(text_to_translate) // 2),
                temperature=0.3,
            )

            # 记录token使用情况并更新统计
            if hasattr(response, "usage") and response.usage:
                usage = response.usage
                current_tokens = usage.total_tokens
                self.total_tokens_used += current_tokens

                # DeepSeek实际价格：输入0.14元/百万token，输出0.28元/百万token
                # 如果用户指定了价格则使用用户价格，否则使用实际价格
                if self.token_price_per_million is not None:
                    # 使用用户指定的统一价格
                    cost = (current_tokens / 1_000_000) * self.token_price_per_million
                else:
                    # 使用DeepSeek实际价格
                    input_cost = (usage.prompt_tokens / 1_000_000) * 0.14
                    output_cost = (usage.completion_tokens / 1_000_000) * 0.28
                    cost = input_cost + output_cost

                # 更新累计总费用
                self.total_cost += cost
                total_cost_formatted = f"{self.total_cost:.4f}"
                output.info(
                    f"✓ 翻译完成 | 本次: {current_tokens} tokens ({cost:.4f}¥) | 累计: {self.total_tokens_used} tokens (¥{total_cost_formatted})"
                )
            else:
                # 估算token使用（约4字符/1token）
                estimated_tokens = len(text) // 4 + 500  # 基础估计
                self.total_tokens_used += estimated_tokens
                # 计算当前批次费用
                price_per_million = (
                    self.token_price_per_million if self.token_price_per_million is not None else 0.21
                )  # DeepSeek平均价格
                current_cost = (estimated_tokens / 1_000_000) * price_per_million
                self.total_cost += current_cost
                total_cost_formatted = f"{self.total_cost:.4f}"
                output.info(
                    f"✓ 翻译完成 | 本次: ~{estimated_tokens} tokens ({current_cost:.4f}¥) | 累计: {self.total_tokens_used} tokens (¥{total_cost_formatted})"
                )

            translated = response.choices[0].message.content
            return translated.strip() if translated else ""

        except Exception as e:
            output.error("DeepSeek翻译失败", details={"exception": str(e)})
            raise e

    def generate_daily_report(self) -> Dict[str, Any]:
        """Generate daily report of new papers"""
        output.do("生成每日报告")

        with self.db.get_session() as session:
            # Get papers from last 24 hours
            cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
            new_papers = (
                session.query(Paper)
                .filter(Paper.created_at >= cutoff)
                .order_by(Paper.published.desc())
                .limit(self.config.REPORT_MAX_PAPERS)
                .all()
            )

            # Get summarized papers
            summarized = [p for p in new_papers if getattr(p, "summarized", False) == True]

            # Group by category/query
            by_query = {}
            for paper in new_papers:
                query = paper.search_query or "Unknown"
                if query not in by_query:
                    by_query[query] = []
                by_query[query].append(paper)

            # Statistics
            stats = {
                "total_new": len(new_papers),
                "summarized_new": len(summarized),
                "papers_by_query": {k: len(v) for k, v in by_query.items()},
                "date_generated": datetime.now().isoformat(),
                "report_type": "daily",
            }

            return {
                "stats": stats,
                "papers": new_papers,
                "summarized_papers": summarized,
                "grouped_papers": by_query,
            }

    def generate_weekly_report(self) -> Dict[str, Any]:
        """Generate weekly report"""
        output.do("生成每周报告")

        with self.db.get_session() as session:
            # Get papers from last 7 days
            cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
            recent_papers = (
                session.query(Paper)
                .filter(Paper.created_at >= cutoff)
                .order_by(Paper.published.desc())
                .limit(self.config.REPORT_MAX_PAPERS)
                .all()
            )

            # Get database stats
            db_stats = self.db.get_statistics()

            # Top categories
            categories = db_stats.get("categories_distribution", {})
            top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]

            # Statistics
            stats = {
                "total_recent": len(recent_papers),
                "database_stats": db_stats,
                "top_categories": dict(top_categories),
                "date_generated": datetime.now().isoformat(),
                "report_type": "weekly",
            }

            return {
                "stats": stats,
                "recent_papers": recent_papers,
                "database_stats": db_stats,
            }

    def save_markdown_report(self, report_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save report as markdown file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_type = report_data.get("stats", {}).get("report_type", "report")
            filename = f"{report_type}_{timestamp}.md"

        filepath = os.path.join(self.config.REPORT_DIR, filename)

        # 重置token统计（每次新报告开始时）
        self.total_tokens_used = 0
        self.total_cost = 0.0
        output.info("开始生成报告 - token计数已重置")

        # Generate markdown content
        stats = report_data["stats"]

        # 报告类型中文映射
        report_type_chinese = {"daily": "每日", "weekly": "每周", "recent": "最近", "search": "搜索"}
        report_type = report_type_chinese.get(stats["report_type"], stats["report_type"])

        markdown_content = f"""# arXiv 文献报告
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**报告类型**: {report_type}报告

## 统计摘要
"""

        if stats["report_type"] == "daily":
            markdown_content += f"""
- **今日新论文**: {stats["total_new"]}
- **今日已总结**: {stats["summarized_new"]}
- **总结率**: {stats["summarized_new"] / stats["total_new"]:.1%} (如果总数 > 0)

### 按搜索查询统计
"""
            for query, count in stats["papers_by_query"].items():
                markdown_content += f"- **{query}**: {count} 篇论文\n"

        elif stats["report_type"] == "weekly":
            markdown_content += f"""
- **本周论文**: {stats["total_recent"]}
- **数据库总论文**: {stats["database_stats"]["total_papers"]}
- **已总结论文**: {stats["database_stats"]["summarized_papers"]}
- **总体总结率**: {stats["database_stats"]["summarized_papers"] / stats["database_stats"]["total_papers"]:.1%} (如果总数 > 0)

### 热门分类
"""
            for category, count in stats["top_categories"].items():
                markdown_content += f"- **{category}**: {count} 篇论文\n"

        elif stats["report_type"] == "recent":
            markdown_content += f"""
- **最近论文**: {stats["total_recent"]} (最近 {stats["days_back"]} 天)
- **数据库总论文**: {stats.get("database_stats", {}).get("total_papers", "N/A")}
- **已总结论文**: {stats.get("database_stats", {}).get("summarized_papers", "N/A")}

### 热门分类
"""
            for category, count in stats.get("top_categories", {}).items():
                markdown_content += f"- **{category}**: {count} 篇论文\n"

        elif stats["report_type"] == "search":
            markdown_content += f"""
- **搜索查询**: {stats.get("original_query", "N/A")}
- **找到论文**: {stats.get("total_found", "N/A")}
- **数据库总论文**: {stats.get("database_stats", {}).get("total_papers", "N/A")}
- **已总结论文**: {stats.get("database_stats", {}).get("summarized_papers", "N/A")}

### 搜索词
"""
            search_terms = stats.get("search_terms", [])
            if isinstance(search_terms, list):
                for term in search_terms[:5]:  # 只显示前5个搜索词
                    markdown_content += f"- **{term}**\n"
            else:
                markdown_content += f"- **{search_terms}**\n"

            markdown_content += "\n### 热门分类\n"
            for category, count in stats.get("top_categories", {}).items():
                markdown_content += f"- **{category}**: {count} 篇论文\n"

        # Add paper details
        if "papers" in report_data and report_data["papers"]:
            markdown_content += "\n## 新论文\n\n"

            papers = report_data["papers"][:50]  # Limit to 50 papers
            total_papers = len(papers)

            for i, paper in enumerate(papers, 1):
                try:
                    output.do(f"[{i}/{total_papers}] 处理论文: {paper.arxiv_id}")
                    authors = json.loads(paper.authors) if paper.authors else []
                    author_names = [a.get("name", "") for a in authors[:3]]
                    if len(authors) > 3:
                        author_names.append("et al.")

                    # 计算相关度评级
                    relevance_score = self.calculate_relevance_score(paper)
                    stars = "★" * relevance_score + "☆" * (5 - relevance_score)

                    # 题目中英双语
                    # 尝试翻译标题
                    output.do(f"[{i}/{total_papers}] 翻译标题")
                    title_translation = self.translate_text(paper.title, "zh")

                    # 根据用户要求：中文标题为主，英文标题放在括号里
                    if title_translation and not title_translation.startswith("*"):
                        markdown_content += f"### {title_translation} ({paper.title})\n\n"
                    else:
                        markdown_content += f"### {paper.title}\n\n"

                    markdown_content += f"**作者 (Authors)**: {', '.join(author_names)}\n"
                    markdown_content += f"**发表日期 (Published)**: {paper.published.strftime('%Y-%m-%d') if paper.published else 'N/A'}\n"

                    # 分类解释
                    category_explanation = self.get_category_explanation(paper.categories or "")
                    markdown_content += f"**分类解释 (Categories)**: {category_explanation}\n"
                    markdown_content += f"**原始分类代码 (Original Codes)**: {paper.categories}\n"

                    markdown_content += f"**搜索查询 (Search Query)**: {paper.search_query}\n"

                    # 相关度评级
                    markdown_content += f"**相关度评级 (Relevance)**: {stars} ({relevance_score}/5)\n\n"

                    # 显示关键发现（如果存在）
                    if paper.summary:
                        summary_data = None

                        # 尝试解析总结JSON
                        try:
                            summary_data = json.loads(paper.summary)
                        except json.JSONDecodeError:
                            # 如果直接解析失败，尝试清理后解析
                            cleaned_summary = self.clean_json_response(paper.summary)
                            try:
                                summary_data = json.loads(cleaned_summary)
                            except json.JSONDecodeError:
                                # 如果仍然不是JSON，忽略总结数据
                                pass

                        # 显示关键发现（如果存在）
                        if summary_data and "key_findings" in summary_data and summary_data["key_findings"]:
                            markdown_content += "**关键发现 (Key Findings)**:\n"
                            for finding in summary_data["key_findings"][:5]:
                                markdown_content += f"- {finding}\n"
                            markdown_content += "\n"

                    # 完整英文摘要和中文翻译
                    if paper.abstract:
                        markdown_content += f"**完整英文摘要 (Full Abstract)**:\n{paper.abstract}\n\n"

                        # 尝试翻译摘要
                        output.do(f"[{i}/{total_papers}] 翻译摘要")
                        chinese_translation = self.translate_text(paper.abstract, "zh")
                        if chinese_translation and not chinese_translation.startswith("*"):
                            markdown_content += f"**中文翻译 (Chinese Translation)**:\n{chinese_translation}\n\n"
                        elif chinese_translation:
                            markdown_content += f"**中文翻译 (Chinese Translation)**: {chinese_translation}\n\n"
                        else:
                            markdown_content += f"**中文翻译 (Chinese Translation)**: *翻译服务不可用*\n\n"
                    else:
                        markdown_content += f"**摘要 (Abstract)**: 无摘要\n\n"

                    markdown_content += f"**arXiv ID**: [{paper.arxiv_id}](https://arxiv.org/abs/{paper.arxiv_id})\n"
                    markdown_content += f"**PDF**: [下载 (Download)]({paper.pdf_url})\n\n"
                    markdown_content += "---\n\n"

                except Exception as e:
                    output.error(
                        f"格式化论文失败: {paper.arxiv_id}",
                        details={"exception": str(e)},
                    )
                    continue

        # Add recommendations section
        markdown_content += "\n## 建议\n\n"

        if stats["report_type"] == "daily":
            markdown_content += "1. 浏览您感兴趣领域的新论文\n"
            markdown_content += "2. 查看已总结的论文以快速了解内容\n"
            markdown_content += "3. 将相关论文添加到阅读列表\n"
        else:
            markdown_content += "1. 回顾您研究领域的每周趋势\n"
            markdown_content += "2. 从热门分类中识别新兴主题\n"
            markdown_content += "3. 规划下周的阅读计划\n"

        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # 显示最终token统计
        if self.total_tokens_used > 0:
            total_cost_formatted = f"{self.total_cost:.4f}"
            output.info(f"报告生成完成 - 总计: {self.total_tokens_used} tokens (¥{total_cost_formatted})")

        output.done(f"报告已保存: {filepath}")
        return filepath

    def save_csv_report(self, report_data: Dict[str, Any], filename: Optional[str] = None) -> Optional[str]:
        """Save report as CSV file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_type = report_data["stats"]["report_type"]
            filename = f"{report_type}_report_{timestamp}.csv"

        filepath = os.path.join(self.config.REPORT_DIR, filename)

        # Convert papers to DataFrame
        papers_data = []
        for paper in report_data.get("papers", []):
            try:
                papers_data.append(
                    {
                        "arxiv_id": paper.arxiv_id,
                        "title": paper.title,
                        "authors": paper.authors,
                        "published": paper.published.isoformat() if paper.published else None,
                        "categories": paper.categories,
                        "primary_category": paper.primary_category,
                        "search_query": paper.search_query,
                        "summarized": paper.summarized,
                        "pdf_url": paper.pdf_url,
                        "doi": paper.doi,
                        "created_at": paper.created_at.isoformat() if paper.created_at else None,
                    }
                )
            except Exception as e:
                output.error(
                    f"处理论文到CSV失败: {paper.arxiv_id}",
                    details={"exception": str(e)},
                )

        if papers_data:
            df = pd.DataFrame(papers_data)

            # 中文列名映射
            chinese_columns = {
                "arxiv_id": "arXiv ID",
                "title": "标题",
                "authors": "作者",
                "published": "发表日期",
                "categories": "分类",
                "primary_category": "主要分类",
                "search_query": "搜索查询",
                "summarized": "已总结",
                "pdf_url": "PDF链接",
                "doi": "DOI",
                "created_at": "创建时间",
            }

            # 重命名列
            df = df.rename(columns=chinese_columns)

            df.to_csv(filepath, index=False, encoding="utf-8")
            output.done(f"CSV报告已保存: {filepath}")
            return filepath
        else:
            output.warn("没有论文数据可保存为CSV")
            return None

    def generate_and_save_daily_report(self) -> List[str]:
        """Generate and save daily report (returns list of saved files)"""
        report_data = self.generate_daily_report()

        saved_files = []

        # Save markdown report
        md_file = self.save_markdown_report(report_data)
        if md_file:
            saved_files.append(md_file)

        # Save CSV report
        csv_file = self.save_csv_report(report_data)
        if csv_file:
            saved_files.append(csv_file)

        return saved_files

    def generate_and_save_weekly_report(self) -> List[str]:
        """Generate and save weekly report"""
        report_data = self.generate_weekly_report()

        saved_files = []

        # Save markdown report
        md_file = self.save_markdown_report(report_data)
        if md_file:
            saved_files.append(md_file)

        # Save CSV report
        csv_file = self.save_csv_report(report_data)
        if csv_file:
            saved_files.append(csv_file)

        return saved_files


def main():
    """Test report generator"""
    generator = ReportGenerator()

    print("Testing report generator...")

    # Generate daily report
    print("\nGenerating daily report...")
    daily_data = generator.generate_daily_report()
    print(f"Daily stats: {daily_data['stats']}")

    # Save reports
    print("\nSaving reports...")
    saved_files = generator.generate_and_save_daily_report()
    print(f"Saved files: {saved_files}")

    # Generate weekly report
    print("\nGenerating weekly report...")
    weekly_data = generator.generate_weekly_report()
    print(f"Weekly stats: {weekly_data['stats'].get('total_recent', 0)} recent papers")

    # Check report directory
    report_dir = Config.REPORT_DIR
    print(f"\nReport directory: {report_dir}")
    if os.path.exists(report_dir):
        files = os.listdir(report_dir)
        print(f"Existing reports: {len(files)} files")


if __name__ == "__main__":
    main()
