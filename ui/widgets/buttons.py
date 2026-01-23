import tkinter as tk
from typing import Optional, Callable, Any
from ui.themes import Theme
from .base import ThemeAwareMixin

class ModernButton(tk.Canvas, ThemeAwareMixin):
    """
    A premium-looking button with hover effects and smooth transitions.
    Uses Canvas to draw custom shapes and backgrounds.
    "primary", "secondary", "danger", "success", "warning", or "info".
    """
    def __init__(self, parent, text: str = "", command: Optional[Callable] = None, 
                 theme: Optional[Theme] = None, width: int = 120, height: int = 35,
                 style: str = "primary", icon: Optional[Any] = None, **kwargs):

        tk.Canvas.__init__(self, parent, width=width, height=height, 
                         highlightthickness=0, cursor="hand2", **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.style_type = style
        self.icon = icon
        self.state = 'normal'
        self._visual_state = 'normal'
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", self._on_resize)
        
        self._draw()

    def _draw(self, state: str = 'normal'):
        self._visual_state = state
        self.delete("all")
        
        if not self.theme:
            # Fallback colors
            bg = "#D4A574"
            fg = "#FFFFFF"
            border = "#A08060"
        else:
            # Determine base colors based on style
            if self.style_type == "danger":
                base_bg = self.theme.error_color
                base_fg = "#FFFFFF"
            elif self.style_type == "success":
                base_bg = self.theme.success_color
                base_fg = "#FFFFFF"
            elif self.style_type == "warning":
                base_bg = self.theme.warning_color
                base_fg = "#000000"
            elif self.style_type == "info":
                base_bg = self.theme.info_color
                base_fg = "#FFFFFF"
            elif self.style_type == "secondary":
                base_bg = self.theme.ui_panel_background
                base_fg = self.theme.ui_text_primary
            else: # primary and others
                base_bg = self.theme.button_background
                base_fg = self.theme.button_text

            if state == 'hover':
                # Simplified hover logic: slightly lighten/darken or use theme prop if available
                # For now using theme.button_hover for primary, or just same bg for others (to be improved)
                if self.style_type == "primary":
                    bg = self.theme.button_hover
                else:
                    bg = base_bg # Placeholder for calculated hover
            elif state == 'pressed':
                if self.style_type == "primary":
                    bg = self.theme.button_pressed
                else:
                    bg = base_bg
            elif state == 'disabled':
                bg = self.theme.button_disabled
            else:
                bg = base_bg
            
            fg = base_fg
            border = base_bg # Border matches bg for flat look usually, or specific border if secondary
            
            if self.style_type == "secondary":
                 border = self.theme.button_border
                 if state == 'hover':
                     bg = self.theme.input_background # Lighten

        # Draw rounded rectangle (simulated with oval + rect)
        radius = 8
        self.create_rounded_rect(2, 2, self.width-2, self.height-2, radius, fill=bg, outline=border, width=1)
        
        # Text
        if self.theme:
            font_family = (self.theme.font_family or "Arial").split(',')[0].strip()
            font_size = max(10, int(getattr(self.theme, "font_size_small", 10)))
        else:
            font_family = "Segoe UI"
            font_size = 10
        font = (font_family, font_size, 'bold')
        self.create_text(self.width//2, self.height//2, text=self.text, fill=fg, font=font)

    def _on_resize(self, event):
        if event.width <= 1 or event.height <= 1:
            return
        if event.width == self.width and event.height == self.height:
            return
        self.width = event.width
        self.height = event.height
        draw_state = 'disabled' if self.state == 'disabled' else self._visual_state
        self._draw(draw_state)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def _on_enter(self, event):
        if self.state == 'normal':
            self._draw('hover')

    def _on_leave(self, event):
        if self.state == 'normal':
            self._draw('normal')

    def _on_press(self, event):
        if self.state == 'normal':
            self._draw('pressed')

    def _on_release(self, event):
        if self.state == 'normal':
            self._draw('hover')
            if self.command:
                self.command()

    def configure_text(self, text: str):
        self.text = text
        self._draw()

    def set_state(self, state: str):
        self.state = state
        self._draw('disabled' if state == 'disabled' else 'normal')
        self.configure(cursor="arrow" if state == 'disabled' else "hand2")

    def update_theme(self, theme: Theme):
        self.theme = theme
        draw_state = 'disabled' if self.state == 'disabled' else self._visual_state
        self._draw(draw_state)
