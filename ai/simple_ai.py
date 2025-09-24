"""
简单AI模块
包含随机AI和贪心AI的实现
"""

import random
import time
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

from .base import AIPlayer, Move, AILevel, EvaluationResult
from core import Board, Rules, MoveResult


class RandomAI(AIPlayer):
    """
    随机AI - 最简单的AI
    随机选择合法位置落子，适合初学者练习
    """
    
    def __init__(self, color: str, board_size: int = 19, **kwargs):
        super().__init__(color, board_size, thinking_time=0.1, level=AILevel.BEGINNER)
        self.avoid_eyes = kwargs.get('avoid_eyes', True)  # 是否避免填眼
    
    def get_move(self, board: Board, game_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """
        随机选择一个合法位置
        
        Args:
            board: 当前棋盘
            game_info: 游戏信息
        
        Returns:
            随机的合法落子位置
        """
        start_time = time.time()
        
        # 获取合法落子
        ko_point = game_info.get('ko_point')
        legal_moves = self.get_legal_moves(board, ko_point)
        
        if not legal_moves:
            return None
        
        # 过滤眼位（如果启用）
        if self.avoid_eyes:
            non_eye_moves = self.filter_obviously_bad_moves(board, legal_moves)
            if non_eye_moves:
                legal_moves = non_eye_moves
        
        # 模拟思考时间
        elapsed = time.time() - start_time
        if elapsed < self.thinking_time:
            time.sleep(self.thinking_time - elapsed)
        
        # 随机选择
        if legal_moves:
            return random.choice(legal_moves)
        
        return None
    
    def get_analysis(self, board: Board, last_move: Optional[Tuple[int, int]] = None) -> str:
        """获取分析（随机AI不提供分析）"""
        return "随机AI: 我只是随机下棋，没有策略分析。"


class GreedyAI(AIPlayer):
    """
    贪心AI - 基础战术AI
    选择即时收益最大的落子（吃子、救子、占大场等）
    """
    
    def __init__(self, color: str, board_size: int = 19, **kwargs):
        super().__init__(color, board_size, thinking_time=0.5, level=AILevel.EASY)
        
        # 评估权重
        self.weights = {
            'capture': kwargs.get('capture_weight', 100),      # 吃子权重
            'save': kwargs.get('save_weight', 80),              # 救子权重
            'atari': kwargs.get('atari_weight', 60),            # 叫吃权重
            'extend': kwargs.get('extend_weight', 40),          # 扩展权重
            'connect': kwargs.get('connect_weight', 30),        # 连接权重
            'territory': kwargs.get('territory_weight', 20),    # 领地权重
            'influence': kwargs.get('influence_weight', 15),    # 势力权重
            'position': kwargs.get('position_weight', 10),      # 位置权重
        }
    
    def get_move(self, board: Board, game_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """
        选择评分最高的落子
        
        Args:
            board: 当前棋盘
            game_info: 游戏信息
        
        Returns:
            最佳落子位置
        """
        start_time = time.time()
        self.nodes_evaluated = 0
        
        # 获取合法落子
        ko_point = game_info.get('ko_point')
        legal_moves = self.get_legal_moves(board, ko_point)
        
        if not legal_moves:
            return None
        
        # 过滤明显的坏着
        legal_moves = self.filter_obviously_bad_moves(board, legal_moves)
        
        if not legal_moves:
            return None
        
        # 评估每个位置
        best_moves = []
        best_score = float('-inf')
        
        for x, y in legal_moves:
            # 时间检查
            if time.time() - start_time > self.thinking_time * 0.9:
                break
            
            score = self._evaluate_move(board, x, y, game_info)
            self.nodes_evaluated += 1
            
            if score > best_score:
                best_score = score
                best_moves = [(x, y)]
            elif score == best_score:
                best_moves.append((x, y))
        
        # 统计时间
        self.time_spent = time.time() - start_time
        
        # 从最佳着法中随机选择（增加变化）
        if best_moves:
            return random.choice(best_moves)
        
        return None
    
    def _evaluate_move(self, board: Board, x: int, y: int, game_info: Dict[str, Any]) -> float:
        """
        评估单个落子的价值
        
        Args:
            board: 棋盘
            x, y: 落子位置
            game_info: 游戏信息
        
        Returns:
            评分
        """
        score = 0.0
        
        # 1. 吃子得分
        capture_score = self._evaluate_captures_at(board, x, y)
        score += capture_score * self.weights['capture']
        
        # 2. 救子得分
        save_score = self._evaluate_saves_at(board, x, y)
        score += save_score * self.weights['save']
        
        # 3. 叫吃得分
        atari_score = self._evaluate_atari_at(board, x, y)
        score += atari_score * self.weights['atari']
        
        # 4. 扩展得分
        extend_score = self._evaluate_extension_at(board, x, y)
        score += extend_score * self.weights['extend']
        
        # 5. 连接得分
        connect_score = self._evaluate_connection_at(board, x, y)
        score += connect_score * self.weights['connect']
        
        # 6. 领地得分
        territory_score = self._evaluate_territory_gain_at(board, x, y)
        score += territory_score * self.weights['territory']
        
        # 7. 势力得分
        influence_score = self._evaluate_influence_at(board, x, y)
        score += influence_score * self.weights['influence']
        
        # 8. 位置得分
        position_score = self._evaluate_position_value(x, y)
        score += position_score * self.weights['position']
        
        # 添加随机因素（5%变化）
        score *= (1 + random.uniform(-0.05, 0.05))
        
        return score
    
    def _evaluate_captures_at(self, board: Board, x: int, y: int) -> float:
        """评估吃子得分"""
        captures = 0
        
        # 模拟落子
        test_board = board.copy()
        test_board.place_stone(x, y, self.color)
        
        # 检查相邻的对方棋子
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                if test_board.get_stone(nx, ny) == self.opponent_color:
                    group = test_board.get_group_at(nx, ny)
                    if group and len(group.liberties) == 0:
                        captures += len(group.stones)
        
        return float(captures)
    
    def _evaluate_saves_at(self, board: Board, x: int, y: int) -> float:
        """评估救子得分"""
        saves = 0
        
        # 检查相邻的己方棋子
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                if board.get_stone(nx, ny) == self.color:
                    group = board.get_group_at(nx, ny)
                    if group and len(group.liberties) == 1:  # 只有一气
                        saves += len(group.stones)
        
        return float(saves)
    
    def _evaluate_atari_at(self, board: Board, x: int, y: int) -> float:
        """评估叫吃得分"""
        atari_value = 0
        
        # 模拟落子
        test_board = board.copy()
        test_board.place_stone(x, y, self.color)
        
        # 检查是否造成叫吃
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                if test_board.get_stone(nx, ny) == self.opponent_color:
                    group = test_board.get_group_at(nx, ny)
                    if group and len(group.liberties) == 1:
                        atari_value += len(group.stones) * 0.5
        
        return atari_value
    
    def _evaluate_extension_at(self, board: Board, x: int, y: int) -> float:
        """评估扩展得分（增加己方棋子的气）"""
        extension_value = 0
        
        # 检查能增加多少气
        test_board = board.copy()
        test_board.place_stone(x, y, self.color)
        
        # 获取新形成的棋块
        group = test_board.get_group_at(x, y)
        if group:
            extension_value = len(group.liberties) * 0.3
        
        return extension_value
    
    def _evaluate_connection_at(self, board: Board, x: int, y: int) -> float:
        """评估连接得分"""
        connections = 0
        
        # 计算能连接多少己方棋子
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                if board.get_stone(nx, ny) == self.color:
                    connections += 1
        
        # 对角线连接（权重较低）
        for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                if board.get_stone(nx, ny) == self.color:
                    connections += 0.3
        
        return connections
    
    def _evaluate_territory_gain_at(self, board: Board, x: int, y: int) -> float:
        """评估领地增益"""
        # 简单估算：周围空点的数量
        empty_neighbors = 0
        
        for radius in [1, 2]:  # 检查1-2格范围
            weight = 1.0 / radius
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:  # 只检查边界
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                            if board.is_empty(nx, ny):
                                empty_neighbors += weight
        
        return empty_neighbors
    
    def _evaluate_influence_at(self, board: Board, x: int, y: int) -> float:
        """评估势力影响"""
        influence = 0.0
        
        # 计算周围3格内的势力平衡
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx == 0 and dy == 0:
                    continue
                
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                    distance = max(abs(dx), abs(dy))
                    weight = 1.0 / (distance + 1)
                    
                    stone = board.get_stone(nx, ny)
                    if stone == self.color:
                        influence += weight
                    elif stone == self.opponent_color:
                        influence -= weight
        
        return influence
    
    def _evaluate_position_value(self, x: int, y: int) -> float:
        """
        评估位置的固有价值
        
        Args:
            x, y: 位置坐标
        
        Returns:
            位置价值得分
        """
        # 边界到中心的距离
        dist_to_edge = min(x, y, self.board_size - 1 - x, self.board_size - 1 - y)
        
        if self.board_size == 19:
            # 星位价值高
            star_points = [
                (3, 3), (3, 9), (3, 15),
                (9, 3), (9, 9), (9, 15),
                (15, 3), (15, 9), (15, 15)
            ]
            if (x, y) in star_points:
                return 3.0
            
            # 小目和高目
            if (x in [3, 15] and y in [4, 14]) or (x in [4, 14] and y in [3, 15]):
                return 2.5
        
        # 根据距离边的远近给分
        if dist_to_edge == 0:  # 第一线
            return -1.0
        elif dist_to_edge == 1:  # 第二线
            return 0.5
        elif dist_to_edge == 2:  # 第三线
            return 2.0
        elif dist_to_edge == 3:  # 第四线
            return 2.5
        else:  # 中腹
            return 1.5
    
    def get_analysis(self, board: Board, last_move: Optional[Tuple[int, int]] = None) -> str:
        """获取分析文本"""
        eval_result = self.evaluate_position(board)
        
        analysis = [
            f"贪心AI分析 (已评估{self.nodes_evaluated}个位置):",
            f"形势评分: {eval_result.score:+.1f}",
            f"领地差距: {eval_result.territory_score:+.1f}",
            f"思考时间: {self.time_spent:.2f}秒"
        ]
        
        return "\n".join(analysis)