import json
import logging
import os
import ssl
import urllib.request
from datetime import datetime
from typing import Any

import pandas as pd

from arxiv_pulse.config import Config
from arxiv_pulse.models import Database
from arxiv_pulse.output_manager import output

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self):
        self.db = Database()
        self.config = Config
        self.total_tokens_used = 0
        from arxiv_pulse.ai.summarizer import PaperSummarizer

        self.summarizer = PaperSummarizer()
        self.figure_cache = {}
        self.use_cache = True

        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        self.category_explanations = {
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
            "cond-mat": "凝聚态物理 (Condensed Matter)",
            "cond-mat.mtrl-sci": "材料科学 (Materials Science)",
            "cond-mat.str-el": "强关联电子系统 (Strongly Correlated Electrons)",
            "cond-mat.supr-con": "超导 (Superconductivity)",
            "cond-mat.mes-hall": "介观系统与量子霍尔效应 (Mesoscopic Systems and Quantum Hall Effect)",
            "cond-mat.soft": "软凝聚态物质 (Soft Condensed Matter)",
            "cond-mat.dis-nn": "无序系统与神经网络 (Disordered Systems and Neural Networks)",
            "cond-mat.stat-mech": "统计力学 (Statistical Mechanics)",
            "cond-mat.quant-gas": "量子气体 (Quantum Gases)",
            "physics": "物理学 (Physics)",
            "physics.comp-ph": "计算物理 (Computational Physics)",
            "physics.chem-ph": "化学物理 (Chemical Physics)",
            "physics.data-an": "数据分析 (Data Analysis, Statistics and Probability)",
            "physics.ins-det": "仪器与探测器 (Instrumentation and Detectors)",
            "math": "数学 (Mathematics)",
            "math.NA": "数值分析 (Numerical Analysis)",
            "math.OC": "优化与控制 (Optimization and Control)",
            "math.ST": "统计 (Statistics)",
            "q-bio": "定量生物学 (Quantitative Biology)",
            "q-bio.BM": "生物分子 (Biomolecules)",
            "q-bio.QM": "定量方法 (Quantitative Methods)",
            "q-fin": "定量金融 (Quantitative Finance)",
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
        categories = [c.strip() for c in category_code.split(",")]
        explanations = []

        for cat in categories:
            if cat in self.category_explanations:
                explanations.append(self.category_explanations[cat])
            else:
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
        text = text.strip()
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        code_match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        if text.startswith("```json"):
            text = text[7:].strip()
        if text.startswith("```"):
            text = text[3:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        return text

    def get_first_figure_url(self, arxiv_id: str, use_cache: bool | None = None) -> str | None:
        """获取论文的第一个图片URL，改进版"""
        if use_cache is None:
            use_cache = getattr(self, "use_cache", True)

        if use_cache and arxiv_id in self.figure_cache:
            output.info(f"✓ 图片缓存命中 ({len(self.figure_cache[arxiv_id])} 字符)")
            return self.figure_cache[arxiv_id]

        if use_cache:
            db_cached_url = self.db.get_figure_cache(arxiv_id)
            if db_cached_url:
                output.info(f"✓ 图片缓存命中 ({len(db_cached_url)} 字符)")
                self.figure_cache[arxiv_id] = db_cached_url
                return db_cached_url

        try:
            url = f"https://arxiv.org/html/{arxiv_id}"
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(url, headers={"User-Agent": "arXiv-Pulse/1.0"})
            response = urllib.request.urlopen(req, timeout=10, context=context)
            html_content = response.read().decode("utf-8", errors="ignore")

            import re

            figure_pattern = r'<figure[^>]*>.*?<img[^>]+src=["\']([^"\']+)["\'][^>]*>.*?</figure>'
            figure_matches = re.findall(figure_pattern, html_content, re.IGNORECASE | re.DOTALL)

            if figure_matches:
                first_img_src = figure_matches[0]
                result = self._normalize_image_url(first_img_src, url)
                if use_cache:
                    self.figure_cache[arxiv_id] = result
                    try:
                        self.db.set_figure_cache(arxiv_id, result)
                    except Exception as e:
                        output.warn(f"保存图片缓存到数据库失败: {arxiv_id} - {str(e)[:100]}")
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

            result = self._normalize_image_url(best_image["src"], url)
            if use_cache:
                self.figure_cache[arxiv_id] = result
                try:
                    self.db.set_figure_cache(arxiv_id, result)
                except Exception as e:
                    output.warn(f"保存图片缓存到数据库失败: {arxiv_id} - {str(e)[:100]}")
            return result

        except Exception:
            return None

    def _normalize_image_url(self, img_src: str, base_url: str) -> str:
        """标准化图片URL：处理相对路径"""
        if img_src.startswith("http"):
            return img_src

        import re

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

    def calculate_relevance_score(self, paper) -> int:
        """计算论文相关度评级 (1-5星)"""
        query = paper.search_query or ""
        categories = paper.categories or ""

        core_domains = [
            "condensed matter physics",
            "density functional theory",
            "first principles calculation",
            "force fields",
            "molecular dynamics",
            "computational materials science",
            "quantum chemistry",
        ]

        related_domains = ["machine learning"]

        target_categories = [
            "cond-mat",
            "physics.comp-ph",
            "physics.chem-ph",
            "quant-ph",
        ]

        related_categories = [
            "cs.ai",
            "cs.lg",
            "stat.ml",
            "cs.ne",
            "physics.data-an",
        ]

        unrelated_categories = [
            "cs.cr",
            "cs.pl",
            "cs.se",
            "cs.cv",
            "cs.cl",
        ]

        query_lower = query.lower()
        categories_lower = categories.lower()

        score = 3

        for domain in core_domains:
            if domain in query_lower:
                score += 2
                break

        for domain in related_domains:
            if domain in query_lower:
                score += 1
                break

        if any(cat in categories_lower for cat in target_categories):
            score += 2

        elif any(cat in categories_lower for cat in related_categories):
            score += 1

        if any(cat in categories_lower for cat in unrelated_categories):
            score -= 1

        if "computational materials science" in query_lower and any(
            cat in categories_lower for cat in unrelated_categories
        ):
            score = max(2, score - 1)

        return max(1, min(5, score))

    def translate_text(self, text: str, target_lang: str = "zh") -> str:
        """使用DeepSeek或OpenAI API翻译文本，优先使用缓存"""
        if not text or not text.strip():
            return ""

        try:
            import openai

            cached_translation = self.db.get_translation_cache(text, target_lang)
            if cached_translation:
                output.info(f"✓ 缓存命中 ({len(text)} 字符)")
                return cached_translation

            if Config.AI_API_KEY:
                translated = self._translate_with_deepseek(text, target_lang)
                if translated and not translated.startswith("*"):
                    self.db.set_translation_cache(text, translated, target_lang)
                return translated
            return "*翻译需要配置DeepSeek API密钥*"

        except ImportError:
            return "*需要安装openai库*"
        except Exception as e:
            output.error("翻译文本失败", details={"exception": str(e)})
            return f"*翻译出错: {str(e)[:100]}*"

    def _translate_with_deepseek(self, text: str, target_lang: str = "zh") -> str:
        """使用DeepSeek API翻译文本"""
        import openai

        from arxiv_pulse.i18n import get_translation_prompt

        client = openai.OpenAI(api_key=Config.AI_API_KEY, base_url=Config.AI_BASE_URL)

        max_chars = 3000
        if len(text) > max_chars:
            text_to_translate = text[:max_chars] + "... [文本过长，已截断]"
        else:
            text_to_translate = text

        system_prompt = get_translation_prompt(target_lang)

        try:
            response = client.chat.completions.create(
                model=Config.AI_MODEL or "DeepSeek-V3.2",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_to_translate},
                ],
                max_tokens=min(2000, len(text_to_translate) // 2),
                temperature=0.3,
            )

            if hasattr(response, "usage") and response.usage:
                usage = response.usage
                current_tokens = usage.total_tokens
                self.total_tokens_used += current_tokens

                output.info(f"✓ 翻译完成 | 本次: {current_tokens} tokens | 累计: {self.total_tokens_used} tokens")
            else:
                estimated_tokens = len(text) // 4 + 500
                self.total_tokens_used += estimated_tokens
                output.info(f"✓ 翻译完成 | 本次: ~{estimated_tokens} tokens | 累计: {self.total_tokens_used} tokens")

            translated = response.choices[0].message.content
            return translated.strip() if translated else ""

        except Exception as e:
            output.error("DeepSeek翻译失败", details={"exception": str(e)})
            raise e

    def save_markdown_report(self, report_data: dict[str, Any], filename: str | None = None) -> str:
        """Save report as markdown file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stats = report_data.get("stats", {})
            report_type = stats.get("report_type", "report")

            if report_type == "search":
                search_query = stats.get("original_query", "")
                if not search_query and stats.get("search_terms"):
                    search_terms = stats.get("search_terms", [])
                    if isinstance(search_terms, list) and len(search_terms) > 0:
                        search_query = search_terms[0]

                if search_query:
                    import re

                    cleaned = re.sub(r"[^\w\s\u4e00-\u9fff]", "_", search_query)
                    cleaned = re.sub(r"\s+", "_", cleaned)
                    keywords = cleaned[:20]
                    keywords = keywords.rstrip("_")
                    filename = f"{report_type}_{timestamp}_{keywords}.md"
                else:
                    filename = f"{report_type}_{timestamp}.md"
            else:
                filename = f"{report_type}_{timestamp}.md"

        filepath = os.path.join(self.config.REPORT_DIR, filename)

        self.total_tokens_used = 0
        output.info("开始生成报告 - token计数已重置")

        stats = report_data["stats"]

        report_type_chinese = {"recent": "最近", "search": "搜索"}
        report_type = report_type_chinese.get(stats["report_type"], stats["report_type"])

        markdown_content = f"""本报告由 [arXiv-Pulse](https://github.com/kYangLi/ArXiv-Pulse) 自动生成。

# arXiv 文献报告
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**报告类型**: {report_type}报告

## 统计摘要
"""

        if stats["report_type"] == "recent":
            markdown_content += f"""
- **最近论文**: {stats["total_recent"]} (最近 {stats["days_back"]} 天)
- **数据库总论文**: {stats.get("database_stats", {}).get("total_papers", "N/A")}
- **已总结论文**: {stats.get("database_stats", {}).get("summarized_papers", "N/A")}

### 分类统计
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
                for term in search_terms[:5]:
                    markdown_content += f"- **{term}**\n"
            else:
                markdown_content += f"- **{search_terms}**\n"

            markdown_content += "\n### 分类统计\n"
            for category, count in stats.get("top_categories", {}).items():
                markdown_content += f"- **{category}**: {count} 篇论文\n"

        if report_data.get("papers"):
            markdown_content += "\n## 论文列表\n\n"

            papers = report_data["papers"][: self.config.REPORT_MAX_PAPERS]
            total_papers = len(papers)
            total_found = stats.get("total_found", total_papers)
            output.info(f"共找到 {total_found} 篇论文，将处理前 {total_papers} 篇")

            for i, paper in enumerate(papers, 1):
                try:
                    output.do(f"[{i}/{total_papers}] 处理论文: {paper.arxiv_id}")

                    summarize_flag = stats.get("summarize", True)
                    max_summarize = stats.get("max_summarize", 10)
                    summarized_count = getattr(self, "_summarized_count", 0)

                    if (
                        summarize_flag
                        and paper.summarized is False
                        and (max_summarize == 0 or summarized_count < max_summarize)
                    ):
                        output.do(f"[{i}/{total_papers}] 总结论文")
                        if self.summarizer.summarize_paper(paper):
                            summarized_count += 1
                            self._summarized_count = summarized_count
                            with self.db.get_session() as session:
                                from arxiv_pulse.models import Paper

                                updated_paper = session.query(Paper).filter_by(arxiv_id=paper.arxiv_id).first()
                                if updated_paper:
                                    paper = updated_paper
                    elif summarize_flag and paper.summarized is True:
                        output.do(f"[{i}/{total_papers}] 总结论文")
                        summary_length = len(str(paper.summary or ""))
                        output.info(f"✓ 缓存命中 ({summary_length} 字符)")

                    authors = json.loads(paper.authors) if paper.authors else []
                    author_names = [a.get("name", "") for a in authors[:3]]
                    if len(authors) > 3:
                        author_names.append("et al.")

                    relevance_score = self.calculate_relevance_score(paper)
                    stars = "★" * relevance_score + "☆" * (5 - relevance_score)

                    output.do(f"[{i}/{total_papers}] 翻译标题")
                    title_translation = self.translate_text(paper.title, "zh")

                    if title_translation and not title_translation.startswith("*"):
                        markdown_content += f"### {title_translation} ({paper.title})\n\n"
                    else:
                        markdown_content += f"### {paper.title}\n\n"

                    markdown_content += f"**作者 (Authors)**: {', '.join(author_names)}\n"
                    markdown_content += f"**发表日期 (Published)**: {paper.published.strftime('%Y-%m-%d') if paper.published else 'N/A'}\n"

                    category_explanation = self.get_category_explanation(paper.categories or "")
                    markdown_content += f"**分类解释 (Categories)**: {category_explanation}\n"
                    markdown_content += f"**原始分类代码 (Original Codes)**: {paper.categories}\n"

                    markdown_content += f"**搜索查询 (Search Query)**: {paper.search_query}\n"

                    markdown_content += f"**相关度评级 (Relevance)**: {stars} ({relevance_score}/5)\n\n"

                    if paper.summary:
                        summary_data = None

                        try:
                            summary_data = json.loads(paper.summary)
                        except json.JSONDecodeError:
                            cleaned_summary = self.clean_json_response(paper.summary)
                            try:
                                summary_data = json.loads(cleaned_summary)
                            except json.JSONDecodeError:
                                pass

                        if summary_data and "key_findings" in summary_data and summary_data["key_findings"]:
                            markdown_content += "**关键发现 (Key Findings)**:\n"
                            for finding in summary_data["key_findings"][:5]:
                                markdown_content += f"- {finding}\n"
                            markdown_content += "\n"

                    if paper.abstract:
                        markdown_content += f"**完整英文摘要 (Full Abstract)**:\n{paper.abstract}\n\n"

                        output.do(f"[{i}/{total_papers}] 翻译摘要")
                        chinese_translation = self.translate_text(paper.abstract, "zh")
                        if chinese_translation and not chinese_translation.startswith("*"):
                            markdown_content += f"**中文翻译 (Chinese Translation)**:\n{chinese_translation}\n\n"
                        elif chinese_translation:
                            markdown_content += f"**中文翻译 (Chinese Translation)**: {chinese_translation}\n\n"
                        else:
                            markdown_content += "**中文翻译 (Chinese Translation)**: *翻译服务不可用*\n\n"
                    else:
                        markdown_content += "**摘要 (Abstract)**: 无摘要\n\n"

                    markdown_content += f"**arXiv ID**: [{paper.arxiv_id}](https://arxiv.org/abs/{paper.arxiv_id})\n"
                    markdown_content += f"**PDF**: [下载 (Download)]({paper.pdf_url})\n"

                    output.do(f"[{i}/{total_papers}] 获取图1图片")
                    figure_url = self.get_first_figure_url(str(paper.arxiv_id), use_cache=self.use_cache)
                    if figure_url:
                        markdown_content += f"\n![图片]({figure_url})\n"

                    markdown_content += "\n---\n\n"

                except Exception as e:
                    output.error(
                        f"格式化论文失败: {paper.arxiv_id}",
                        details={"exception": str(e)},
                    )
                    continue

        markdown_content += "\n## 建议\n\n"

        markdown_content += "1. 浏览您感兴趣领域的论文\n"
        markdown_content += "2. 查看已总结的论文以快速了解内容\n"
        markdown_content += "3. 将相关论文添加到阅读列表\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        if self.total_tokens_used > 0:
            output.info(f"报告生成完成 - 总计: {self.total_tokens_used} tokens")

        output.done(f"报告已保存: {filepath}")
        return filepath

    def save_csv_report(self, report_data: dict[str, Any], filename: str | None = None) -> str | None:
        """Save report as CSV file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_type = report_data["stats"]["report_type"]
            filename = f"{report_type}_report_{timestamp}.csv"

        filepath = os.path.join(self.config.REPORT_DIR, filename)

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

            df = df.rename(columns=chinese_columns)

            df.to_csv(filepath, index=False, encoding="utf-8")
            output.done(f"CSV报告已保存: {filepath}")
            return filepath
        output.warn("没有论文数据可保存为CSV")
        return None
