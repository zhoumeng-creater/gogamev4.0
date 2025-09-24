"""
AI基类模块
定义所有AI玩家的基础接口和共用功能
"""

import time
import random
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Set, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

# 导入核心模块
from core import Board, Rules, MoveResult, Territory


class AILevel(Enum):
    """AI难度级别枚举"""
    BEGINNER = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    EXPERT = 5
    MASTER = 6


@dataclass
class Move:
    """AI棋步数据类"""
    x: int
    y: int
    color: str
    score: float = 0.0
    visits: int = 0
    win_rate: float = 0.0
    confidence: float = 0.0
    analysis: str = ""
    variations: List['Move'] = field(default_factory=list)
    
    def to_tuple(self) -> Tuple[int, int]:
        """转换为坐标元组"""
        return (self.x, self.y)
    
    def is_pass(self) -> bool:
        """判断是否为虚手"""
        return self.x < 0 or self.y < 0


@dataclass
class EvaluationResult:
    """局面评估结果"""
    score: float  # 总体评分
    territory_score: float  # 领地评分
    influence_score: float  # 势力评分
    capture_score: float  # 吃子评分
    pattern_score: float  # 模式评分
    safety_score: float  # 安全评分
    best_moves: List[Move]  # 推荐着法
    winning_probability: float  # 胜率
    analysis_text: str = ""  # 分析文本


