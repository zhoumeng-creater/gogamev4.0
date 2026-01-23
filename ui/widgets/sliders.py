import tkinter as tk
from typing import Optional, Callable
from ui.themes import Theme
from .base import ThemeAwareMixin

class ModernSlider(tk.Canvas, ThemeAwareMixin):
    """
    A custom slider widget.
    """
    def __init__(self, parent, from_: float = 0.0, to: float = 100.0, 
                 variable: Optional[tk.DoubleVar] = None, orient: str = 'horizontal',
                 theme: Optional[Theme] = None, length: int = 200, command: Optional[Callable] = None, **kwargs):
        height = 20 if orient == 'horizontal' else length
        width = length if orient == 'horizontal' else 20

        self.state = kwargs.pop("state", "normal")

        cursor = "arrow" if self.state == "disabled" else "hand2"
        kwargs.setdefault("cursor", cursor)

        tk.Canvas.__init__(self, parent, width=width, height=height, highlightthickness=0, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.from_ = float(from_)
        self.to = float(to)
        self.variable = variable
        self.orient = orient
        self.command = command
        self.length = length
        
        self.value = self.from_
        if self.variable:
            self.value = self.variable.get()
            self.trace_id = self.variable.trace_add("write", self._on_var_changed)
            
        self.hovering = False
        self.dragging = False
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", self._on_resize)
        
        self._draw()

    def _on_var_changed(self, *args):
        self.value = self.variable.get()
        self._draw()

    def set(self, value):
        value = max(self.from_, min(self.to, float(value)))
        self.value = value
        if self.variable:
            self.variable.set(value)
        self._draw()

    def get(self):
        return self.value

    def _draw(self):
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width <= 1: return
        
        # Style
        if self.theme:
            bg_color = self.theme.ui_panel_background
            if self.state == "disabled":
                track_color = self.theme.button_disabled
                active_color = self.theme.button_disabled
                knob_color = self.theme.button_disabled
            else:
                track_color = self.theme.button_disabled
                active_color = self.theme.button_pressed
                knob_color = self.theme.button_background
            knob_border = self.theme.button_border
        else:
            bg_color = "#F0F0F0"
            if self.state == "disabled":
                track_color = "#DDDDDD"
                active_color = "#DDDDDD"
                knob_color = "#DDDDDD"
            else:
                track_color = "#CCCCCC"
                active_color = "#4080FF"
                knob_color = "#FFFFFF"
            knob_border = "#808080"
            
        self.configure(bg=bg_color)
        
        # Calculate coords
        padding = 10
        
        pct = (self.value - self.from_) / (self.to - self.from_) if self.to != self.from_ else 0
        pct = max(0.0, min(1.0, pct))
        
        if self.orient == 'horizontal':
            track_y = height // 2
            track_start = padding
            track_end = width - padding
            track_len = track_end - track_start
            
            x = track_start + track_len * pct
            
            # Track background
            self.create_line(track_start, track_y, track_end, track_y, fill=track_color, width=4, capstyle="round")
            # Active track
            self.create_line(track_start, track_y, x, track_y, fill=active_color, width=4, capstyle="round")
            
            # Knob
            r = 8
            k_fill = knob_color if not self.dragging else active_color
            if self.state != "disabled" and self.hovering and not self.dragging:
                 k_fill = self.theme.button_hover if self.theme else "#E0E0E0"
                 
            self.create_oval(x-r, track_y-r, x+r, track_y+r, fill=k_fill, outline=knob_border, width=1)
            
        else:
            pass # Vertical todo if needed

    def _on_resize(self, event):
        self._draw()

    def _on_enter(self, event):
        if self.state == "disabled":
            return
        self.hovering = True
        self._draw()

    def _on_leave(self, event):
        if self.state == "disabled":
            return
        self.hovering = False
        if not self.dragging:
            self._draw()

    def _on_press(self, event):
        if self.state == "disabled":
            return
        self.dragging = True
        self._update_from_event(event)

    def _on_drag(self, event):
        if self.state == "disabled":
            return
        self._update_from_event(event)

    def _on_release(self, event):
        if self.state == "disabled":
            return
        self.dragging = False
        self._draw()
        if self.command:
            self.command(self.value)

    def _update_from_event(self, event):
        if self.state == "disabled":
            return
        width = self.winfo_width()
        padding = 10
        track_start = padding
        track_end = width - padding
        track_len = track_end - track_start
        
        if track_len <= 0: return
        
        x = max(track_start, min(track_end, event.x))
        pct = (x - track_start) / track_len
        
        self.value = self.from_ + (self.to - self.from_) * pct
        
        if self.variable:
            self.variable.set(self.value)
        
        self._draw()
        if self.command: # send continuous updates?
             # ttk.Scale triggers command on drag usually
             self.command(self.value)

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._draw()

    def configure(self, cnf=None, **kw):
        state_changed = False
        if cnf is None and not kw:
            return super().configure()
        if cnf:
            if isinstance(cnf, dict):
                kw = {**cnf, **kw}
            else:
                return super().configure(cnf, **kw)
        if "command" in kw:
            self.command = kw.pop("command")
        if "state" in kw:
            self.state = kw.pop("state")
            self.dragging = False
            self.hovering = False
            state_changed = True
            if "cursor" not in kw:
                kw["cursor"] = "arrow" if self.state == "disabled" else "hand2"
        result = super().configure(**kw) if kw else super().configure()
        if state_changed:
            self._draw()
        return result

    config = configure
