"""
复盘系统模块
支持分支变化、评注、棋谱浏览等功能
"""

import json
import time
import hashlib
from typing import List, Dict, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np

# 导入核心模块
from core import Board, Game, GamePhase, Move, MoveSequence
from ai import AIFactory
from ui.translator import Translator, get_translator
from utils.content_db import get_content_db
from utils.user_db import get_user_db


class NodeType(Enum):
    """节点类型"""
    MAIN = 'main'  # 主线
    VARIATION = 'variation'  # 变化
    COMMENT = 'comment'  # 评注节点


_EVALUATION_CACHE: Optional[Dict[str, Dict[str, str]]] = None


def _get_evaluation_catalog(language: str = 'zh') -> Dict[str, Dict[str, str]]:
    global _EVALUATION_CACHE
    if _EVALUATION_CACHE is not None:
        return _EVALUATION_CACHE
    try:
        _EVALUATION_CACHE = get_content_db().list_comment_evaluations(language)
    except Exception:
        _EVALUATION_CACHE = {}
    return _EVALUATION_CACHE


def _get_evaluation_symbol(key: Optional[str]) -> str:
    if not key:
        return ''
    catalog = _get_evaluation_catalog()
    item = catalog.get(key)
    if item and item.get('symbol'):
        return str(item['symbol'])
    return ''


@dataclass
class Comment:
    """评注数据类"""
    text: str
    author: str = ""
    timestamp: float = field(default_factory=time.time)
    move_evaluation: Optional[str] = None  # 好手/恶手/疑问手等
    
    EVALUATIONS = {
        'good': '!',  # 好手
        'excellent': '!!',  # 妙手
        'bad': '?',  # 恶手
        'very_bad': '??',  # 大恶手
        'interesting': '!?',  # 有趣的一手
        'dubious': '?!',  # 疑问手
    }
    
    def to_sgf(self) -> str:
        """转换为SGF格式的评注"""
        sgf_text = self.text
        if self.move_evaluation:
            symbol = _get_evaluation_symbol(self.move_evaluation)
            if not symbol:
                symbol = self.EVALUATIONS.get(self.move_evaluation, '')
            if symbol:
                sgf_text = f"{symbol} {sgf_text}"
        if self.author:
            sgf_text = f"[{self.author}] {sgf_text}"
        return sgf_text


@dataclass
class Variation:
    """变化分支"""
    name: str
    moves: List[Move]
    comment: Optional[Comment] = None
    parent_node: Optional['MoveNode'] = None
    
    def get_first_move(self) -> Optional[Move]:
        """获取第一手"""
        return self.moves[0] if self.moves else None
    
    def get_move_at(self, index: int) -> Optional[Move]:
        """获取指定位置的棋步"""
        if 0 <= index < len(self.moves):
            return self.moves[index]
        return None


class MoveNode:
    """棋谱树节点"""
    
    def __init__(self, move: Optional[Move] = None, parent: Optional['MoveNode'] = None):
        self.move = move
        self.parent = parent
        self.children: List['MoveNode'] = []
        self.variations: List[Variation] = []
        self.comments: List[Comment] = []
        self.node_type = NodeType.MAIN
        
        # 分析数据
        self.analysis_data: Dict[str, Any] = {}
        self.winrate: Optional[float] = None
        self.best_moves: List[Move] = []
        
    def add_child(self, move: Move) -> 'MoveNode':
        """添加子节点"""
        child = MoveNode(move, self)
        self.children.append(child)
        return child
    
    def add_variation(self, variation: Variation) -> 'MoveNode':
        """添加变化分支"""
        variation.parent_node = self
        self.variations.append(variation)
        
        # 创建变化分支的节点树
        if variation.moves:
            var_node = MoveNode(variation.moves[0], self)
            var_node.node_type = NodeType.VARIATION
            
            current = var_node
            for move in variation.moves[1:]:
                current = current.add_child(move)
            
            return var_node
        return self
    
    def add_comment(self, comment: Comment):
        """添加评注"""
        self.comments.append(comment)
    
    def get_main_line(self) -> List[Move]:
        """获取主线棋谱"""
        moves = []
        if self.move:
            moves.append(self.move)
        
        # 递归获取主线的子节点
        for child in self.children:
            if child.node_type == NodeType.MAIN:
                moves.extend(child.get_main_line())
                break
        
        return moves
    
    def get_path_to_root(self) -> List['MoveNode']:
        """获取到根节点的路径"""
        path = []
        current = self
        while current:
            path.append(current)
            current = current.parent
        return list(reversed(path))
    
    def is_leaf(self) -> bool:
        """是否为叶子节点"""
        return len(self.children) == 0
    
    def has_variations(self) -> bool:
        """是否有变化分支"""
        return len(self.variations) > 0
    
    def get_move_number(self) -> int:
        """获取手数"""
        path = self.get_path_to_root()
        return len([n for n in path if n.move is not None])


