from tkinter import Text, ttk
from typing import Optional
from ui.themes import Theme
from .base import ThemeAwareMixin

class ModernText(Text, ThemeAwareMixin):
    """
    A ThemeAware Text widget.
    """
    def __init__(self, parent, theme: Optional[Theme] = None,
                 background: Optional[str] = None,
                 font_size: Optional[int] = None,
                 **kwargs):
        self._background_override = background
        self._font_size = font_size
        Text.__init__(self, parent, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        # Default visuals
        self.configure(relief="flat", highlightthickness=1)
        self._apply_style()

    def _apply_style(self):
        if self.theme:
            bg = self._background_override or self.theme.input_background
            fg = self.theme.input_text
            border = self.theme.input_border
            insert_color = self.theme.input_text
            font_family = (self.theme.font_family or "Arial").split(',')[0].strip()
            font_size = (
                int(self._font_size)
                if self._font_size is not None
                else int(getattr(self.theme, "font_size_normal", 12))
            )
            font = (font_family, font_size)
        else:
            bg = self._background_override or "#FFFFFF"
            fg = "#000000"
            border = "#C0C0C0"
            insert_color = "#000000"
            font = None
            
        highlight = self.theme.input_focus_border if self.theme else "blue"
        kwargs = {
            "bg": bg,
            "fg": fg,
            "highlightbackground": border,
            "highlightcolor": highlight,
            "insertbackground": insert_color,
        }
        if font:
            kwargs["font"] = font
        self.configure(**kwargs)

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._apply_style()
