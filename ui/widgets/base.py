from abc import ABC, abstractmethod
from typing import Optional
from ui.themes import Theme

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
