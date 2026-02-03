import json
import logging
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import time
import re

from arxiv_pulse.models import Database, Paper
from arxiv_pulse.config import Config
from arxiv_pulse.output_manager import output

# 使用根日志记录器的配置（保留用于向后兼容）
logger = logging.getLogger(__name__)


class PaperSummarizer:
    def __init__(self):
        self.db = Database()
        self.config = Config

        # Token使用累计统计
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0

        # 抑制第三方库的详细日志
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        if self.config.AI_API_KEY:
            # openai 2.x版本不需要全局设置，将在使用时创建客户端
            pass
        else:
            output.warn("AI API密钥未设置，使用基础总结")

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text using simple heuristics"""
        # Simple keyword extraction (can be improved)
        words = re.findall(r"\b[A-Za-z][a-z]{3,}\b", text.lower())
        common_words = {
            "this",
            "that",
            "with",
            "from",
            "have",
            "which",
            "there",
            "their",
            "about",
            "using",
            "based",
            "approach",
            "method",
            "study",
            "paper",
            "research",
            "results",
            "show",
            "find",
            "found",
            "propose",
            "proposed",
        }

        word_freq = {}
        for word in words:
            if word not in common_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, _ in sorted_words[:max_keywords]]

        return keywords

    def basic_summary(self, paper: Paper) -> str:
        """Generate basic summary without AI"""
        abstract_str = str(paper.abstract) if paper.abstract else ""
        title_str = str(paper.title) if paper.title else ""

        # Simple extraction of first few sentences
        sentences = re.split(r"[.!?]+", abstract_str)
        if len(sentences) > 3:
            summary = ". ".join(sentences[:3]) + "."
        else:
            summary = abstract_str[:500] + "..." if len(abstract_str) > 500 else abstract_str

        keywords = self.extract_keywords(f"{title_str} {abstract_str}")

        return json.dumps(
            {
                "summary": "",
                "keywords": keywords,
                "method": "basic",
                "key_findings": [],
            }
        )

    def deepseek_summary(self, paper: Paper) -> Optional[str]:
        """Generate summary using DeepSeek"""
        if not self.config.AI_API_KEY:
            return None

        prompt = f"""
        请用结构化的格式总结以下研究论文：
        
        标题: {paper.title}
        
        摘要: {paper.abstract}
        
        请提供：
        1. 关键发现/贡献（要点列表）
        2. 使用的方法论/方法
        3. 与凝聚态物理、DFT、机器学习或力场的相关性
        4. 潜在影响/重要性
        
        请将回答格式化为JSON对象，包含以下字段：
        - key_findings: 字符串数组
        - methodology: 字符串
        - relevance: 字符串
        - impact: 字符串
        - keywords: 相关关键词数组（5-10个）
        """

        try:
            output.do(f"总结论文: {paper.arxiv_id}")

            # 创建openai客户端 (openai 2.x版本)
            import openai

            client = openai.OpenAI(api_key=self.config.AI_API_KEY, base_url=self.config.AI_BASE_URL)

            response = client.chat.completions.create(
                model=self.config.AI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个总结物理学和计算科学论文的研究助手。",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.config.SUMMARY_MAX_TOKENS,
                temperature=0.3,
            )

            # 记录token使用情况
            if hasattr(response, "usage") and response.usage:
                usage = response.usage
                # 更新累计token统计
                self.total_prompt_tokens += usage.prompt_tokens
                self.total_completion_tokens += usage.completion_tokens
                self.total_tokens += usage.total_tokens

                output.info(
                    f"Token 使用: 本次 提示 {usage.prompt_tokens}, 完成 {usage.completion_tokens}, 总计 {usage.total_tokens} | "
                    f"累计 提示 {self.total_prompt_tokens}, 完成 {self.total_completion_tokens}, 总计 {self.total_tokens}"
                )
            else:
                # 估算token使用（约4字符/1token）
                prompt_chars = len(prompt)
                estimated_tokens = prompt_chars // 4 + self.config.SUMMARY_MAX_TOKENS // 2
                # 更新累计token统计（估算）
                self.total_tokens += estimated_tokens
                output.info(f"Token 使用: 估算约 {estimated_tokens} tokens | 累计总计 {self.total_tokens} tokens")

            result = response.choices[0].message.content

            def clean_json_response(text):
                """清理AI响应中的JSON代码块标记"""
                import re

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

            # 清理响应
            cleaned_result = clean_json_response(result)

            # Try to parse as JSON, fallback to text
            try:
                summary_data = json.loads(cleaned_result)
            except json.JSONDecodeError:
                # 如果清理后仍然不是JSON，尝试原始结果
                try:
                    summary_data = json.loads(result)
                except json.JSONDecodeError:
                    # If not JSON, wrap it
                    summary_data = {
                        "summary": "",
                        "key_findings": [],
                        "methodology": "",
                        "relevance": "",
                        "impact": "",
                        "keywords": self.extract_keywords(f"{paper.title} {paper.abstract}"),
                    }

            return json.dumps(summary_data)

        except Exception as e:
            output.error(f"DeepSeek API 错误: {paper.arxiv_id}", details={"exception": str(e)})
            return None

    def summarize_paper(self, paper: Paper) -> bool:
        """Summarize a single paper"""
        try:
            summary_json = None

            # Try DeepSeek summary if API key is available
            if self.config.AI_API_KEY:
                summary_json = self.deepseek_summary(paper)

            # Fall back to basic summary if OpenAI failed or not available
            if not summary_json:
                summary_json = self.basic_summary(paper)
                # 估算basic summary的token使用（标题+摘要）
                text_length = len(str(paper.title or "")) + len(str(paper.abstract or ""))
                estimated_tokens = text_length // 4
                self.total_tokens += estimated_tokens
                output.info(f"基础总结Token估算: 约 {estimated_tokens} tokens | 累计总计 {self.total_tokens} tokens")

            if summary_json:
                # Extract keywords for separate storage
                try:
                    summary_data = json.loads(summary_json)
                    keywords = summary_data.get("keywords", [])
                except:
                    keywords = []

                # Update paper
                success = self.db.update_paper(
                    paper.arxiv_id,
                    summarized=True,
                    summary=summary_json,
                    keywords=json.dumps(keywords),
                )

                if success:
                    output.done(f"总结完成: {paper.arxiv_id}")
                    return True

            return False

        except Exception as e:
            output.error(f"总结论文失败: {paper.arxiv_id}", details={"exception": str(e)})
            return False

    def summarize_pending_papers(self, limit: int = 20) -> Dict[str, Any]:
        """Summarize papers that need summarization"""
        papers = self.db.get_papers_to_summarize(limit=limit)
        output.do(f"找到 {len(papers)} 篇需要总结的论文")

        successful = 0
        failed = 0

        for paper in tqdm(papers, desc="Summarizing papers"):
            if self.summarize_paper(paper):
                successful += 1
            else:
                failed += 1

            # Rate limiting
            time.sleep(0.5)

        return {
            "total_processed": len(papers),
            "successful": successful,
            "failed": failed,
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summarization statistics"""
        with self.db.get_session() as session:
            total = session.query(Paper).count()
            summarized = session.query(Paper).filter_by(summarized=True).count()

            # Quality metrics
            papers = session.query(Paper).filter_by(summarized=True).all()
            avg_summary_length = 0
            if papers:
                total_length = sum(len(p.summary or "") for p in papers)
                avg_summary_length = total_length / len(papers)

            return {
                "total_papers": total,
                "summarized_papers": summarized,
                "summarization_rate": summarized / total if total > 0 else 0,
                "avg_summary_length": avg_summary_length,
                "token_usage": {
                    "total_prompt_tokens": self.total_prompt_tokens,
                    "total_completion_tokens": self.total_completion_tokens,
                    "total_tokens": self.total_tokens,
                },
            }


