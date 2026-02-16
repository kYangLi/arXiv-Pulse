"""
Internationalization (i18n) module for arXiv Pulse.

Provides translation support for UI messages and AI prompts.
"""

from typing import Literal

from arxiv_pulse.i18n.en import EN_DICT
from arxiv_pulse.i18n.zh import ZH_DICT

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
        "zh": "Translate the following English text to Chinese. Keep technical terms accurate and the language fluent. Return only the translation, no explanation.",
        "en": "",  # English doesn't need translation
        "ru": "Translate the following English text to Russian. Keep technical terms accurate and the language fluent. Return only the translation, no explanation.",
        "fr": "Translate the following English text to French. Keep technical terms accurate and the language fluent. Return only the translation, no explanation.",
        "de": "Translate the following English text to German. Keep technical terms accurate and the language fluent. Return only the translation, no explanation.",
        "es": "Translate the following English text to Spanish. Keep technical terms accurate and the language fluent. Return only the translation, no explanation.",
        "ar": "Translate the following English text to Arabic. Keep technical terms accurate and the language fluent. Return only the translation, no explanation.",
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
