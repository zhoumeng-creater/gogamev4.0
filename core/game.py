"""
游戏控制模块
负责游戏流程、状态管理、历史记录等
"""

import time
import json
from typing import List, Tuple, Optional, Dict, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime

from .board import Board, StoneColor
from .rules import Rules, MoveResult
from .territory import Territory
from .scoring import ScoringSystem, ChineseScoring, JapaneseScoring


class GamePhase(Enum):
    """游戏阶段枚举"""
    NOT_STARTED = 'not_started'
    PLAYING = 'playing'
    SCORING = 'scoring'  # 点目阶段
    ENDED = 'ended'
    PAUSED = 'paused'
    ANALYZING = 'analyzing'  # 分析模式


@dataclass
class Move:
    """棋步数据类"""
    x: int
    y: int
    color: str
    move_number: int
    timestamp: float = field(default_factory=time.time)
    time_spent: float = 0.0  # 思考时间
    captured: List[Tuple[int, int]] = field(default_factory=list)
    comment: str = ""
    variations: List['MoveSequence'] = field(default_factory=list)  # 变化图
    
    def to_sgf_coords(self, board_size: int = 19) -> str:
        """转换为SGF坐标格式"""
        if self.x < 0 or self.y < 0:  # 虚手
            return ""
        col = chr(ord('a') + self.x)
        row = chr(ord('a') + self.y)
        return f"{col}{row}"
    
    @classmethod
    def from_sgf_coords(cls, coords: str, color: str, move_number: int) -> 'Move':
        """从SGF坐标创建Move对象"""
        if not coords or len(coords) != 2:
            return cls(-1, -1, color, move_number)  # 虚手
        
        x = ord(coords[0]) - ord('a')
        y = ord(coords[1]) - ord('a')
        return cls(x, y, color, move_number)


@dataclass
class MoveSequence:
    """棋步序列（用于变化图）"""
    moves: List[Move] = field(default_factory=list)
    comment: str = ""
    name: str = ""
    
    def add_move(self, move: Move):
        """添加一手棋"""
        self.moves.append(move)
    
    def get_board_at(self, index: int, initial_board: Board) -> Board:
        """获取某一步时的棋盘状态"""
        board = initial_board.copy()
        rules = Rules()
        
        for i, move in enumerate(self.moves):
            if i > index:
                break
            if move.x >= 0 and move.y >= 0:
                rules.execute_move(board, move.x, move.y, move.color, i + 1)
        
        return board


@dataclass
class GameState:
    """游戏状态快照"""
    board: List[List[str]]
    current_player: str
    move_number: int
    captured_black: int
    captured_white: int
    ko_point: Optional[Tuple[int, int]]
    last_move: Optional[Tuple[int, int]]
    pass_count: int
    phase: GamePhase
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'board': self.board,
            'current_player': self.current_player,
            'move_number': self.move_number,
            'captured_black': self.captured_black,
            'captured_white': self.captured_white,
            'ko_point': self.ko_point,
            'last_move': self.last_move,
            'pass_count': self.pass_count,
            'phase': self.phase.value,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameState':
        """从字典创建"""
        data['phase'] = GamePhase(data['phase'])
        return cls(**data)


@dataclass
class GameInfo:
    """游戏信息"""
    black_player: str = "Black"
    white_player: str = "White"
    black_rank: str = ""
    white_rank: str = ""
    event: str = ""
    round: str = ""
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    place: str = ""
    result: str = ""  # W+2.5, B+Resign, etc.
    time_settings: Dict[str, Any] = field(default_factory=dict)
    rules: str = "chinese"
    komi: float = 7.5
    handicap: int = 0
    
    def to_sgf_properties(self) -> str:
        """转换为SGF属性字符串"""
        props = []
        if self.black_player:
            props.append(f"PB[{self.black_player}]")
        if self.white_player:
            props.append(f"PW[{self.white_player}]")
        if self.black_rank:
            props.append(f"BR[{self.black_rank}]")
        if self.white_rank:
            props.append(f"WR[{self.white_rank}]")
        if self.event:
            props.append(f"EV[{self.event}]")
        if self.round:
            props.append(f"RO[{self.round}]")
        if self.date:
            props.append(f"DT[{self.date}]")
        if self.place:
            props.append(f"PC[{self.place}]")
        if self.result:
            props.append(f"RE[{self.result}]")
        props.append(f"RU[{self.rules}]")
        props.append(f"KM[{self.komi}]")
        if self.handicap > 0:
            props.append(f"HA[{self.handicap}]")
        
        return ''.join(props)