def main():
    """Test the summarizer"""
    summarizer = PaperSummarizer()

    print("Testing paper summarizer...")

    # Get a paper to summarize
    db = Database()
    with db.get_session() as session:
        paper = session.query(Paper).filter_by(summarized=False).first()

        if paper:
            print(f"\nPaper to summarize:")
            print(f"Title: {paper.title[:100]}...")
            print(f"Abstract preview: {paper.abstract[:200]}...")

            # Test summarization
            print(f"\nSummarizing...")
            success = summarizer.summarize_paper(paper)

            if success:
                print("Summary successful!")

                # Get updated paper
                updated = session.query(Paper).filter_by(arxiv_id=paper.arxiv_id).first()
                if updated and updated.summary:
                    try:
                        summary_data = json.loads(updated.summary)
                        print(f"\nSummary: {summary_data.get('summary', '')[:300]}...")
                        print(f"Keywords: {summary_data.get('keywords', [])[:5]}")
                    except:
                        print(f"Summary: {updated.summary[:300]}...")
        else:
            print("No papers available for summarization")

    # Get stats
    stats = summarizer.get_summary_stats()
    print(f"\nSummarization stats:")
    print(f"Total papers: {stats['total_papers']}")
    print(f"Summarized: {stats['summarized_papers']}")
    print(f"Rate: {stats['summarization_rate']:.1%}")


if __name__ == "__main__":
    main()
