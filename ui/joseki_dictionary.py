"""
Joseki dictionary window.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Tuple
import webbrowser
from urllib.parse import quote_plus

from features.joseki import JosekiDatabase, JosekiMove, JosekiSequence, JosekiType
from ui.board_canvas import BoardCanvas
from ui.translator import Translator
from ui.themes import Theme


class JosekiDictionaryWindow(tk.Toplevel):
    """Joseki dictionary window with search and preview."""

    def __init__(
        self,
        parent: tk.Misc,
        database: Optional[JosekiDatabase] = None,
        translator: Optional[Translator] = None,
        theme: Optional[Theme] = None,
        board_size: int = 19,
        show_coordinates: bool = True,
        show_move_numbers: bool = True,
    ):
        super().__init__(parent)

        self.database = database or JosekiDatabase()
        self.translator = translator or Translator()
        self.theme = theme or Theme(name="default")
        self.full_board_size = max(9, int(board_size))
        self._preview_padding = 2
        self._preview_min_size = 7

        self.current_joseki: Optional[JosekiSequence] = None
        self.current_move_index = 0
        self._list_items: List[JosekiSequence] = []
        self._web_search_keyword: Optional[str] = None

        self.title(self.translator.get("joseki_dictionary"))
        self.geometry("1040x720")
        self.minsize(920, 620)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._create_widgets(show_coordinates, show_move_numbers)
        self._load_list()

    def _create_widgets(self, show_coordinates: bool, show_move_numbers: bool) -> None:
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        search_frame = ttk.Frame(container)
        search_frame.pack(fill="x", pady=(0, 8))

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

        paned = ttk.PanedWindow(container, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        list_frame = ttk.LabelFrame(left, text=self.translator.get("joseki_list"))
        list_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.joseki_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            exportselection=False,
        )
        scrollbar.config(command=self.joseki_listbox.yview)
        self.joseki_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.joseki_listbox.bind("<<ListboxSelect>>", self._on_select)

        right = ttk.Frame(paned)
        paned.add(right, weight=2)

        info_frame = ttk.LabelFrame(right, text=self.translator.get("joseki_info"))
        info_frame.pack(fill="x", pady=(0, 6))
        self.info_text = tk.Text(info_frame, height=6, wrap="word")
        self.info_text.pack(fill="both", expand=True, padx=6, pady=6)

        board_frame = ttk.LabelFrame(right, text=self.translator.get("board_preview"))
        board_frame.pack(fill="both", expand=True, pady=(0, 6))

        self.board_canvas = BoardCanvas(
            board_frame,
            board_size=self.full_board_size,
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

        control_frame = ttk.Frame(right)
        control_frame.pack(fill="x")

        ttk.Button(
            control_frame,
            text=self.translator.get("nav_first"),
            command=self._first_move,
            width=3,
        ).pack(
            side="left", padx=2
        )
        ttk.Button(
            control_frame,
            text=self.translator.get("nav_prev"),
            command=self._prev_move,
            width=3,
        ).pack(
            side="left", padx=2
        )
        ttk.Button(
            control_frame,
            text=self.translator.get("nav_next"),
            command=self._next_move,
            width=3,
        ).pack(
            side="left", padx=2
        )
        ttk.Button(
            control_frame,
            text=self.translator.get("nav_last"),
            command=self._last_move,
            width=3,
        ).pack(
            side="left", padx=2
        )

        self.move_label = ttk.Label(
            control_frame,
            text=self._format_move_progress(0, 0),
        )
        self.move_label.pack(side="left", padx=10)

        comment_frame = ttk.LabelFrame(right, text=self.translator.get("comment"))
        comment_frame.pack(fill="both", expand=True, pady=(6, 0))
        self.comment_text = tk.Text(comment_frame, height=5, wrap="word")
        self.comment_text.pack(fill="both", expand=True, padx=6, pady=6)
        self._set_text(self.info_text, "")
        self._set_text(self.comment_text, "")

    def _set_text(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _format_move_progress(self, current: int, total: int) -> str:
        return self.translator.get("move_progress", current=current, total=total)

    def _load_list(self, joseki_list: Optional[List[JosekiSequence]] = None) -> None:
        self.joseki_listbox.delete(0, "end")
        self._list_items = []
        self._web_search_keyword = None
        self.current_joseki = None
        self.current_move_index = 0
        self._set_text(self.info_text, "")
        self._set_text(self.comment_text, "")
        if self.board_canvas.board_size != self.full_board_size:
            self.board_canvas.set_board_size(self.full_board_size)
        self.board_canvas.set_coordinate_mapping(0, 0, self.full_board_size, refresh=False)
        self.board_canvas.clear_board()
        self.move_label.config(text=self._format_move_progress(0, 0))

        items = joseki_list or self.database.search_joseki()
        for joseki in items:
            display_name = self._localize_joseki_name(joseki)
            display = f"{display_name} ({joseki.popularity}%)"
            self.joseki_listbox.insert("end", display)
            self._list_items.append(joseki)

        if not items:
            self._set_text(self.info_text, self.translator.get("no_results"))

    def _on_search(self) -> None:
        keyword = self.search_var.get().strip()
        if not keyword:
            self._load_list()
            return

        results = []
        lowered = keyword.lower()
        for joseki in self.database.joseki_dict.values():
            if self._matches_keyword(joseki, lowered):
                results.append(joseki)
        results.sort(key=lambda item: item.popularity, reverse=True)
        if results:
            self._load_list(results)
            return

        self.joseki_listbox.delete(0, "end")
        self._list_items = []
        self._web_search_keyword = keyword
        label = f"{self.translator.get('search_web')}: {keyword}"
        self.joseki_listbox.insert("end", label)
        self._set_text(self.info_text, self.translator.get("no_results"))
        self._set_text(self.comment_text, "")
        if self.board_canvas.board_size != self.full_board_size:
            self.board_canvas.set_board_size(self.full_board_size)
        self.board_canvas.set_coordinate_mapping(0, 0, self.full_board_size, refresh=False)
        self.board_canvas.clear_board()
        self.move_label.config(text=self._format_move_progress(0, 0))

    def _on_select(self, _event=None) -> None:
        selection = self.joseki_listbox.curselection()
        if not selection:
            return

        if self._web_search_keyword and not self._list_items:
            self._open_web_search(self._web_search_keyword)
            self.joseki_listbox.selection_clear(0, "end")
            return

        index = selection[0]
        if index >= len(self._list_items):
            return

        self.current_joseki = self._list_items[index]
        self.current_move_index = 0
        self._update_display()

    def _update_display(self) -> None:
        if not self.current_joseki:
            return

        joseki_type = self._format_joseki_type(self.current_joseki.type)
        joseki_name = self._localize_joseki_name(self.current_joseki)
        joseki_result = self._localize_result(self.current_joseki)
        star = "\u2605"
        difficulty_marks = star * max(0, int(self.current_joseki.difficulty))
        info = [
            f"{self.translator.get('name')}: {joseki_name}",
            f"{self.translator.get('type')}: {joseki_type}",
            f"{self.translator.get('difficulty')}: {difficulty_marks}",
            f"{self.translator.get('popularity')}: {self.current_joseki.popularity}%",
            f"{self.translator.get('result')}: {joseki_result}",
        ]
        self._set_text(self.info_text, "\n".join(info))

        main_line = self.current_joseki.get_main_line()
        if not main_line:
            self.move_label.config(text=self._format_move_progress(0, 0))
            self.board_canvas.clear_board()
            return

        self.current_move_index = max(0, min(self.current_move_index, len(main_line) - 1))
        self.move_label.config(
            text=self._format_move_progress(
                self.current_move_index + 1,
                len(main_line),
            )
        )

        current_move = main_line[self.current_move_index]
        comment = self._localize_move_comment(current_move)
        if not comment:
            comment = self._localize_joseki_comment(self.current_joseki)
        self._set_text(self.comment_text, comment)

        self._render_board(main_line[: self.current_move_index + 1])

    def _render_board(self, moves: List) -> None:
        if not moves:
            if self.board_canvas.board_size != self.full_board_size:
                self.board_canvas.set_board_size(self.full_board_size)
            self.board_canvas.set_coordinate_mapping(0, 0, self.full_board_size, refresh=False)
            self.board_canvas.clear_board()
            return

        region_moves = moves
        if self.current_joseki:
            region_moves = self.current_joseki.get_main_line() or moves
        preview_size, offset_x, offset_y = self._calculate_preview_region(region_moves)
        if preview_size != self.board_canvas.board_size:
            self.board_canvas.set_board_size(preview_size, reset_coord=False)
        self.board_canvas.set_coordinate_mapping(
            offset_x,
            offset_y,
            self.full_board_size,
            refresh=False,
        )

        board_state = [["" for _ in range(preview_size)] for _ in range(preview_size)]
        move_numbers = {}
        last_move = None

        for idx, move in enumerate(moves, start=1):
            nx = move.x - offset_x
            ny = move.y - offset_y
            if 0 <= nx < preview_size and 0 <= ny < preview_size:
                board_state[ny][nx] = move.color
                move_numbers[(nx, ny)] = idx
                last_move = (nx, ny)

        self.board_canvas.board_state = board_state
        self.board_canvas.move_numbers = move_numbers
        self.board_canvas.last_move = last_move
        self.board_canvas._hint_pos = None
        self.board_canvas.delete("hint")
        self.board_canvas.refresh()

    def _first_move(self) -> None:
        self.current_move_index = 0
        self._update_display()

    def _last_move(self) -> None:
        if not self.current_joseki:
            return
        main_line = self.current_joseki.get_main_line()
        if not main_line:
            return
        self.current_move_index = len(main_line) - 1
        self._update_display()

    def _next_move(self) -> None:
        if not self.current_joseki:
            return
        main_line = self.current_joseki.get_main_line()
        if self.current_move_index < len(main_line) - 1:
            self.current_move_index += 1
            self._update_display()

    def _prev_move(self) -> None:
        if self.current_move_index > 0:
            self.current_move_index -= 1
            self._update_display()

    def _format_joseki_type(self, joseki_type: JosekiType) -> str:
        mapping = {
            JosekiType.CORNER: self.translator.get("joseki_type_corner"),
            JosekiType.SIDE: self.translator.get("joseki_type_side"),
            JosekiType.INVASION: self.translator.get("joseki_type_invasion"),
            JosekiType.REDUCTION: self.translator.get("joseki_type_reduction"),
            JosekiType.SPECIAL: self.translator.get("joseki_type_special"),
            JosekiType.OPENING: self.translator.get("joseki_type_opening"),
            JosekiType.FIGHTING: self.translator.get("joseki_type_fighting"),
        }
        return mapping.get(joseki_type, joseki_type.value)

    def _localize_joseki_name(self, joseki: JosekiSequence) -> str:
        key = getattr(joseki, "key", "") or ""
        if key:
            return self.translator.get(f"joseki_name_{key}", joseki.name)
        return joseki.name

    def _localize_joseki_comment(self, joseki: JosekiSequence) -> str:
        key = getattr(joseki, "key", "") or ""
        if key:
            return self.translator.get(f"joseki_comment_{key}", joseki.comment)
        return joseki.comment

    def _localize_move_comment(self, move: JosekiMove) -> str:
        key = getattr(move, "comment_key", "") or ""
        if key:
            text = self._lookup_translation(key)
            if text:
                return text
        if getattr(self.translator, "language", "") == "zh":
            return move.comment
        return ""

    def _localize_result(self, joseki: JosekiSequence) -> str:
        result_key = f"joseki_result_{joseki.result.value}"
        return self.translator.get(result_key, joseki.result.value)

    def _lookup_translation(self, key: str) -> str:
        translations = getattr(self.translator, "translations", {}) or {}
        lang = getattr(self.translator, "language", "") or ""
        lang_dict = translations.get(lang, {})
        if key in lang_dict:
            return lang_dict[key]
        en_dict = translations.get("en", {})
        if key in en_dict:
            return en_dict[key]
        return ""

    def _matches_keyword(self, joseki: JosekiSequence, keyword: str) -> bool:
        if not keyword:
            return True
        name = self._localize_joseki_name(joseki).lower()
        comment = self._localize_joseki_comment(joseki).lower()
        if keyword in name or keyword in comment:
            return True
        tags = [str(tag).lower() for tag in joseki.tags]
        return any(keyword in tag for tag in tags)

    def _calculate_preview_region(self, moves: List) -> Tuple[int, int, int]:
        min_x = min(move.x for move in moves)
        max_x = max(move.x for move in moves)
        min_y = min(move.y for move in moves)
        max_y = max(move.y for move in moves)

        width = max_x - min_x + 1
        height = max_y - min_y + 1
        preview_size = max(
            width + self._preview_padding * 2,
            height + self._preview_padding * 2,
            self._preview_min_size,
        )
        preview_size = min(preview_size, self.full_board_size)

        center_x = (min_x + max_x) // 2
        center_y = (min_y + max_y) // 2

        offset_x = center_x - preview_size // 2
        offset_y = center_y - preview_size // 2

        max_offset = self.full_board_size - preview_size
        offset_x = max(0, min(offset_x, max_offset))
        offset_y = max(0, min(offset_y, max_offset))
        return preview_size, offset_x, offset_y

    def _open_web_search(self, keyword: str) -> None:
        if not keyword:
            return
        url = self._build_search_url(keyword, self.translator.get("joseki_dictionary"))
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


__all__ = ["JosekiDictionaryWindow"]
