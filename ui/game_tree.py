"""
棋谱树 / 棋谱浏览窗口

当前版本以“主线棋谱浏览”为主：
- 左侧列表展示每一手（包含虚手）
- 右侧棋盘用于预览任意手数的局面

后续若要支持真正的“树”（分支变化），可在此窗口中引入分支节点与编辑流程。
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, List

from core import Board, Game
from .board_canvas import BoardCanvas
from .translator import Translator
from .themes import Theme


class GameTreeWindow(tk.Toplevel):
    """棋谱树窗口（主线浏览 + 预览棋盘）。"""

    def __init__(
        self,
        parent: tk.Misc,
        game: Game,
        translator: Optional[Translator] = None,
        theme: Optional[Theme] = None,
        show_coordinates: bool = True,
        show_move_numbers: bool = False,
    ):
        super().__init__(parent)

        self.game = game
        self.translator = translator or Translator()
        self.theme = theme or Theme(name="default")
        self._show_coordinates = bool(show_coordinates)
        self._show_move_numbers = bool(show_move_numbers)

        self.title(self.translator.get("game_tree"))
        self.geometry("980x700")
        self.minsize(820, 560)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._moves_by_number: Dict[int, Any] = {}

        self._create_widgets()
        self._populate_moves()
        self._select_default()

    # --- UI ---

    def _create_widgets(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        paned = ttk.PanedWindow(container, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        # 左侧：手顺列表
        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        self.tree = ttk.Treeview(
            left,
            columns=("player", "move", "captured"),
            show="tree headings",
            height=18,
        )
        self.tree.heading("#0", text="#")
        self.tree.heading("player", text=self.translator.get("current_player"))
        self.tree.heading("move", text=self.translator.get("move"))
        self.tree.heading("captured", text=self.translator.get("captured"))

        self.tree.column("#0", width=60, stretch=False, anchor="e")
        self.tree.column("player", width=90, stretch=False, anchor="w")
        self.tree.column("move", width=110, stretch=False, anchor="w")
        self.tree.column("captured", width=70, stretch=False, anchor="e")

        yscroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # 右侧：预览棋盘
        right = ttk.Frame(paned)
        paned.add(right, weight=2)

        self.preview_canvas = BoardCanvas(
            right,
            board_size=self.game.board_size,
            theme=self.theme,
            show_coordinates=self._show_coordinates,
        )
        self.preview_canvas.pack(fill="both", expand=True)
        self.preview_canvas.set_show_move_numbers(self._show_move_numbers)

        # 底部按钮
        bottom = ttk.Frame(container)
        bottom.pack(fill="x", pady=(8, 0))

        ttk.Button(bottom, text=self.translator.get("close"), command=self.destroy).pack(side="right")

    # --- 数据 ---

    def _populate_moves(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        # move_number -> Move（仅统计对局手数，忽略让子(第0手)）
        self._moves_by_number = {
            int(getattr(m, "move_number", 0) or 0): m
            for m in (self.game.move_history or [])
            if int(getattr(m, "move_number", 0) or 0) > 0
        }

        # 初始局面（0手）
        self.tree.insert(
            "",
            "end",
            iid="0",
            text="0",
            values=("-", self.translator.get("start"), ""),
        )

        max_move = int(getattr(self.game, "move_number", 0) or 0)
        for n in range(1, max_move + 1):
            m = self._moves_by_number.get(n)
            if not m:
                continue

            player = self.translator.get(getattr(m, "color", ""))
            move_text = self._format_move(getattr(m, "x", -1), getattr(m, "y", -1))
            captured = ""
            try:
                captured = str(len(getattr(m, "captured", []) or []))
            except Exception:
                captured = "0"

            self.tree.insert(
                "",
                "end",
                iid=str(n),
                text=str(n),
                values=(player, move_text, captured),
            )

    def _select_default(self) -> None:
        target = str(int(getattr(self.game, "move_number", 0) or 0))
        if target not in self.tree.get_children(""):
            target = "0"
        self.tree.selection_set(target)
        self.tree.see(target)
        self._show_position(int(target))

    def _format_move(self, x: int, y: int) -> str:
        if x < 0 or y < 0:
            return self.translator.get("pass")
        letters = "ABCDEFGHJKLMNOPQRST"[: self.game.board_size]
        try:
            col = letters[int(x)]
        except Exception:
            col = "?"
        row = self.game.board_size - int(y)
        return f"{col}{row}"

    def _build_preview_board(self, move_number: int) -> Board:
        # 基于 state_history 预览局面；state_history[0] 为初始局面
        state = self.game.state_history[move_number]

        board = Board(self.game.board_size)
        board.grid = [row[:] for row in state.board]

        # 给 BoardCanvas.update_board 提供 fallback：用 move_history 推导手数/最后一手
        history: List[Any] = []
        for m in (self.game.move_history or []):
            mn = int(getattr(m, "move_number", 0) or 0)
            if mn == 0 or mn <= move_number:
                history.append(m)
        setattr(board, "move_history", history)

        return board

    # --- 事件 ---

    def _on_select(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        try:
            move_number = int(sel[0])
        except Exception:
            return
        self._show_position(move_number)

    def _show_position(self, move_number: int) -> None:
        if not self.game:
            return
        if move_number < 0 or move_number >= len(self.game.state_history):
            return
        board = self._build_preview_board(move_number)
        self.preview_canvas.update_board(board)

