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

from core import Board, Game, Rules
from .board_canvas import BoardCanvas
from .translator import Translator
from .themes import Theme
from .widgets import ModernScrollbar
from features.replay import ReplayManager, MoveNode


class GameTreeWindow(tk.Toplevel):
    """棋谱树窗口（支持主线 + 变化分支的浏览）。"""

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

        self.replay = ReplayManager(game)
        self._node_map: Dict[str, MoveNode] = {}

        # 默认跳转到主线最后一手，方便直接看到当前局面
        node = self.replay.move_tree.root
        while node.children:
            node = node.children[-1]
        self.replay.move_tree.current_node = node

        self._create_widgets()
        self._populate_moves()
        self._select_default()

    # --- UI ---

    def _create_widgets(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        paned = ttk.PanedWindow(container, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        # 左侧：手顺/分支列表
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

        yscroll = ModernScrollbar(
            left,
            orient="vertical",
            command=self.tree.yview,
            theme=self.theme,
            match_widget=self.tree,
        )
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
        # 预览棋盘只读：屏蔽交互/阴影
        self.preview_canvas.unbind("<Button-1>")
        self.preview_canvas.unbind("<Button-3>")
        self.preview_canvas.unbind("<Motion>")
        self.preview_canvas.on_click = None
        self.preview_canvas.on_hover = None
        self.preview_canvas.on_right_click = None

        # 底部按钮
        bottom = ttk.Frame(container)
        bottom.pack(fill="x", pady=(8, 0))

        ttk.Button(bottom, text=self.translator.get("close"), command=self.destroy).pack(side="right")

    # --- 数据 ---

    def _populate_moves(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._node_map.clear()

        def add_node(node: MoveNode, parent_id: str):
            move = node.move
            move_num = node.get_move_number()
            iid = f"n{len(self._node_map)}"
            self._node_map[iid] = node

            if move:
                player = self.translator.get(getattr(move, "color", ""))
                move_text = self._format_move(move.x, move.y)
                try:
                    captured = str(len(getattr(move, "captured", []) or []))
                except Exception:
                    captured = ""
            else:
                player = "-"
                move_text = self.translator.get("start")
                captured = ""

            self.tree.insert(
                parent_id,
                "end",
                iid=iid,
                text=str(move_num),
                values=(player, move_text, captured),
            )

            # 先主线，再变化
            for child in node.children:
                add_node(child, iid)
            for var in node.variations:
                # 预览模式仅遍历已有 variation 节点，不修改原树
                if not var.moves:
                    continue
                var_root = MoveNode(var.moves[0], node)
                current = var_root
                for mv in var.moves[1:]:
                    current = current.add_child(mv)
                add_node(var_root, iid)

        add_node(self.replay.move_tree.root, "")

    def _select_default(self) -> None:
        # 默认选中当前手数对应的节点（如果存在），否则根节点
        # 选中当前节点；若不存在则选中首个
        current = self.replay.move_tree.current_node
        target_id = None
        for iid, node in self._node_map.items():
            if node is current:
                target_id = iid
                break
        if not target_id:
            target_id = next(iter(self._node_map.keys()), None)
        if target_id:
            self.tree.selection_set(target_id)
            self.tree.see(target_id)
            self._show_position_by_id(target_id)

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

    def _build_preview_board(self, node: MoveNode) -> Board:
        """根据 MoveNode 路径重放到当前节点，支持分支。"""
        board = Board(self.game.board_size)
        rules = Rules(self.game.game_info.rules, self.game.game_info.komi)

        path = node.get_path_to_root()
        for step in path:
            mv = step.move
            if not mv:
                continue
            if mv.x < 0 or mv.y < 0:
                # pass，不用处理棋盘
                continue
            # 忽略合法性，直接执行（需通过 rules 以便吃子/劫）
            ok, _, _ = rules.execute_move(board, mv.x, mv.y, mv.color, mv.move_number)
            if not ok:
                board.place_stone(mv.x, mv.y, mv.color)

        # 提供 move_history 作为 fallback（方便显示手数/最后一手）
        setattr(board, "move_history", [step.move for step in path if step.move])
        return board

    # --- 事件 ---

    def _on_select(self, _event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        self._show_position_by_id(sel[0])

    def _show_position_by_id(self, iid: str) -> None:
        node = self._node_map.get(iid)
        if not node:
            return
        self.replay.move_tree.current_node = node
        board = self._build_preview_board(node)
        self.preview_canvas.update_board(board)