class MoveTree:
    """棋谱树"""
    
    def __init__(self, board_size: int = 19):
        self.root = MoveNode()
        self.current_node = self.root
        self.board_size = board_size
        
        # 游戏信息
        self.game_info = {
            'black_player': '',
            'white_player': '',
            'result': '',
            'date': '',
            'event': '',
            'round': '',
            'komi': 7.5,
            'rules': 'chinese',
            'time_limit': 0
        }
    
    def add_move(self, move: Move) -> MoveNode:
        """添加一手棋"""
        new_node = self.current_node.add_child(move)
        self.current_node = new_node
        return new_node
    
    def back_to_parent(self) -> bool:
        """回到父节点"""
        if self.current_node.parent:
            self.current_node = self.current_node.parent
            return True
        return False
    
    def go_to_child(self, index: int = 0) -> bool:
        """前进到子节点"""
        if index < len(self.current_node.children):
            self.current_node = self.current_node.children[index]
            return True
        return False
    
    def go_to_node(self, node: MoveNode) -> bool:
        """跳转到指定节点"""
        # 检查节点是否在树中
        if self._node_exists(node):
            self.current_node = node
            return True
        return False
    
    def _node_exists(self, node: MoveNode, current: Optional[MoveNode] = None) -> bool:
        """检查节点是否存在于树中"""
        if current is None:
            current = self.root
        
        if current == node:
            return True
        
        for child in current.children:
            if self._node_exists(node, child):
                return True
        
        return False
    
    def get_current_board(self) -> Board:
        """获取当前节点的棋盘状态"""
        board = Board(self.board_size)
        path = self.current_node.get_path_to_root()
        
        for node in path:
            if node.move and node.move.x >= 0 and node.move.y >= 0:
                board.place_stone(node.move.x, node.move.y, node.move.color)
        
        return board
    
    def export_to_sgf(self) -> str:
        """导出为SGF格式"""
        sgf = f"(;FF[4]GM[1]SZ[{self.board_size}]"
        
        # 添加游戏信息
        if self.game_info['black_player']:
            sgf += f"PB[{self.game_info['black_player']}]"
        if self.game_info['white_player']:
            sgf += f"PW[{self.game_info['white_player']}]"
        if self.game_info['result']:
            sgf += f"RE[{self.game_info['result']}]"
        if self.game_info['komi']:
            sgf += f"KM[{self.game_info['komi']}]"
        
        # 递归添加节点
        sgf += self._node_to_sgf(self.root)
        sgf += ")"
        
        return sgf
    
    def _node_to_sgf(self, node: MoveNode) -> str:
        """将节点转换为SGF格式"""
        sgf = ""
        
        if node.move:
            color = 'B' if node.move.color == 'black' else 'W'
            coords = node.move.to_sgf_coords(self.board_size)
            sgf += f";{color}[{coords}]"
            
            # 添加评注
            if node.comments:
                comment_text = "\n".join(c.to_sgf() for c in node.comments)
                sgf += f"C[{comment_text}]"
        
        # 处理变化分支
        if node.variations:
            for variation in node.variations:
                sgf += "("
                for move in variation.moves:
                    color = 'B' if move.color == 'black' else 'W'
                    coords = move.to_sgf_coords(self.board_size)
                    sgf += f";{color}[{coords}]"
                sgf += ")"
        
        # 递归处理子节点
        for child in node.children:
            sgf += self._node_to_sgf(child)
        
        return sgf


