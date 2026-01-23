import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import sys
from ui.themes import Theme
from .base import ThemeAwareMixin
from .buttons import ModernButton

class ModernTitleBar(ttk.Frame, ThemeAwareMixin):
    """
    Custom title bar with drag support and window controls.
    """
    MAXIMIZE_TEXT = "□"
    RESTORE_TEXT = "❐"

    def __init__(self, parent, window, title: str = "Application", theme: Optional[Theme] = None, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self.window = window
        self.pack_propagate(False)
        
        # Title
        self.title_label = ttk.Label(self, text=title)
        self.title_label.pack(side="left", padx=10)
        
        # Controls Container
        self.controls = ttk.Frame(self)
        self.controls.pack(side="right")
        
        # Buttons
        self.btn_close = ModernButton(self.controls, text="×", width=40, height=30, 
                                      command=self.window.close, theme=theme)
        self.btn_close.pack(side="right")

        self.btn_max = ModernButton(
            self.controls,
            text=self.MAXIMIZE_TEXT,
            width=40,
            height=30,
            command=self.window.toggle_maximize,
            theme=theme,
        )
        self.btn_max.pack(side="right")
        
        self.btn_min = ModernButton(self.controls, text="-", width=40, height=30, 
                                    command=self.window.minimize, theme=theme)
        self.btn_min.pack(side="right")
        
        # Dragging
        self.bind("<Button-1>", self._start_move)
        self.bind("<B1-Motion>", self._on_move)
        self.bind("<Double-Button-1>", self._on_double_click)
        self.title_label.bind("<Button-1>", self._start_move)
        self.title_label.bind("<B1-Motion>", self._on_move)
        self.title_label.bind("<Double-Button-1>", self._on_double_click)
        
        self._apply_style()

    def _start_move(self, event):
        self.x = event.x
        self.y = event.y

    def _on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")

    def _on_double_click(self, event):
        try:
            self.window.toggle_maximize()
        except Exception:
            pass

    def set_maximized(self, is_maximized: bool):
        self.btn_max.configure_text(self.RESTORE_TEXT if is_maximized else self.MAXIMIZE_TEXT)

    def _apply_style(self):
        style_name = f"TitleBar_{id(self)}.TFrame"
        style = ttk.Style()
        
        if self.theme:
            bg = self.theme.ui_panel_background
            fg = self.theme.ui_text_primary
        else:
            bg = "#D4A574"
            fg = "#FFFFFF"
            
        style.configure(style_name, background=bg)
        self.configure(style=style_name, height=30)
        
        # Controls bg
        style.configure(f"Controls_{id(self)}.TFrame", background=bg)
        self.controls.configure(style=f"Controls_{id(self)}.TFrame")
        
        # Title Label
        lbl_style = f"TitleLabel_{id(self)}.TLabel"
        if self.theme:
            font_family = (self.theme.font_family or "Arial").split(',')[0].strip()
            font_size = max(10, int(getattr(self.theme, "font_size_small", 10)))
        else:
            font_family = "Segoe UI"
            font_size = 10
        style.configure(lbl_style, background=bg, foreground=fg, font=(font_family, font_size, 'bold'))
        self.title_label.configure(style=lbl_style)

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._apply_style()
        self.btn_close.update_theme(theme)
        self.btn_max.update_theme(theme)
        self.btn_min.update_theme(theme)


class ModernWindow(tk.Tk, ThemeAwareMixin):
    """
    A custom window with no OS decorations.
    """
    def __init__(self, theme: Optional[Theme] = None, title: str = "Go Game", **kwargs):
        tk.Tk.__init__(self, **kwargs)
        ThemeAwareMixin.__init__(self, theme=theme)
        
        self._geometry_positioned = False
        self._is_maximized = False
        self._restore_geometry = None
        self.overrideredirect(True)
        self.geometry("1024x768")
        
        # Main container with border
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True) # Will have padding for border
        
        # Title Bar
        self.title_bar = ModernTitleBar(self.container, self, title=title, theme=theme)
        self.title_bar.pack(side="top", fill="x")
        
        # Content Area
        self.content_area = ttk.Frame(self.container)
        self.content_area.pack(side="top", fill="both", expand=True)
        
        # Resize Grip (Bottom Right)
        self.grip = ttk.Label(self.container, text="◢", cursor="size_nw_se")
        self.grip.place(relx=1.0, rely=1.0, anchor="se")
        self.grip.bind("<B1-Motion>", self._on_resize)
        
        self._apply_style()
        self.after(10, self._set_initial_pos)

    def _set_initial_pos(self):
        if self._geometry_positioned:
            return
        # Center on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def minimize(self):
        self.state('iconic') # This might not work well with overrideredirect on some OS
        # With overrideredirect, minimize is tricky.
        # Alternative: withdraw() and show a tray icon? Or just standard state('iconic') usually needs overrideredirect=False temporarily.
        self.overrideredirect(False)
        self.iconify()
        self.bind("<Map>", self._on_restore)

    def _on_restore(self, event):
        self.overrideredirect(True)
        self.unbind("<Map>")

    def close(self):
        self.destroy()

    def toggle_maximize(self):
        if self._is_maximized:
            self._restore_from_maximize()
        else:
            self._maximize_to_workarea()

    def _maximize_to_workarea(self):
        if self._is_maximized:
            return
        self._restore_geometry = self.geometry()
        self._is_maximized = True
        x, y, width, height = self._get_workarea_geometry()
        self.geometry(f"{width}x{height}+{x}+{y}")
        try:
            self.grip.place_forget()
        except Exception:
            pass
        try:
            self.title_bar.set_maximized(True)
        except Exception:
            pass

    def _restore_from_maximize(self):
        if not self._is_maximized:
            return
        if self._restore_geometry:
            self.geometry(self._restore_geometry)
        self._is_maximized = False
        try:
            self.grip.place(relx=1.0, rely=1.0, anchor="se")
        except Exception:
            pass
        try:
            self.title_bar.set_maximized(False)
        except Exception:
            pass

    def _get_workarea_geometry(self):
        if sys.platform.startswith("win"):
            try:
                import ctypes
                from ctypes import wintypes
                SPI_GETWORKAREA = 0x0030
                rect = wintypes.RECT()
                if ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0):
                    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
            except Exception:
                pass
        return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

    def title(self, string=None):
        if string is None:
            return super().title()
        result = super().title(string)
        try:
            self.title_bar.title_label.configure(text=string)
        except Exception:
            pass
        return result

    def geometry(self, newGeometry=None):
        if newGeometry is not None:
            if isinstance(newGeometry, str) and ("+" in newGeometry or "-" in newGeometry):
                self._geometry_positioned = True
            return super().geometry(newGeometry)
        return super().geometry()

    def _on_resize(self, event):
        x1 = self.winfo_pointerx()
        y1 = self.winfo_pointery()
        x0 = self.winfo_rootx()
        y0 = self.winfo_rooty()
        self.geometry(f"{x1-x0}x{y1-y0}")

    def _apply_style(self):
        # Border color
        if self.theme:
            bg = self.theme.ui_panel_background
            border = self.theme.ui_panel_border
        else:
            bg = "#E8DCC0"
            border = "#A08060"
            
        self.configure(bg=border)
        # Padding for 1px border
        self.container.pack_configure(padx=1, pady=1)
        
        style = ttk.Style()
        style.configure(f"WinContainer_{id(self)}.TFrame", background=bg)
        self.container.configure(style=f"WinContainer_{id(self)}.TFrame")
        
        style.configure(f"ContentArea_{id(self)}.TFrame", background=bg)
        self.content_area.configure(style=f"ContentArea_{id(self)}.TFrame")
        
        # Grip
        style.configure(f"Grip_{id(self)}.TLabel", background=bg, foreground=border)
        self.grip.configure(style=f"Grip_{id(self)}.TLabel")

    def update_theme(self, theme: Theme):
        self.theme = theme
        self._apply_style()
        self.title_bar.update_theme(theme)
