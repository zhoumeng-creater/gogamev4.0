import tkinter as tk
from typing import Optional, Callable
from ui.themes import Theme
from .base import ThemeAwareMixin

class ModernScrollbar(tk.Canvas, ThemeAwareMixin):
    """
    A modern styled scrollbar (vertical or horizontal) using Canvas.
    """
    def __init__(self, parent, orient: str = 'vertical', command: Optional[Callable] = None, 
                 theme: Optional[Theme] = None, width: int = 14, **kwargs):
        
        if orient == 'vertical':
            height = kwargs.pop('height', 100)
        else:
            height = width
            width = kwargs.pop('width', 100) # swap for logic but keep arg name

        tk.Canvas.__init__(self, parent, width=width, height=height, 
                           highlightthickness=0, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.orient = orient
        self.command = command
        self.thumb_start = 0.0
        self.thumb_end = 1.0
        
        self.width = width
        self.height = height
        
        # State
        self.hovering = False
        self.dragging = False
        self.drag_start_pos = 0
        self.drag_start_thumb_start = 0
        
        # Bindings
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", self._on_resize)
        
        self._draw()

    def set(self, first: float, last: float):
        self.thumb_start = float(first)
        self.thumb_end = float(last)
        self._draw()

    def configure(self, cnf=None, **kw):
        if cnf is None and not kw:
            return super().configure()
        if cnf:
            if isinstance(cnf, dict):
                kw = {**cnf, **kw}
            else:
                return super().configure(cnf, **kw)
        if "command" in kw:
            self.command = kw.pop("command")
        if "orient" in kw:
            kw.pop("orient")
        return super().configure(**kw) if kw else super().configure()

    config = configure

    def _draw(self):
        self.delete("all")
        
        # Colors
        if not self.theme:
            bg_color = "#F0F0F0"
            thumb_color = "#C0C0C0"
            thumb_hover = "#A0A0A0"
            thumb_active = "#808080"
        else:
            bg_color = self.theme.ui_panel_background # or slightly darker?
            thumb_color = self.theme.button_disabled # generic greyish
            thumb_hover = self.theme.button_border
            thumb_active = self.theme.button_pressed

        # Fallback if theme colors are not ideal for scrollbar, maybe add to theme later
        # For now reusing button colors is a decent heuristic for "interactive element"
        
        self.configure(bg=bg_color)
        
        # Draw track (optional, maybe just bg)
        
        # Draw Thumb
        current_thumb_color = thumb_color
        if self.dragging:
            current_thumb_color = thumb_active
        elif self.hovering:
            current_thumb_color = thumb_hover
            
        if self.orient == 'vertical':
            full_len = self.height
            thickness = self.width
            
            y1 = full_len * self.thumb_start
            y2 = full_len * self.thumb_end
            
            # Min thumb size
            if y2 - y1 < 10:
                mid = (y1 + y2) / 2
                y1 = mid - 5
                y2 = mid + 5
            
            self.create_rounded_rect(2, y1, thickness-2, y2, 4, fill=current_thumb_color, outline="")
            
        else: # horizontal
            full_len = self.width
            thickness = self.height
            
            x1 = full_len * self.thumb_start
            x2 = full_len * self.thumb_end
            
             # Min thumb size
            if x2 - x1 < 10:
                mid = (x1 + x2) / 2
                x1 = mid - 5
                x2 = mid + 5
                
            self.create_rounded_rect(x1, 2, x2, thickness-2, 4, fill=current_thumb_color, outline="")

    def _on_resize(self, event):
        if self.orient == 'vertical':
            self.height = event.height
            self.width = event.width
        else:
            self.width = event.width
            self.height = event.height
        self._draw()

    def _on_enter(self, event):
        self.hovering = True
        self._draw()

    def _on_leave(self, event):
        self.hovering = False
        if not self.dragging:
            self._draw()

    def _on_press(self, event):
        self.dragging = True
        self.drag_start_thumb_start = self.thumb_start
        if self.orient == 'vertical':
            self.drag_start_pos = event.y
        else:
            self.drag_start_pos = event.x
        self._draw()

    def _on_release(self, event):
        self.dragging = False
        self._draw()

    def _on_drag(self, event):
        if not self.command:
            return

        if self.orient == 'vertical':
            delta_px = event.y - self.drag_start_pos
            total_px = self.height
        else:
            delta_px = event.x - self.drag_start_pos
            total_px = self.width
            
        if total_px <= 0:
            return

        delta_pct = delta_px / total_px
        new_start = self.drag_start_thumb_start + delta_pct
        
        # Clamp handled by widget usually, but we send 'moveto'
        self.command('moveto', new_start)

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._draw()

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)