class ReplayManager:
    """复盘管理器"""
    
    def __init__(self, game: Optional[Game] = None, user_db=None, session_id: Optional[str] = None):
        self.game = game
        self.move_tree = MoveTree(game.board.size if game else 19)
        self.current_board = Board(self.move_tree.board_size)
        self.user_db = user_db or get_user_db()
        self.session_id = session_id or self._compute_session_id(game)
        
        # 分析引擎
        self.analysis_engine = None
        self.ai_analyzer = None
        
        # 如果有游戏，导入棋谱
        if game:
            self._import_from_game(game)
        self._load_persisted_comments()
    
    def _import_from_game(self, game: Game):
        """从游戏导入棋谱"""
        self.move_tree.game_info.update({
            'black_player': game.game_info.black_player,
            'white_player': game.game_info.white_player,
            'result': game.game_info.result,
            'komi': game.game_info.komi,
            'rules': game.game_info.rules
        })
        
        # 导入棋步
        for move in game.move_history:
            self.move_tree.add_move(move)
        
        # 回到开始
        self.move_tree.current_node = self.move_tree.root

    def _compute_session_id(self, game: Optional[Game]) -> str:
        if not game:
            return f"replay_{int(time.time())}"
        payload = {
            "board_size": game.board.size,
            "black": game.game_info.black_player,
            "white": game.game_info.white_player,
            "moves": [(m.x, m.y, m.color) for m in game.move_history],
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
        return f"game_{digest}"

    def _build_node_path(self, node: MoveNode) -> str:
        tokens: List[str] = []
        current = node
        while current and current.parent:
            parent = current.parent
            token = None
            if parent.children:
                for idx, child in enumerate(parent.children):
                    if child is current:
                        token = f"c{idx}"
                        break
            if token is None and parent.variations:
                for idx, variation in enumerate(parent.variations):
                    if variation.moves and current.move and variation.moves[0] == current.move:
                        token = f"v{idx}"
                        break
            if token is None:
                break
            tokens.append(token)
            current = parent
        return "/".join(reversed(tokens))

    def _find_node_by_path(self, path: str) -> Optional[MoveNode]:
        if not path:
            return self.move_tree.root
        current = self.move_tree.root
        for token in path.split("/"):
            if not token:
                continue
            if token.startswith("c"):
                try:
                    idx = int(token[1:])
                except Exception:
                    return None
                if idx < 0 or idx >= len(current.children):
                    return None
                current = current.children[idx]
                continue
            if token.startswith("v"):
                try:
                    idx = int(token[1:])
                except Exception:
                    return None
                if idx < 0 or idx >= len(current.variations):
                    return None
                variation = current.variations[idx]
                if not variation.moves:
                    return None
                current = MoveNode(variation.moves[0], current)
                current.node_type = NodeType.VARIATION
                for move in variation.moves[1:]:
                    current = current.add_child(move)
                continue
        return current

    def _find_node_by_move_number(self, move_number: int) -> Optional[MoveNode]:
        current = self.move_tree.root
        if move_number <= 0:
            return current
        while current.children:
            current = current.children[0]
            if current.get_move_number() == move_number:
                return current
        return None

    def _load_persisted_comments(self) -> None:
        if not self.user_db or not self.session_id:
            return
        try:
            items = self.user_db.list_replay_comments(self.session_id)
        except Exception:
            return
        for item in items:
            path = str(item.get("node_path") or "")
            move_number = int(item.get("move_number") or 0)
            node = self._find_node_by_path(path)
            if not node and move_number:
                node = self._find_node_by_move_number(move_number)
            if not node:
                continue
            node.comments.append(
                Comment(
                    text=str(item.get("text") or ""),
                    author=str(item.get("author") or ""),
                    move_evaluation=item.get("evaluation"),
                )
            )
    
    def initialize_ai_analyzer(self, ai_level: str = 'expert'):
        """初始化AI分析器"""
        self.ai_analyzer = AIFactory.create_ai(
            ai_level, 
            'black', 
            self.move_tree.board_size
        )
    
    def navigate_to_move(self, move_number: int) -> bool:
        """导航到指定手数"""
        # 回到根节点
        self.move_tree.current_node = self.move_tree.root
        
        # 前进到指定手数
        for _ in range(move_number):
            if not self.move_tree.go_to_child():
                return False
        
        self.current_board = self.move_tree.get_current_board()
        return True
    
    def next_move(self) -> bool:
        """前进一手"""
        if self.move_tree.go_to_child():
            self.current_board = self.move_tree.get_current_board()
            return True
        return False
    
    def previous_move(self) -> bool:
        """后退一手"""
        if self.move_tree.back_to_parent():
            self.current_board = self.move_tree.get_current_board()
            return True
        return False
    
    def go_to_variation(self, variation_index: int) -> bool:
        """进入变化分支"""
        current = self.move_tree.current_node
        if variation_index < len(current.variations):
            variation = current.variations[variation_index]
            if variation.moves:
                # 创建变化节点并切换
                var_node = current.add_variation(variation)
                self.move_tree.current_node = var_node
                self.current_board = self.move_tree.get_current_board()
                return True
        return False
    
    def add_variation_from_current(self, moves: List[Move], name: str = "", 
                                   comment: str = "") -> Variation:
        """从当前位置添加变化"""
        if not name:
            translator = get_translator()
            name = translator.get(
                "variation_label_format",
                index=len(self.move_tree.current_node.variations) + 1,
            )
        variation = Variation(
            name=name,
            moves=moves,
            comment=Comment(comment) if comment else None
        )
        
        self.move_tree.current_node.add_variation(variation)
        return variation
    
    def add_comment(self, text: str, author: str = "", 
                   evaluation: Optional[str] = None) -> Comment:
        """添加评注"""
        comment = Comment(
            text=text,
            author=author,
            move_evaluation=evaluation
        )
        
        self.move_tree.current_node.add_comment(comment)
        if self.user_db and self.session_id:
            try:
                node_path = self._build_node_path(self.move_tree.current_node)
                self.user_db.add_replay_comment(
                    session_id=self.session_id,
                    node_path=node_path,
                    move_number=self.move_tree.current_node.get_move_number(),
                    text=text,
                    author=author,
                    evaluation=evaluation,
                )
            except Exception:
                pass
        return comment
    
    def analyze_current_position(self) -> Dict[str, Any]:
        """分析当前局面"""
        if not self.ai_analyzer:
            self.initialize_ai_analyzer()
        
        board = self.move_tree.get_current_board()
        current_color = self._get_current_color()
        
        # 获取AI分析
        eval_result = self.ai_analyzer.evaluate_position(board)
        
        # 获取最佳着法
        game_info = {'ko_point': None, 'move_number': self.move_tree.current_node.get_move_number()}
        legal_moves = self.ai_analyzer.get_legal_moves(board)
        
        # 为每个合法着法评分
        move_scores = []
        for x, y in legal_moves[:10]:  # 只分析前10个候选
            test_board = board.copy()
            test_board.place_stone(x, y, current_color)
            score = self.ai_analyzer.evaluate_position(test_board).score
            move_scores.append((x, y, score))
        
        move_scores.sort(key=lambda m: m[2], reverse=True)
        
        analysis = {
            'winrate': eval_result.winning_probability,
            'score': eval_result.score,
            'best_moves': move_scores[:5],
            'territory_score': eval_result.territory_score,
            'current_player': current_color
        }
        
        # 存储到节点
        self.move_tree.current_node.analysis_data = analysis
        self.move_tree.current_node.winrate = eval_result.winning_probability
        
        return analysis
    
    def _get_current_color(self) -> str:
        """获取当前玩家颜色"""
        move_number = self.move_tree.current_node.get_move_number()
        return 'black' if move_number % 2 == 0 else 'white'
    
    def find_mistakes(self, threshold: float = 0.1) -> List[Tuple[MoveNode, float]]:
        """查找错着（胜率下降超过阈值的着法）"""
        mistakes = []
        
        def traverse(node: MoveNode, parent_winrate: Optional[float] = None):
            if node.winrate is not None and parent_winrate is not None:
                drop = parent_winrate - node.winrate
                if drop > threshold:
                    mistakes.append((node, drop))
            
            for child in node.children:
                traverse(child, node.winrate)
        
        traverse(self.move_tree.root)
        return mistakes
    
    def export_with_analysis(self, include_variations: bool = True,
                            include_comments: bool = True) -> str:
        """导出带分析的棋谱"""
        sgf = self.move_tree.export_to_sgf()
        
        # TODO: 添加分析数据到SGF
        
        return sgf


class ReplayViewer(tk.Frame):
    """复盘查看器UI组件"""
    
    def __init__(
        self,
        parent,
        replay_manager: ReplayManager,
        translator: Optional[Translator] = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.replay_manager = replay_manager
        self.translator = translator or Translator()
        
        self._create_widgets()
        self._bind_events()
        self.update_display()
    
    def _create_widgets(self):
        """创建控件"""
        # 控制按钮
        control_frame = ttk.Frame(self)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(
            control_frame,
            text=self.translator.get("nav_first"),
            command=self.go_to_start,
            width=3,
        ).pack(side='left', padx=2)
        ttk.Button(
            control_frame,
            text=self.translator.get("nav_prev"),
            command=self.previous_move,
            width=3,
        ).pack(side='left', padx=2)
        ttk.Button(
            control_frame,
            text=self.translator.get("nav_next"),
            command=self.next_move,
            width=3,
        ).pack(side='left', padx=2)
        ttk.Button(
            control_frame,
            text=self.translator.get("nav_last"),
            command=self.go_to_end,
            width=3,
        ).pack(side='left', padx=2)
        
        # 手数显示
        self.move_label = ttk.Label(
            control_frame,
            text=self.translator.get("move_progress", current=0, total=0),
        )
        self.move_label.pack(side='left', padx=10)
        
        # 变化列表
        variation_frame = ttk.LabelFrame(
            self,
            text=self.translator.get("variation_branches"),
        )
        variation_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.variation_listbox = tk.Listbox(variation_frame, height=4)
        self.variation_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        self.variation_listbox.bind('<<ListboxSelect>>', self.on_variation_select)
        
        # 评注显示
        comment_frame = ttk.LabelFrame(self, text=self.translator.get("comment"))
        comment_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.comment_text = tk.Text(comment_frame, height=6, wrap='word')
        self.comment_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 分析数据
        analysis_frame = ttk.LabelFrame(self, text=self.translator.get("analysis"))
        analysis_frame.pack(fill='x', padx=5, pady=5)
        
        self.winrate_label = ttk.Label(
            analysis_frame,
            text=self.translator.get("win_rate_format", value="--"),
        )
        self.winrate_label.pack(anchor='w', padx=5, pady=2)
        
        self.best_moves_label = ttk.Label(
            analysis_frame,
            text=self.translator.get("best_moves_format", value="--"),
        )
        self.best_moves_label.pack(anchor='w', padx=5, pady=2)
        
        # 操作按钮
        action_frame = ttk.Frame(self)
        action_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(
            action_frame,
            text=self.translator.get("analyze_current"),
            command=self.analyze_current,
        ).pack(side='left', padx=2)
        ttk.Button(
            action_frame,
            text=self.translator.get("add_comment"),
            command=self.add_comment,
        ).pack(side='left', padx=2)
        ttk.Button(
            action_frame,
            text=self.translator.get("add_variation"),
            command=self.add_variation,
        ).pack(side='left', padx=2)
    
    def _bind_events(self):
        """绑定事件"""
        self.bind_all('<Left>', lambda e: self.previous_move())
        self.bind_all('<Right>', lambda e: self.next_move())
        self.bind_all('<Home>', lambda e: self.go_to_start())
        self.bind_all('<End>', lambda e: self.go_to_end())
    
    def update_display(self):
        """更新显示"""
        current = self.replay_manager.move_tree.current_node
        
        # 更新手数
        move_num = current.get_move_number()
        total_moves = self._get_total_moves()
        self.move_label.config(
            text=self.translator.get(
                "move_progress",
                current=move_num,
                total=total_moves,
            )
        )
        
        # 更新变化列表
        self.variation_listbox.delete(0, 'end')
        for i, var in enumerate(current.variations):
            self.variation_listbox.insert('end', var.name)
        
        # 更新评注
        self.comment_text.delete('1.0', 'end')
        for comment in current.comments:
            self.comment_text.insert('end', f"{comment.text}\n")
        
        # 更新分析数据
        if current.analysis_data:
            winrate = current.analysis_data.get('winrate', 0)
            self.winrate_label.config(
                text=self.translator.get(
                    "win_rate_format",
                    value=f"{winrate:.1%}",
                )
            )
            
            best_moves = current.analysis_data.get('best_moves', [])
            if best_moves:
                moves_text = ", ".join(f"({x},{y})" for x, y, _ in best_moves[:3])
                self.best_moves_label.config(
                    text=self.translator.get(
                        "best_moves_format",
                        value=moves_text,
                    )
                )
        else:
            self.winrate_label.config(
                text=self.translator.get("win_rate_format", value="--")
            )
            self.best_moves_label.config(
                text=self.translator.get("best_moves_format", value="--")
            )
    
    def _get_total_moves(self) -> int:
        """获取总手数"""
        main_line = self.replay_manager.move_tree.root.get_main_line()
        return len(main_line)
    
    def go_to_start(self):
        """回到开始"""
        self.replay_manager.move_tree.current_node = self.replay_manager.move_tree.root
        self.update_display()
        self.on_position_changed()
    
    def go_to_end(self):
        """跳到结束"""
        while self.replay_manager.next_move():
            pass
        self.update_display()
        self.on_position_changed()
    
    def next_move(self):
        """前进一手"""
        if self.replay_manager.next_move():
            self.update_display()
            self.on_position_changed()
    
    def previous_move(self):
        """后退一手"""
        if self.replay_manager.previous_move():
            self.update_display()
            self.on_position_changed()
    
    def on_variation_select(self, event):
        """选择变化分支"""
        selection = self.variation_listbox.curselection()
        if selection:
            index = selection[0]
            if self.replay_manager.go_to_variation(index):
                self.update_display()
                self.on_position_changed()
    
    def analyze_current(self):
        """分析当前局面"""
        analysis = self.replay_manager.analyze_current_position()
        self.update_display()
        
        # 显示分析结果
        messagebox.showinfo(
            self.translator.get("analysis_complete"),
            self.translator.get(
                "analysis_result_format",
                winrate=f"{analysis['winrate']:.1%}",
                score=f"{analysis['score']:.1f}",
            ),
        )
    
    def add_comment(self):
        """添加评注对话框"""
        dialog = tk.Toplevel(self)
        dialog.title(self.translator.get("add_comment"))
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text=self.translator.get("comment_content_label")).pack(
            anchor='w', padx=5, pady=5
        )
        
        text = tk.Text(dialog, height=10)
        text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 评价选择
        eval_frame = ttk.Frame(dialog)
        eval_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(eval_frame, text=self.translator.get("comment_evaluation_label")).pack(
            side='left'
        )
        
        eval_var = tk.StringVar()
        eval_combo = ttk.Combobox(eval_frame, textvariable=eval_var, width=15)
        options, eval_map = self._get_evaluation_options()
        eval_combo['values'] = options
        eval_combo.pack(side='left', padx=5)
        
        def save_comment():
            comment_text = text.get('1.0', 'end').strip()
            if comment_text:
                evaluation = eval_map.get(eval_var.get())
                
                self.replay_manager.add_comment(comment_text, evaluation=evaluation)
                self.update_display()
                dialog.destroy()
        
        ttk.Button(dialog, text=self.translator.get("save"), command=save_comment).pack(pady=5)

    def _get_evaluation_options(self) -> Tuple[List[str], Dict[str, str]]:
        order = ['good', 'excellent', 'bad', 'very_bad', 'interesting', 'dubious']
        labels: List[str] = []
        mapping: Dict[str, str] = {}
        catalog = _get_evaluation_catalog()
        for key in order:
            label = catalog.get(key, {}).get('label') if catalog else None
            if label:
                labels.append(label)
                mapping[label] = key
        if labels:
            return [''] + labels, mapping

        fallback_labels = [
            self.translator.get('evaluation_good'),
            self.translator.get('evaluation_excellent'),
            self.translator.get('evaluation_bad'),
            self.translator.get('evaluation_very_bad'),
            self.translator.get('evaluation_interesting'),
            self.translator.get('evaluation_dubious'),
        ]
        fallback_map = {
            self.translator.get('evaluation_good'): 'good',
            self.translator.get('evaluation_excellent'): 'excellent',
            self.translator.get('evaluation_bad'): 'bad',
            self.translator.get('evaluation_very_bad'): 'very_bad',
            self.translator.get('evaluation_interesting'): 'interesting',
            self.translator.get('evaluation_dubious'): 'dubious',
        }
        return [''] + fallback_labels, fallback_map
    
    def add_variation(self):
        """添加变化分支（需要棋盘交互）"""
        messagebox.showinfo(
            self.translator.get("add_variation"),
            self.translator.get("add_variation_hint"),
        )
    
    def on_position_changed(self):
        """局面改变回调（供外部调用）"""
        pass
