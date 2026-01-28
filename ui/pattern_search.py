"""
Pattern search window.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import webbrowser
from urllib.parse import quote_plus

from ai.pattern_ai import PatternLibrary, Pattern
from core import Board
from ui.board_canvas import BoardCanvas
from ui.translator import Translator
from ui.themes import Theme
from ui.widgets import ModernScrollbar


@dataclass
class PatternResult:
    label: str
    pattern: Pattern
    category: str
    source: str
    anchor: Optional[Tuple[int, int]] = None
    color: Optional[str] = None
    next_moves: List[Tuple[int, int, float]] = field(default_factory=list)


class PatternSearchWindow(tk.Toplevel):
    """Pattern search window with library search and board scan."""

    def __init__(
        self,
        parent: tk.Misc,
        get_game=None,
        translator: Optional[Translator] = None,
        theme: Optional[Theme] = None,
        show_coordinates: bool = True,
        show_move_numbers: bool = False,
    ):
        super().__init__(parent)

        self._get_game = get_game or (lambda: None)
        self.translator = translator or Translator()
        self.theme = theme or Theme(name="default")

        self.pattern_library = PatternLibrary()
        self.pattern_catalog = self._build_catalog()

        self._results: List[PatternResult] = []
        self._list_mode = "results"
        self._web_search_keyword: Optional[str] = None

        self.title(self.translator.get("pattern_search"))
        self.geometry("1120x760")
        self.minsize(960, 640)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._create_widgets(show_coordinates, show_move_numbers)
        self._sync_board()
        self._show_catalog()

    def _create_widgets(self, show_coordinates: bool, show_move_numbers: bool) -> None:
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        search_frame = ttk.Frame(container)
        search_frame.pack(fill="x", pady=(0, 6))

        ttk.Label(search_frame, text=self.translator.get("search")).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.search_entry.bind("<Return>", lambda _e: self._on_search())

        ttk.Button(
            search_frame,
            text=self.translator.get("search"),
            command=self._on_search,
        ).pack(side="left")

        filter_frame = ttk.Frame(container)
        filter_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(filter_frame, text=self.translator.get("pattern_category")).pack(
            side="left"
        )
        self.category_var = tk.StringVar(value=self.translator.get("pattern_filter_all"))
        categories = self._category_labels()
        self.category_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.category_var,
            values=list(categories.keys()),
            state="readonly",
            width=14,
        )
        self.category_combo.pack(side="left", padx=6)
        self.category_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_search())

        ttk.Label(filter_frame, text=self.translator.get("pattern_color")).pack(
            side="left", padx=(8, 0)
        )
        self.color_var = tk.StringVar(value=self.translator.get("color_auto"))
        color_labels = self._color_labels()
        self.color_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.color_var,
            values=list(color_labels.keys()),
            state="readonly",
            width=10,
        )
        self.color_combo.pack(side="left", padx=6)

        ttk.Button(
            filter_frame,
            text=self.translator.get("pattern_scan"),
            command=self._on_scan_board,
        ).pack(side="left", padx=8)

        self.match_label = ttk.Label(filter_frame, text="")
        self.match_label.pack(side="right")

        paned = ttk.PanedWindow(container, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        list_frame = ttk.LabelFrame(left, text=self.translator.get("pattern_matches"))
        list_frame.pack(fill="both", expand=True)

        self.result_listbox = tk.Listbox(
            list_frame,
            exportselection=False,
        )
        scrollbar = ModernScrollbar(
            list_frame,
            orient="vertical",
            theme=self.theme,
            match_widget=self.result_listbox,
        )
        self.result_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.result_listbox.yview)
        self.result_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.result_listbox.bind("<<ListboxSelect>>", self._on_select)

        right = ttk.Frame(paned)
        paned.add(right, weight=2)

        detail_frame = ttk.LabelFrame(right, text=self.translator.get("pattern_details"))
        detail_frame.pack(fill="x", pady=(0, 6))
        self.detail_text = tk.Text(detail_frame, height=10, wrap="word")
        self.detail_text.pack(fill="both", expand=True, padx=6, pady=6)
        self._set_text(self.detail_text, "")

        board_frame = ttk.LabelFrame(right, text=self.translator.get("board_preview"))
        board_frame.pack(fill="both", expand=True)

        board_size = 19
        game = self._get_game()
        if game is not None:
            board_size = getattr(game, "board_size", board_size)

        self.board_canvas = BoardCanvas(
            board_frame,
            board_size=board_size,
            theme=self.theme,
            show_coordinates=show_coordinates,
        )
        self.board_canvas.pack(fill="both", expand=True, padx=6, pady=6)
        self.board_canvas.set_show_move_numbers(show_move_numbers)
        self.board_canvas.unbind("<Button-1>")
        self.board_canvas.unbind("<Button-3>")
        self.board_canvas.unbind("<Motion>")
        self.board_canvas.on_click = None
        self.board_canvas.on_hover = None
        self.board_canvas.on_right_click = None

    def _set_text(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _category_labels(self) -> Dict[str, str]:
        return {
            self.translator.get("pattern_filter_all"): "all",
            self.translator.get("pattern_category_joseki"): "joseki",
            self.translator.get("pattern_category_tactical"): "tactical",
            self.translator.get("pattern_category_life_death"): "life_death",
            self.translator.get("pattern_category_tesuji"): "tesuji",
        }

    def _color_labels(self) -> Dict[str, str]:
        return {
            self.translator.get("color_auto"): "auto",
            self.translator.get("black"): "black",
            self.translator.get("white"): "white",
        }

    def _selected_category(self) -> Optional[str]:
        label = self.category_var.get()
        return self._category_labels().get(label, "all")

    def _selected_color(self) -> str:
        label = self.color_var.get()
        return self._color_labels().get(label, "auto")

    def _build_catalog(self) -> List[Tuple[str, Pattern]]:
        catalog = []
        seen = set()

        for category, patterns in self.pattern_library.patterns.items():
            for pattern in patterns:
                base_name = self._base_pattern_name(pattern.name)
                if base_name != pattern.name:
                    continue
                key = (category, base_name)
                if key in seen:
                    continue
                seen.add(key)
                catalog.append((category, pattern))

        catalog.sort(key=lambda item: item[1].name.lower())
        return catalog

    def _show_catalog(self) -> None:
        category_filter = self._selected_category()
        keyword = self.search_var.get().strip().lower()
        results = []

        for category, pattern in self.pattern_catalog:
            if category_filter != "all" and category != category_filter:
                continue
            base_name = self._base_pattern_name(pattern.name)
            display_name = self._localize_pattern_name(base_name)
            context_text = self._localize_pattern_context(base_name, pattern.context)
            if keyword:
                if keyword not in display_name.lower() and keyword not in context_text.lower():
                    continue
            label = f"{display_name} ({self._format_category(category)})"
            results.append(
                PatternResult(
                    label=label,
                    pattern=pattern,
                    category=category,
                    source="library",
                    next_moves=list(pattern.next_moves),
                )
            )

        if results:
            self._set_results(results)
        else:
            self._set_results([], web_search_keyword=self.search_var.get().strip())

    def _on_search(self) -> None:
        self._show_catalog()

    def _on_scan_board(self) -> None:
        board = self._sync_board()
        if not board:
            messagebox.showinfo(self.translator.get("info"), self.translator.get("no_results"))
            return

        category_filter = self._selected_category()
        color_choice = self._selected_color()
        colors = [self._resolve_color_choice(color_choice)] if color_choice != "auto" else [self._resolve_color_choice("auto")]

        results: List[PatternResult] = []
        seen = set()
        categories = (
            [category_filter]
            if category_filter and category_filter != "all"
            else list(self.pattern_library.patterns.keys())
        )

        for color in colors:
            for category in categories:
                for y in range(board.size):
                    for x in range(board.size):
                        matches = self.pattern_library.find_matching_patterns(
                            board, x, y, color, category
                        )
                        for pattern in matches:
                            base_name = self._base_pattern_name(pattern.name)
                            display_name = self._localize_pattern_name(base_name)
                            key = (base_name, x, y, color, category)
                            if key in seen:
                                continue
                            seen.add(key)
                            next_moves = self._resolve_next_moves(pattern, x, y, board.size)
                            label = f"{display_name} @ {self._format_coord(x, y, board.size)} ({self._format_color(color)})"
                            results.append(
                                PatternResult(
                                    label=label,
                                    pattern=pattern,
                                    category=category,
                                    source="match",
                                    anchor=(x, y),
                                    color=color,
                                    next_moves=next_moves,
                                )
                            )

        if results:
            results.sort(key=lambda item: item.label.lower())
            self._set_results(results)
        else:
            self._set_results([])

    def _set_results(self, results: List[PatternResult], web_search_keyword: str = "") -> None:
        self.result_listbox.delete(0, "end")
        self._results = results
        self._web_search_keyword = None
        self._list_mode = "results"
        self._set_text(self.detail_text, "")
        self._clear_markers()

        if results:
            for item in results:
                self.result_listbox.insert("end", item.label)
            self.match_label.config(text=f"{self.translator.get('pattern_matches')}: {len(results)}")
            return

        keyword = web_search_keyword.strip()
        if keyword:
            label = f"{self.translator.get('search_web')}: {keyword}"
            self.result_listbox.insert("end", label)
            self._web_search_keyword = keyword
            self._list_mode = "web"
        else:
            self.result_listbox.insert("end", self.translator.get("no_results"))
            self._list_mode = "empty"

        self.match_label.config(text=f"{self.translator.get('pattern_matches')}: 0")

    def _on_select(self, _event=None) -> None:
        selection = self.result_listbox.curselection()
        if not selection:
            return

        if self._list_mode == "web" and self._web_search_keyword:
            self._open_web_search(self._web_search_keyword)
            self.result_listbox.selection_clear(0, "end")
            return

        if self._list_mode != "results":
            return

        index = selection[0]
        if index >= len(self._results):
            return
        result = self._results[index]
        self._show_pattern_detail(result)
        self._highlight_result(result)

    def _show_pattern_detail(self, result: PatternResult) -> None:
        pattern = result.pattern
        base_name = self._base_pattern_name(pattern.name)
        display_name = self._localize_pattern_name(base_name)
        context_text = self._localize_pattern_context(base_name, pattern.context)
        lines = [
            f"{self.translator.get('name')}: {display_name}",
            f"{self.translator.get('pattern_category')}: {self._format_category(result.category)}",
            f"{self.translator.get('pattern_context')}: {context_text}",
        ]

        if result.anchor:
            lines.append(
                f"{self.translator.get('pattern_anchor')}: {self._format_coord(result.anchor[0], result.anchor[1], self.board_canvas.board_size)}"
            )
        if result.color:
            lines.append(f"{self.translator.get('pattern_color')}: {self._format_color(result.color)}")

        stones = ", ".join(
            [f"({dx:+d},{dy:+d})={stone}" for dx, dy, stone in pattern.stones]
        )
        empties = ", ".join([f"({dx:+d},{dy:+d})" for dx, dy in pattern.empty_points])
        lines.append(f"{self.translator.get('pattern_stones')}: {stones or '-'}")
        lines.append(f"{self.translator.get('pattern_empty_points')}: {empties or '-'}")

        if result.next_moves:
            if result.anchor:
                next_moves = ", ".join(
                    [
                        f"{self._format_coord(x, y, self.board_canvas.board_size)}({priority:.2f})"
                        for x, y, priority in result.next_moves
                    ]
                )
            else:
                next_moves = ", ".join(
                    [
                        f"({dx:+d},{dy:+d})({priority:.2f})"
                        for dx, dy, priority in result.next_moves
                    ]
                )
            lines.append(f"{self.translator.get('pattern_next_moves')}: {next_moves}")

        self._set_text(self.detail_text, "\n".join(lines))

    def _highlight_result(self, result: PatternResult) -> None:
        self._clear_markers()
        if result.anchor is None:
            return

        self._draw_anchor_marker(result.anchor)
        if result.next_moves:
            best_move = max(result.next_moves, key=lambda item: item[2])
            self.board_canvas.show_hint(best_move[0], best_move[1])

    def _clear_markers(self) -> None:
        self.board_canvas.delete("pattern_anchor")
        self.board_canvas.delete("hint")
        self.board_canvas._hint_pos = None

    def _draw_anchor_marker(self, anchor: Tuple[int, int]) -> None:
        x, y = anchor
        renderer = self.board_canvas.renderer
        cx = renderer.margin_x + x * renderer.cell_size
        cy = renderer.margin_y + y * renderer.cell_size
        radius = renderer.cell_size * 0.3
        self.board_canvas.create_rectangle(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            outline="#22c55e",
            width=2,
            tags=("pattern_anchor",),
        )

    def _sync_board(self) -> Optional[Board]:
        game = self._get_game()
        if not game:
            return None

        board = getattr(game, "board", None)
        if not board:
            return None

        board_copy = board.copy()
        size = board_copy.size
        if size != self.board_canvas.board_size:
            self.board_canvas.set_board_size(size)
        self.board_canvas.update_board(board_copy)
        return board_copy

    def _resolve_color_choice(self, choice: str) -> str:
        if choice != "auto":
            return choice

        game = self._get_game()
        if game and hasattr(game, "current_player"):
            return game.current_player
        return "black"

    def _resolve_next_moves(
        self, pattern: Pattern, x: int, y: int, board_size: int
    ) -> List[Tuple[int, int, float]]:
        moves = []
        for dx, dy, priority in pattern.next_moves:
            nx, ny = x + dx, y + dy
            if 0 <= nx < board_size and 0 <= ny < board_size:
                moves.append((nx, ny, priority))
        return moves

    def _format_color(self, color: str) -> str:
        if color == "black":
            return self.translator.get("black")
        if color == "white":
            return self.translator.get("white")
        return color

    def _format_category(self, category: str) -> str:
        mapping = {
            "joseki": self.translator.get("pattern_category_joseki"),
            "tactical": self.translator.get("pattern_category_tactical"),
            "life_death": self.translator.get("pattern_category_life_death"),
            "tesuji": self.translator.get("pattern_category_tesuji"),
        }
        return mapping.get(category, category)

    def _localize_pattern_name(self, base_name: str) -> str:
        return self.translator.get(f"pattern_name_{base_name}", base_name)

    def _localize_pattern_context(self, base_name: str, fallback: str) -> str:
        return self.translator.get(f"pattern_context_{base_name}", fallback)

    def _format_coord(self, x: int, y: int, size: int) -> str:
        letters = "ABCDEFGHJKLMNOPQRST"[:size]
        try:
            col = letters[int(x)]
        except Exception:
            col = "?"
        row = size - int(y)
        return f"{col}{row}"

    def _base_pattern_name(self, name: str) -> str:
        base = name
        while True:
            if base.endswith("_r90"):
                base = base[:-4]
                continue
            if base.endswith("_mh"):
                base = base[:-3]
                continue
            break
        return base

    def _open_web_search(self, keyword: str) -> None:
        if not keyword:
            return
        url = self._build_search_url(keyword, self.translator.get("pattern_search"))
        try:
            webbrowser.open(url)
        except Exception:
            messagebox.showwarning(self.translator.get("warning"), url)

    def _build_search_url(self, keyword: str, context: str = "") -> str:
        query = keyword.strip()
        if context:
            query = f"{query} {context}".strip()

        engine = "google" if getattr(self.translator, "language", "") == "en" else "bing"
        base_url = "https://www.google.com/search?q=" if engine == "google" else "https://www.bing.com/search?q="
        return base_url + quote_plus(query)


__all__ = ["PatternSearchWindow"]
