"""
UI 翻译入口
与 utils.translator 保持一致，避免重复实现
"""

from utils.translator import Translator, get_translator, set_global_language, t

__all__ = [
    "Translator",
    "get_translator",
    "set_global_language",
    "t",
]