class AIPlayer(ABC):
    """AI玩家基类"""
    
    def __init__(self, color: str, board_size: int = 19, 
                 thinking_time: float = 1.0, level: AILevel = AILevel.MEDIUM):
        """
        初始化AI玩家
        
        Args:
            color: 棋子颜色 (black/white)
            board_size: 棋盘大小
            thinking_time: 思考时间限制（秒）
            level: AI难度级别
        """
        self.color = color
        self.opponent_color = 'white' if color == 'black' else 'black'
        self.board_size = board_size
        self.thinking_time = thinking_time
        self.level = level
        
        # 统计信息
        self.nodes_evaluated = 0
        self.time_spent = 0.0
        self.move_count = 0
        
        # 缓存
        self._evaluation_cache = {}
        self._pattern_cache = {}
        
        # 初始化规则引擎
        self.rules = Rules()
    
    @abstractmethod
    def get_move(self, board: Board, game_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """
        获取AI的下一步棋（必须实现）
        
        Args:
            board: 当前棋盘
            game_info: 游戏信息（包含历史、俘虏数等）
        
        Returns:
            (x, y) 落子位置，或None表示虚手
        """
        pass
    
    def evaluate_position(self, board: Board) -> EvaluationResult:
        """
        评估当前局面
        
        Args:
            board: 棋盘状态
        
        Returns:
            评估结果
        """
        # 检查缓存
        board_hash = self._get_board_hash(board)
        if board_hash in self._evaluation_cache:
            return self._evaluation_cache[board_hash]
        
        # 计算各项评分
        territory_score = self._evaluate_territory(board)
        influence_score = self._evaluate_influence(board)
        capture_score = self._evaluate_captures(board)
        pattern_score = self._evaluate_patterns(board)
        safety_score = self._evaluate_safety(board)
        
        # 综合评分
        total_score = (
            territory_score * 1.0 +
            influence_score * 0.8 +
            capture_score * 1.5 +
            pattern_score * 0.6 +
            safety_score * 0.9
        )
        
        # 计算胜率
        winning_prob = self._score_to_winning_probability(total_score)
        
        result = EvaluationResult(
            score=total_score,
            territory_score=territory_score,
            influence_score=influence_score,
            capture_score=capture_score,
            pattern_score=pattern_score,
            safety_score=safety_score,
            best_moves=[],
            winning_probability=winning_prob
        )
        
        # 缓存结果
        self._evaluation_cache[board_hash] = result
        
        return result
    
    def get_legal_moves(self, board: Board, ko_point: Optional[Tuple[int, int]] = None) -> List[Tuple[int, int]]:
        """
        获取所有合法落子位置
        
        Args:
            board: 当前棋盘
            ko_point: 劫点位置
        
        Returns:
            合法位置列表
        """
        legal_moves = []
        
        for y in range(self.board_size):
            for x in range(self.board_size):
                if board.is_empty(x, y):
                    result = self.rules.is_legal_move(
                        board, x, y, self.color, ko_point
                    )
                    if result == MoveResult.SUCCESS:
                        legal_moves.append((x, y))
        
        return legal_moves
    
    def filter_obviously_bad_moves(self, board: Board, moves: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        过滤明显的坏着（如填眼）
        
        Args:
            board: 当前棋盘
            moves: 候选着法列表
        
        Returns:
            过滤后的着法列表
        """
        filtered = []
        
        for x, y in moves:
            # 检查是否为己方的眼
            if not self._is_eye(board, x, y, self.color):
                filtered.append((x, y))
        
        # 如果过滤后没有着法，返回原列表（避免必须填眼的情况）
        return filtered if filtered else moves
    
    def _is_eye(self, board: Board, x: int, y: int, color: str) -> bool:
        """
        判断是否为眼位
        
        Args:
            board: 棋盘
            x, y: 位置坐标
            color: 己方颜色
        
        Returns:
            是否为眼
        """
        # 检查四个正交方向
        orthogonal_count = 0
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                if board.get_stone(nx, ny) == color:
                    orthogonal_count += 1
            else:
                # 边界算作己方
                orthogonal_count += 1
        
        # 如果正交方向不全是己方棋子，不是眼
        if orthogonal_count < 4:
            return False
        
        # 检查对角线方向（至少3个己方或边界）
        diagonal_count = 0
        for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                stone = board.get_stone(nx, ny)
                if stone == color or stone == '':
                    diagonal_count += 1
            else:
                diagonal_count += 1
        
        return diagonal_count >= 3
    
    def _evaluate_territory(self, board: Board) -> float:
        """评估领地得分"""
        territory = Territory(board)
        territory_map = territory.calculate_territory()
        
        my_territory = territory_map[self.color]
        opp_territory = territory_map[self.opponent_color]
        
        return float(my_territory - opp_territory)
    
    def _evaluate_influence(self, board: Board) -> float:
        """评估势力得分"""
        influence_map = self._calculate_influence_map(board)
        return float(np.sum(influence_map))
    
    def _evaluate_captures(self, board: Board) -> float:
        """评估吃子潜力"""
        score = 0.0
        
        # 检查可以吃掉的对方棋子
        for group in board.get_all_groups():
            if group.color == self.opponent_color:
                liberties = len(group.liberties)
                if liberties == 1:  # 叫吃
                    score += 50
                elif liberties == 2:  # 可能的攻击目标
                    score += 10
        
        return score
    
    def _evaluate_patterns(self, board: Board) -> float:
        """评估棋形模式得分"""
        # 子类可以覆盖实现具体的模式识别
        return 0.0
    
    def _evaluate_safety(self, board: Board) -> float:
        """评估己方棋子安全性"""
        score = 0.0
        
        # 检查己方棋子的安全性
        for group in board.get_all_groups():
            if group.color == self.color:
                liberties = len(group.liberties)
                stones = len(group.stones)
                
                if liberties == 1:  # 危险
                    score -= 30 * stones
                elif liberties == 2:  # 需要注意
                    score -= 5 * stones
                elif liberties >= 4:  # 安全
                    score += 5 * stones
        
        return score
    
    def _calculate_influence_map(self, board: Board) -> np.ndarray:
        """
        计算势力图
        
        Returns:
            势力图数组（正值为己方势力，负值为对方势力）
        """
        influence = np.zeros((self.board_size, self.board_size), dtype=np.float32)
        
        for y in range(self.board_size):
            for x in range(self.board_size):
                stone = board.get_stone(x, y)
                if stone:
                    # 确定势力值
                    strength = 10.0 if stone == self.color else -10.0
                    
                    # 向周围传播势力（使用高斯衰减）
                    for dy in range(max(0, y-5), min(self.board_size, y+6)):
                        for dx in range(max(0, x-5), min(self.board_size, x+6)):
                            distance = max(abs(x - dx), abs(y - dy))
                            if distance > 0:
                                decay = np.exp(-distance * 0.5)
                                influence[dy, dx] += strength * decay
        
        return influence
    
    def _score_to_winning_probability(self, score: float) -> float:
        """
        将评分转换为胜率
        
        Args:
            score: 局面评分
        
        Returns:
            胜率 (0-1)
        """
        # 使用sigmoid函数
        return 1.0 / (1.0 + np.exp(-score / 50.0))
    
    def _get_board_hash(self, board: Board) -> str:
        """获取棋盘哈希值（用于缓存）"""
        return board.get_hash()
    
    def clear_cache(self):
        """清除缓存"""
        self._evaluation_cache.clear()
        self._pattern_cache.clear()
    
    def get_analysis(self, board: Board, last_move: Optional[Tuple[int, int]] = None) -> str:
        """
        获取局面分析文本
        
        Args:
            board: 当前棋盘
            last_move: 上一手棋
        
        Returns:
            分析文本
        """
        eval_result = self.evaluate_position(board)
        
        analysis = []
        
        # 形势判断
        if eval_result.winning_probability > 0.7:
            analysis.append(f"{self.color}方形势大优")
        elif eval_result.winning_probability > 0.55:
            analysis.append(f"{self.color}方略优")
        elif eval_result.winning_probability < 0.3:
            analysis.append(f"{self.opponent_color}方形势大优")
        elif eval_result.winning_probability < 0.45:
            analysis.append(f"{self.opponent_color}方略优")
        else:
            analysis.append("形势均衡")
        
        # 详细评分
        analysis.append(f"胜率: {eval_result.winning_probability:.1%}")
        analysis.append(f"领地: {eval_result.territory_score:+.1f}")
        analysis.append(f"势力: {eval_result.influence_score:+.1f}")
        
        return "\n".join(analysis)