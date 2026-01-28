import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from typing import Optional, Callable, Any
from .menus import ModernMenu
from ui.themes import Theme
from .base import ThemeAwareMixin, resolve_font_family


def _font_tuple(theme: Optional[Theme], size: int, weight: Optional[str] = None):
    family = resolve_font_family(theme)
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
                 font_size: Optional[int] = None,
                 background: Optional[str] = None,
                 **kwargs):
        
        # Initialize Canvas container
        tk.Canvas.__init__(self, parent, width=width, height=height, 
                           highlightthickness=0, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.width = width
        self.height = height
        self.placeholder_text = placeholder
        self.show_char = show
        self.font_size = font_size if font_size is not None else (
            int(getattr(theme, "font_size_normal", 10)) if theme else 10
        )
        self._background_override = background
        
        # State
        self.is_focused = False
        self.is_hovered = False
        self.state = 'normal'
        
        # Create text variable if not provided
        self.var = textvariable if textvariable else tk.StringVar()
        
        # Determine internal font
        self.font = _font_tuple(theme, self.font_size)
        
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
            bg = self._background_override or "#FFFFFF"
            border = "#C0C0C0"
            focus = "#4080FF"
            text_color = "#000000"
        else:
            bg = self._background_override or self.theme.input_background
            border = self.theme.input_border
            focus = self.theme.input_focus_border
            text_color = self.theme.input_text
            
        # Determine current border color
        if self.state == 'disabled':
            current_border = border # Could dim this
            bg = self._background_override or "#F0F0F0" # Disabled bg
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
        self.entry.configure(
            bg=bg,
            fg=text_color,
            disabledbackground=bg,
            readonlybackground=bg,
        )
        
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


class ModernSpinbox(tk.Canvas, ThemeAwareMixin):
    """
    A themed spinbox with custom triangle arrows (no boxed buttons).
    """
    def __init__(
        self,
        parent,
        from_: float = 0.0,
        to: float = 100.0,
        increment: float = 1.0,
        textvariable: Optional[tk.Variable] = None,
        theme: Optional[Theme] = None,
        width: int = 140,
        height: int = 32,
        background: Optional[str] = None,
        font_size: Optional[int] = None,
        command: Optional[Callable] = None,
        state: str = "normal",
        **kwargs,
    ):
        tk.Canvas.__init__(self, parent, width=width, height=height, highlightthickness=0, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)

        self.width = width
        self.height = height
        self.from_ = from_
        self.to = to
        self.increment = increment
        self.command = command
        self.state = state
        self._background_override = background
        self._font_size = font_size
        self._hover_target: Optional[str] = None
        self._arrow_area = 22

        self.var = textvariable if textvariable is not None else tk.StringVar()
        self._is_int_var = isinstance(self.var, tk.IntVar)
        self._precision = self._infer_precision(increment)

        font_size_val = (
            int(font_size)
            if font_size is not None
            else int(getattr(theme, "font_size_normal", 10)) if theme else 10
        )
        self.font = _font_tuple(theme, font_size_val)

        self.entry = tk.Entry(self, bd=0, highlightthickness=0, textvariable=self.var, font=self.font)
        self.entry_window = self.create_window(8, height // 2, window=self.entry, anchor='w')

        self.configure(cursor="hand2" if state != "disabled" else "arrow")

        # Bindings
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Up>", lambda _e: self._step(1))
        self.entry.bind("<Down>", lambda _e: self._step(-1))
        self.entry.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Enter>", lambda _e: self._draw())
        self.bind("<Configure>", self._on_resize)

        self._draw()

    def _infer_precision(self, increment: float) -> int:
        try:
            if float(increment).is_integer():
                return 0
        except Exception:
            return 0
        text = str(increment)
        if "e" in text or "E" in text:
            try:
                from decimal import Decimal
                return max(0, abs(Decimal(text).as_tuple().exponent))
            except Exception:
                return 2
        if "." in text:
            return max(0, len(text.split(".")[1]))
        return 0

    def _current_value(self) -> float:
        try:
            return float(self.var.get())
        except Exception:
            return float(self.from_)

    def _set_value(self, value: float):
        if self._is_int_var:
            self.var.set(int(round(value)))
        else:
            if self._precision > 0:
                self.var.set(round(value, self._precision))
            else:
                self.var.set(value)
        if self.command:
            try:
                self.command()
            except Exception:
                pass

    def _step(self, direction: int):
        if self.state == "disabled":
            return
        current = self._current_value()
        new_value = current + direction * float(self.increment)
        new_value = max(float(self.from_), min(float(self.to), new_value))
        self._set_value(new_value)
        self._draw()

    def _on_click(self, event):
        target = self._hit_target(event.x, event.y)
        if target == "up":
            self._step(1)
            return
        if target == "down":
            self._step(-1)
            return
        self.entry.focus_set()

    def _on_motion(self, event):
        target = self._hit_target(event.x, event.y)
        if target != self._hover_target:
            self._hover_target = target
            self._draw()

    def _on_leave(self, _event):
        self._hover_target = None
        self._draw()

    def _on_mousewheel(self, event):
        if event.delta > 0:
            self._step(1)
        elif event.delta < 0:
            self._step(-1)

    def _on_focus_in(self, _event):
        self._draw(focused=True)

    def _on_focus_out(self, _event):
        self._draw(focused=False)

    def _on_resize(self, event):
        if event.width <= 1 or event.height <= 1:
            return
        self.width = event.width
        self.height = event.height
        self._draw()

    def _hit_target(self, x: int, y: int) -> Optional[str]:
        if x < self.width - self._arrow_area:
            return None
        return "up" if y < self.height / 2 else "down"

    def _position_entry(self):
        entry_width = max(20, self.width - self._arrow_area - 16)
        self.coords(self.entry_window, 8, self.height // 2)
        self.itemconfigure(self.entry_window, width=entry_width)

    def _draw(self, focused: Optional[bool] = None):
        self.delete("border")
        width = self.width
        height = self.height

        if self.theme:
            bg = self._background_override or self.theme.input_background
            border = self.theme.input_border
            focus = self.theme.input_focus_border
            fg = self.theme.input_text
            arrow = self.theme.ui_text_secondary
            arrow_hover = self.theme.button_hover
            disabled_fg = self.theme.ui_text_disabled
            disabled_bg = self.theme.button_disabled
        else:
            bg = self._background_override or "#FFFFFF"
            border = "#C0C0C0"
            focus = "#4080FF"
            fg = "#000000"
            arrow = "#666666"
            arrow_hover = "#4080FF"
            disabled_fg = "#888888"
            disabled_bg = "#F0F0F0"

        if self.state == "disabled":
            fg = disabled_fg
            arrow = disabled_fg
            bg = disabled_bg if not self._background_override else bg

        if focused is None:
            focused = self.entry == self.focus_get()

        current_border = focus if focused else border

        try:
            parent_bg = self.master.cget('bg')
        except Exception:
            parent_bg = self.theme.ui_panel_background if self.theme else "#F0F0F0"
        self.configure(bg=parent_bg)

        radius = 6
        self._create_rounded_rect(1, 1, width - 1, height - 1, radius,
                                  fill=bg, outline=current_border, width=1, tags="border")

        self.entry.configure(
            bg=bg,
            fg=fg,
            disabledbackground=bg,
            readonlybackground=bg,
            insertbackground=fg,
            state="disabled" if self.state == "disabled" else "normal",
        )

        mid_x = width - self._arrow_area / 2
        up_y = height * 0.35
        down_y = height * 0.65
        size = 4
        up_color = arrow_hover if self._hover_target == "up" and self.state != "disabled" else arrow
        down_color = arrow_hover if self._hover_target == "down" and self.state != "disabled" else arrow

        self.create_polygon(
            mid_x - size, up_y + size,
            mid_x + size, up_y + size,
            mid_x, up_y - size,
            fill=up_color,
            outline="",
            tags="border",
        )
        self.create_polygon(
            mid_x - size, down_y - size,
            mid_x + size, down_y - size,
            mid_x, down_y + size,
            fill=down_color,
            outline="",
            tags="border",
        )

        self._position_entry()
        self.tag_raise(self.entry_window)

    def _create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1,
            x2, y1 + r, x2, y1 + r, x2, y2 - r, x2, y2 - r, x2, y2,
            x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2, x1, y2,
            x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)

    def update_theme(self, theme: Theme):
        self.theme = theme
        font_size_val = (
            int(self._font_size)
            if self._font_size is not None
            else int(getattr(theme, "font_size_normal", 10))
        )
        self.font = _font_tuple(theme, font_size_val)
        try:
            self.entry.configure(font=self.font)
        except Exception:
            pass
        self._draw()

    def set_state(self, state: str):
        self.state = state
        self.configure(cursor="arrow" if state == "disabled" else "hand2")
        self._draw()

    def get(self):
        return self.var.get()

    def set(self, value: Any):
        try:
            self.var.set(value)
        except Exception:
            pass


class ModernSelect(tk.Canvas, ThemeAwareMixin):
    """
    A themed dropdown selector using ModernMenu (no native ttk combobox).
    """
    def __init__(self, parent, values: list, variable: Optional[tk.Variable] = None,
                 command: Optional[Callable] = None, theme: Optional[Theme] = None,
                 width: int = 200, height: int = 32,
                 font_size: Optional[int] = None,
                 background: Optional[str] = None,
                 state: str = "readonly",
                 **kwargs):
        cursor = kwargs.pop("cursor", "hand2" if state != "disabled" else "arrow")
        tk.Canvas.__init__(self, parent, width=width, height=height, highlightthickness=0, cursor=cursor, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)

        self.width = width
        self.height = height
        self.values = self._normalize_values(values)
        self.variable = variable if variable is not None else tk.StringVar()
        self.command = command
        self.state = state
        self.font_size = font_size if font_size is not None else (
            int(getattr(theme, "font_size_normal", 10)) if theme else 10
        )
        self._background_override = background
        self._menu = ModernMenu(self, theme=self.theme, min_width=self.width)

        if not self.variable.get() and self.values:
            self.variable.set(self.values[0][1])

        self._build_menu()
        self.variable.trace_add("write", lambda *_a: self._draw())

        self.bind("<Button-1>", self._toggle_menu)
        self.bind("<Configure>", self._on_resize)

        self._draw()

    def _normalize_values(self, values: list) -> list[tuple[str, Any]]:
        items = []
        for item in values:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                label, value = item
            else:
                label, value = item, item
            items.append((str(label), value))
        return items

    def _build_menu(self):
        try:
            self._menu.clear_items()
        except Exception:
            pass
        for label, value in self.values:
            self._menu.add_radiobutton(
                label=label,
                variable=self.variable,
                value=value,
                command=self._on_select,
            )

    def _current_label(self) -> str:
        current = self.variable.get()
        for label, value in self.values:
            if str(current) == str(value):
                return label
        return str(current) if current is not None else ""

    def _draw(self):
        self.delete("all")
        width = self.winfo_width() if self.winfo_width() > 1 else self.width
        height = self.winfo_height() if self.winfo_height() > 1 else self.height

        if self.theme:
            bg = self._background_override or self.theme.ui_panel_background
            border = self.theme.input_border
            fg = self.theme.input_text
            arrow = self.theme.ui_text_secondary
        else:
            bg = self._background_override or "#FFFFFF"
            border = "#C0C0C0"
            fg = "#000000"
            arrow = "#666666"

        if self.state == "disabled":
            fg = self.theme.ui_text_disabled if self.theme else "#888888"
            arrow = fg

        self.configure(bg=self.master.cget("bg") if hasattr(self.master, "cget") else bg)

        radius = 6
        self._create_rounded_rect(1, 1, width - 1, height - 1, radius, fill=bg, outline=border, width=1)

        font = _font_tuple(self.theme, self.font_size)
        text = self._current_label()
        self.create_text(10, height // 2, text=text, anchor="w", fill=fg, font=font)

        # Arrow
        self.create_text(width - 14, height // 2, text="▼", anchor="center", fill=arrow, font=font)

    def _create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def _on_resize(self, event):
        if event.width <= 1 or event.height <= 1:
            return
        self.width = event.width
        self.height = event.height
        self._menu.min_width = self.width
        self._draw()

    def _toggle_menu(self, _event=None):
        if self.state == "disabled":
            return
        if self._menu.winfo_viewable():
            self._menu.close_all()
            return
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self._menu.show(x, y)

    def _on_select(self):
        self._draw()
        if self.command:
            try:
                self.command()
            except Exception:
                pass

    def update_theme(self, theme: Theme):
        self.theme = theme
        try:
            self._menu.update_theme(theme)
        except Exception:
            pass
        self._draw()


class ModernCheckbutton(tk.Canvas, ThemeAwareMixin):
    """
    Custom drawn checkbox.
    """
    def __init__(self, parent, text: str = "", variable: Optional[tk.BooleanVar] = None,
                 command: Optional[Callable] = None, theme: Optional[Theme] = None,
                 font_size: Optional[int] = None, state: str = "normal", **kwargs):
        tk.Canvas.__init__(self, parent, height=24, highlightthickness=0, cursor="hand2", **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.text = text
        self.variable = variable if variable else tk.BooleanVar()
        self.command = command
        self.font_size = font_size if font_size is not None else (
            int(getattr(theme, "font_size_normal", 10)) if theme else 10
        )
        self.state = state
        self._is_hovered = False
        
        # Calculate width needed
        font = _font_tuple(self.theme, self.font_size)
        try:
            text_width = tkfont.Font(font=font).measure(text)
        except Exception:
            text_width = len(text) * 8
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
        if self.state == "disabled":
            return
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
        disabled = self.state == "disabled"
        if disabled and self.theme:
            fg = self.theme.ui_text_disabled
            accent_bg = self.theme.button_disabled
            check_color = self.theme.ui_text_disabled
        
        # Box coordinates
        bx, by, bs = 2, 4, 16 
        
        # Draw box
        box_outline = fg if self._is_hovered and not disabled else (
            self.theme.ui_text_secondary if self.theme else "#666"
        )
        box_fill = accent_bg if checked else bg
        
        self.create_rectangle(bx, by, bx+bs, by+bs, outline=box_outline, fill=box_fill, width=1.5, tags="box")
        
        # Draw checkmark
        if checked:
            # Checkmark points
            cx, cy = bx + 2, by + 4
            self.create_line(cx, cy+4, cx+4, cy+8, cx+10, cy, fill=check_color, width=2, capstyle="round")
            
        # Draw text
        self.create_text(
            bx + bs + 8,
            12,
            text=self.text,
            anchor='w',
            fill=fg,
            font=_font_tuple(self.theme, self.font_size),
        )

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._draw()

    def set_state(self, state: str):
        self.state = state
        self.configure(cursor="arrow" if state == "disabled" else "hand2")
        self._draw()


class ModernSwitch(tk.Canvas, ThemeAwareMixin):
    """
    Toggle switch style checkbox.
    """
    def __init__(self, parent, text: str = "", variable: Optional[tk.BooleanVar] = None,
                 command: Optional[Callable] = None, theme: Optional[Theme] = None,
                 state: str = "normal", **kwargs):
        tk.Canvas.__init__(self, parent, height=24, highlightthickness=0, cursor="hand2", **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.text = text
        self.variable = variable if variable else tk.BooleanVar()
        self.command = command
        self.state = state
        
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
        if self.state == "disabled":
            return
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

        if self.state == "disabled" and self.theme:
            fg = self.theme.ui_text_disabled
            bg_off = self.theme.button_disabled
            bg_on = self.theme.button_disabled
            handle = self.theme.ui_text_disabled
            
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
            self.create_text(
                self.sw_w + 10,
                12,
                text=self.text,
                anchor='w',
                fill=fg,
                font=_font_tuple(self.theme, 10),
            )

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._draw()

    def set_state(self, state: str):
        self.state = state
        self.configure(cursor="arrow" if state == "disabled" else "hand2")
        self._draw()


class ModernRadioButton(tk.Canvas, ThemeAwareMixin):
    """
    Custom Radio Button.
    """
    def __init__(self, parent, text: str = "", value: Any = None, variable: Optional[tk.Variable] = None,
                 command: Optional[Callable] = None, theme: Optional[Theme] = None,
                 font_size: Optional[int] = None, **kwargs):
        tk.Canvas.__init__(self, parent, height=24, highlightthickness=0, cursor="hand2", **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.text = text
        self.value = value
        self.variable = variable
        self.command = command
        self.font_size = font_size if font_size is not None else (
            int(getattr(theme, "font_size_normal", 10)) if theme else 10
        )
        self._is_hovered = False
        
        try:
            text_width = tkfont.Font(font=_font_tuple(self.theme, self.font_size)).measure(text)
        except Exception:
            text_width = len(text) * 8
        self.width = 24 + 8 + text_width
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
        self.create_text(24, 12, text=self.text, anchor='w', fill=fg, font=_font_tuple(self.theme, self.font_size))

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._draw()