class Game:
    """游戏控制类"""
    
    def __init__(self, board_size: int = 19, rule_set: str = 'chinese',
                 komi: float = 7.5, handicap: int = 0, rules: Optional[str] = None):
        """
        初始化游戏
        
        Args:
            board_size: 棋盘大小
            rule_set: 规则集
            rules: 规则集（兼容旧参数名）
            komi: 贴目
            handicap: 让子数
        """
        effective_rule_set = rules if rules is not None else rule_set
        # 核心组件
        self.board = Board(board_size)
        self.rules = Rules(effective_rule_set, komi)
        
        # 游戏信息
        self.game_info = GameInfo(rules=effective_rule_set, komi=komi, handicap=handicap)
        
        # 游戏状态
        self.current_player = StoneColor.BLACK.value
        self.phase = GamePhase.NOT_STARTED
        
        # 历史记录
        self.move_history: List[Move] = []
        # 状态历史：保存“每一手之后”的完整状态，供悔棋/重做使用
        self.state_history: List[GameState] = []
        # 重做栈：保存 (棋步, 该棋步执行后的状态)
        self._redo_stack: List[Tuple[Move, GameState]] = []
        self.current_branch: MoveSequence = MoveSequence(name="Main")  # 主分支
        self.branches: List[MoveSequence] = []  # 所有分支
        
        # 计数器
        self.captured_black = 0
        self.captured_white = 0
        self.pass_count = 0
        self.move_number = 0
        
        # 特殊位置
        self.ko_point: Optional[Tuple[int, int]] = None
        self.last_move: Optional[Tuple[int, int]] = None
        
        # 死活标记
        self.dead_stones: Set[Tuple[int, int]] = set()

        # 兼容层：保存最近一次提子列表，供UI查询
        self._last_captures: List[Tuple[int, int]] = []

        # 游戏开始时间（用于统计）
        self._start_time = time.time()
        
        # 设置让子
        if handicap > 0:
            self._place_handicap_stones()

        # 开始游戏
        self.phase = GamePhase.PLAYING

        # 保存初始状态（处于 PLAYING 阶段，供悔棋/重做使用）
        self._save_state()

    # --- 兼容 main.py 的 API（旧版 UI 依赖这些方法名） ---

    @property
    def board_size(self) -> int:
        return self.board.size

    def cleanup(self):
        """清理资源（计时器等）。当前核心层无外部资源，保留接口供UI调用。"""
        return

    def is_ended(self) -> bool:
        """兼容旧接口：非对局阶段视为结束/不可落子。"""
        return self.phase != GamePhase.PLAYING

    def get_current_player(self) -> str:
        return self.current_player

    def set_player_info(self, black_name: str = "Black", white_name: str = "White", **kwargs):
        self.game_info.black_player = black_name
        self.game_info.white_player = white_name

    def set_time_control(self, time_settings: Any):
        """
        保存时间控制设置（核心不直接驱动计时器，先记录到 game_info 里）。
        """
        try:
            self.game_info.time_settings = asdict(time_settings)
        except Exception:
            try:
                self.game_info.time_settings = dict(time_settings)
            except Exception:
                self.game_info.time_settings = {'raw': repr(time_settings)}

    def place_stone(self, x: int, y: int) -> MoveResult:
        """
        兼容旧接口：执行落子并返回 MoveResult。
        最近一次提子可通过 get_last_captures() 获取。
        """
        result, captured = self.make_move(x, y)
        self._last_captures = captured
        return result

    def get_last_captures(self) -> List[Tuple[int, int]]:
        return list(self._last_captures)

    def can_undo(self) -> bool:
        return len(self.state_history) > 1 and self.phase in (GamePhase.PLAYING, GamePhase.SCORING)

    def can_redo(self) -> bool:
        return bool(self._redo_stack) and self.phase in (GamePhase.PLAYING, GamePhase.SCORING)

    def redo_move(self) -> bool:
        """重做 - 前进到下一个状态"""
        if not self.can_redo():
            return False

        move, state = self._redo_stack.pop()

        # 恢复棋步与状态
        self.move_history.append(move)
        if self.current_branch.moves is not None:
            self.current_branch.moves.append(move)

        self.state_history.append(state)
        self._load_state(state)

        # 供 UI 查询最近一次提子
        try:
            self._last_captures = list(getattr(move, 'captured', []) or [])
        except Exception:
            self._last_captures = []
        return True

    def pause_timers(self):
        return

    def resume_timers(self):
        return

    def enter_scoring_phase(self):
        """进入点目/数子阶段（兼容旧接口）。"""
        if self.phase == GamePhase.PLAYING:
            self.phase = GamePhase.SCORING

    def toggle_dead_stone(self, x: int, y: int):
        if (x, y) in self.dead_stones:
            self.dead_stones.remove((x, y))
        else:
            self.dead_stones.add((x, y))

    def get_dead_stones(self) -> List[Tuple[int, int]]:
        return sorted(self.dead_stones)

    def calculate_final_score(self) -> Dict[str, Any]:
        score = self.calculate_score()
        winner = score.get('winner')
        margin = score.get('margin', 0)
        if winner == 'draw':
            winner = None
        return {
            **score,
            'winner': winner,
            'score_difference': margin,
            'reason': ''
        }

    def get_result(self) -> Dict[str, Any]:
        if self.game_info.result:
            # 解析类似 "B+Resign" / "W+2.5"
            result = self.game_info.result
            winner = None
            score_diff = 0.0
            reason = ''
            try:
                if result.startswith('B+'):
                    winner = 'black'
                elif result.startswith('W+'):
                    winner = 'white'
                payload = result.split('+', 1)[1]
                if payload.lower().startswith('resign'):
                    reason = 'resign'
                else:
                    score_diff = float(payload)
            except Exception:
                pass
            return {'winner': winner, 'score_difference': score_diff, 'reason': reason}

        return self.calculate_final_score()

    def get_game_statistics(self):
        """
        兼容旧接口：返回 utils.GameStats 对象（若utils不可用则返回摘要字典）。
        """
        try:
            from utils import GameStats as _GameStats  # 避免核心层顶部引入utils

            duration = int(max(0, time.time() - getattr(self, '_start_time', time.time())))
            result_text = self.game_info.result or ""
            resignation = "Resign" in result_text
            timeout = "Time" in result_text

            # prisoners: 黑方提白子数=white被提=captured_white；白方提黑子数=black被提=captured_black
            captures_black = self.captured_white
            captures_white = self.captured_black

            return _GameStats(
                game_id=f"game_{int(time.time())}",
                date=datetime.now().strftime("%Y-%m-%d"),
                duration=duration,
                board_size=self.board.size,
                player_black=self.game_info.black_player,
                player_white=self.game_info.white_player,
                black_rating=None,
                white_rating=None,
                result=result_text,
                move_count=self.move_number,
                resignation=resignation,
                timeout=timeout,
                captures_black=captures_black,
                captures_white=captures_white,
                passes=sum(1 for m in self.move_history if m.x < 0 or m.y < 0)
            )
        except Exception:
            return self.get_game_summary()

    def get_game_info(self) -> Dict[str, Any]:
        """
        返回提供给 UI/AI 的游戏信息字典。
        """
        # prisoners: 玩家视角
        black_prisoners = self.captured_white
        white_prisoners = self.captured_black

        return {
            'board_size': self.board.size,
            'rules': self.game_info.rules,
            'komi': self.game_info.komi,
            'handicap': self.game_info.handicap,
            'player_black': self.game_info.black_player,
            'player_white': self.game_info.white_player,
            'move_number': self.move_number,
            'current_player': self.current_player,
            'captured_black': black_prisoners,
            'captured_white': white_prisoners,
            'ko_point': self.ko_point,
            'last_move': self.last_move,
            'phase': self.phase.value,
            'result': self.game_info.result,
        }

    def to_dict(self) -> Dict[str, Any]:
        """序列化为可存档的字典（供 StorageManager 使用）。"""
        moves = []
        for move in self.move_history:
            # 跳过让子（move_number==0）以免重放时重复
            if move.move_number == 0 and self.game_info.handicap > 0:
                continue
            moves.append({
                'x': move.x,
                'y': move.y,
                'color': move.color,
                'move_number': move.move_number,
                'captured': list(move.captured),
                'comment': move.comment,
                'timestamp': move.timestamp,
                'time_spent': move.time_spent,
            })

        return {
            'board_size': self.board.size,
            'rules': self.game_info.rules,
            'komi': self.game_info.komi,
            'handicap': self.game_info.handicap,
            'player_black': self.game_info.black_player,
            'player_white': self.game_info.white_player,
            'result': self.game_info.result,
            'phase': self.phase.value,
            'moves': moves,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Game':
        game = cls(
            board_size=data.get('board_size', 19),
            rule_set=data.get('rules', 'chinese'),
            komi=data.get('komi', 7.5),
            handicap=data.get('handicap', 0),
        )
        game.set_player_info(
            black_name=data.get('player_black', 'Black'),
            white_name=data.get('player_white', 'White'),
        )

        for move in data.get('moves', []):
            x = move.get('x', -1)
            y = move.get('y', -1)
            if x < 0 or y < 0:
                game.pass_turn()
            else:
                game.make_move(x, y)

        try:
            game.phase = GamePhase(data.get('phase', game.phase.value))
        except Exception:
            pass

        game.game_info.result = data.get('result', game.game_info.result)
        return game
    
    def _place_handicap_stones(self):
        """放置让子"""
        positions = self.board.get_handicap_positions(self.game_info.handicap)
        
        for x, y in positions:
            self.board.place_stone(x, y, StoneColor.BLACK.value, 0)
            # 记录为第0手
            move = Move(x, y, StoneColor.BLACK.value, 0)
            self.move_history.append(move)
            self.current_branch.add_move(move)
        
        if positions:
            self.current_player = StoneColor.WHITE.value
            self.last_move = positions[-1] if positions else None
    
    def make_move(self, x: int, y: int) -> Tuple[MoveResult, List[Tuple[int, int]]]:
        """
        执行落子
        
        Args:
            x, y: 落子位置
            
        Returns:
            (落子结果, 被吃掉的棋子列表)
        """
        if self.phase != GamePhase.PLAYING:
            return MoveResult.ILLEGAL, []
        
        # 检查落子合法性
        result = self.rules.is_legal_move(
            self.board, x, y, self.current_player, self.ko_point
        )
        
        if result != MoveResult.SUCCESS:
            return result, []
        
        # 执行落子和吃子
        success, captured_stones, new_ko_point = self.rules.execute_move(
            self.board, x, y, self.current_player, self.move_number + 1
        )
        
        if not success:
            return MoveResult.ILLEGAL, []
        
        # 更新游戏状态
        self.move_number += 1
        self.ko_point = new_ko_point
        self.last_move = (x, y)
        self.pass_count = 0  # 重置虚手计数
        
        # 更新吃子计数
        if self.current_player == StoneColor.BLACK.value:
            self.captured_white += len(captured_stones)
        else:
            self.captured_black += len(captured_stones)
        
        # 记录棋步
        move = Move(
            x=x,
            y=y,
            color=self.current_player,
            move_number=self.move_number,
            captured=captured_stones.copy()
        )
        self.move_history.append(move)
        self.current_branch.add_move(move)

        # 对局有新进展：清空 redo 栈
        self._redo_stack.clear()
        
        # 切换玩家
        self._switch_player()

        # 保存“此手之后”的状态（供悔棋/重做使用）
        self._save_state()
        
        return MoveResult.SUCCESS, captured_stones
    
    def pass_turn(self) -> bool:
        """
        虚手
        
        Returns:
            是否进入点目阶段
        """
        if self.phase != GamePhase.PLAYING:
            return False
        
        # 记录虚手
        self.move_number += 1
        move = Move(-1, -1, self.current_player, self.move_number)
        move.comment = "Pass"
        self.move_history.append(move)
        self.current_branch.add_move(move)

        # 对局有新进展：清空 redo 栈
        self._redo_stack.clear()
        
        # 更新状态
        self.pass_count += 1
        self.ko_point = None  # 虚手后清除劫点
        
        # 检查是否结束
        if self.pass_count >= 2:
            self.phase = GamePhase.SCORING
            # 保存“此手之后”的状态
            self._save_state()
            return True
        
        # 切换玩家
        self._switch_player()

        # 保存“此手之后”的状态
        self._save_state()
        
        return False
    
    def resign(self):
        """认输"""
        if self.phase != GamePhase.PLAYING:
            return
        
        winner = StoneColor.opposite(self.current_player)
        winner_initial = winner[0].upper()
        self.game_info.result = f"{winner_initial}+Resign"
        self.phase = GamePhase.ENDED
    
    def undo_move(self) -> bool:
        """
        悔棋 - 回退到上一个状态
        
        Returns:
            是否成功悔棋
        """
        if len(self.state_history) <= 1:  # 保留初始状态
            return False
        
        if self.phase not in [GamePhase.PLAYING, GamePhase.SCORING]:
            return False

        # 当前（最后一手之后）的状态，用于 redo
        state_after_move = self.state_history.pop()

        # 移除最后一手
        if not self.move_history:
            # 理论上不应发生：len(state_history)>1 意味着至少有一手
            self.state_history.append(state_after_move)
            return False

        last_move = self.move_history.pop()
        if self.current_branch.moves:
            self.current_branch.moves.pop()

        self._redo_stack.append((last_move, state_after_move))

        # 恢复到上一个状态（也就是 state_history 现在的最后一个）
        self._load_state(self.state_history[-1])

        # 更新最近一次提子列表（供 UI 查询）
        try:
            prev = self.move_history[-1] if self.move_history else None
            if prev and getattr(prev, 'move_number', 0) > 0:
                self._last_captures = list(getattr(prev, 'captured', []) or [])
            else:
                self._last_captures = []
        except Exception:
            self._last_captures = []

        return True
    
    def undo_to_move(self, move_number: int) -> bool:
        """
        悔棋到指定手数
        
        Args:
            move_number: 目标手数
            
        Returns:
            是否成功
        """
        if move_number < 0:
            return False

        changed = False

        # 向后（悔棋）
        while self.move_number > move_number:
            if not self.undo_move():
                break
            changed = True

        # 向前（重做）
        while self.move_number < move_number:
            if not self.redo_move():
                break
            changed = True

        return changed
    
    def create_branch(self, name: str = "") -> MoveSequence:
        """
        创建分支（用于变化图）
        
        Args:
            name: 分支名称
            
        Returns:
            新创建的分支
        """
        # 复制当前的棋步序列
        branch = MoveSequence(
            moves=self.current_branch.moves.copy(),
            name=name or f"Branch {len(self.branches) + 1}"
        )
        self.branches.append(branch)
        return branch
    
    def switch_branch(self, branch: MoveSequence):
        """切换到指定分支"""
        self.current_branch = branch
        # 重新应用分支的所有棋步
        self._replay_moves(branch.moves)
    
    def _replay_moves(self, moves: List[Move]):
        """重放棋步序列"""
        # 重置到初始状态
        self.reset()
        
        # 重新执行所有棋步
        for move in moves:
            if move.x >= 0 and move.y >= 0:
                self.make_move(move.x, move.y)
            else:
                self.pass_turn()
    
    def mark_dead_stones(self, stones: List[Tuple[int, int]]):
        """
        标记死子（点目阶段）
        
        Args:
            stones: 死子位置列表
        """
        if self.phase != GamePhase.SCORING:
            return
        
        for x, y in stones:
            if (x, y) in self.dead_stones:
                self.dead_stones.remove((x, y))  # 取消标记
            else:
                self.dead_stones.add((x, y))  # 标记为死子
    
    def calculate_score(self) -> Dict[str, Any]:
        """
        计算最终得分
        
        Returns:
            得分信息字典
        """
        # 选择计分系统
        if self.game_info.rules == 'japanese':
            scoring_system = JapaneseScoring(self.game_info.komi)
        else:
            scoring_system = ChineseScoring(self.game_info.komi)
        
        # 计算得分
        result = scoring_system.calculate_score(
            self.board,
            self.captured_black,
            self.captured_white,
            self.dead_stones
        )
        
        return result
    
    def end_game(self, accept_score: bool = True):
        """
        结束游戏
        
        Args:
            accept_score: 是否接受当前点目结果
        """
        if accept_score and self.phase == GamePhase.SCORING:
            score = self.calculate_score()
            margin = float(score.get('margin', score.get('difference', 0) or 0) or 0)
            
            # 设置游戏结果
            if score['winner'] == 'black':
                self.game_info.result = f"B+{margin:.1f}"
            elif score['winner'] == 'white':
                self.game_info.result = f"W+{margin:.1f}"
            else:
                self.game_info.result = "Draw"
        
        self.phase = GamePhase.ENDED
    
    def get_legal_moves(self) -> List[Tuple[int, int]]:
        """
        获取所有合法落子位置
        
        Returns:
            合法位置列表
        """
        legal_moves = []
        
        for y in range(self.board.size):
            for x in range(self.board.size):
                if self.board.is_empty(x, y):
                    result = self.rules.is_legal_move(
                        self.board, x, y, self.current_player, self.ko_point
                    )
                    if result == MoveResult.SUCCESS:
                        legal_moves.append((x, y))
        
        return legal_moves
    
    def get_board_as_array(self) -> List[List[str]]:
        """获取棋盘数组表示"""
        return [row[:] for row in self.board.grid]
    
    def _save_state(self):
        """保存当前游戏状态"""
        state = GameState(
            board=self.get_board_as_array(),
            current_player=self.current_player,
            move_number=self.move_number,
            captured_black=self.captured_black,
            captured_white=self.captured_white,
            ko_point=self.ko_point,
            last_move=self.last_move,
            pass_count=self.pass_count,
            phase=self.phase
        )
        self.state_history.append(state)
    
    def _load_state(self, state: GameState):
        """加载游戏状态"""
        # 重建棋盘
        self.board = Board(len(state.board))
        for y, row in enumerate(state.board):
            for x, color in enumerate(row):
                if color and color != StoneColor.EMPTY.value:
                    self.board.place_stone(x, y, color)
        
        # 恢复其他状态
        self.current_player = state.current_player
        self.move_number = state.move_number
        self.captured_black = state.captured_black
        self.captured_white = state.captured_white
        self.ko_point = state.ko_point
        self.last_move = state.last_move
        self.pass_count = state.pass_count
        self.phase = state.phase
        
        # 清除规则历史（避免超级劫误判）
        self.rules.clear_history()
    
    def _switch_player(self):
        """切换当前玩家"""
        self.current_player = StoneColor.opposite(self.current_player)
    
    def reset(self):
        """重置游戏到初始状态"""
        self.__init__(
            board_size=self.board.size,
            rule_set=self.game_info.rules,
            komi=self.game_info.komi,
            handicap=self.game_info.handicap
        )
    
    def get_game_summary(self) -> Dict[str, Any]:
        """
        获取游戏摘要信息
        
        Returns:
            包含游戏关键信息的字典
        """
        return {
            'board_size': self.board.size,
            'rules': self.game_info.rules,
            'komi': self.game_info.komi,
            'handicap': self.game_info.handicap,
            'moves_played': self.move_number,
            'captured_black': self.captured_black,
            'captured_white': self.captured_white,
            'current_player': self.current_player,
            'phase': self.phase.value,
            'result': self.game_info.result,
            'black_player': self.game_info.black_player,
            'white_player': self.game_info.white_player,
            'date': self.game_info.date
        }
    
    def export_to_sgf(self) -> str:
        """
        导出为SGF格式
        
        Returns:
            SGF格式字符串
        """
        sgf = f"(;FF[4]GM[1]SZ[{self.board.size}]"
        sgf += self.game_info.to_sgf_properties()
        
        # 添加棋步
        for move in self.move_history:
            if move.x >= 0 and move.y >= 0:
                color_marker = 'B' if move.color == StoneColor.BLACK.value else 'W'
                coords = move.to_sgf_coords(self.board.size)
                sgf += f";{color_marker}[{coords}]"
                
                if move.comment:
                    sgf += f"C[{move.comment}]"
            else:
                # 虚手
                color_marker = 'B' if move.color == StoneColor.BLACK.value else 'W'
                sgf += f";{color_marker}[]"
        
        sgf += ")"
        return sgf
    
    def import_from_sgf(self, sgf_content: str):
        """
        从SGF格式导入
        
        Args:
            sgf_content: SGF格式字符串
        """
        # 这里需要完整的SGF解析器
        # 暂时留作接口，具体实现在sgf.py模块中
        pass
