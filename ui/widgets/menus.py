import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List, Any
from ui.themes import Theme
from .base import ThemeAwareMixin
from .buttons import ModernButton

class ModernMenuItem(tk.Canvas, ThemeAwareMixin):
    """
    A single item in a ModernMenu.
    """
    def __init__(self, parent, text: str, command: Optional[Callable], theme: Optional[Theme], 
                 shortcut: str = "", item_type: str = "command", 
                 variable: Optional[tk.Variable] = None, value: Any = None, 
                 submenu: Optional['ModernMenu'] = None, **kwargs):
        tk.Canvas.__init__(self, parent, height=30, highlightthickness=0, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.text = text
        self.command = command
        self.shortcut = shortcut
        self.item_type = item_type # command, separator, check, radio, submenu
        self.variable = variable
        self.value = value
        self.submenu = submenu
        
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

        current_bg = hover_bg if self.hovering else bg
        self.configure(bg=current_bg)

        if self.theme:
            font_family = (self.theme.font_family or "Arial").split(',')[0].strip()
            font_size = max(10, int(getattr(self.theme, "font_size_small", 10)))
        else:
            font_family = "Segoe UI"
            font_size = 10
        font = (font_family, font_size)
        bold_font = (font_family, font_size, "bold")
        arrow_font = (font_family, max(8, font_size - 2))
        
        # Icon/Check area
        icon_x = 15
        text_x = 35
        
        # Check/Radio indicator
        if self.variable:
            is_checked = False
            if self.item_type == "check":
                # BooleanVar or 0/1
                val = self.variable.get()
                is_checked = bool(val)
            elif self.item_type == "radio":
                is_checked = (str(self.variable.get()) == str(self.value))
            
            if is_checked:
                # Draw checkmark or dot
                self.create_text(icon_x, height//2, text="✓" if self.item_type == "check" else "●",
                                 fill=accent, font=bold_font)

        # Text
        self.create_text(text_x, height//2, text=self.text, fill=fg, font=font, anchor="w")
        
        # Shortcut or Submenu arrow
        if self.shortcut and self.item_type != "submenu":
            self.create_text(self.width-15, height//2, text=self.shortcut, fill=fg, font=font, anchor="e")
        elif self.item_type == "submenu":
            self.create_text(self.width-15, height//2, text="▶", fill=fg, font=arrow_font, anchor="e")

    def _on_resize(self, event):
        self._draw()

    def _on_enter(self, event):
        if self.item_type != "separator":
            self.hovering = True
            self._draw()
            
            if self.item_type == "submenu" and self.submenu:
                # Show submenu
                x = self.winfo_rootx() + self.width
                y = self.winfo_rooty()
                self.submenu.show(x, y)

    def _on_leave(self, event):
        if self.item_type != "separator":
            self.hovering = False
            self._draw()
            # Logic to close submenu if not entering submenu?
            # Complex. For now, let submenu handle its own focus out.
            
    def _on_click(self, event):
        pass

    def _on_release(self, event):
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
        
        if self.command:
             self.command()
             
        # Close menu (unless submenu)
        if self.item_type != "submenu":
             # Close all levels of menus (root + submenus).
             self.master.master.close_all() 

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._draw()


class ModernMenu(tk.Toplevel, ThemeAwareMixin):
    """
    A custom menu popup (Toplevel).
    """
    def __init__(self, parent, theme: Optional[Theme] = None, **kwargs):
        tk.Toplevel.__init__(self, parent, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.overrideredirect(True)
        self.withdraw() # Start hidden
        
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        
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

    def add_command(self, label: str, command: Callable, shortcut: str = ""):
        item = ModernMenuItem(self.container, label, command, self.theme, shortcut=shortcut)
        item.pack(fill="x")
        self.items.append(item)
    
    def add_checkbutton(self, label: str, variable: tk.Variable, command: Optional[Callable] = None):
        item = ModernMenuItem(self.container, label, command, self.theme, item_type="check", variable=variable)
        item.pack(fill="x")
        self.items.append(item)

    def add_radiobutton(self, label: str, variable: tk.Variable, value: Any, command: Optional[Callable] = None):
        item = ModernMenuItem(self.container, label, command, self.theme, item_type="radio", variable=variable, value=value)
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

    def show(self, x, y):
        # Calculate size needed
        # Force a geometry update
        self.update_idletasks()

        if not self.items:
            return
        
        req_width = 200 # Fixed width for now
        total_height = sum([item.winfo_reqheight() for item in self.items])
        if total_height <= 0:
            total_height = 1
        
        self.geometry(f"{req_width}x{total_height}+{x}+{y}")
        self.deiconify()
        self.focus_set() # Grab focus to detect blur

    def close(self):
        self.withdraw()

    def _close_recursive(self):
        for submenu in self._submenus:
            submenu._close_recursive()
        self.close()

    def close_all(self):
        root = self
        while getattr(root, "_parent_menu", None):
            root = root._parent_menu
        root._close_recursive()

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
         self.container.pack_configure(padx=1, pady=1) # 1px border
         
         style_name = f"ModernMenuFrame_{id(self)}.TFrame"
         style = ttk.Style()
         style.configure(style_name, background=bg)
         self.container.configure(style=style_name)

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._apply_style()
        for item in self.items:
            item.update_theme(theme)


class ModernMenuBar(ttk.Frame, ThemeAwareMixin):
    """
    Replaces the standard window menu bar.
    """
    def __init__(self, parent, theme: Optional[Theme] = None, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.buttons = {}
        self.menus = {}
        
        self._apply_style()

    def add_cascade(self, label: str, menu: ModernMenu):
        btn = ModernButton(self, text=label, width=60, height=30, 
                           command=lambda: self._show_menu(label), theme=self.theme)
        btn.pack(side="left", padx=2)
        
        self.buttons[label] = btn
        self.menus[label] = menu

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
        for menu in self.menus.values():
            menu.update_theme(theme)

