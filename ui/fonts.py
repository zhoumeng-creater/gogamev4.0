"""
Font loading and selection helpers.
Ensures consistent font usage with graceful fallbacks.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence

from tkinter import font as tkfont

from utils import resource_path


_UI_FONT_CANDIDATES = [
    # LXGW WenKai family (霞鹭文楷)
    "LXGW WenKai",
    "LXGW WenKai Regular",
    "Lxgw WenKai",
    "LxgWWenKai",
    "LxgWWenKai Regular",
    "LXGWWenKai",
    "LXGWWenKai Regular",
    "霞鹭文楷",
]

_MONO_FONT_CANDIDATES = [
    "LXGW WenKai Mono",
    "LXGW WenKaiMono",
    "LXGWWenKaiMono",
    "LXGWWenKai Mono",
]

_JP_FONT_CANDIDATES = [
    "G OTF 常改教科書ICA ProN L",
    "G OTF 常改教科書ICA ProN L_cn",
    "G OTF 常改教科書ICA ProN L CN",
    "G OTF 教科書ICA ProN L",
    "G-OTF 教科書ICA ProN L",
    "G OTF KyoKaisho ICA ProN L",
    "G-OTF KyoKaisho ICA ProN L",
    "Kyokasho ICA ProN L",
]

_CJK_FALLBACKS = [
    "Microsoft YaHei UI",
    "Microsoft YaHei",
    "PingFang SC",
    "PingFang TC",
    "Heiti SC",
    "Hiragino Sans GB",
    "Noto Sans CJK SC",
    "Noto Sans CJK JP",
    "Source Han Sans SC",
    "SimSun",
    "Songti SC",
]

_LATIN_FALLBACKS = [
    "Segoe UI",
    "Helvetica Neue",
    "Helvetica",
    "Arial",
    "Sans Serif",
]

_FONTS_REGISTERED = False


def _normalize_name(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum())


def _list_families(root=None) -> list[str]:
    try:
        families = list(tkfont.families(root))
    except Exception:
        families = list(tkfont.families())
    # Filter out vertical font faces on Windows (names prefixed with "@")
    return [fam for fam in families if not str(fam).startswith("@")]


def _find_family(candidates: Sequence[str], families: Sequence[str]) -> Optional[str]:
    if not candidates:
        return None
    if not families:
        return None
    # Prefer horizontal faces; ignore vertical "@" variants if present
    filtered = [fam for fam in families if not str(fam).startswith("@")]
    normalized = {_normalize_name(fam): fam for fam in filtered}
    for cand in candidates:
        key = _normalize_name(cand)
        if key in normalized:
            return normalized[key]
    # Fuzzy contains match
    for cand in candidates:
        key = _normalize_name(cand)
        if not key:
            continue
        for fam in filtered:
            if key in _normalize_name(fam):
                return fam
    return None


def _font_files() -> list[str]:
    base_dir = Path(__file__).resolve().parents[1]
    candidates = [
        "LxgWWenKai-Regular.ttf",
        "LXGWWenKai-Regular.ttf",
        "LXGWWenKaiMono-Regular.ttf",
        "G OTF 常改教科書ICA ProN L_cn.zitiziyuan.com.otf",
        os.path.join("assets", "fonts", "LxgWWenKai-Regular.ttf"),
        os.path.join("assets", "fonts", "LXGWWenKai-Regular.ttf"),
        os.path.join("assets", "fonts", "LXGWWenKaiMono-Regular.ttf"),
        os.path.join("assets", "fonts", "G OTF 常改教科書ICA ProN L_cn.zitiziyuan.com.otf"),
    ]

    files: list[str] = []
    for rel in candidates:
        try:
            path = resource_path(rel)
        except Exception:
            path = rel
        if path and os.path.exists(path):
            files.append(os.path.abspath(path))
        local = base_dir / rel
        if local.exists():
            files.append(str(local.resolve()))
    # Deduplicate
    return list(dict.fromkeys(files))


def _font_kind(path: str) -> str:
    name = Path(path).name.lower()
    if "wenkaimono" in name or "wenkai-mono" in name or "mono" in name:
        return "mono"
    if "wenkai" in name:
        return "ui"
    if name.endswith(".otf") or "otf" in name:
        return "jp"
    return "ui"


def _register_font_windows(path: str) -> bool:
    try:
        import ctypes
        from ctypes import wintypes

        FR_PRIVATE = 0x10
        AddFontResourceExW = ctypes.windll.gdi32.AddFontResourceExW
        AddFontResourceExW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID]
        AddFontResourceExW.restype = wintypes.INT
        return AddFontResourceExW(path, FR_PRIVATE, None) > 0
    except Exception:
        return False


def _register_font_macos(path: str) -> bool:
    # Best-effort: if it fails, fall back silently.
    try:
        import ctypes
        from ctypes import c_bool, c_void_p, c_uint32

        core_foundation = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
        )
        core_text = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreText.framework/CoreText"
        )

        kCFStringEncodingUTF8 = 0x08000100

        core_foundation.CFStringCreateWithCString.restype = c_void_p
        core_foundation.CFStringCreateWithCString.argtypes = [c_void_p, ctypes.c_char_p, c_uint32]

        core_foundation.CFURLCreateWithFileSystemPath.restype = c_void_p
        core_foundation.CFURLCreateWithFileSystemPath.argtypes = [
            c_void_p,
            c_void_p,
            c_uint32,
            c_bool,
        ]

        core_text.CTFontManagerRegisterFontsForURL.restype = c_bool
        core_text.CTFontManagerRegisterFontsForURL.argtypes = [c_void_p, c_uint32, c_void_p]

        cf_path = core_foundation.CFStringCreateWithCString(
            None, os.fsencode(path), kCFStringEncodingUTF8
        )
        if not cf_path:
            return False

        # kCFURLPOSIXPathStyle = 0
        url_ref = core_foundation.CFURLCreateWithFileSystemPath(None, cf_path, 0, False)
        if not url_ref:
            return False

        # kCTFontManagerScopeProcess = 1
        return bool(core_text.CTFontManagerRegisterFontsForURL(url_ref, 1, None))
    except Exception:
        return False


def _register_font_file(path: str) -> bool:
    if sys.platform.startswith("win"):
        return _register_font_windows(path)
    if sys.platform == "darwin":
        return _register_font_macos(path)
    return False


def ensure_project_fonts_loaded(root=None) -> None:
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return

    for path in _font_files():
        _register_font_file(path)

    _FONTS_REGISTERED = True
    # Refresh font families cache if possible
    try:
        _ = _list_families(root)
    except Exception:
        pass


def resolve_font_families(root=None, language: Optional[str] = None) -> dict[str, str]:
    """
    Resolve font families (ui/mono/jp) with fallbacks.
    When language is Japanese, prefer the JP font for UI.
    """
    ensure_project_fonts_loaded(root)
    families = _list_families(root)

    ui_font = _find_family(_UI_FONT_CANDIDATES, families)
    jp_font = _find_family(_JP_FONT_CANDIDATES, families)
    mono_font = _find_family(_MONO_FONT_CANDIDATES, families)
    latin_font = _find_family(_LATIN_FALLBACKS, families)

    # Prefer LXGWWenKai Mono for Chinese UI
    if mono_font and "wenkai" in mono_font.lower():
        ui_font = mono_font

    if not ui_font:
        ui_font = _find_family(_CJK_FALLBACKS + _LATIN_FALLBACKS, families)
    if not jp_font:
        jp_font = _find_family(_CJK_FALLBACKS + _LATIN_FALLBACKS, families)
    if not mono_font:
        mono_font = _find_family(
            [
                "Consolas",
                "Menlo",
                "Monaco",
                "Courier New",
                "SF Mono",
                "Noto Sans Mono CJK SC",
                "Noto Sans Mono",
            ],
            families,
        )

    # Ultimate fallback: Tk default font family
    if not ui_font:
        try:
            ui_font = tkfont.nametofont("TkDefaultFont").actual("family")
        except Exception:
            ui_font = "Arial"
    if not jp_font:
        jp_font = ui_font
    if not mono_font:
        mono_font = ui_font

    lang = str(language or "").lower()
    if lang.startswith("ja"):
        ui_font = jp_font or ui_font
    elif lang.startswith("en") and latin_font:
        ui_font = latin_font

    return {
        "ui": ui_font,
        "mono": mono_font,
        "jp": jp_font,
    }


def apply_app_fonts(root, theme_manager, language: Optional[str] = None) -> dict[str, str]:
    """
    Apply resolved fonts to all themes and Tk defaults.
    """
    families = resolve_font_families(root, language=language)
    ui_font = families["ui"]
    mono_font = families["mono"]
    jp_font = families["jp"]

    for theme in getattr(theme_manager, "themes", {}).values():
        theme.font_family = ui_font
        theme.font_family_mono = mono_font
        theme.font_family_jp = jp_font

    # Update fallback theme too
    try:
        theme_manager.FALLBACK_THEME.font_family = ui_font
        theme_manager.FALLBACK_THEME.font_family_mono = mono_font
        theme_manager.FALLBACK_THEME.font_family_jp = jp_font
    except Exception:
        pass

    # Apply to Tk defaults for consistent widgets
    try:
        from ui.themes import apply_theme_to_tk

        apply_theme_to_tk(root, theme_manager.get_current_theme())
    except Exception:
        pass

    return families
