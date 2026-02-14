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
        "zh": "你是一个专业的翻译助手。将以下英文文本翻译成中文，保持专业术语准确，语言流畅。",
        "en": "You are a professional translation assistant. Keep the original English text as is, no translation needed.",
        "ja": "You are a professional translation assistant. Translate the following text into Japanese, keeping technical terms accurate and the language fluent.",
        "ko": "You are a professional translation assistant. Translate the following text into Korean, keeping technical terms accurate and the language fluent.",
        "fr": "You are a professional translation assistant. Translate the following text into French, keeping technical terms accurate and the language fluent.",
        "ru": "You are a professional translation assistant. Translate the following text into Russian, keeping technical terms accurate and the language fluent.",
        "de": "You are a professional translation assistant. Translate the following text into German, keeping technical terms accurate and the language fluent.",
        "es": "You are a professional translation assistant. Translate the following text into Spanish, keeping technical terms accurate and the language fluent.",
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
            "ja": "中国語",
            "ko": "중국어",
            "fr": "Chinois",
            "ru": "Китайский",
            "de": "Chinesisch",
            "es": "Chino",
        },
        "en": {
            "zh": "英文",
            "en": "English",
            "ja": "英語",
            "ko": "영어",
            "fr": "Anglais",
            "ru": "Английский",
            "de": "Englisch",
            "es": "Inglés",
        },
        "ja": {
            "zh": "日文",
            "en": "Japanese",
            "ja": "日本語",
            "ko": "일본어",
            "fr": "Japonais",
            "ru": "Японский",
            "de": "Japanisch",
            "es": "Japonés",
        },
        "ko": {
            "zh": "韩文",
            "en": "Korean",
            "ja": "韓国語",
            "ko": "한국어",
            "fr": "Coréen",
            "ru": "Корейский",
            "de": "Koreanisch",
            "es": "Coreano",
        },
        "fr": {
            "zh": "法文",
            "en": "French",
            "ja": "フランス語",
            "ko": "프랑스어",
            "fr": "Français",
            "ru": "Французский",
            "de": "Französisch",
            "es": "Francés",
        },
        "ru": {
            "zh": "俄文",
            "en": "Russian",
            "ja": "ロシア語",
            "ko": "러시아어",
            "fr": "Russe",
            "ru": "Русский",
            "de": "Russisch",
            "es": "Ruso",
        },
        "de": {
            "zh": "德文",
            "en": "German",
            "ja": "ドイツ語",
            "ko": "독일어",
            "fr": "Allemand",
            "ru": "Немецкий",
            "de": "Deutsch",
            "es": "Alemán",
        },
        "es": {
            "zh": "西班牙文",
            "en": "Spanish",
            "ja": "スペイン語",
            "ko": "스페인어",
            "fr": "Espagnol",
            "ru": "Испанский",
            "de": "Spanisch",
            "es": "Español",
        },
    }
    return names.get(lang, {}).get(target_lang, lang)
