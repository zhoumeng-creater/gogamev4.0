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
                 komi: float = 7.5, handicap: int = 0):
        """
        初始化游戏
        
        Args:
            board_size: 棋盘大小
            rule_set: 规则集
            komi: 贴目
            handicap: 让子数
        """
        # 核心组件
        self.board = Board(board_size)
        self.rules = Rules(rule_set, komi)
        
        # 游戏信息
        self.game_info = GameInfo(rules=rule_set, komi=komi, handicap=handicap)
        
        # 游戏状态
        self.current_player = StoneColor.BLACK.value
        self.phase = GamePhase.NOT_STARTED
        
        # 历史记录
        self.move_history: List[Move] = []
        self.state_history: List[GameState] = []  # 完整状态历史，用于悔棋
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
        
        # 设置让子
        if handicap > 0:
            self._place_handicap_stones()
        
        # 保存初始状态
        self._save_state()
        
        # 开始游戏
        self.phase = GamePhase.PLAYING
    
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
        
        # 保存当前状态（用于悔棋）
        self._save_state()
        
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
        
        # 切换玩家
        self._switch_player()
        
        return MoveResult.SUCCESS, captured_stones
    
    def pass_turn(self) -> bool:
        """
        虚手
        
        Returns:
            是否进入点目阶段
        """
        if self.phase != GamePhase.PLAYING:
            return False
        
        # 保存状态
        self._save_state()
        
        # 记录虚手
        self.move_number += 1
        move = Move(-1, -1, self.current_player, self.move_number)
        move.comment = "Pass"
        self.move_history.append(move)
        self.current_branch.add_move(move)
        
        # 更新状态
        self.pass_count += 1
        self.ko_point = None  # 虚手后清除劫点
        
        # 检查是否结束
        if self.pass_count >= 2:
            self.phase = GamePhase.SCORING
            return True
        
        # 切换玩家
        self._switch_player()
        
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
        
        # 移除最后的状态和棋步
        self.state_history.pop()
        if self.move_history:
            last_move = self.move_history.pop()
            if self.current_branch.moves:
                self.current_branch.moves.pop()
        
        # 恢复到上一个状态
        previous_state = self.state_history[-1]
        self._load_state(previous_state)
        
        # 如果之前在点目阶段，回到对局阶段
        if self.phase == GamePhase.SCORING:
            self.phase = GamePhase.PLAYING
        
        return True
    
    def undo_to_move(self, move_number: int) -> bool:
        """
        悔棋到指定手数
        
        Args:
            move_number: 目标手数
            
        Returns:
            是否成功
        """
        if move_number < 0 or move_number >= len(self.state_history):
            return False
        
        # 回退到指定状态
        self.state_history = self.state_history[:move_number + 1]
        self.move_history = self.move_history[:move_number]
        self.current_branch.moves = self.current_branch.moves[:move_number]
        
        # 加载状态
        self._load_state(self.state_history[-1])
        
        return True
    
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
            
            # 设置游戏结果
            if score['winner'] == 'black':
                self.game_info.result = f"B+{score['difference']:.1f}"
            elif score['winner'] == 'white':
                self.game_info.result = f"W+{score['difference']:.1f}"
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