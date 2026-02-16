"""
Internationalization (i18n) module for arXiv Pulse.

Provides translation support for UI messages and AI prompts.
"""

from typing import Literal

from arxiv_pulse.i18n.zh import ZH_DICT
from arxiv_pulse.i18n.en import EN_DICT

Language = Literal["zh", "en", "ja", "ko", "fr", "ru", "de", "es"]

_DICTS = {
    "zh": ZH_DICT,
    "en": EN_DICT,
}


def t(key: str, lang: Language = "zh", **kwargs) -> str:
    """Translate a key to the target language.

    Args:
        key: Translation key (dot-separated, e.g., "common.success")
        lang: Target language ("zh" or "en")
        **kwargs: Format arguments for string interpolation

    Returns:
        Translated string
    """
    lang_dict = _DICTS.get(lang, ZH_DICT)

    keys = key.split(".")
    value = lang_dict
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, key)
        else:
            return key

    if not isinstance(value, str):
        return key

    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, ValueError):
            return value

    return value


def get_translation_prompt(lang: str = "zh") -> str:
    """Get the translation prompt for AI.

    Args:
        lang: Target language for translation

    Returns:
        System prompt for translation
    """
    prompts = {
        "zh": "你是一个专业的翻译助手。将以下英文文本翻译成中文，保持专业术语准确，语言流畅。只返回翻译结果，不要添加任何解释。",
        "en": "",  # English doesn't need translation
        "ru": "Вы профессиональный переводчик. Переведите следующий английский текст на русский язык, сохраняя точность технических терминов и беглость языка. Верните только перевод без пояснений.",
        "fr": "Vous êtes un assistant de traduction professionnel. Traduisez le texte anglais suivant en français, en gardant les termes techniques précis et le langage fluide. Retournez uniquement la traduction sans explication.",
        "de": "Sie sind ein professioneller Übersetzungsassistent. Übersetzen Sie den folgenden englischen Text ins Deutsche, wobei Sie die technischen Begriffe präzise und die Sprache flüssig halten. Geben Sie nur die Übersetzung ohne Erklärung zurück.",
        "es": "Eres un asistente de traducción profesional. Traduce el siguiente texto en inglés al español, manteniendo los términos técnicos precisos y el lenguaje fluido. Devuelve solo la traducción sin explicación.",
        "ar": "أنت مساعد ترجمة محترف. ترجم النص الإنجليزي التالي إلى اللغة العربية، مع الحفاظ على دقة المصطلحات الفنية وسلاسة اللغة. أرجع الترجمة فقط بدون شرح.",
    }
    return prompts.get(lang, prompts["zh"])


def get_language_name(lang: str, target_lang: str = "zh") -> str:
    """Get language name in target language.

    Args:
        lang: Language code to get name for
        target_lang: Language to display name in

    Returns:
        Language name in target language
    """
    names = {
        "zh": {
            "zh": "中文",
            "en": "Chinese",
            "fr": "Chinois",
            "ru": "Китайский",
            "de": "Chinesisch",
            "es": "Chino",
            "ar": "الصينية",
        },
        "en": {
            "zh": "英文",
            "en": "English",
            "fr": "Anglais",
            "ru": "Английский",
            "de": "Englisch",
            "es": "Inglés",
            "ar": "الإنجليزية",
        },
        "fr": {
            "zh": "法文",
            "en": "French",
            "fr": "Français",
            "ru": "Французский",
            "de": "Französisch",
            "es": "Francés",
            "ar": "الفرنسية",
        },
        "ru": {
            "zh": "俄文",
            "en": "Russian",
            "fr": "Russe",
            "ru": "Русский",
            "de": "Russisch",
            "es": "Ruso",
            "ar": "الروسية",
        },
        "de": {
            "zh": "德文",
            "en": "German",
            "fr": "Allemand",
            "ru": "Немецкий",
            "de": "Deutsch",
            "es": "Alemán",
            "ar": "الألمانية",
        },
        "es": {
            "zh": "西班牙文",
            "en": "Spanish",
            "fr": "Espagnol",
            "ru": "Испанский",
            "de": "Spanisch",
            "es": "Español",
            "ar": "الإسبانية",
        },
        "ar": {
            "zh": "阿拉伯文",
            "en": "Arabic",
            "fr": "Arabe",
            "ru": "Арабский",
            "de": "Arabisch",
            "es": "Árabe",
            "ar": "العربية",
        },
    }
    return names.get(lang, {}).get(target_lang, lang)
