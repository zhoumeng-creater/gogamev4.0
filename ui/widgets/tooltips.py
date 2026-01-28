import tkinter as tk
from typing import Optional
from ui.themes import Theme
from .base import ThemeAwareMixin, resolve_font_family

class ModernTooltip(ThemeAwareMixin):
    """
    A modern tooltip that appears on hover.
    """
    def __init__(self, widget, text: str = "", theme: Optional[Theme] = None, delay: int = 500):
        super().__init__(theme)
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.id = None
        
        self.widget.bind("<Enter>", self._schedule)
        self.widget.bind("<Leave>", self._cancel)
        self.widget.bind("<ButtonPress>", self._cancel)
        
    def _schedule(self, event=None):
        self._cancel()
        self.id = self.widget.after(self.delay, self._show)
        
    def _cancel(self, event=None):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        self._hide()
        
    def _show(self):
        if not self.text:
            return
            
        x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        if self.theme:
            bg = self.theme.ui_panel_background  # Or a specific tooltip color if added to theme
            fg = self.theme.ui_text_primary
            border = self.theme.board_border_color # Use a subtle border
        else:
            bg = "#FFFFDD"
            fg = "#000000"
            border = "#000000"
            
        font_family = resolve_font_family(self.theme)
        font_size = max(9, int(getattr(self.theme, "font_size_small", 9))) if self.theme else 9
        label = tk.Label(tw, text=self.text, justify='left',
                         background=bg, foreground=fg,
                         relief='solid', borderwidth=1,
                         font=(font_family, font_size))
        label.pack(ipadx=1)
        
    def _hide(self):
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()

    def update_theme(self, theme: Theme):
        self.theme = theme
        # If tooltip is currently showing, we could update it, 
        # but usually it's transient so we just update internal state for next show.
