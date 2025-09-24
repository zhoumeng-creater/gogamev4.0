"""
模式AI模块
包含定式AI、战术AI等基于模式识别的AI实现
"""

import json
import random
import time
from typing import List, Tuple, Optional, Dict, Any, Set
from dataclasses import dataclass
import numpy as np

from .base import AIPlayer, Move, AILevel
from .search_ai import MonteCarloAI
from core import Board, Rules, MoveResult


@dataclass
class Pattern:
    """棋形模式"""
    name: str
    stones: List[Tuple[int, int, str]]  # (x, y, color)
    empty_points: List[Tuple[int, int]]  # 必须为空的点
    next_moves: List[Tuple[int, int, float]]  # (x, y, priority)
    context: str = ""  # 使用场景描述
    
    def matches(self, board: Board, x: int, y: int, color: str) -> bool:
        """检查模式是否匹配"""
        for dx, dy, expected_color in self.stones:
            bx, by = x + dx, y + dy
            if not (0 <= bx < board.size and 0 <= by < board.size):
                return False
            
            actual = board.get_stone(bx, by)
            if expected_color == 'X':  # 己方
                if actual != color:
                    return False
            elif expected_color == 'O':  # 对方
                opponent = 'white' if color == 'black' else 'black'
                if actual != opponent:
                    return False
            elif expected_color == '.':  # 空
                if actual != '':
                    return False
        
        # 检查必须为空的点
        for dx, dy in self.empty_points:
            bx, by = x + dx, y + dy
            if not (0 <= bx < board.size and 0 <= by < board.size):
                return False
            if board.get_stone(bx, by) != '':
                return False
        
        return True
    
    def rotate_90(self) -> 'Pattern':
        """旋转90度"""
        rotated_stones = [(-y, x, color) for x, y, color in self.stones]
        rotated_empty = [(-y, x) for x, y in self.empty_points]
        rotated_moves = [(-y, x, priority) for x, y, priority in self.next_moves]
        
        return Pattern(
            name=f"{self.name}_r90",
            stones=rotated_stones,
            empty_points=rotated_empty,
            next_moves=rotated_moves,
            context=self.context
        )
    
    def mirror_horizontal(self) -> 'Pattern':
        """水平镜像"""
        mirrored_stones = [(-x, y, color) for x, y, color in self.stones]
        mirrored_empty = [(-x, y) for x, y in self.empty_points]
        mirrored_moves = [(-x, y, priority) for x, y, priority in self.next_moves]
        
        return Pattern(
            name=f"{self.name}_mh",
            stones=mirrored_stones,
            empty_points=mirrored_empty,
            next_moves=mirrored_moves,
            context=self.context
        )


class PatternLibrary:
    """模式库"""
    
    def __init__(self):
        self.patterns = {
            'joseki': [],      # 定式
            'tactical': [],    # 战术
            'life_death': [],  # 死活
            'tesuji': []       # 手筋
        }
        self._load_patterns()
    
    def _load_patterns(self):
        """加载内置模式"""
        # 角部定式
        self.patterns['joseki'].extend([
            # 三三定式
            Pattern(
                name="san_san_invasion",
                stones=[(3, 3, 'O')],  # 对方占三三
                empty_points=[(3, 4), (4, 3)],
                next_moves=[(3, 4, 0.6), (4, 3, 0.4)],
                context="三三入侵应对"
            ),
            # 星位定式
            Pattern(
                name="star_point_approach",
                stones=[(3, 3, 'X')],  # 己方占星位
                empty_points=[(5, 3), (3, 5)],
                next_moves=[(5, 3, 0.5), (3, 5, 0.5)],
                context="星位小飞挂"
            ),
            # 小目定式
            Pattern(
                name="komoku_approach",
                stones=[(3, 4, 'X')],  # 己方占小目
                empty_points=[(5, 3), (5, 4)],
                next_moves=[(5, 3, 0.6), (5, 4, 0.4)],
                context="小目一间高挂"
            )
        ])
        
        # 战术模式
        self.patterns['tactical'].extend([
            # 断点
            Pattern(
                name="cut_point",
                stones=[(0, 1, 'O'), (1, 0, 'O')],
                empty_points=[(0, 0), (1, 1)],
                next_moves=[(1, 1, 0.8)],
                context="切断对方连接"
            ),
            # 双叫吃
            Pattern(
                name="double_atari",
                stones=[
                    (-1, 0, 'O'), (1, 0, 'O'),
                    (0, -1, 'X'), (0, 1, 'X')
                ],
                empty_points=[(0, 0)],
                next_moves=[(0, 0, 1.0)],
                context="双叫吃"
            ),
            # 扳
            Pattern(
                name="hane",
                stones=[(0, 1, 'O'), (1, 1, 'X')],
                empty_points=[(1, 0)],
                next_moves=[(1, 0, 0.7)],
                context="扳头"
            ),
            # 虎口
            Pattern(
                name="tiger_mouth",
                stones=[(0, 1, 'X'), (1, 0, 'X')],
                empty_points=[(1, 1)],
                next_moves=[(1, 1, 0.6)],
                context="虎口补强"
            )
        ])
        
        # 死活模式
        self.patterns['life_death'].extend([
            # 直三做眼
            Pattern(
                name="straight_three_eyes",
                stones=[
                    (-1, 0, 'X'), (0, 0, '.'), (1, 0, 'X'),
                    (0, 1, 'X'), (0, -1, 'X')
                ],
                empty_points=[(0, 0)],
                next_moves=[(0, 0, 1.0)],
                context="直三做眼"
            ),
            # 曲三做眼
            Pattern(
                name="bent_three_eyes",
                stones=[
                    (0, 0, '.'), (1, 0, 'X'), (2, 0, 'X'),
                    (0, 1, 'X'), (0, -1, 'X')
                ],
                empty_points=[(0, 0)],
                next_moves=[(0, 0, 1.0)],
                context="曲三做眼"
            )
        ])
        
        # 为每个模式生成旋转和镜像变体
        for category in self.patterns:
            original_patterns = self.patterns[category].copy()
            for pattern in original_patterns:
                # 生成3个旋转（90, 180, 270度）
                rotated = pattern
                for _ in range(3):
                    rotated = rotated.rotate_90()
                    self.patterns[category].append(rotated)
                
                # 生成镜像
                mirrored = pattern.mirror_horizontal()
                self.patterns[category].append(mirrored)
    
    def find_matching_patterns(self, board: Board, x: int, y: int, 
                               color: str, category: str = None) -> List[Pattern]:
        """查找匹配的模式"""
        matches = []
        
        categories = [category] if category else self.patterns.keys()
        
        for cat in categories:
            for pattern in self.patterns[cat]:
                if pattern.matches(board, x, y, color):
                    matches.append(pattern)
        
        return matches


