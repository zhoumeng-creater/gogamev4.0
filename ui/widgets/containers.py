from tkinter import ttk
from typing import Optional, Union
from ui.themes import Theme
from .base import ThemeAwareMixin

class ModernCard(ttk.Frame, ThemeAwareMixin):
    """
    A themed container frame with a distinct background and border.
    """
    def __init__(self, parent, theme: Optional[Theme] = None, padding: Union[int, tuple] = 10, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        self.padding = padding
        self._apply_style()

    def _apply_style(self):
        style_name = f"ModernCard_{id(self)}.TFrame"
        style = ttk.Style()
        
        bg = self.theme.ui_panel_background if self.theme else "#E8DCC0"
        # border = self.theme.ui_panel_border if self.theme else "#C8B090" # Border is handled by relief/borderwidth, but frame usually doesn't color border directly unless specific theme. 
        # Standard ttk frame border color is tricky. For now relying on relief.
        
        style.configure(style_name, background=bg, relief='solid', borderwidth=1)
        self.configure(style=style_name, padding=self.padding)

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._apply_style()
