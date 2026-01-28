import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Any
from ui.themes import Theme
from .base import ThemeAwareMixin, resolve_font_family

class ModernButton(tk.Canvas, ThemeAwareMixin):
    """
    A premium-looking button with hover effects and smooth transitions.
    Uses Canvas to draw custom shapes and backgrounds.
    "primary", "secondary", "danger", "success", "warning", or "info".
    """
    def __init__(self, parent, text: str = "", command: Optional[Callable] = None,
                 theme: Optional[Theme] = None, width: int = 120, height: int = 35,
                 style: str = "primary", icon: Optional[Any] = None,
                 canvas_bg: Optional[str] = None, **kwargs):

        tk.Canvas.__init__(self, parent, width=width, height=height, 
                         highlightthickness=0, cursor="hand2", **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.style_type = style
        self.icon = icon
        self.canvas_bg = canvas_bg
        self.state = 'normal'
        self._visual_state = 'normal'
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", self._on_resize)
        
        self._apply_canvas_bg()
        self._draw()

    def _resolve_canvas_bg(self):
        if self.canvas_bg:
            return self.canvas_bg

        # Try to match parent ttk style background first.
        try:
            if isinstance(self.master, ttk.Widget):
                style_name = self.master.cget("style")
                if style_name:
                    style = ttk.Style()
                    bg = style.lookup(style_name, "background")
                    if bg:
                        return bg
        except Exception:
            pass

        # Fallback to parent tk background if available.
        for opt in ("background", "bg"):
            try:
                bg = self.master.cget(opt)
                if bg:
                    return bg
            except Exception:
                continue

        if self.theme:
            return self.theme.ui_panel_background
        return "#E8DCC0"

    def _apply_canvas_bg(self):
        bg = self._resolve_canvas_bg()
        try:
            self.configure(bg=bg)
        except Exception:
            pass

    @staticmethod
    def _hex_to_rgb(value: str):
        if not isinstance(value, str):
            return None
        value = value.strip()
        if not value.startswith("#"):
            return None
        hex_value = value[1:]
        if len(hex_value) == 3:
            hex_value = "".join(ch * 2 for ch in hex_value)
        if len(hex_value) != 6:
            return None
        try:
            r = int(hex_value[0:2], 16)
            g = int(hex_value[2:4], 16)
            b = int(hex_value[4:6], 16)
            return r, g, b
        except Exception:
            return None

    @staticmethod
    def _rgb_to_hex(rgb):
        if not rgb:
            return None
        r, g, b = rgb
        return f"#{r:02X}{g:02X}{b:02X}"

    @classmethod
    def _blend(cls, base: str, target: str, ratio: float) -> str:
        base_rgb = cls._hex_to_rgb(base)
        target_rgb = cls._hex_to_rgb(target)
        if not base_rgb or not target_rgb:
            return base
        ratio = max(0.0, min(1.0, float(ratio)))
        r = int(base_rgb[0] + (target_rgb[0] - base_rgb[0]) * ratio)
        g = int(base_rgb[1] + (target_rgb[1] - base_rgb[1]) * ratio)
        b = int(base_rgb[2] + (target_rgb[2] - base_rgb[2]) * ratio)
        return cls._rgb_to_hex((r, g, b)) or base

    def _draw(self, state: str = 'normal'):
        self._visual_state = state
        self.delete("all")
        self._apply_canvas_bg()
        
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
                bg = self._blend(base_bg, self.theme.button_hover, 0.35)
            elif state == 'pressed':
                bg = self._blend(base_bg, self.theme.button_pressed, 0.45)
            elif state == 'disabled':
                bg = self.theme.button_disabled
            else:
                bg = base_bg
            
            fg = base_fg
            border = bg
            
            if self.style_type == "secondary":
                 border = self.theme.button_border
                 if state == 'disabled':
                     border = self.theme.button_disabled

            if state == 'disabled':
                fg = self.theme.ui_text_disabled

        # Draw rounded rectangle (simulated with oval + rect)
        radius = 8
        self.create_rounded_rect(2, 2, self.width-2, self.height-2, radius, fill=bg, outline=border, width=1)
        
        # Text
        font_family = resolve_font_family(self.theme)
        font_size = max(10, int(getattr(self.theme, "font_size_small", 10))) if self.theme else 10
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
        self._apply_canvas_bg()
        draw_state = 'disabled' if self.state == 'disabled' else self._visual_state
        self._draw(draw_state)