class JosekiAI(AIPlayer):
    """
    定式AI - 专注于开局定式
    主要用于序盘阶段的标准下法
    """
    
    def __init__(self, color: str, board_size: int = 19, **kwargs):
        super().__init__(color, board_size, thinking_time=1.0, level=AILevel.EXPERT)
        
        self.pattern_library = PatternLibrary()
        self.joseki_database = self._load_joseki_database()
        self.opening_threshold = kwargs.get('opening_threshold', 30)  # 开局手数阈值
        
        # 备用AI（用于中后盘）
        self.fallback_ai = MonteCarloAI(color, board_size, simulations=500)
    
    def _load_joseki_database(self) -> Dict[str, List[Tuple[int, int]]]:
        """加载定式数据库"""
        # 这里使用简化的定式库，实际应用中应从文件加载
        return {
            # 星位定式
            'star_point': [
                (3, 3), (15, 15), (3, 15), (15, 3)  # 占角
            ],
            'star_approach': [
                (5, 3), (3, 5), (13, 3), (15, 5),  # 小飞挂
                (6, 3), (3, 6), (12, 3), (15, 6)   # 大飞挂
            ],
            # 小目定式
            'komoku': [
                (3, 4), (4, 3), (15, 14), (14, 15)  # 小目
            ],
            'komoku_approach': [
                (5, 3), (3, 5), (13, 15), (15, 13)  # 小目挂角
            ],
            # 三三定式
            'san_san': [
                (2, 2), (16, 16), (2, 16), (16, 2)  # 三三
            ]
        }
    
    def get_move(self, board: Board, game_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """
        获取下一步棋
        
        Args:
            board: 当前棋盘
            game_info: 游戏信息
        
        Returns:
            落子位置
        """
        move_count = game_info.get('move_number', 0)
        
        # 判断是否还在开局阶段
        if move_count < self.opening_threshold:
            # 尝试使用定式
            joseki_move = self._find_joseki_move(board, game_info)
            if joseki_move:
                return joseki_move
        
        # 使用备用AI
        return self.fallback_ai.get_move(board, game_info)
    
    def _find_joseki_move(self, board: Board, game_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """查找定式着法"""
        ko_point = game_info.get('ko_point')
        legal_moves = self.get_legal_moves(board, ko_point)
        
        if not legal_moves:
            return None
        
        # 检查角部情况
        corner_moves = []
        
        for corner_x, corner_y in [(3, 3), (15, 15), (3, 15), (15, 3)]:
            # 检查角部是否有棋子
            has_stone = False
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    x, y = corner_x + dx, corner_y + dy
                    if 0 <= x < board.size and 0 <= y < board.size:
                        if board.get_stone(x, y):
                            has_stone = True
                            break
                if has_stone:
                    break
            
            if not has_stone:
                # 空角，考虑占角
                for x, y in self.joseki_database['star_point']:
                    if (x, y) in legal_moves:
                        corner_moves.append((x, y))
            else:
                # 已有子，查找匹配的定式模式
                patterns = self.pattern_library.find_matching_patterns(
                    board, corner_x, corner_y, self.color, 'joseki'
                )
                
                for pattern in patterns:
                    for dx, dy, priority in pattern.next_moves:
                        x, y = corner_x + dx, corner_y + dy
                        if (x, y) in legal_moves:
                            corner_moves.append((x, y))
        
        if corner_moves:
            return random.choice(corner_moves)
        
        # 没有找到定式，考虑边和中腹的大场
        return self._find_big_point(board, legal_moves)
    
    def _find_big_point(self, board: Board, legal_moves: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """寻找大场"""
        big_points = []
        
        for x, y in legal_moves:
            # 计算周围的空间
            empty_count = 0
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < board.size and 0 <= ny < board.size:
                        if board.is_empty(nx, ny):
                            empty_count += 1
            
            if empty_count > 15:  # 周围比较空旷
                big_points.append((x, y))
        
        if big_points:
            return random.choice(big_points)
        
        return None


class TacticalAI(AIPlayer):
    """
    战术AI - 专注于局部战斗
    擅长攻击、防守、死活等战术计算
    """
    
    def __init__(self, color: str, board_size: int = 19, **kwargs):
        super().__init__(color, board_size, thinking_time=2.0, level=AILevel.EXPERT)
        
        self.pattern_library = PatternLibrary()
        self.attack_threshold = kwargs.get('attack_threshold', 0.6)  # 攻击倾向
        self.defense_threshold = kwargs.get('defense_threshold', 0.4)  # 防守倾向
    
    def get_move(self, board: Board, game_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """
        获取下一步棋
        
        Args:
            board: 当前棋盘
            game_info: 游戏信息
        
        Returns:
            落子位置
        """
        ko_point = game_info.get('ko_point')
        legal_moves = self.get_legal_moves(board, ko_point)
        
        if not legal_moves:
            return None
        
        # 优先级：
        # 1. 紧急防守（救活己方危险棋子）
        # 2. 紧急攻击（杀死对方棋子）
        # 3. 战术模式（断、连、扳等）
        # 4. 一般着法
        
        # 1. 检查紧急防守
        defense_moves = self._find_defense_moves(board, legal_moves)
        if defense_moves:
            return self._select_best_move(defense_moves)
        
        # 2. 检查紧急攻击
        attack_moves = self._find_attack_moves(board, legal_moves)
        if attack_moves:
            return self._select_best_move(attack_moves)
        
        # 3. 查找战术模式
        tactical_moves = self._find_tactical_moves(board, legal_moves)
        if tactical_moves:
            return self._select_best_move(tactical_moves)
        
        # 4. 使用一般评估
        return self._select_by_evaluation(board, legal_moves, game_info)
    
    def _find_defense_moves(self, board: Board, legal_moves: List[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], float]]:
        """查找防守着法"""
        defense_moves = []
        
        # 检查己方危险棋块
        for group in board.get_all_groups():
            if group.color == self.color:
                liberties = len(group.liberties)
                
                if liberties == 1:  # 只有一气，必须救
                    for x, y in group.liberties:
                        if (x, y) in legal_moves:
                            # 检查下了之后是否真的能救活
                            test_board = board.copy()
                            test_board.place_stone(x, y, self.color)
                            new_group = test_board.get_group_at(x, y)
                            if new_group and len(new_group.liberties) > 1:
                                priority = len(group.stones) * 10  # 根据棋块大小确定优先级
                                defense_moves.append(((x, y), priority))
                
                elif liberties == 2:  # 两气，需要注意
                    for x, y in group.liberties:
                        if (x, y) in legal_moves:
                            priority = len(group.stones) * 2
                            defense_moves.append(((x, y), priority))
        
        return defense_moves
    
    def _find_attack_moves(self, board: Board, legal_moves: List[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], float]]:
        """查找攻击着法"""
        attack_moves = []
        
        # 检查对方危险棋块
        for group in board.get_all_groups():
            if group.color == self.opponent_color:
                liberties = len(group.liberties)
                
                if liberties == 1:  # 叫吃
                    for x, y in group.liberties:
                        if (x, y) in legal_moves:
                            priority = len(group.stones) * 10
                            attack_moves.append(((x, y), priority))
                
                elif liberties == 2:  # 可以追击
                    for x, y in group.liberties:
                        if (x, y) in legal_moves:
                            # 检查是否能形成好的攻击
                            test_board = board.copy()
                            test_board.place_stone(x, y, self.color)
                            
                            # 重新获取对方棋块
                            for nx, ny in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
                                if 0 <= nx < board.size and 0 <= ny < board.size:
                                    if test_board.get_stone(nx, ny) == self.opponent_color:
                                        target_group = test_board.get_group_at(nx, ny)
                                        if target_group and len(target_group.liberties) == 1:
                                            priority = len(group.stones) * 5
                                            attack_moves.append(((x, y), priority))
                                            break
        
        return attack_moves
    
    def _find_tactical_moves(self, board: Board, legal_moves: List[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], float]]:
        """查找战术模式着法"""
        tactical_moves = []
        
        for x, y in legal_moves:
            # 查找匹配的战术模式
            patterns = self.pattern_library.find_matching_patterns(
                board, x, y, self.color, 'tactical'
            )
            
            if patterns:
                # 计算优先级
                priority = sum(1.0 for p in patterns)
                tactical_moves.append(((x, y), priority))
        
        return tactical_moves
    
    def _select_best_move(self, moves: List[Tuple[Tuple[int, int], float]]) -> Tuple[int, int]:
        """从候选着法中选择最佳"""
        if not moves:
            return None
        
        # 按优先级排序
        moves.sort(key=lambda x: x[1], reverse=True)
        
        # 选择优先级最高的（可以加入随机性）
        top_priority = moves[0][1]
        top_moves = [m for m, p in moves if p >= top_priority * 0.9]
        
        return random.choice(top_moves)
    
    def _select_by_evaluation(self, board: Board, legal_moves: List[Tuple[int, int]], 
                             game_info: Dict[str, Any]) -> Tuple[int, int]:
        """使用评估函数选择着法"""
        best_moves = []
        best_score = float('-inf')
        
        for x, y in legal_moves:
            score = self._evaluate_tactical_move(board, x, y)
            
            if score > best_score:
                best_score = score
                best_moves = [(x, y)]
            elif score == best_score:
                best_moves.append((x, y))
        
        return random.choice(best_moves) if best_moves else None
    
    def _evaluate_tactical_move(self, board: Board, x: int, y: int) -> float:
        """评估战术着法"""
        score = 0.0
        
        # 基础位置价值
        dist_to_edge = min(x, y, board.size - 1 - x, board.size - 1 - y)
        if dist_to_edge >= 2:
            score += 2
        
        # 连接价值
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < board.size and 0 <= ny < board.size:
                if board.get_stone(nx, ny) == self.color:
                    score += 3
                elif board.get_stone(nx, ny) == self.opponent_color:
                    score += 1  # 贴着对方下也有价值
        
        return score


class PatternAI(AIPlayer):
    """
    综合模式AI - 专家级
    结合定式、战术、死活等多种模式
    """
    
    def __init__(self, color: str, board_size: int = 19, **kwargs):
        super().__init__(color, board_size, thinking_time=3.0, level=AILevel.EXPERT)
        
        # 组合多个专门AI
        self.joseki_ai = JosekiAI(color, board_size)
        self.tactical_ai = TacticalAI(color, board_size)
        
        # MCTS作为后备
        self.mcts_ai = MonteCarloAI(color, board_size, simulations=500)
        
        self.opening_phase = kwargs.get('opening_phase', 30)
        self.middle_phase = kwargs.get('middle_phase', 100)
    
    def get_move(self, board: Board, game_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """
        根据局面阶段选择合适的AI策略
        
        Args:
            board: 当前棋盘
            game_info: 游戏信息
        
        Returns:
            落子位置
        """
        move_count = game_info.get('move_number', 0)
        
        # 开局阶段 - 重视定式
        if move_count < self.opening_phase:
            # 70%使用定式，30%使用战术
            if random.random() < 0.7:
                move = self.joseki_ai._find_joseki_move(board, game_info)
                if move:
                    return move
        
        # 中盘阶段 - 重视战斗
        elif move_count < self.middle_phase:
            # 使用战术AI
            return self.tactical_ai.get_move(board, game_info)
        
        # 收官阶段 - 使用MCTS精确计算
        return self.mcts_ai.get_move(board, game_info)
    
    def get_analysis(self, board: Board, last_move: Optional[Tuple[int, int]] = None) -> str:
        """获取综合分析"""
        eval_result = self.evaluate_position(board)
        
        analysis = [
            "专家AI综合分析:",
            f"形势判断: {eval_result.analysis_text}",
            f"推荐胜率: {eval_result.winning_probability:.1%}"
        ]
        
        # 添加阶段性建议
        move_count = sum(1 for y in range(board.size) for x in range(board.size) 
                        if board.get_stone(x, y))
        
        if move_count < self.opening_phase:
            analysis.append("当前处于开局阶段，应注重占据大场和角部定式")
        elif move_count < self.middle_phase:
            analysis.append("当前处于中盘阶段，应注重攻防和势力扩张")
        else:
            analysis.append("当前处于收官阶段，应精确计算每手棋的价值")
        
        return "\n".join(analysis)