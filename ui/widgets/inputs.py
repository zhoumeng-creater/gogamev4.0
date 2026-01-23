import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Any
from ui.themes import Theme
from .base import ThemeAwareMixin


def _font_tuple(theme: Optional[Theme], size: int, weight: Optional[str] = None):
    family = "Arial"
    if theme:
        family = (theme.font_family or "Arial").split(",")[0].strip()
    if weight:
        return (family, size, weight)
    return (family, size)

class ModernEntry(tk.Canvas, ThemeAwareMixin):
    """
    Styled entry with custom border, focus effects, and placeholder text.
    Uses a Canvas as a container to draw the border, with a native Entry widget placed inside.
    """
    def __init__(self, parent, theme: Optional[Theme] = None, 
                 width: int = 200, height: int = 35, 
                 placeholder: str = "", show: Optional[str] = None,
                 textvariable: Optional[tk.StringVar] = None,
                 font_size: int = 10, **kwargs):
        
        # Initialize Canvas container
        tk.Canvas.__init__(self, parent, width=width, height=height, 
                           highlightthickness=0, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.width = width
        self.height = height
        self.placeholder_text = placeholder
        self.show_char = show
        self.font_size = font_size
        
        # State
        self.is_focused = False
        self.is_hovered = False
        self.state = 'normal'
        
        # Create text variable if not provided
        self.var = textvariable if textvariable else tk.StringVar()
        
        # Determine internal font
        self.font = _font_tuple(theme, font_size)
        
        # Actual Entry widget
        self.entry = tk.Entry(self, bd=0, highlightthickness=0, 
                              textvariable=self.var, font=self.font,
                              show=show)
        
        # Place entry inside canvas (centered)
        # We'll adjust the window size in _draw, but initial placement needed
        self.entry_window = self.create_window(10, height//2, window=self.entry, anchor='w', width=width-20)
        
        # Bind events
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda e: self.entry.focus_set())
        
        # Placeholder logic
        if self.placeholder_text:
            self._update_placeholder()
            self.var.trace_add("write", lambda *args: self._update_placeholder_style())
            
        self._draw()

    def _draw(self):
        self.delete("border")
        
        if not self.theme:
            # Fallback colors
            bg = "#FFFFFF"
            border = "#C0C0C0"
            focus = "#4080FF"
            text_color = "#000000"
        else:
            bg = self.theme.input_background
            border = self.theme.input_border
            focus = self.theme.input_focus_border
            text_color = self.theme.input_text
            
        # Determine current border color
        if self.state == 'disabled':
            current_border = border # Could dim this
            bg = "#F0F0F0" # Disabled bg
        elif self.is_focused:
            current_border = focus
        elif self.is_hovered:
            current_border = focus # Or slight variation
        else:
            current_border = border
            
        # Update Canvas background to match (for corners if not rounded, or just transparent-ish)
        # Actually canvas bg should match parent or transparent if possible, 
        # but here we fill the "box" with input_background.
        
        try:
            parent_bg = self.master.cget('bg')
        except Exception:
            # Likely a ttk widget or other widget without bg option.
            # Try to guess or use default.
            if self.theme:
                parent_bg = self.theme.ui_panel_background
            else:
                parent_bg = "#F0F0F0"

        self.configure(bg=parent_bg) # Match parent bg for the canvas itself
        
        # Draw rounded rect for border/background
        radius = 6
        self._create_rounded_rect(1, 1, self.width-1, self.height-1, radius, 
                                  fill=bg, outline=current_border, width=1, tags="border")
        
        # Update Entry colors
        self.entry.configure(bg=bg, fg=text_color, disabledbackground=bg)
        
        # Re-stack entry on top
        self.tag_raise(self.entry_window)

    def _create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def _on_focus_in(self, event):
        self.is_focused = True
        self._draw()
        
    def _on_focus_out(self, event):
        self.is_focused = False
        self._draw()
        
    def _on_enter(self, event):
        self.is_hovered = True
        if not self.is_focused:
            self._draw()
            
    def _on_leave(self, event):
        self.is_hovered = False
        if not self.is_focused:
            self._draw()
            
    def _update_placeholder(self):
        # Basic placeholder handling - simplified for now
        # Ideally we might draw text on canvas if empty, or use the entry with grey color
        pass
        
    def _update_placeholder_style(self):
        # Can implement style toggling here
        pass

    def get(self):
        return self.var.get()
        
    def set(self, value):
        self.var.set(value)

    def update_theme(self, theme: Theme):
        self.theme = theme
        self.font = _font_tuple(theme, self.font_size)
        try:
            self.entry.configure(font=self.font)
        except Exception:
            pass
        self._draw()


class ModernCheckbutton(tk.Canvas, ThemeAwareMixin):
    """
    Custom drawn checkbox.
    """
    def __init__(self, parent, text: str = "", variable: Optional[tk.BooleanVar] = None,
                 command: Optional[Callable] = None, theme: Optional[Theme] = None, **kwargs):
        tk.Canvas.__init__(self, parent, height=24, highlightthickness=0, cursor="hand2", **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.text = text
        self.variable = variable if variable else tk.BooleanVar()
        self.command = command
        self._is_hovered = False
        
        # Calculate width needed
        font = _font_tuple(self.theme, 10)
        text_width = getattr(self, 'measure_text_width', lambda t, f: len(t) * 8)(text, font) # Simplified measure
        self.width = 24 + 8 + text_width + 10 # Icon + pad + text + pad
        self.configure(width=self.width)
        
        self.bind("<Button-1>", self._toggle)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Listen to variable changes
        self.variable_trace = self.variable.trace_add("write", lambda *a: self._draw())
        
        self._draw()
        
    # Helper to measure text (rough approx if font metrics not avail in easy way without font obj)
    # Ideally should use tkFont.Font(font=...).measure(text)
    
    def _toggle(self, event=None):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()
        self._draw()
        
    def _on_enter(self, event):
        self._is_hovered = True
        self._draw()
        
    def _on_leave(self, event):
        self._is_hovered = False
        self._draw()
        
    def _draw(self):
        self.delete("all")
        
        if not self.theme:
            # Fallback
            bg = "#F5F5DC" 
            fg = "#2C2C2C"
            accent_bg = "#D4A574" 
            check_color = "#FFFFFF"
        else:
            bg = self.theme.ui_panel_background
            fg = self.theme.ui_text_primary
            accent_bg = self.theme.button_background
            check_color = self.theme.button_text
            
        self.configure(bg=bg)
        
        checked = self.variable.get()
        
        # Box coordinates
        bx, by, bs = 2, 4, 16 
        
        # Draw box
        box_outline = fg if self._is_hovered else self.theme.ui_text_secondary if self.theme else "#666"
        box_fill = accent_bg if checked else bg
        
        self.create_rectangle(bx, by, bx+bs, by+bs, outline=box_outline, fill=box_fill, width=1.5, tags="box")
        
        # Draw checkmark
        if checked:
            # Checkmark points
            cx, cy = bx + 2, by + 4
            self.create_line(cx, cy+4, cx+4, cy+8, cx+10, cy, fill=check_color, width=2, capstyle="round")
            
        # Draw text
        self.create_text(bx + bs + 8, 12, text=self.text, anchor='w', fill=fg, font=_font_tuple(self.theme, 10))

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._draw()


class ModernSwitch(tk.Canvas, ThemeAwareMixin):
    """
    Toggle switch style checkbox.
    """
    def __init__(self, parent, text: str = "", variable: Optional[tk.BooleanVar] = None,
                 command: Optional[Callable] = None, theme: Optional[Theme] = None, **kwargs):
        tk.Canvas.__init__(self, parent, height=24, highlightthickness=0, cursor="hand2", **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.text = text
        self.variable = variable if variable else tk.BooleanVar()
        self.command = command
        
        # Switch dimensions
        self.sw_w = 40
        self.sw_h = 20
        
        # Calc total width
        self.width = self.sw_w + 10 + (len(text)*8)
        self.configure(width=self.width)
        
        self.bind("<Button-1>", self._toggle)
        self.variable.trace_add("write", lambda *a: self._draw())
        
        self._draw()
        
    def _toggle(self, event=None):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()
            
    def _draw(self):
        self.delete("all")
        
        if not self.theme:
            bg_off = "#CCCCCC"
            bg_on = "#D4A574"
            handle = "#FFFFFF"
            fg = "#000000"
            panel_bg = "#F0F0F0"
        else:
            bg_off = self.theme.button_disabled#"#CCCCCC"
            bg_on = self.theme.success_color if hasattr(self.theme, 'success_color') else self.theme.button_background
            handle = "#FFFFFF"
            fg = self.theme.ui_text_primary
            panel_bg = self.theme.ui_panel_background
            
        self.configure(bg=panel_bg)
        
        active = self.variable.get()
        
        # Track color
        track_col = bg_on if active else bg_off
        
        # Draw track (rounded rect)
        r = self.sw_h / 2
        self.create_oval(0, 2, self.sw_h, 2+self.sw_h, fill=track_col, outline=track_col)
        self.create_oval(self.sw_w-self.sw_h, 2, self.sw_w, 2+self.sw_h, fill=track_col, outline=track_col)
        self.create_rectangle(r, 2, self.sw_w-r, 2+self.sw_h, fill=track_col, outline=track_col)
        
        # Draw handle
        hx = self.sw_w - r if active else r
        self.create_oval(hx-r+2, 4, hx+r-2, 2+self.sw_h-2, fill=handle, outline="")
        
        # Text
        if self.text:
            self.create_text(self.sw_w + 10, 12, text=self.text, anchor='w', fill=fg, font=_font_tuple(self.theme, 10))

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._draw()


class ModernRadioButton(tk.Canvas, ThemeAwareMixin):
    """
    Custom Radio Button.
    """
    def __init__(self, parent, text: str = "", value: Any = None, variable: Optional[tk.Variable] = None,
                 command: Optional[Callable] = None, theme: Optional[Theme] = None, **kwargs):
        tk.Canvas.__init__(self, parent, height=24, highlightthickness=0, cursor="hand2", **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.text = text
        self.value = value
        self.variable = variable
        self.command = command
        self._is_hovered = False
        
        self.width = 24 + 8 + (len(text) * 8)
        self.configure(width=self.width)
        
        self.bind("<Button-1>", self._select)
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        
        if self.variable:
            self.variable.trace_add("write", lambda *a: self._draw())
        
        self._draw()
        
    def _select(self, event=None):
        if self.variable:
            self.variable.set(self.value)
        if self.command:
            self.command()
        self._draw()
        
    def _set_hover(self, val):
        self._is_hovered = val
        self._draw()
        
    def _draw(self):
        self.delete("all")
        
        if self.theme:
            bg = self.theme.ui_panel_background
            fg = self.theme.ui_text_primary
            active_col = self.theme.button_background
        else:
            bg = "#F0F0F0"
            fg = "#000000"
            active_col = "#D4A574"
            
        self.configure(bg=bg)
        
        selected = (self.variable.get() == self.value) if self.variable else False
        
        # Outer circle
        cx, cy, r = 10, 12, 7
        outline = fg if self._is_hovered else self.theme.ui_text_secondary if self.theme else "#666"
        self.create_oval(cx-r, cy-r, cx+r, cy+r, outline=outline, width=1.5)
        
        # Inner dot
        if selected:
            ir = 4
            self.create_oval(cx-ir, cy-ir, cx+ir, cy+ir, fill=active_col, outline=active_col)
            
        # Text
        self.create_text(24, 12, text=self.text, anchor='w', fill=fg, font=_font_tuple(self.theme, 10))

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._draw()
