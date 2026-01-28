from abc import ABC, abstractmethod
from typing import Optional
from tkinter import font as tkfont
from ui.themes import Theme


def resolve_font_family(theme: Optional[Theme] = None) -> str:
    """
    Resolve the primary font family. Prefer theme font, then Tk default.
    """
    if theme and getattr(theme, "font_family", None):
        return (theme.font_family or "Arial").split(",")[0].strip()
    try:
        return tkfont.nametofont("TkDefaultFont").actual("family")
    except Exception:
        return "Arial"


class ThemeAwareMixin(ABC):
    """
    Mixin for widgets that need to respond to theme changes.
    """
    def __init__(self, theme: Optional[Theme] = None, **kwargs):
        self.theme = theme
        # Ideally, we don't call super().__init__ here because it might be mixed into different bases
        # But if used with multiple inheritance, we might need to. 
        # For now, let's assume it's a simple mixin.

    @abstractmethod
    def update_theme(self, theme: Theme):
        """
        Update the visual appearance of the widget based on the new theme.
        """
        self.theme = theme
        # Subclasses must implement drawing/styling logic here
