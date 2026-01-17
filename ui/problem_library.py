"""
Problem library window.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional
from urllib.parse import quote_plus
import webbrowser

from features.teaching import TeachingSystem, Puzzle
from ui.board_canvas import BoardCanvas
from ui.themes import Theme
from ui.translator import Translator
from utils.content_db import get_content_db


@dataclass
class ProblemEntry:
    puzzle: Puzzle
    category: str
    search_text: str


class ProblemLibraryWindow(tk.Toplevel):
    """Problem library window with local puzzles and online resources."""

    def __init__(
        self,
        parent: tk.Misc,
        teaching_system: Optional[TeachingSystem] = None,
        translator: Optional[Translator] = None,
        theme: Optional[Theme] = None,
        show_coordinates: bool = True,
        show_move_numbers: bool = False,
    ):
        super().__init__(parent)

        self.translator = translator or Translator()
        self.theme = theme or Theme(name="default")
        self.content_db = get_content_db()
        self.teaching_system = teaching_system or TeachingSystem(
            self.translator,
            content_db=self.content_db,
        )

        self._entries = self._build_catalog()
        self._list_items: List[ProblemEntry] = []
        self._web_search_keyword: Optional[str] = None
        self._active_entry: Optional[ProblemEntry] = None
        self._puzzle_solved = False
        self._resource_buttons: List[ttk.Button] = []
        self._resource_canvas = None
        self._resource_inner = None
        self._resource_window = None
        self._preview_padding = 2
        self._preview_min_size = 7
        self._preview_offset_x = 0
        self._preview_offset_y = 0
        self._preview_full_size = 0
        self._solution_index = 0
        self._solution_window: Optional[tk.Toplevel] = None
        self._solution_board: Optional[BoardCanvas] = None
        self._solution_title: Optional[ttk.Label] = None

        self._resources = self._load_resources("problem_library")

        self.title(self.translator.get("problem_library"))
        self.geometry("1040x680")
        self.minsize(900, 560)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._create_widgets(show_coordinates, show_move_numbers)
        self._load_list()

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
        filter_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(filter_frame, text=self.translator.get("pattern_category")).pack(
            side="left"
        )
        self.category_var = tk.StringVar(value=self.translator.get("pattern_filter_all"))
        category_labels = self._category_labels()
        self.category_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.category_var,
            values=list(category_labels.keys()),
            state="readonly",
            width=14,
        )
        self.category_combo.pack(side="left", padx=6)
        self.category_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_search())

        ttk.Label(filter_frame, text=self.translator.get("difficulty")).pack(
            side="left", padx=(8, 0)
        )
        self.difficulty_var = tk.StringVar(value=self.translator.get("pattern_filter_all"))
        difficulty_values = [self.translator.get("pattern_filter_all")] + [
            str(value) for value in range(1, 6)
        ]
        self.difficulty_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.difficulty_var,
            values=difficulty_values,
            state="readonly",
            width=8,
        )
        self.difficulty_combo.pack(side="left", padx=6)
        self.difficulty_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_search())

        actions_frame = ttk.Frame(filter_frame)
        actions_frame.pack(side="right")

        ttk.Label(
            actions_frame, text=self.translator.get("problem_import_hint")
        ).pack(side="left", padx=(0, 6))

        ttk.Label(
            actions_frame, text=self.translator.get("problem_import_strategy")
        ).pack(side="left", padx=(0, 4))

        self.import_strategy_var = tk.StringVar(
            value=self.translator.get("problem_import_strategy_copy")
        )
        self.import_strategy_combo = ttk.Combobox(
            actions_frame,
            textvariable=self.import_strategy_var,
            values=list(self._import_strategy_labels().keys()),
            state="readonly",
            width=10,
        )
        self.import_strategy_combo.pack(side="left", padx=(0, 6))

        ttk.Button(
            actions_frame,
            text=self.translator.get("problem_import_guide"),
            command=self._show_import_guide,
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            actions_frame,
            text=self.translator.get("import"),
            command=self._on_import,
        ).pack(side="left")

        ttk.Button(
            actions_frame,
            text=self.translator.get("problem_rebuild"),
            command=self._on_rebuild_default_pack,
        ).pack(side="left", padx=(6, 0))

        paned = ttk.PanedWindow(container, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        list_frame = ttk.LabelFrame(left, text=self.translator.get("problem_list"))
        list_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.problem_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            exportselection=False,
        )
        scrollbar.config(command=self.problem_listbox.yview)
        self.problem_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.problem_listbox.bind("<<ListboxSelect>>", self._on_select)

        right = ttk.Frame(paned)
        paned.add(right, weight=2)

        info_frame = ttk.LabelFrame(right, text=self.translator.get("problem_info"))
        info_frame.pack(fill="x", pady=(0, 6))
        self.info_text = tk.Text(info_frame, height=8, wrap="word")
        self.info_text.pack(fill="both", expand=True, padx=6, pady=6)
        self._set_text(self.info_text, "")

        board_frame = ttk.LabelFrame(right, text=self.translator.get("board_preview"))
        board_frame.pack(fill="both", expand=True)

        self.board_canvas = BoardCanvas(
            board_frame,
            board_size=19,
            theme=self.theme,
            show_coordinates=show_coordinates,
        )
        self.board_canvas.pack(fill="both", expand=True, padx=6, pady=6)
        self.board_canvas.set_show_move_numbers(show_move_numbers)
        self.board_canvas.on_click = self._on_board_click
        self.board_canvas.on_right_click = None

        control_frame = ttk.Frame(right)
        control_frame.pack(fill="x", pady=(6, 0))

        self.hint_button = ttk.Button(
            control_frame,
            text=self.translator.get("hint"),
            command=self._on_show_hint,
        )
        self.hint_button.pack(side="left", padx=4)

        ttk.Button(
            control_frame,
            text=self.translator.get("problem_show_solution"),
            command=self._on_show_solution,
        ).pack(side="left", padx=4)

        ttk.Button(
            control_frame,
            text=self.translator.get("problem_reset_board"),
            command=self._on_reset_board,
        ).pack(side="left", padx=4)

        self.status_var = tk.StringVar(value=self.translator.get("problem_status_ready"))
        self.status_label = ttk.Label(right, textvariable=self.status_var)
        self.status_label.pack(anchor="w", pady=(4, 0))

        resource_frame = ttk.LabelFrame(
            right, text=self.translator.get("problem_resources")
        )
        resource_frame.pack(fill="x", pady=(8, 0))

        self._resource_canvas = tk.Canvas(
            resource_frame, highlightthickness=0, borderwidth=0, height=120
        )
        resource_scrollbar = ttk.Scrollbar(
            resource_frame, orient="vertical", command=self._resource_canvas.yview
        )
        self._resource_canvas.configure(yscrollcommand=resource_scrollbar.set)

        resource_scrollbar.pack(side="right", fill="y")
        self._resource_canvas.pack(side="left", fill="both", expand=True)

        self._resource_inner = ttk.Frame(self._resource_canvas)
        self._resource_window = self._resource_canvas.create_window(
            (0, 0), window=self._resource_inner, anchor="nw"
        )

        self._resource_inner.bind("<Configure>", self._on_resource_inner_configure)
        self._resource_canvas.bind("<Configure>", self._on_resource_canvas_configure)
        self._resource_canvas.bind("<Enter>", self._bind_resource_mousewheel)
        self._resource_canvas.bind("<Leave>", self._unbind_resource_mousewheel)
        self._resource_inner.bind("<Enter>", self._bind_resource_mousewheel)
        self._resource_inner.bind("<Leave>", self._unbind_resource_mousewheel)

        self._resource_buttons = []
        for resource in self._resources:
            button = ttk.Button(
                self._resource_inner,
                text=resource["label"],
                command=lambda url=resource["url"]: self._open_link(url),
            )
            self._resource_buttons.append(button)

        self.after(0, self._layout_resources)

    def _set_text(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _load_resources(self, category: str) -> List[Dict[str, str]]:
        language = getattr(self.translator, "language", "zh")
        try:
            resources = self.content_db.list_resources(category, language)
            if resources:
                return resources
        except Exception:
            pass
        if category == "problem_library":
            return [
                {
                    "label": "Online-Go.com Puzzles",
                    "url": "https://online-go.com/puzzles",
                },
                {
                    "label": "GoProblems.com",
                    "url": "https://www.goproblems.com/",
                },
                {
                    "label": "Tsumego Hero",
                    "url": "https://tsumego-hero.com/",
                },
                {
                    "label": "101weiqi Tsumego",
                    "url": "https://www.101weiqi.com/",
                },
                {
                    "label": "Sensei's Library Tsumego",
                    "url": "https://senseis.xmp.net/?Tsumego",
                },
            ]
        return []

    def _puzzle_text(self, puzzle: Puzzle, field: str) -> str:
        if not puzzle:
            return ""
        if hasattr(self.teaching_system, "get_puzzle_text"):
            text = self.teaching_system.get_puzzle_text(puzzle, field)
            if text:
                return text
        return getattr(puzzle, field, "") or ""

    def _on_resource_inner_configure(self, _event=None) -> None:
        if not self._resource_canvas:
            return
        self._resource_canvas.configure(scrollregion=self._resource_canvas.bbox("all"))

    def _on_resource_canvas_configure(self, event) -> None:
        if not self._resource_canvas or self._resource_window is None:
            return
        self._resource_canvas.itemconfigure(self._resource_window, width=event.width)
        self._layout_resources()

    def _on_resource_mousewheel(self, event) -> None:
        if not self._resource_canvas:
            return
        try:
            delta = int(-1 * (event.delta / 120))
        except Exception:
            delta = -1 if getattr(event, "delta", 0) > 0 else 1
        self._resource_canvas.yview_scroll(delta, "units")

    def _bind_resource_mousewheel(self, _event=None) -> None:
        if self._resource_canvas:
            self._resource_canvas.bind_all("<MouseWheel>", self._on_resource_mousewheel)

    def _unbind_resource_mousewheel(self, _event=None) -> None:
        if self._resource_canvas:
            self._resource_canvas.unbind_all("<MouseWheel>")

    def _layout_resources(self) -> None:
        if not self._resource_buttons or not self._resource_canvas or not self._resource_inner:
            return
        available_width = self._resource_canvas.winfo_width()
        if available_width <= 1:
            return
        self._resource_inner.update_idletasks()
        max_width = max(button.winfo_reqwidth() for button in self._resource_buttons) + 12
        columns = max(1, int(available_width // max_width))
        for button in self._resource_buttons:
            button.grid_forget()
        for index, button in enumerate(self._resource_buttons):
            row = index // columns
            col = index % columns
            button.grid(row=row, column=col, padx=4, pady=4, sticky="w")
        for col in range(columns):
            self._resource_inner.grid_columnconfigure(col, weight=1)
        if self._resource_canvas:
            self._resource_canvas.configure(scrollregion=self._resource_canvas.bbox("all"))

    def _category_labels(self) -> dict:
        return {
            self.translator.get("pattern_filter_all"): "all",
            self.translator.get("pattern_category_life_death"): "life_death",
            self.translator.get("pattern_category_tactical"): "tactical",
            self.translator.get("pattern_category_tesuji"): "tesuji",
        }

    def _import_strategy_labels(self) -> dict:
        return {
            self.translator.get("problem_import_strategy_overwrite"): "overwrite",
            self.translator.get("problem_import_strategy_skip"): "skip",
            self.translator.get("problem_import_strategy_copy"): "copy",
        }

    def _build_catalog(self) -> List[ProblemEntry]:
        entries: List[ProblemEntry] = []
        for puzzle in self.teaching_system.puzzles.values():
            category = self._infer_category(puzzle)
            title = self._puzzle_text(puzzle, "title")
            objective = self._puzzle_text(puzzle, "objective")
            search_text = " ".join(
                [
                    puzzle.id,
                    title,
                    objective,
                ]
            ).lower()
            entries.append(
                ProblemEntry(
                    puzzle=puzzle,
                    category=category,
                    search_text=search_text,
                )
            )
        return entries

    def _infer_category(self, puzzle: Puzzle) -> str:
        pid = puzzle.id.lower()
        if pid.startswith("tesuji"):
            return "tesuji"
        if pid.startswith(("capture", "ladder", "net", "atari")):
            return "tactical"
        return "life_death"

    def _on_search(self) -> None:
        keyword = self.search_var.get().strip()
        entries = self._filter_entries(keyword)
        if entries:
            self._load_list(entries)
            return

        self.problem_listbox.delete(0, "end")
        self._list_items = []
        self._web_search_keyword = keyword if keyword else None
        if keyword:
            label = f"{self.translator.get('search_web')}: {keyword}"
            self.problem_listbox.insert("end", label)
        self._set_text(self.info_text, self.translator.get("no_results"))
        self.board_canvas.clear_board()
        self.status_var.set(self.translator.get("problem_status_ready"))

    def _show_import_guide(self) -> None:
        messagebox.showinfo(
            self.translator.get("problem_import_guide_title"),
            self.translator.get("problem_import_guide_body"),
            parent=self,
        )

    def _on_import(self) -> None:
        filetypes = [
            (self.translator.get("sgf_files"), "*.sgf"),
            ("JSON", "*.json"),
            (self.translator.get("all_files"), "*.*"),
        ]
        paths = filedialog.askopenfilenames(
            parent=self,
            title=self.translator.get("problem_import_guide_title"),
            filetypes=filetypes,
        )
        if not paths:
            return

        strategy_labels = self._import_strategy_labels()
        strategy = strategy_labels.get(self.import_strategy_var.get(), "copy")
        added, errors = self.teaching_system.import_puzzles(list(paths), strategy=strategy)
        if added:
            self._entries = self._build_catalog()
            self._load_list()
            message = self.translator.get("problem_import_success", count=added)
            preview = errors[:6]
            if preview:
                message = message + "\n" + "\n".join(preview)
            messagebox.showinfo(self.translator.get("info"), message, parent=self)
            return

        message = self.translator.get("problem_import_failed")
        preview = errors[:6]
        if preview:
            message = message + "\n" + "\n".join(preview)
        messagebox.showwarning(self.translator.get("warning"), message, parent=self)

    def _on_rebuild_default_pack(self) -> None:
        if not messagebox.askyesno(
            self.translator.get("problem_rebuild_title"),
            self.translator.get("problem_rebuild_confirm"),
            parent=self,
        ):
            return
        added, errors = self.teaching_system.rebuild_default_pack()
        if added >= 0:
            self._entries = self._build_catalog()
            self._load_list()
        message = self.translator.get("problem_rebuild_done", count=added)
        preview = errors[:6]
        if preview:
            message = message + "\n" + "\n".join(preview)
        if errors:
            messagebox.showwarning(self.translator.get("warning"), message, parent=self)
        else:
            messagebox.showinfo(self.translator.get("info"), message, parent=self)

    def _filter_entries(self, keyword: str) -> List[ProblemEntry]:
        keyword = keyword.lower().strip()
        category_labels = self._category_labels()
        selected_category = category_labels.get(self.category_var.get(), "all")
        difficulty_label = self.difficulty_var.get()
        try:
            selected_difficulty = int(difficulty_label)
        except Exception:
            selected_difficulty = None

        results: List[ProblemEntry] = []
        for entry in self._entries:
            if selected_category != "all" and entry.category != selected_category:
                continue
            if selected_difficulty and entry.puzzle.difficulty != selected_difficulty:
                continue
            if keyword and keyword not in entry.search_text:
                continue
            results.append(entry)
        return results

    def _load_list(self, entries: Optional[List[ProblemEntry]] = None) -> None:
        self.problem_listbox.delete(0, "end")
        self._list_items = []
        self._web_search_keyword = None
        self._active_entry = None
        self._puzzle_solved = False
        self._set_text(self.info_text, "")
        self.status_var.set(self.translator.get("problem_status_ready"))
        self.board_canvas.clear_board()

        items = entries or self._entries
        for entry in items:
            difficulty_marks = "*" * max(1, int(entry.puzzle.difficulty))
            title = self._puzzle_text(entry.puzzle, "title")
            display = f"{title} ({difficulty_marks})"
            self.problem_listbox.insert("end", display)
            self._list_items.append(entry)

        if not items:
            self._set_text(self.info_text, self.translator.get("no_results"))

    def _on_select(self, _event=None) -> None:
        selection = self.problem_listbox.curselection()
        if not selection:
            return

        if self._web_search_keyword and not self._list_items:
            self._open_web_search(self._web_search_keyword)
            self.problem_listbox.selection_clear(0, "end")
            return

        index = selection[0]
        if index >= len(self._list_items):
            return

        entry = self._list_items[index]
        self._active_entry = entry
        self._puzzle_solved = False
        self._update_display(entry)

    def _update_display(self, entry: ProblemEntry) -> None:
        puzzle = entry.puzzle
        category_label = self._category_label(entry.category)
        difficulty_marks = "*" * max(1, int(puzzle.difficulty))
        player_label = self.translator.get(puzzle.player_color, puzzle.player_color)
        title = self._puzzle_text(puzzle, "title")
        objective = self._puzzle_text(puzzle, "objective")
        hint = self._puzzle_text(puzzle, "hint")

        info_lines = [
            f"{self.translator.get('name')}: {title}",
            f"{self.translator.get('pattern_category')}: {category_label}",
            f"{self.translator.get('difficulty')}: {difficulty_marks}",
            f"{self.translator.get('problem_objective')}: {objective}",
            f"{self.translator.get('player')}: {player_label}",
        ]
        if hint:
            info_lines.append(f"{self.translator.get('hint')}: {hint}")
        self._set_text(self.info_text, "\n".join(info_lines))

        self._reset_board(puzzle)
        self.hint_button.config(state="normal" if puzzle.hint else "disabled")
        self.status_var.set(self.translator.get("problem_status_ready"))

    def _category_label(self, category: str) -> str:
        mapping = {
            "life_death": self.translator.get("pattern_category_life_death"),
            "tactical": self.translator.get("pattern_category_tactical"),
            "tesuji": self.translator.get("pattern_category_tesuji"),
        }
        return mapping.get(category, category)

    def _calculate_preview_region(self, puzzle: Puzzle) -> tuple[int, int, int]:
        full_size = len(puzzle.board_state)
        points = []
        for y, row in enumerate(puzzle.board_state):
            for x, stone in enumerate(row):
                if stone:
                    points.append((x, y))
        if puzzle.solution:
            points.extend(puzzle.solution)
        if puzzle.wrong_moves:
            points.extend(puzzle.wrong_moves.keys())
        if not points:
            return full_size, 0, 0

        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        width = max_x - min_x + 1
        height = max_y - min_y + 1
        preview_size = max(
            width + self._preview_padding * 2,
            height + self._preview_padding * 2,
            self._preview_min_size,
        )
        preview_size = min(preview_size, full_size)

        center_x = (min_x + max_x) // 2
        center_y = (min_y + max_y) // 2
        offset_x = center_x - preview_size // 2
        offset_y = center_y - preview_size // 2

        max_offset = full_size - preview_size
        offset_x = max(0, min(offset_x, max_offset))
        offset_y = max(0, min(offset_y, max_offset))
        return preview_size, offset_x, offset_y

    def _render_puzzle_board(self, puzzle: Puzzle, include_solution: bool = False) -> None:
        full_size = len(puzzle.board_state)
        preview_size, offset_x, offset_y = self._calculate_preview_region(puzzle)
        self._preview_offset_x = offset_x
        self._preview_offset_y = offset_y
        self._preview_full_size = full_size

        if preview_size != self.board_canvas.board_size:
            self.board_canvas.set_board_size(preview_size, reset_coord=False)
        self.board_canvas.set_coordinate_mapping(
            offset_x, offset_y, full_size, refresh=False
        )

        board_state = [["" for _ in range(preview_size)] for _ in range(preview_size)]
        for y, row in enumerate(puzzle.board_state):
            for x, stone in enumerate(row):
                if not stone:
                    continue
                nx = x - offset_x
                ny = y - offset_y
                if 0 <= nx < preview_size and 0 <= ny < preview_size:
                    board_state[ny][nx] = stone

        if include_solution:
            sequence = self._get_solution_sequence(puzzle)
            for index, move in enumerate(sequence):
                x, y = move
                nx = x - offset_x
                ny = y - offset_y
                if 0 <= nx < preview_size and 0 <= ny < preview_size:
                    if not board_state[ny][nx]:
                        board_state[ny][nx] = self._color_for_index(puzzle, index)

        self.board_canvas.board_state = board_state
        self.board_canvas.last_move = None
        self.board_canvas.move_numbers.clear()
        self.board_canvas._hint_pos = None
        self.board_canvas.delete("hint")
        self.board_canvas.set_current_player(puzzle.player_color)
        self.board_canvas.refresh()

        if include_solution and puzzle.solution:
            last_x, last_y = puzzle.solution[-1]
            lx = last_x - offset_x
            ly = last_y - offset_y
            if 0 <= lx < preview_size and 0 <= ly < preview_size:
                self.board_canvas.set_last_move(lx, ly)

    def _get_solution_sequence(self, puzzle: Puzzle) -> List[tuple[int, int]]:
        return [(int(x), int(y)) for x, y in puzzle.solution]

    def _color_for_index(self, puzzle: Puzzle, index: int) -> str:
        if index % 2 == 0:
            return puzzle.player_color
        return "white" if puzzle.player_color == "black" else "black"

    def _apply_auto_responses(self, puzzle: Puzzle) -> None:
        sequence = self._get_solution_sequence(puzzle)
        while self._solution_index < len(sequence):
            expected_color = self._color_for_index(puzzle, self._solution_index)
            if expected_color == puzzle.player_color:
                return
            x, y = sequence[self._solution_index]
            nx = x - self._preview_offset_x
            ny = y - self._preview_offset_y
            if 0 <= nx < self.board_canvas.board_size and 0 <= ny < self.board_canvas.board_size:
                if not self.board_canvas.board_state[ny][nx]:
                    self.board_canvas.place_stone(nx, ny, expected_color, animate=False)
                self.board_canvas.set_last_move(nx, ny)
            self._solution_index += 1

    def _reset_board(self, puzzle: Puzzle) -> None:
        self._solution_index = 0
        self._render_puzzle_board(puzzle, include_solution=False)

    def _on_board_click(self, x: int, y: int) -> None:
        if not self._active_entry or self._puzzle_solved:
            return

        puzzle = self._active_entry.puzzle
        sequence = self._get_solution_sequence(puzzle)
        if not sequence:
            return

        full_size = self._preview_full_size or len(puzzle.board_state)
        full_x = x + self._preview_offset_x
        full_y = y + self._preview_offset_y
        if not (0 <= full_x < full_size and 0 <= full_y < full_size):
            return
        if self.board_canvas.board_state[y][x]:
            return

        if self._solution_index >= len(sequence):
            return

        expected_color = self._color_for_index(puzzle, self._solution_index)
        if expected_color != puzzle.player_color:
            return

        expected_move = sequence[self._solution_index]
        if (full_x, full_y) != expected_move:
            feedback = ""
            if hasattr(self.teaching_system, "get_puzzle_wrong_move_message"):
                feedback = self.teaching_system.get_puzzle_wrong_move_message(
                    puzzle, full_x, full_y
                )
            if not feedback and puzzle.wrong_moves:
                feedback = puzzle.wrong_moves.get((full_x, full_y)) or puzzle.wrong_moves.get(
                    f"{full_x},{full_y}"
                )
            self.status_var.set(
                feedback or self.translator.get("problem_status_incorrect")
            )
            if getattr(self.teaching_system, "user_db", None):
                try:
                    self.teaching_system.user_db.record_puzzle_attempt(
                        self.teaching_system.user_id,
                        puzzle.id,
                        success=False,
                        time_spent=0,
                        hints_used=0,
                    )
                except Exception:
                    pass
            return

        self.board_canvas.place_stone(x, y, puzzle.player_color, animate=False)
        self.board_canvas.set_last_move(x, y)
        self._solution_index += 1
        self._apply_auto_responses(puzzle)

        if self._solution_index >= len(sequence):
            self.status_var.set(self.translator.get("problem_status_completed"))
            self._puzzle_solved = True
            if getattr(self.teaching_system, "user_db", None):
                try:
                    self.teaching_system.user_db.record_puzzle_attempt(
                        self.teaching_system.user_id,
                        puzzle.id,
                        success=True,
                        time_spent=0,
                        hints_used=0,
                    )
                    self.teaching_system.user_db.mark_puzzle_completed(
                        self.teaching_system.user_id,
                        puzzle.id,
                    )
                except Exception:
                    pass
        else:
            self.status_var.set(self.translator.get("problem_status_continue"))

    def _on_show_hint(self) -> None:
        if not self._active_entry:
            return
        hint = self._puzzle_text(self._active_entry.puzzle, "hint")
        if not hint:
            return
        messagebox.showinfo(self.translator.get("hint"), hint, parent=self)

    def _on_show_solution(self) -> None:
        if not self._active_entry:
            return
        puzzle = self._active_entry.puzzle
        self._show_solution_window(puzzle)
        self._render_solution(puzzle)

    def _on_reset_board(self) -> None:
        if not self._active_entry:
            return
        self._puzzle_solved = False
        self._solution_index = 0
        self._reset_board(self._active_entry.puzzle)
        self.status_var.set(self.translator.get("problem_status_ready"))

    def _render_solution(self, puzzle: Puzzle) -> None:
        self._render_puzzle_board(puzzle, include_solution=True)

    def _show_solution_window(self, puzzle: Puzzle) -> None:
        window = self._solution_window
        if window is None or not window.winfo_exists():
            window = tk.Toplevel(self)
            window.title(self.translator.get("problem_solution"))
            window.geometry("640x600")
            window.minsize(420, 420)
            window.protocol("WM_DELETE_WINDOW", self._close_solution_window)

            container = ttk.Frame(window, padding=10)
            container.pack(fill="both", expand=True)

            self._solution_title = ttk.Label(
                container, text="", font=("Arial", 12, "bold")
            )
            self._solution_title.pack(anchor="w", pady=(0, 6))

            board_frame = ttk.Frame(container)
            board_frame.pack(fill="both", expand=True)

            self._solution_board = BoardCanvas(
                board_frame,
                board_size=9,
                theme=self.theme,
                show_coordinates=False,
            )
            self._solution_board.pack(fill="both", expand=True)
            self._solution_board.set_show_move_numbers(True)
            self._solution_board.on_click = None
            self._solution_board.on_hover = None
            self._solution_board.on_right_click = None

            ttk.Button(
                container,
                text=self.translator.get("close"),
                command=self._close_solution_window,
            ).pack(anchor="e", pady=(8, 0))

            self._solution_window = window

        if self._solution_title is not None:
            self._solution_title.config(text=self._puzzle_text(puzzle, "title"))
        self._update_solution_board(puzzle)
        window.lift()
        window.focus_force()

    def _close_solution_window(self) -> None:
        if self._solution_window is None:
            return
        try:
            self._solution_window.destroy()
        finally:
            self._solution_window = None
            self._solution_board = None
            self._solution_title = None

    def _build_solution_state(
        self, puzzle: Puzzle
    ) -> tuple[int, int, int, int, list[list[str]], dict[tuple[int, int], int], Optional[tuple[int, int]]]:
        full_size = len(puzzle.board_state)
        preview_size, offset_x, offset_y = self._calculate_preview_region(puzzle)
        board_state = [["" for _ in range(preview_size)] for _ in range(preview_size)]
        for y, row in enumerate(puzzle.board_state):
            for x, stone in enumerate(row):
                if not stone:
                    continue
                nx = x - offset_x
                ny = y - offset_y
                if 0 <= nx < preview_size and 0 <= ny < preview_size:
                    board_state[ny][nx] = stone

        move_numbers: dict[tuple[int, int], int] = {}
        last_move: Optional[tuple[int, int]] = None
        sequence = self._get_solution_sequence(puzzle)
        for index, (x, y) in enumerate(sequence, start=1):
            nx = x - offset_x
            ny = y - offset_y
            if 0 <= nx < preview_size and 0 <= ny < preview_size:
                board_state[ny][nx] = self._color_for_index(puzzle, index - 1)
                move_numbers[(nx, ny)] = index
                last_move = (nx, ny)

        return (
            preview_size,
            offset_x,
            offset_y,
            full_size,
            board_state,
            move_numbers,
            last_move,
        )

    def _update_solution_board(self, puzzle: Puzzle) -> None:
        if self._solution_board is None:
            return

        (
            preview_size,
            offset_x,
            offset_y,
            full_size,
            board_state,
            move_numbers,
            last_move,
        ) = self._build_solution_state(puzzle)

        if preview_size != self._solution_board.board_size:
            self._solution_board.set_board_size(preview_size, reset_coord=False)
        self._solution_board.set_coordinate_mapping(
            offset_x, offset_y, full_size, refresh=False
        )
        self._solution_board.board_state = board_state
        self._solution_board.move_numbers = move_numbers
        self._solution_board.last_move = last_move
        self._solution_board._hint_pos = None
        self._solution_board.delete("hint")
        self._solution_board.set_current_player(puzzle.player_color)
        self._solution_board.set_show_move_numbers(True)
        self._solution_board.refresh()

    def _format_solution(self, puzzle: Puzzle) -> str:
        sequence = self._get_solution_sequence(puzzle)
        if not sequence:
            return self.translator.get("no_results")
        size = len(puzzle.board_state)
        parts = []
        for index, (x, y) in enumerate(sequence):
            color = self._color_for_index(puzzle, index)
            label = self.translator.get(color, color)
            parts.append(f"{label}:{self._format_coord(x, y, size)}")
        moves = " -> ".join(parts)
        return f"{self.translator.get('problem_solution')}: {moves}"

    def _format_coord(self, x: int, y: int, size: int) -> str:
        letters = "ABCDEFGHJKLMNOPQRST"[:size]
        try:
            col = letters[int(x)]
        except Exception:
            col = "?"
        row = size - int(y)
        return f"{col}{row}"

    def _open_web_search(self, keyword: str) -> None:
        if not keyword:
            return
        url = self._build_search_url(keyword, "go tsumego")
        try:
            webbrowser.open(url)
        except Exception:
            messagebox.showwarning(self.translator.get("warning"), url)

    def _build_search_url(self, keyword: str, context: str = "") -> str:
        query = keyword.strip()
        if context:
            query = f"{query} {context}".strip()

        engine = "google" if getattr(self.translator, "language", "") == "en" else "bing"
        base_url = (
            "https://www.google.com/search?q="
            if engine == "google"
            else "https://www.bing.com/search?q="
        )
        return base_url + quote_plus(query)

    def _open_link(self, url: str) -> None:
        try:
            webbrowser.open(url, new=2)
        except Exception as exc:
            messagebox.showerror(
                self.translator.get("error"),
                f"Unable to open link: {exc}",
                parent=self,
            )


__all__ = ["ProblemLibraryWindow"]
