import json
import logging
import re
import time
from typing import Any

from tqdm import tqdm

from arxiv_pulse.config import Config
from arxiv_pulse.models import Database, Paper
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

    def extract_keywords(self, text: str, max_keywords: int = 10) -> list[str]:
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

    def get_summary_prompt(self, paper: Paper, lang: str = "zh") -> tuple[str, str]:
        """Get summary prompt and system message based on language"""

        prompts = {
            "zh": {
                "prompt": f"""
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
""",
                "system": "你是一个总结物理学和计算科学论文的研究助手。",
            },
            "en": {
                "prompt": f"""
Please summarize the following research paper in a structured format:

Title: {paper.title}

Abstract: {paper.abstract}

Please provide:
1. Key findings/contributions (bullet points)
2. Methodology/approach used
3. Relevance to condensed matter physics, DFT, machine learning, or force fields
4. Potential impact/significance

Please format your response as a JSON object with the following fields:
- key_findings: array of strings
- methodology: string
- relevance: string
- impact: string
- keywords: array of relevant keywords (5-10)
""",
                "system": "You are a research assistant specializing in summarizing physics and computational science papers.",
            },
            "ru": {
                "prompt": f"""
Пожалуйста, обобщите следующую научную статью в структурированном формате:

Название: {paper.title}

Аннотация: {paper.abstract}

Пожалуйста, предоставьте:
1. Ключевые выводы/вклад (список)
2. Используемая методология/подход
3. Отношение к физике конденсированного состояния, DFT, машинному обучению или силовым полям
4. Потенциальное влияние/значимость

Пожалуйста, отформатируйте ответ как JSON-объект со следующими полями:
- key_findings: массив строк
- methodology: строка
- relevance: строка
- impact: строка
- keywords: массив релевантных ключевых слов (5-10)
""",
                "system": "Вы - научный ассистент, специализирующийся на обобщении статей по физике и вычислительным наукам.",
            },
            "fr": {
                "prompt": f"""
Veuillez résumer l'article de recherche suivant dans un format structuré:

Titre: {paper.title}

Résumé: {paper.abstract}

Veuillez fournir:
1. Conclusions/contributions clés (liste à puces)
2. Méthodologie/approche utilisée
3. Pertinence pour la physique de la matière condensée, DFT, l'apprentissage automatique ou les champs de force
4. Impact/signification potentielle

Veuillez formater votre réponse sous forme d'objet JSON avec les champs suivants:
- key_findings: tableau de chaînes
- methodology: chaîne
- relevance: chaîne
- impact: chaîne
- keywords: tableau de mots-clés pertinents (5-10)
""",
                "system": "Vous êtes un assistant de recherche spécialisé dans la synthèse d'articles de physique et de sciences computationnelles.",
            },
            "de": {
                "prompt": f"""
Bitte fassen Sie den folgenden Forschungsartikel in einem strukturierten Format zusammen:

Titel: {paper.title}

Zusammenfassung: {paper.abstract}

Bitte geben Sie:
1. Wichtigste Erkenntnisse/Beiträge (Aufzählung)
2. Verwendete Methodik/Ansatz
3. Relevanz für kondensierte Materie, DFT, maschinelles Lernen oder Kraftfelder
4. Potenzielle Auswirkungen/Bedeutung

Bitte formatieren Sie Ihre Antwort als JSON-Objekt mit folgenden Feldern:
- key_findings: Array von Strings
- methodology: String
- relevance: String
- impact: String
- keywords: Array relevanter Schlüsselwörter (5-10)
""",
                "system": "Sie sind ein Forschungsassistent, der sich auf die Zusammenfassung von Physik- und Computerwissenschaftsartikeln spezialisiert hat.",
            },
            "es": {
                "prompt": f"""
Por favor, resuma el siguiente artículo de investigación en un formato estructurado:

Título: {paper.title}

Resumen: {paper.abstract}

Por favor proporcione:
1. Hallazgos/contribuciones clave (lista con viñetas)
2. Metodología/enfoque utilizado
3. Relevancia para la física de la materia condensada, DFT, aprendizaje automático o campos de fuerza
4. Impacto/significancia potencial

Por favor formate su respuesta como un objeto JSON con los siguientes campos:
- key_findings: array de cadenas
- methodology: cadena
- relevance: cadena
- impact: cadena
- keywords: array de palabras clave relevantes (5-10)
""",
                "system": "Eres un asistente de investigación especializado en resumir artículos de física y ciencias computacionales.",
            },
            "ar": {
                "prompt": f"""
يرجى تلخيص ورقة البحث التالية بتنسيق منظم:

العنوان: {paper.title}

الملخص: {paper.abstract}

يرجى تقديم:
1. النتائج/المساهمات الرئيسية (قائمة نقطية)
2. المنهجية/النهج المستخدم
3. الصلة بفيزياء المادة المكثفة أو DFT أو التعلم الآلي أو مجالات القوة
4. التأثير/الأهمية المحتملة

يرجى تنسيق ردك ككائن JSON بالحقول التالية:
- key_findings: مصفوفة من السلاسل
- methodology: سلسلة
- relevance: سلسلة
- impact: سلسلة
- keywords: مصفوفة من الكلمات المفتاحية ذات الصلة (5-10)
""",
                "system": "أنت مساعد بحث متخصص في تلخيص أوراق الفيزياء والعلوم الحاسوبية.",
            },
        }

        lang_prompt = prompts.get(lang, prompts["en"])
        return lang_prompt["prompt"], lang_prompt["system"]

    def deepseek_summary(self, paper: Paper) -> str | None:
        """Generate summary using DeepSeek"""
        if not self.config.AI_API_KEY:
            return None

        prompt, system_msg = self.get_summary_prompt(paper, self.config.TRANSLATE_LANGUAGE)

        try:
            output.do(f"总结论文: {paper.arxiv_id}")

            # 创建openai客户端 (openai 2.x版本)
            import openai

            client = openai.OpenAI(api_key=self.config.AI_API_KEY, base_url=self.config.AI_BASE_URL)

            response = client.chat.completions.create(
                model=self.config.AI_MODEL,
                messages=[
                    {"role": "system", "content": system_msg},
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

    def summarize_pending_papers(self, limit: int = 20) -> dict[str, Any]:
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

    def get_summary_stats(self) -> dict[str, Any]:
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
