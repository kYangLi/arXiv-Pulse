"""
Translation service - 文本翻译服务
"""

import re

from arxiv_pulse.core import Config
from arxiv_pulse.web.dependencies import get_db


def _is_valid_translation(text: str, original: str) -> bool:
    """验证翻译结果是否有效"""
    if not text or not text.strip():
        return False

    invalid_patterns = [
        r"<\|[^|]*\|>",
        r"<｜[^｜]*｜>",
        r"fim[_▁]?begin",
        r"fim[_▁]?end",
        r"CodingTest",
        r"package\s+\w+;",
        r"import\s+java\.",
        r"public\s+class",
        r"BOJ_\d+",
        r"\.java\b",
    ]

    for pattern in invalid_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False

    if len(text) < len(original) * 0.1:
        return False

    return True


def translate_text(text: str, target_lang: str = "zh") -> str:
    """使用AI API翻译文本，优先使用缓存"""
    if not text or not text.strip():
        return ""

    if target_lang == "en":
        return ""

    db = get_db()

    cached_translation = db.get_translation_cache(text, target_lang)
    if cached_translation:
        return cached_translation

    if not Config.AI_API_KEY:
        return ""

    try:
        import openai

        from arxiv_pulse.i18n import get_translation_prompt

        client = openai.OpenAI(api_key=Config.AI_API_KEY, base_url=Config.AI_BASE_URL)
        max_chars = 3000
        text_to_translate = text[:max_chars] + "... [文本过长，已截断]" if len(text) > max_chars else text

        system_prompt = get_translation_prompt(target_lang)

        response = client.chat.completions.create(
            model=Config.AI_MODEL or "DeepSeek-V3.2",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_to_translate},
            ],
            max_tokens=min(2000, len(text_to_translate) // 2),
            temperature=0.3,
        )

        translated = response.choices[0].message.content or ""
        if translated and not translated.startswith("*") and _is_valid_translation(translated, text):
            db.set_translation_cache(text, translated, target_lang)
            return translated
        return ""
    except Exception:
        return ""
