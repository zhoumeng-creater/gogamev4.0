"""
主题管理模块
负责UI主题的定义、加载和管理
"""

import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class Theme:
    """主题数据类"""
    # 基本信息
    name: str
    author: str = ""
    version: str = "1.0"
    description: str = ""
    
    # 棋盘颜色
    board_background: str = "#F4D0A4"  # 棋盘背景
    board_grid_color: str = "#8B4513"  # 网格线颜色
    board_star_color: str = "#000000"  # 星位颜色
    board_coordinate_color: str = "#4A4A4A"  # 坐标颜色
    board_border_color: str = "#8B6914"  # 边框颜色
    
    # 棋子颜色
    stone_black_color: str = "#000000"
    stone_white_color: str = "#FFFFFF"
    stone_black_border: str = "#333333"
    stone_white_border: str = "#CCCCCC"
    stone_shadow_color: str = "rgba(0, 0, 0, 0.3)"
    stone_highlight_color: str = "rgba(255, 255, 255, 0.3)"
    
    # 标记颜色
    last_move_marker_color: str = "#FF0000"
    hover_indicator_color: str = "rgba(100, 100, 100, 0.3)"
    selection_color: str = "#00FF00"
    territory_black_color: str = "rgba(0, 0, 0, 0.3)"
    territory_white_color: str = "rgba(255, 255, 255, 0.3)"
    territory_neutral_color: str = "rgba(128, 128, 128, 0.2)"
    dead_stone_marker_color: str = "#FF0000"
    
    # UI颜色
    ui_background: str = "#F5F5DC"
    ui_panel_background: str = "#E8DCC0"
    ui_panel_border: str = "#C8B090"
    ui_text_primary: str = "#2C2C2C"
    ui_text_secondary: str = "#666666"
    ui_text_disabled: str = "#999999"
    
    # 按钮颜色
    button_background: str = "#D4A574"
    button_hover: str = "#C19656"
    button_pressed: str = "#B08040"
    button_disabled: str = "#E0D0C0"
    button_text: str = "#FFFFFF"
    button_border: str = "#A08060"
    
    # 输入框颜色
    input_background: str = "#FFFFFF"
    input_border: str = "#C0C0C0"
    input_focus_border: str = "#4080FF"
    input_text: str = "#000000"
    input_placeholder: str = "#999999"
    
    # 状态颜色
    success_color: str = "#28A745"
    warning_color: str = "#FFC107"
    error_color: str = "#DC3545"
    info_color: str = "#17A2B8"
    
    # 字体设置
    font_family: str = "Arial, sans-serif"
    font_size_normal: int = 12
    font_size_small: int = 10
    font_size_large: int = 14
    font_size_title: int = 16
    
    # 特效设置
    enable_shadows: bool = True
    enable_animations: bool = True
    animation_speed: float = 0.3  # 秒
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Theme':
        """从字典创建"""
        return cls(**data)
    
    @classmethod
    def _flatten_payload(cls, data: Dict[str, Any], name_override: Optional[str]) -> Dict[str, Any]:
        name = name_override or str(data.get("id") or data.get("name") or "theme")
        base = cls(name=name).to_dict()
        if data.get("author"):
            base["author"] = str(data.get("author"))
        if data.get("version"):
            base["version"] = str(data.get("version"))
        if data.get("description"):
            base["description"] = str(data.get("description"))
        elif data.get("name"):
            base["description"] = str(data.get("name"))

        board = data.get("board") or {}
        base["board_background"] = board.get("background", base["board_background"])
        base["board_grid_color"] = board.get("grid_color", base["board_grid_color"])
        base["board_star_color"] = board.get("star_point_color", base["board_star_color"])
        base["board_coordinate_color"] = board.get(
            "coordinate_color", base["board_coordinate_color"]
        )
        base["board_border_color"] = board.get("border_color", base["board_border_color"])

        stones = data.get("stones") or {}
        base["stone_black_color"] = stones.get("black", base["stone_black_color"])
        base["stone_white_color"] = stones.get("white", base["stone_white_color"])
        base["stone_black_border"] = stones.get("black_border", base["stone_black_border"])
        base["stone_white_border"] = stones.get("white_border", base["stone_white_border"])
        if "shadow" in stones:
            base["enable_shadows"] = bool(stones.get("shadow"))

        markers = data.get("markers") or {}
        base["last_move_marker_color"] = markers.get(
            "last_move", base["last_move_marker_color"]
        )
        base["territory_black_color"] = markers.get(
            "territory_black", base["territory_black_color"]
        )
        base["territory_white_color"] = markers.get(
            "territory_white", base["territory_white_color"]
        )
        base["hover_indicator_color"] = markers.get(
            "hover", base["hover_indicator_color"]
        )

        ui = data.get("ui") or {}
        base["ui_background"] = ui.get("background", base["ui_background"])
        base["ui_panel_background"] = ui.get("panel_bg", base["ui_panel_background"])
        base["ui_text_primary"] = ui.get("text_primary", base["ui_text_primary"])
        base["ui_text_secondary"] = ui.get("text_secondary", base["ui_text_secondary"])
        base["button_background"] = ui.get("button_bg", base["button_background"])
        base["button_hover"] = ui.get("button_hover", base["button_hover"])
        base["button_text"] = ui.get("button_text", base["button_text"])

        return base

    @classmethod
    def from_payload(cls, data: Dict[str, Any], name_override: Optional[str] = None) -> 'Theme':
        """从主题配置负载创建（兼容嵌套结构与扁平结构）"""
        if not isinstance(data, dict):
            return cls(name_override or "theme")
        if any(key in data for key in ("board", "stones", "ui", "markers")):
            payload = cls._flatten_payload(data, name_override)
            return cls.from_dict(payload)

        payload = dict(data)
        if name_override and not payload.get("name"):
            payload["name"] = name_override
        return cls.from_dict(payload)

    @classmethod
    def from_json(cls, json_path: str, name_override: Optional[str] = None) -> 'Theme':
        """从JSON文件加载"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_payload(data, name_override=name_override)
    
    def to_json(self, json_path: str):
        """保存到JSON文件"""
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


class ThemeManager:
    """主题管理器"""

    FALLBACK_THEME = Theme(name="classic", author="System", description="Classic")

    def __init__(self, themes_dir: Optional[str] = None):
        """
        初始化主题管理器

        Args:
            themes_dir: 自定义主题目录路径
        """
        self.default_themes_dir = self._default_assets_themes_dir()
        self.themes_dir = Path(themes_dir) if themes_dir else self._default_user_themes_dir()
        self.themes: Dict[str, Theme] = {}
        self._builtin_names: set[str] = set()
        self.current_theme: Optional[Theme] = None

        self._load_default_themes()
        self._load_custom_themes()

    def _default_assets_themes_dir(self) -> Path:
        try:
            base = Path(sys._MEIPASS)
        except Exception:
            base = Path(__file__).resolve().parents[1]
        return base / "assets" / "themes"

    def _default_user_themes_dir(self) -> Path:
        return Path.home() / ".go_master" / "themes"

    def _load_default_themes(self) -> None:
        if not self.default_themes_dir.exists():
            return
        for theme_file in self.default_themes_dir.glob("*.json"):
            try:
                theme = Theme.from_json(str(theme_file), name_override=theme_file.stem)
            except Exception as e:
                print(f"加载主题文件 {theme_file} 失败: {e}")
                continue
            self.themes[theme.name] = theme
            self._builtin_names.add(theme.name)

    def _load_custom_themes(self) -> None:
        if not self.themes_dir or not self.themes_dir.exists():
            return
        for theme_file in self.themes_dir.glob("*.json"):
            try:
                theme = Theme.from_json(str(theme_file), name_override=theme_file.stem)
            except Exception as e:
                print(f"加载主题文件 {theme_file} 失败: {e}")
                continue
            if theme.name in self._builtin_names:
                continue
            self.themes[theme.name] = theme

    def get_theme(self, name: str) -> Optional[Theme]:
        return self.themes.get(name)

    def set_current_theme(self, name: str) -> bool:
        theme = self.get_theme(name)
        if theme:
            self.current_theme = theme
            return True
        return False

    def get_current_theme(self) -> Theme:
        if not self.current_theme:
            if self.themes:
                first_name = sorted(self.themes.keys())[0]
                self.current_theme = self.themes[first_name]
            else:
                self.current_theme = self.FALLBACK_THEME
        return self.current_theme

    def list_themes(self) -> list:
        return [
            {
                "name": theme.name,
                "author": theme.author,
                "description": theme.description,
                "builtin": theme.name in self._builtin_names,
            }
            for theme in self.themes.values()
        ]

    def add_theme(self, theme: Theme) -> bool:
        if theme.name in self._builtin_names:
            return False
        self.themes[theme.name] = theme
        if self.themes_dir:
            self.themes_dir.mkdir(parents=True, exist_ok=True)
            theme_file = self.themes_dir / f"{theme.name}.json"
            theme.to_json(str(theme_file))
        return True

    def remove_theme(self, name: str) -> bool:
        if name in self._builtin_names or name not in self.themes:
            return False
        del self.themes[name]
        if self.themes_dir:
            theme_file = self.themes_dir / f"{name}.json"
            if theme_file.exists():
                theme_file.unlink()
        return True

    def export_theme(self, name: str, export_path: str) -> bool:
        theme = self.get_theme(name)
        if theme:
            theme.to_json(export_path)
            return True
        return False

    def import_theme(self, import_path: str) -> Optional[str]:
        try:
            theme = Theme.from_json(import_path)
            if theme.name in self._builtin_names:
                theme.name = f"{theme.name}_custom"
            self.add_theme(theme)
            return theme.name
        except Exception as e:
            print(f"导入主题失败: {e}")
            return None

    def create_custom_theme(
        self, base_theme: str, name: str, modifications: Dict[str, Any]
    ) -> Theme:
        base = self.get_theme(base_theme) or self.get_current_theme()
        theme_dict = base.to_dict()
        theme_dict["name"] = name
        theme_dict["author"] = "User"
        theme_dict.update(modifications)
        new_theme = Theme.from_dict(theme_dict)
        self.add_theme(new_theme)
        return new_theme


def apply_theme_to_tk(widget, theme: Theme):
    """
    将主题应用到Tkinter控件
    
    Args:
        widget: Tkinter控件
        theme: 主题对象
    """
    import tkinter as tk
    from tkinter import ttk
    
    # 配置ttk样式
    style = ttk.Style(widget)
    
    # 配置颜色
    style.configure('TFrame', background=theme.ui_panel_background)
    style.configure('TLabel', 
                   background=theme.ui_panel_background,
                   foreground=theme.ui_text_primary)
    style.configure('TButton',
                   background=theme.button_background,
                   foreground=theme.button_text,
                   bordercolor=theme.button_border)
    style.map('TButton',
             background=[('active', theme.button_hover),
                        ('pressed', theme.button_pressed),
                        ('disabled', theme.button_disabled)])
    
    # 配置输入框
    style.configure('TEntry',
                   fieldbackground=theme.input_background,
                   bordercolor=theme.input_border,
                   foreground=theme.input_text)
    style.map('TEntry',
             bordercolor=[('focus', theme.input_focus_border)])
    
    # 配置其他控件
    style.configure('TCheckbutton',
                   background=theme.ui_panel_background,
                   foreground=theme.ui_text_primary)
    style.configure('TRadiobutton',
                   background=theme.ui_panel_background,
                   foreground=theme.ui_text_primary)
    style.configure('TCombobox',
                   fieldbackground=theme.input_background,
                   background=theme.button_background,
                   foreground=theme.input_text)
    
    # 设置字体
    default_font = (theme.font_family.split(',')[0].strip(), 
                   theme.font_size_normal)
    widget.option_add('*Font', default_font)
