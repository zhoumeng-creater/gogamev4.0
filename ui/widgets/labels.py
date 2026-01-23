from tkinter import ttk
from typing import Optional
from ui.themes import Theme
from .base import ThemeAwareMixin

class ModernLabel(ttk.Label, ThemeAwareMixin):
    """
    A themed label with consistent typography.
    """
    def __init__(self, parent, theme: Optional[Theme] = None, font_style: str = 'normal', **kwargs):
        ttk.Label.__init__(self, parent, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        self.font_style = font_style
        self._apply_style(font_style)

    def _apply_style(self, font_style):
        style_name = f"ModernLabel_{id(self)}.TLabel"
        style = ttk.Style()
        
        if self.theme:
            bg = self.theme.ui_panel_background
            fg = self.theme.ui_text_primary
            size = self.theme.font_size_normal
            if font_style == 'title':
                size = self.theme.font_size_title
                weight = 'bold'
            elif font_style == 'section':
                size = self.theme.font_size_normal
                weight = 'bold'
            elif font_style == 'small':
                size = self.theme.font_size_small
                weight = 'normal'
            else:
                weight = 'normal'
            
            font = (self.theme.font_family.split(',')[0].strip(), size, weight)
        else:
            bg = "#E8DCC0"
            fg = "#2C2C2C"
            font = ('Arial', 10)
            
        style.configure(style_name, background=bg, foreground=fg, font=font)
        self.configure(style=style_name)

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._apply_style(self.font_style)
