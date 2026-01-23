import tkinter as tk
from typing import Optional
from ui.themes import Theme
from .base import ThemeAwareMixin

class ModernProgressBar(tk.Canvas, ThemeAwareMixin):
    """
    A polished progress bar for winrate or other metrics.
    """
    def __init__(self, parent, theme: Optional[Theme] = None, width: int = 200, height: int = 20, **kwargs):
        tk.Canvas.__init__(self, parent, width=width, height=height, highlightthickness=0, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        self.width = width
        self.height = height
        self.value = 50.0  # 0 to 100
        self.bind("<Configure>", self._on_resize)
        self._draw()

    def _draw(self):
        self.delete("all")

        if self.width <= 1 or self.height <= 1:
            return
        
        bg = self.theme.ui_panel_background if self.theme else "#E8DCC0"
        self.configure(bg=bg)
        
        # Track
        self.create_rounded_rect(0, 0, self.width, self.height, 10, fill="#f0f0f0", outline="")
        
        # Progress (Winrate colors)
        black_color = "#2c2c2c"
        white_color = "#e0e0e0"
        
        value = max(0.0, min(100.0, float(self.value)))
        split = (value / 100.0) * self.width
        split = max(0.0, min(self.width, split))
        
        # Black part (left)
        if split > 0:
            self.create_rounded_rect(0, 0, split, self.height, 10, fill=black_color, outline="")
        # Overlay a rect to cover the rounded right side if it's not at the end
        if split < self.width - 5:
            self.create_rectangle(max(0.0, split-5), 0, split, self.height, fill=black_color, outline="")
        
        # White part (right)
        if split < self.width:
            self.create_rounded_rect(split, 0, self.width, self.height, 10, fill=white_color, outline="")
        # Overlay a rect to cover the rounded left side
        if split > 5:
            self.create_rectangle(split, 0, split+5, self.height, fill=white_color, outline="")

        # Middle line
        self.create_line(self.width//2, 0, self.width//2, self.height, fill="red", width=1)

    def set_value(self, value: float):
        try:
            value = float(value)
        except Exception:
            value = 0.0
        if value <= 1.0:
            value *= 100.0
        self.value = max(0.0, min(100.0, value))
        self._draw()

    def _on_resize(self, event):
        if event.width <= 1 or event.height <= 1:
            return
        if event.width == self.width and event.height == self.height:
            return
        self.width = event.width
        self.height = event.height
        self._draw()

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._draw()

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)
