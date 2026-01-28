import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from typing import Optional, Callable, List, Any
try:
    from ui.themes import Theme
except ModuleNotFoundError:
    # Allow running this module directly by adding project root to sys.path.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from ui.themes import Theme
from .base import ThemeAwareMixin, resolve_font_family
from .buttons import ModernButton
from .scrolling import ModernScrollbar

class ModernMenuItem(tk.Canvas, ThemeAwareMixin):
    """
    A single item in a ModernMenu.
    """
    def __init__(self, parent, text: str, command: Optional[Callable], theme: Optional[Theme], 
                 shortcut: str = "", item_type: str = "command", 
                 variable: Optional[tk.Variable] = None, value: Any = None, 
                 submenu: Optional['ModernMenu'] = None,
                 state: str = "normal",
                 font_style: str = "normal",
                 **kwargs):
        cursor = kwargs.pop("cursor", "hand2" if state != "disabled" else "arrow")
        tk.Canvas.__init__(self, parent, height=30, highlightthickness=0, cursor=cursor, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.text = text
        self.command = command
        self.shortcut = shortcut
        self.item_type = item_type # command, separator, check, radio, submenu
        self.variable = variable
        self.value = value
        self.submenu = submenu
        self.state = state
        self.font_style = font_style
        
        if self.item_type == "separator":
            self.configure(height=10)
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", self._on_resize)
        
        self.width = 200 # Default
        self.hovering = False
        
        # Trace variable if check/radio
        if self.variable:
            self.trace_id = self.variable.trace_add("write", lambda *args: self._draw())

        self._draw()

    def _draw(self):
        self.delete("all")
        width = self.winfo_width()
        self.width = width if width > 1 else 200
        height = self.winfo_height()
        
        if not self.theme: 
             # Fallback
             bg = "#FFFFFF"
             fg = "#000000"
             hover_bg = "#E0E0E0"
             accent = "#007ACC"
        else:
             bg = self.theme.ui_panel_background
             fg = self.theme.ui_text_primary
             hover_bg = self.theme.button_hover
             accent = self.theme.button_pressed

        if self.item_type == "separator":
            self.configure(bg=bg)
            self.create_line(10, height//2, self.width-10, height//2, fill=fg, width=1)
            return

        disabled = self.state == "disabled"
        selected_bg = self.theme.input_background if self.theme else "#F2F2F2"
        is_checked = False
        if self.variable:
            if self.item_type == "check":
                val = self.variable.get()
                is_checked = bool(val)
            elif self.item_type == "radio":
                is_checked = (str(self.variable.get()) == str(self.value))

        if not disabled:
            if is_checked:
                current_bg = selected_bg
            else:
                current_bg = hover_bg if self.hovering else bg
        else:
            current_bg = bg
        self.configure(bg=current_bg)

        font_family = resolve_font_family(self.theme)
        font_size = max(10, int(getattr(self.theme, "font_size_small", 10))) if self.theme else 10
        font_style = "italic" if self.font_style == "italic" else "normal"
        font = (font_family, font_size, font_style) if font_style != "normal" else (font_family, font_size)
        bold_font = (font_family, font_size, "bold")
        arrow_font = (font_family, max(8, font_size - 2))
        if disabled:
            text_color = self.theme.ui_text_disabled if self.theme else "#888888"
        else:
            text_color = fg
        
        # Icon/Check area
        icon_x = 15
        text_x = 35
        
        # Check/Radio indicator
        if self.variable:
            if is_checked:
                # Draw checkmark or dot
                self.create_text(icon_x, height//2, text="✓" if self.item_type == "check" else "●",
                                 fill=accent if not disabled else text_color, font=bold_font)

        # Text
        self.create_text(text_x, height//2, text=self.text, fill=text_color, font=font, anchor="w")
        
        # Shortcut or Submenu arrow
        if self.shortcut and self.item_type != "submenu":
            self.create_text(self.width-15, height//2, text=self.shortcut, fill=text_color, font=font, anchor="e")
        elif self.item_type == "submenu":
            self.create_text(self.width-15, height//2, text="▶", fill=text_color, font=arrow_font, anchor="e")

    def _on_resize(self, event):
        self._draw()

    def _on_enter(self, event):
        if self.item_type != "separator" and self.state != "disabled":
            self.hovering = True
            self._draw()
            
            if self.item_type == "submenu" and self.submenu:
                # Show submenu
                x = self.winfo_rootx() + self.width
                y = self.winfo_rooty()
                self.submenu.show(x, y)

    def _on_leave(self, event):
        if self.item_type != "separator" and self.state != "disabled":
            self.hovering = False
            self._draw()
            # Logic to close submenu if not entering submenu?
            # Complex. For now, let submenu handle its own focus out.
            
    def _on_click(self, event):
        pass

    def _on_release(self, event):
        if self.state == "disabled":
            return
        if self.item_type == "separator":
            return
            
        if self.item_type in ["check", "radio"] and self.variable:
            # ... (same) ...
            if self.item_type == "check":
                try:
                    current = self.variable.get()
                    if isinstance(current, bool):
                        self.variable.set(not current)
                    elif isinstance(current, int):
                        self.variable.set(1 - current)
                except:
                    pass
            elif self.item_type == "radio":
                self.variable.set(self.value)

        # Close menu (unless submenu) before running command to avoid z-order issues.
        top_menu = None
        menu_set = set()
        root_window = None
        if self.item_type != "submenu":
            try:
                top_menu = self.winfo_toplevel()
            except Exception:
                top_menu = None
            if top_menu and hasattr(top_menu, "_collect_menus"):
                try:
                    menu_set = top_menu._collect_menus()
                except Exception:
                    menu_set = {top_menu}
            elif top_menu:
                menu_set = {top_menu}

            if top_menu and hasattr(top_menu, "_root_window"):
                root_window = getattr(top_menu, "_root_window", None)

        pre_existing = set()
        if root_window and top_menu and hasattr(top_menu, "_non_menu_toplevels"):
            try:
                pre_existing = set(top_menu._non_menu_toplevels(root_window, menu_set))
            except Exception:
                pre_existing = set()

        if self.item_type != "submenu":
            if top_menu and hasattr(top_menu, "close_all"):
                try:
                    top_menu.close_all()
                except Exception:
                    pass

        if self.command and self.item_type != "submenu":
            try:
                (top_menu or self).after(0, self.command)
            except Exception:
                self.command()

        if root_window and top_menu and hasattr(top_menu, "_restore_owner_focus") and self.item_type != "submenu":
            try:
                root_window.after(140, lambda: top_menu._restore_owner_focus(pre_existing, menu_set))
            except Exception:
                top_menu._restore_owner_focus(pre_existing, menu_set)

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._draw()


class ModernMenu(tk.Toplevel, ThemeAwareMixin):
    """
    A custom menu popup (Toplevel).
    """
    def __init__(self, parent, theme: Optional[Theme] = None, max_height: Optional[int] = None,
                 min_width: int = 200, **kwargs):
        tk.Toplevel.__init__(self, parent, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.overrideredirect(True)
        self.withdraw() # Start hidden

        self._root_window = None
        try:
            self._root_window = parent.winfo_toplevel()
            if self._root_window is not self:
                self.transient(self._root_window)
        except Exception:
            self._root_window = None

        self.max_height = max_height
        self.min_width = min_width
        self._visible_height = 0
        self._content_width = min_width
        self._scrollbar_width = 12

        self._frame = ttk.Frame(self)
        self._frame.pack(fill="both", expand=True, padx=1, pady=1)

        self._canvas = tk.Canvas(self._frame, highlightthickness=0, borderwidth=0)
        self._canvas.pack(side="left", fill="both", expand=True)

        self._scrollbar = ModernScrollbar(
            self._frame,
            orient='vertical',
            command=self._canvas.yview,
            theme=self.theme,
            width=self._scrollbar_width,
            autohide=True,
            match_widget=self._canvas,
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._scrollbar.pack(side="right", fill="y")

        self.container = ttk.Frame(self._canvas)
        self._container_window = self._canvas.create_window((0, 0), window=self.container, anchor="nw")
        self.container.bind("<Configure>", self._on_container_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)
        
        self.items = []
        self._submenus = []
        self._parent_menu = None
        
        # Bindings to close
        self.bind("<FocusOut>", self._on_focus_out)
        
        self._apply_style()

    def add_cascade(self, label: str, menu: 'ModernMenu'):
        # menu arg is the submenu
        menu._parent_menu = self
        if menu not in self._submenus:
            self._submenus.append(menu)
        item = ModernMenuItem(self.container, label, None, self.theme, item_type="submenu", submenu=menu)
        item.pack(fill="x")
        self.items.append(item)
        # We need to make sure the submenu's master is correct or it manages itself?
        # ModernMenu is a Toplevel, so it's independent. But we logic link them.

    def add_command(self, label: str, command: Optional[Callable], shortcut: str = "",
                    state: str = "normal", font_style: str = "normal"):
        item = ModernMenuItem(
            self.container,
            label,
            command,
            self.theme,
            shortcut=shortcut,
            state=state,
            font_style=font_style,
        )
        item.pack(fill="x")
        self.items.append(item)
    
    def add_checkbutton(self, label: str, variable: tk.Variable, command: Optional[Callable] = None,
                        state: str = "normal"):
        item = ModernMenuItem(
            self.container,
            label,
            command,
            self.theme,
            item_type="check",
            variable=variable,
            state=state,
        )
        item.pack(fill="x")
        self.items.append(item)

    def add_radiobutton(self, label: str, variable: tk.Variable, value: Any, command: Optional[Callable] = None,
                        state: str = "normal"):
        item = ModernMenuItem(
            self.container,
            label,
            command,
            self.theme,
            item_type="radio",
            variable=variable,
            value=value,
            state=state,
        )
        item.pack(fill="x")
        self.items.append(item)

    def add_separator(self):
        item = ModernMenuItem(self.container, "", None, self.theme, item_type="separator")
        item.pack(fill="x")
        self.items.append(item)

    def clear_items(self):
        for item in self.items:
            try:
                item.destroy()
            except Exception:
                pass
        self.items = []
        try:
            self._canvas.configure(scrollregion=(0, 0, self.min_width, 1))
            self._scrollbar.set(0.0, 1.0)
        except Exception:
            pass

    def show(self, x, y):
        # Calculate size needed
        # Force a geometry update
        if not self._exists():
            return
        self.update_idletasks()

        if not self.items:
            return
        
        req_width = max(self.min_width, 200)
        total_height = sum([item.winfo_reqheight() for item in self.items]) or 1

        screen_h = self.winfo_screenheight()
        screen_w = self.winfo_screenwidth()
        max_height = self.max_height if self.max_height else int(screen_h * 0.6)
        visible_height = min(total_height, max_height)
        needs_scroll = total_height > visible_height + 1

        scrollbar_width = self._scrollbar_width if needs_scroll else 0
        total_width = req_width + scrollbar_width

        # Update canvas and scroll region
        self._content_width = req_width
        self._visible_height = visible_height
        self._canvas.configure(width=req_width, height=visible_height)
        self._canvas.itemconfigure(self._container_window, width=req_width)
        self._canvas.configure(scrollregion=(0, 0, req_width, total_height))
        self._canvas.yview_moveto(0)
        if needs_scroll:
            self._scrollbar.set(0.0, visible_height / max(total_height, 1))
        else:
            self._scrollbar.set(0.0, 1.0)

        # Ensure menu stays on screen
        if x + total_width > screen_w - 10:
            x = max(0, screen_w - total_width - 10)
        if y + visible_height > screen_h - 10:
            y = max(0, screen_h - visible_height - 10)
        
        self.geometry(f"{total_width}x{visible_height}+{x}+{y}")
        self.deiconify()
        try:
            self.lift()
        except Exception:
            pass
        try:
            self.focus_force()
        except Exception:
            try:
                self.focus_set()
            except Exception:
                pass

    def close(self):
        if not self._exists():
            return
        try:
            self.withdraw()
            self._canvas.yview_moveto(0)
        except tk.TclError:
            pass

    def _close_recursive(self):
        for submenu in list(self._submenus):
            try:
                submenu._close_recursive()
            except Exception:
                pass
        self.close()

    def close_all(self):
        root = self
        while getattr(root, "_parent_menu", None):
            root = root._parent_menu
        if not root._exists():
            return
        root._close_recursive()

    def _collect_toplevels(self, root: tk.Misc) -> List[tk.Toplevel]:
        result: List[tk.Toplevel] = []
        stack = [root]
        seen = set()
        while stack:
            widget = stack.pop()
            if widget in seen:
                continue
            seen.add(widget)
            try:
                children = widget.winfo_children()
            except Exception:
                continue
            for child in children:
                if child in seen:
                    continue
                if isinstance(child, tk.Toplevel):
                    result.append(child)
                stack.append(child)
        return result

    def _non_menu_toplevels(self, root: tk.Misc, menus: set) -> List[tk.Toplevel]:
        windows: List[tk.Toplevel] = []
        for win in self._collect_toplevels(root):
            if win in menus:
                continue
            try:
                if not win.winfo_exists():
                    continue
                if not win.winfo_viewable():
                    continue
            except Exception:
                continue
            windows.append(win)
        return windows

    def _restore_owner_focus(self, pre_existing: Optional[set] = None, menus: Optional[set] = None) -> None:
        root = self._root_window
        if not root:
            return
        try:
            if not root.winfo_exists():
                return
        except Exception:
            return

        try:
            grab_widget = root.grab_current()
        except Exception:
            grab_widget = None
        if grab_widget and grab_widget is not root:
            return

        menu_set = menus if menus is not None else self._collect_menus()
        pre = pre_existing if pre_existing is not None else set()
        try:
            current_windows = self._non_menu_toplevels(root, menu_set)
        except Exception:
            current_windows = []

        new_windows = [w for w in current_windows if w not in pre]
        target = new_windows[-1] if new_windows else None
        if not target:
            target = root

        try:
            target.deiconify()
            target.lift()
            target.focus_force()
            if sys.platform.startswith("win"):
                target.attributes("-topmost", True)
                target.after(80, lambda: target.attributes("-topmost", False))
        except Exception:
            pass

    def _exists(self) -> bool:
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def _on_focus_out(self, event):
        # Check if focus moved to a child? Toplevel focus out is tricky.
        # Simple approach: close on any click outside.
        # For now, just close.
        focus_widget = self.focus_get()
        if focus_widget and self._is_focus_within_menus(focus_widget):
            return
        self.close_all()

    def _collect_menus(self):
        menus = {self}
        for submenu in self._submenus:
            menus.update(submenu._collect_menus())
        return menus

    def _is_focus_within_menus(self, widget: tk.Widget) -> bool:
        try:
            top = widget.winfo_toplevel()
        except Exception:
            return False
        return top in self._collect_menus()

    def _apply_style(self):
         if self.theme:
             bg = self.theme.ui_panel_background
             border = self.theme.ui_panel_border
         else:
             bg = "#FFFFFF"
             border = "#000000"
             
         self.configure(bg=border) # Border color via background
         
         style_name = f"ModernMenuFrame_{id(self)}.TFrame"
         style = ttk.Style()
         style.configure(style_name, background=bg)
         try:
             self._frame.configure(style=style_name)
         except Exception:
             pass
         self.container.configure(style=style_name)
         try:
             self._canvas.configure(bg=bg)
         except Exception:
             pass

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._apply_style()
        for item in self.items:
            item.update_theme(theme)
        if getattr(self, "_scrollbar", None):
            self._scrollbar.update_theme(theme)

    def _on_container_configure(self, _event):
        if not self._exists():
            return
        try:
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        except Exception:
            pass

    def _on_canvas_configure(self, event):
        if not self._exists():
            return
        try:
            self._canvas.itemconfigure(self._container_window, width=event.width)
        except Exception:
            pass

    def _bind_mousewheel(self, _event=None):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event=None):
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if not self._exists():
            return
        if self._visible_height <= 0:
            return
        try:
            delta = int(-1 * (event.delta / 120))
        except Exception:
            delta = -1 if getattr(event, 'num', 0) == 4 else 1
        self._canvas.yview_scroll(delta, "units")


class ModernMenuBar(ttk.Frame, ThemeAwareMixin):
    """
    Replaces the standard window menu bar.
    """
    def __init__(self, parent, theme: Optional[Theme] = None, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.buttons = {}
        self.menus = {}
        self._show_job = None
        self._button_min_width = 60
        self._button_padding_x = 16
        self._button_min_height = 30
        
        self._apply_style()

    def _button_font(self):
        if self.theme:
            font_family = resolve_font_family(self.theme)
            font_size = max(10, int(getattr(self.theme, "font_size_small", 10)))
        else:
            font_family = resolve_font_family(None)
            font_size = 10
        return (font_family, font_size, "bold")

    def _measure_button_size(self, label: str) -> tuple[int, int]:
        try:
            font = tkfont.Font(family=self._button_font()[0],
                               size=self._button_font()[1],
                               weight="bold")
            text_width = font.measure(label or "")
            text_height = font.metrics("linespace")
        except Exception:
            text_width = 0
            text_height = 0
        width = max(self._button_min_width, text_width + self._button_padding_x * 2)
        height = max(self._button_min_height, text_height + 12)
        return int(width), int(height)

    def add_cascade(self, label: str, menu: ModernMenu):
        width, height = self._measure_button_size(label)
        btn = ModernButton(self, text=label, width=width, height=height, 
                           command=lambda l=label: self._defer_show_menu(l), theme=self.theme)
        btn.pack(side="left", padx=2)
        
        self.buttons[label] = btn
        self.menus[label] = menu

    def _defer_show_menu(self, label: str) -> None:
        # Defer menu popup until after the button release event finishes.
        if self._show_job:
            try:
                self.after_cancel(self._show_job)
            except Exception:
                pass
        self._show_job = self.after_idle(lambda: self._show_menu(label))

    def _show_menu(self, label):
        menu = self.menus[label]
        btn = self.buttons[label]

        if menu.winfo_viewable():
            menu.close_all()
            return

        for other_label, other_menu in self.menus.items():
            if other_label == label:
                continue
            try:
                other_menu.close_all()
            except Exception:
                other_menu.close()
        
        # Calculate position
        x = btn.winfo_rootx()
        y = btn.winfo_rooty() + btn.winfo_height()
        
        menu.show(x, y)

    def _apply_style(self):
        style_name = f"ModernMenuBar_{id(self)}.TFrame"
        style = ttk.Style()
        if self.theme:
            bg = self.theme.ui_panel_background
        else:
            bg = "#E8DCC0"
        style.configure(style_name, background=bg)
        self.configure(style=style_name)

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._apply_style()
        for btn in self.buttons.values():
            btn.update_theme(theme)
        for label, btn in self.buttons.items():
            width, height = self._measure_button_size(label)
            try:
                btn.configure(width=width, height=height)
            except Exception:
                pass
        for menu in self.menus.values():
            menu.update_theme(theme)

