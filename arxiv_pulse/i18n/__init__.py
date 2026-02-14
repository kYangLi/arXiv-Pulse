"""
Internationalization (i18n) module for arXiv Pulse.

Provides translation support for UI messages and AI prompts.
"""

from typing import Literal

from arxiv_pulse.i18n.zh import ZH_DICT
from arxiv_pulse.i18n.en import EN_DICT

Language = Literal["zh", "en"]

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

    # Navigate nested dict using dot notation
    keys = key.split(".")
    value = lang_dict
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, key)
        else:
            return key

    if not isinstance(value, str):
        return key

    # Format string with kwargs
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, ValueError):
            return value

    return value


def get_translation_prompt(lang: Language = "zh") -> str:
    """Get the translation prompt for AI.

    Args:
        lang: Target language for translation

    Returns:
        System prompt for translation
    """
    if lang == "zh":
        return "你是一个专业的翻译助手。将以下英文文本翻译成中文，保持专业术语准确，语言流畅。"
    else:
        return "You are a professional translation assistant. Translate the following text into English, keeping technical terms accurate and the language fluent."


def get_language_name(lang: Language, target_lang: Language = "zh") -> str:
    """Get language name in target language.

    Args:
        lang: Language code to get name for
        target_lang: Language to display name in

    Returns:
        Language name in target language
    """
    names = {
        "zh": {"zh": "中文", "en": "Chinese"},
        "en": {"zh": "英文", "en": "English"},
    }
    return names.get(lang, {}).get(target_lang, lang)
