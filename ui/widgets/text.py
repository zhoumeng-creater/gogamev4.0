from tkinter import Text, ttk
from typing import Optional
from ui.themes import Theme
from .base import ThemeAwareMixin

class ModernText(Text, ThemeAwareMixin):
    """
    A ThemeAware Text widget.
    """
    def __init__(self, parent, theme: Optional[Theme] = None, **kwargs):
        Text.__init__(self, parent, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        # Default visuals
        self.configure(relief="flat", highlightthickness=1)
        self._apply_style()

    def _apply_style(self):
        if self.theme:
            bg = self.theme.input_background
            fg = self.theme.input_text
            border = self.theme.input_border
            insert_color = self.theme.input_text
        else:
            bg = "#FFFFFF"
            fg = "#000000"
            border = "#C0C0C0"
            insert_color = "#000000"
            
        self.configure(bg=bg, fg=fg, highlightbackground=border, highlightcolor="blue", insertbackground=insert_color)

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._apply_style()
