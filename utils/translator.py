"""
翻译系统模块
从 assets/translations/*.json 读取翻译文本
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional, Any


def _default_translations_dir() -> Path:
    try:
        base = Path(sys._MEIPASS)
    except Exception:
        base = Path(__file__).resolve().parents[1]
    return base / "assets" / "translations"


class Translator:
    """翻译器类"""

    def __init__(
        self,
        language: str = "zh",
        custom_translations: Optional[str] = None,
        translations_dir: Optional[str] = None,
    ):
        self.language = language or "zh"
        self.translations: Dict[str, Dict[str, str]] = {}

        self._load_translation_files(translations_dir)
        if custom_translations:
            self._load_custom_translations(custom_translations)

    def _load_translation_files(self, translations_dir: Optional[str]) -> None:
        base_dir = Path(translations_dir) if translations_dir else _default_translations_dir()
        if not base_dir.exists():
            return
        for path in base_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            lang_code = path.stem
            self.translations[lang_code] = {str(k): str(v) for k, v in data.items()}

    def _load_custom_translations(self, file_path: str) -> None:
        try:
            data = json.loads(Path(file_path).read_text(encoding="utf-8"))
        except Exception:
            return
        if not isinstance(data, dict):
            return
        for lang, mapping in data.items():
            if not isinstance(mapping, dict):
                continue
            current = self.translations.setdefault(str(lang), {})
            for key, value in mapping.items():
                current[str(key)] = str(value)

    def get(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        lang_dict = self.translations.get(self.language, {})
        if key not in lang_dict:
            lang_dict = self.translations.get("en", {})
        if key not in lang_dict:
            lang_dict = self.translations.get("zh", {})
        text = lang_dict.get(key, default or key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                pass
        return text

    def set_language(self, language: str) -> None:
        if language in self.translations:
            self.language = language
        else:
            print(f"不支持的语言: {language}")

    def get_available_languages(self) -> list:
        return list(self.translations.keys())

    def add_translation(self, language: str, key: str, value: str) -> None:
        self.translations.setdefault(language, {})[key] = value

    def export_translations(self, file_path: str, language: Optional[str] = None) -> None:
        try:
            if language:
                data = {language: self.translations.get(language, {})}
            else:
                data = self.translations
            Path(file_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:
            print(f"导出翻译失败: {exc}")

    def check_completeness(self, language: str) -> Dict[str, list]:
        base_keys = set(self.translations.get("en", {}).keys())
        lang_keys = set(self.translations.get(language, {}).keys())
        return {
            "missing": list(base_keys - lang_keys),
            "extra": list(lang_keys - base_keys),
        }


_global_translator: Optional[Translator] = None


def get_translator() -> Translator:
    global _global_translator
    if _global_translator is None:
        _global_translator = Translator()
    return _global_translator


def set_global_language(language: str) -> None:
    translator = get_translator()
    translator.set_language(language)


def t(key: str, **kwargs) -> str:
    translator = get_translator()
    return translator.get(key, **kwargs)
