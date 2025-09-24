"""
主题管理模块
负责UI主题的定义、加载和管理
"""

import json
import os
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
    def from_json(cls, json_path: str) -> 'Theme':
        """从JSON文件加载"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def to_json(self, json_path: str):
        """保存到JSON文件"""
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


class ThemeManager:
    """主题管理器"""
    
    # 内置主题定义
    BUILTIN_THEMES = {
        'classic': Theme(
            name='classic',
            author='System',
            description='经典木纹主题',
            board_background='#F4D0A4',
            board_grid_color='#8B4513',
            ui_background='#F5F5DC',
            ui_panel_background='#E8DCC0'
        ),
        'modern': Theme(
            name='modern',
            author='System',
            description='现代简约主题',
            board_background='#FFFFFF',
            board_grid_color='#333333',
            board_star_color='#666666',
            ui_background='#FAFAFA',
            ui_panel_background='#F0F0F0',
            ui_panel_border='#E0E0E0',
            button_background='#4CAF50',
            button_hover='#45A049'
        ),
        'dark': Theme(
            name='dark',
            author='System',
            description='深色护眼主题',
            board_background='#2B2B2B',
            board_grid_color='#808080',
            board_star_color='#A0A0A0',
            board_coordinate_color='#C0C0C0',
            stone_black_color='#1A1A1A',
            stone_white_color='#E0E0E0',
            ui_background='#1E1E1E',
            ui_panel_background='#2D2D2D',
            ui_panel_border='#404040',
            ui_text_primary='#E0E0E0',
            ui_text_secondary='#B0B0B0',
            button_background='#4A4A4A',
            button_hover='#5A5A5A',
            button_text='#E0E0E0',
            input_background='#3A3A3A',
            input_border='#505050',
            input_text='#E0E0E0'
        ),
        'bamboo': Theme(
            name='bamboo',
            author='System',
            description='竹林清新主题',
            board_background='#E8F5E9',
            board_grid_color='#4CAF50',
            board_star_color='#2E7D32',
            ui_background='#F1F8E9',
            ui_panel_background='#DCEDC8',
            button_background='#66BB6A',
            button_hover='#4CAF50'
        ),
        'ocean': Theme(
            name='ocean',
            author='System',
            description='海洋蓝色主题',
            board_background='#E3F2FD',
            board_grid_color='#1976D2',
            board_star_color='#0D47A1',
            ui_background='#F5F9FF',
            ui_panel_background='#BBDEFB',
            button_background='#42A5F5',
            button_hover='#2196F3'
        ),
        'sakura': Theme(
            name='sakura',
            author='System',
            description='樱花粉色主题',
            board_background='#FCE4EC',
            board_grid_color='#C2185B',
            board_star_color='#880E4F',
            ui_background='#FFF0F5',
            ui_panel_background='#F8BBD0',
            button_background='#EC407A',
            button_hover='#E91E63'
        )
    }
    
    def __init__(self, themes_dir: Optional[str] = None):
        """
        初始化主题管理器
        
        Args:
            themes_dir: 主题目录路径
        """
        self.themes_dir = Path(themes_dir) if themes_dir else None
        self.themes: Dict[str, Theme] = {}
        self.current_theme: Optional[Theme] = None
        
        # 加载内置主题
        self._load_builtin_themes()
        
        # 加载自定义主题
        if self.themes_dir and self.themes_dir.exists():
            self._load_custom_themes()
    
    def _load_builtin_themes(self):
        """加载内置主题"""
        for name, theme in self.BUILTIN_THEMES.items():
            self.themes[name] = theme
    
    def _load_custom_themes(self):
        """加载自定义主题"""
        if not self.themes_dir:
            return
        
        for theme_file in self.themes_dir.glob('*.json'):
            try:
                theme = Theme.from_json(str(theme_file))
                self.themes[theme.name] = theme
            except Exception as e:
                print(f"加载主题文件 {theme_file} 失败: {e}")
    
    def get_theme(self, name: str) -> Optional[Theme]:
        """
        获取主题
        
        Args:
            name: 主题名称
            
        Returns:
            主题对象
        """
        return self.themes.get(name)
    
    def set_current_theme(self, name: str) -> bool:
        """
        设置当前主题
        
        Args:
            name: 主题名称
            
        Returns:
            是否成功
        """
        theme = self.get_theme(name)
        if theme:
            self.current_theme = theme
            return True
        return False
    
    def get_current_theme(self) -> Theme:
        """
        获取当前主题
        
        Returns:
            当前主题，如果没有则返回默认主题
        """
        if not self.current_theme:
            self.current_theme = self.BUILTIN_THEMES['classic']
        return self.current_theme
    
    def list_themes(self) -> list:
        """
        列出所有可用主题
        
        Returns:
            主题信息列表
        """
        return [
            {
                'name': theme.name,
                'author': theme.author,
                'description': theme.description,
                'builtin': theme.name in self.BUILTIN_THEMES
            }
            for theme in self.themes.values()
        ]
    
    def add_theme(self, theme: Theme) -> bool:
        """
        添加自定义主题
        
        Args:
            theme: 主题对象
            
        Returns:
            是否成功
        """
        if theme.name not in self.BUILTIN_THEMES:
            self.themes[theme.name] = theme
            
            # 保存到文件
            if self.themes_dir:
                theme_file = self.themes_dir / f"{theme.name}.json"
                theme.to_json(str(theme_file))
            
            return True
        return False
    
    def remove_theme(self, name: str) -> bool:
        """
        删除自定义主题
        
        Args:
            name: 主题名称
            
        Returns:
            是否成功
        """
        if name not in self.BUILTIN_THEMES and name in self.themes:
            del self.themes[name]
            
            # 删除文件
            if self.themes_dir:
                theme_file = self.themes_dir / f"{name}.json"
                if theme_file.exists():
                    theme_file.unlink()
            
            return True
        return False
    
    def export_theme(self, name: str, export_path: str) -> bool:
        """
        导出主题
        
        Args:
            name: 主题名称
            export_path: 导出路径
            
        Returns:
            是否成功
        """
        theme = self.get_theme(name)
        if theme:
            theme.to_json(export_path)
            return True
        return False
    
    def import_theme(self, import_path: str) -> Optional[str]:
        """
        导入主题
        
        Args:
            import_path: 导入路径
            
        Returns:
            导入的主题名称，失败返回None
        """
        try:
            theme = Theme.from_json(import_path)
            
            # 避免覆盖内置主题
            if theme.name in self.BUILTIN_THEMES:
                theme.name = f"{theme.name}_custom"
            
            self.add_theme(theme)
            return theme.name
        except Exception as e:
            print(f"导入主题失败: {e}")
            return None
    
    def create_custom_theme(self, base_theme: str, name: str, 
                          modifications: Dict[str, Any]) -> Theme:
        """
        基于现有主题创建自定义主题
        
        Args:
            base_theme: 基础主题名称
            name: 新主题名称
            modifications: 修改的属性
            
        Returns:
            新主题对象
        """
        base = self.get_theme(base_theme)
        if not base:
            base = self.BUILTIN_THEMES['classic']
        
        # 复制基础主题
        theme_dict = base.to_dict()
        theme_dict['name'] = name
        theme_dict['author'] = 'User'
        
        # 应用修改
        theme_dict.update(modifications)
        
        # 创建新主题
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