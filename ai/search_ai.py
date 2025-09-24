"""
搜索AI模块
包含极小极大搜索和蒙特卡洛树搜索的AI实现
"""

import time
import math
import random
import copy
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass, field

from .base import AIPlayer, Move, AILevel
from core import Board, Rules, MoveResult


class MinimaxAI(AIPlayer):
    """
    极小极大搜索AI - 中等难度
    使用Alpha-Beta剪枝的极小极大搜索
    """
    
    def __init__(self, color: str, board_size: int = 19, **kwargs):
        super().__init__(color, board_size, thinking_time=2.0, level=AILevel.MEDIUM)
        
        self.max_depth = kwargs.get('max_depth', 3)
        self.max_width = kwargs.get('max_width', 10)  # 每层最多考虑的着法数
        self.use_iterative_deepening = kwargs.get('iterative_deepening', True)
        self.use_killer_heuristic = kwargs.get('killer_heuristic', True)
        
        # 杀手启发式存储
        self.killer_moves = {}  # depth -> [(move1, score), (move2, score)]
        
        # 转置表（缓存已评估的局面）
        self.transposition_table = {}
    
    def get_move(self, board: Board, game_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """
        使用极小极大搜索选择最佳落子
        
        Args:
            board: 当前棋盘
            game_info: 游戏信息
        
        Returns:
            最佳落子位置
        """
        start_time = time.time()
        self.nodes_evaluated = 0
        self.transposition_table.clear()
        
        # 获取候选着法
        ko_point = game_info.get('ko_point')
        legal_moves = self.get_legal_moves(board, ko_point)
        
        if not legal_moves:
            return None
        
        # 过滤明显坏着
        legal_moves = self.filter_obviously_bad_moves(board, legal_moves)
        
        if not legal_moves:
            return None
        
        # 如果只有一个选择，直接返回
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # 对候选着法进行初步排序
        candidates = self._order_moves(board, legal_moves, game_info)[:self.max_width]
        
        best_move = None
        best_score = float('-inf')
        
        if self.use_iterative_deepening:
            # 迭代加深搜索
            for depth in range(1, self.max_depth + 1):
                if time.time() - start_time > self.thinking_time * 0.8:
                    break
                
                for x, y in candidates:
                    if time.time() - start_time > self.thinking_time:
                        break
                    
                    # 模拟落子
                    test_board = board.copy()
                    test_board.place_stone(x, y, self.color)
                    
                    # 递归搜索
                    score = self._minimax(
                        test_board, depth - 1, False, 
                        float('-inf'), float('inf'),
                        game_info
                    )
                    
                    if score > best_score:
                        best_score = score
                        best_move = (x, y)
                    
                    # 更新杀手启发式
                    if self.use_killer_heuristic:
                        self._update_killer_moves(depth, (x, y), score)
        else:
            # 固定深度搜索
            for x, y in candidates:
                if time.time() - start_time > self.thinking_time:
                    break
                
                test_board = board.copy()
                test_board.place_stone(x, y, self.color)
                
                score = self._minimax(
                    test_board, self.max_depth - 1, False,
                    float('-inf'), float('inf'),
                    game_info
                )
                
                if score > best_score:
                    best_score = score
                    best_move = (x, y)
        
        self.time_spent = time.time() - start_time
        return best_move
    
    def _minimax(self, board: Board, depth: int, is_maximizing: bool,
                 alpha: float, beta: float, game_info: Dict[str, Any]) -> float:
        """
        极小极大搜索with Alpha-Beta剪枝
        
        Args:
            board: 当前棋盘
            depth: 剩余搜索深度
            is_maximizing: 是否为极大节点
            alpha: Alpha值
            beta: Beta值
            game_info: 游戏信息
        
        Returns:
            评估分数
        """
        self.nodes_evaluated += 1
        
        # 检查转置表
        board_hash = board.get_hash()
        if board_hash in self.transposition_table:
            cached = self.transposition_table[board_hash]
            if cached['depth'] >= depth:
                return cached['score']
        
        # 达到搜索深度或游戏结束
        if depth == 0:
            score = self._evaluate_board_simple(board)
            self.transposition_table[board_hash] = {'depth': depth, 'score': score}
            return score
        
        current_color = self.color if is_maximizing else self.opponent_color
        ko_point = game_info.get('ko_point')
        legal_moves = self.get_legal_moves(board, ko_point)
        
        if not legal_moves:
            # 虚手
            score = self._evaluate_board_simple(board)
            self.transposition_table[board_hash] = {'depth': depth, 'score': score}
            return score
        
        # 限制搜索宽度
        if len(legal_moves) > self.max_width:
            legal_moves = self._order_moves(board, legal_moves, game_info)[:self.max_width]
        
        if is_maximizing:
            max_eval = float('-inf')
            
            for x, y in legal_moves:
                test_board = board.copy()
                test_board.place_stone(x, y, current_color)
                
                eval_score = self._minimax(
                    test_board, depth - 1, False,
                    alpha, beta, game_info
                )
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    break  # Beta剪枝
            
            self.transposition_table[board_hash] = {'depth': depth, 'score': max_eval}
            return max_eval
        else:
            min_eval = float('inf')
            
            for x, y in legal_moves:
                test_board = board.copy()
                test_board.place_stone(x, y, current_color)
                
                eval_score = self._minimax(
                    test_board, depth - 1, True,
                    alpha, beta, game_info
                )
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break  # Alpha剪枝
            
            self.transposition_table[board_hash] = {'depth': depth, 'score': min_eval}
            return min_eval
    
    def _order_moves(self, board: Board, moves: List[Tuple[int, int]], 
                     game_info: Dict[str, Any]) -> List[Tuple[int, int]]:
        """
        对着法进行排序（用于剪枝优化）
        
        Args:
            board: 棋盘
            moves: 着法列表
            game_info: 游戏信息
        
        Returns:
            排序后的着法列表
        """
        scored_moves = []
        
        for x, y in moves:
            score = self._quick_evaluate_move(board, x, y)
            
            # 检查杀手启发式
            if self.use_killer_heuristic:
                for depth in self.killer_moves:
                    for killer_move, killer_score in self.killer_moves[depth]:
                        if killer_move == (x, y):
                            score += killer_score * 0.1
            
            scored_moves.append((score, x, y))
        
        # 按分数降序排序
        scored_moves.sort(reverse=True)
        
        return [(x, y) for _, x, y in scored_moves]
    
    def _quick_evaluate_move(self, board: Board, x: int, y: int) -> float:
        """快速评估着法（用于排序）"""
        score = 0.0
        
        # 检查吃子
        test_board = board.copy()
        test_board.place_stone(x, y, self.color)
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                if test_board.get_stone(nx, ny) == self.opponent_color:
                    group = test_board.get_group_at(nx, ny)
                    if group and len(group.liberties) == 0:
                        score += len(group.stones) * 10
        
        # 位置价值
        dist_to_edge = min(x, y, self.board_size - 1 - x, self.board_size - 1 - y)
        if dist_to_edge >= 2:
            score += 2
        
        return score
    
    def _evaluate_board_simple(self, board: Board) -> float:
        """简单的棋盘评估函数"""
        score = 0.0
        
        # 统计棋子数
        for y in range(self.board_size):
            for x in range(self.board_size):
                stone = board.get_stone(x, y)
                if stone == self.color:
                    score += 1
                elif stone == self.opponent_color:
                    score -= 1
        
        # 统计气数
        for group in board.get_all_groups():
            liberty_score = len(group.liberties) * 0.5
            if group.color == self.color:
                score += liberty_score
            else:
                score -= liberty_score
        
        return score
    
    def _update_killer_moves(self, depth: int, move: Tuple[int, int], score: float):
        """更新杀手启发式表"""
        if depth not in self.killer_moves:
            self.killer_moves[depth] = []
        
        # 保持最多2个杀手着法
        self.killer_moves[depth].append((move, score))
        self.killer_moves[depth].sort(key=lambda x: x[1], reverse=True)
        self.killer_moves[depth] = self.killer_moves[depth][:2]


@dataclass
class MCTSNode:
    """蒙特卡洛树搜索节点"""
    board: Board
    move: Optional[Tuple[int, int]]
    parent: Optional['MCTSNode']
    current_color: str
    
    wins: float = 0.0
    visits: int = 0
    untried_moves: List[Tuple[int, int]] = field(default_factory=list)
    children: List['MCTSNode'] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化未尝试的着法"""
        if not self.untried_moves:
            self.untried_moves = self._get_legal_moves()
    
    def _get_legal_moves(self) -> List[Tuple[int, int]]:
        """获取合法着法"""
        moves = []
        for y in range(self.board.size):
            for x in range(self.board.size):
                if self.board.is_empty(x, y):
                    # 简单的合法性检查
                    moves.append((x, y))
        return moves
    
    def select_child(self, c_param: float = 1.4) -> 'MCTSNode':
        """使用UCB选择子节点"""
        return max(
            self.children,
            key=lambda c: c.wins / c.visits + c_param * math.sqrt(2 * math.log(self.visits) / c.visits)
        )
    
    def add_child(self, move: Tuple[int, int]) -> 'MCTSNode':
        """添加子节点"""
        # 创建新棋盘
        new_board = self.board.copy()
        new_board.place_stone(move[0], move[1], self.current_color)
        
        # 切换颜色
        next_color = 'white' if self.current_color == 'black' else 'black'
        
        # 创建子节点
        child = MCTSNode(new_board, move, self, next_color)
        
        self.untried_moves.remove(move)
        self.children.append(child)
        
        return child
    
    def update(self, result: float):
        """更新节点统计"""
        self.visits += 1
        self.wins += result


class MonteCarloAI(AIPlayer):
    """
    蒙特卡洛树搜索AI - 高难度
    使用MCTS算法进行决策
    """
    
    def __init__(self, color: str, board_size: int = 19, **kwargs):
        super().__init__(color, board_size, thinking_time=5.0, level=AILevel.HARD)
        
        self.simulations = kwargs.get('simulations', 1000)
        self.c_param = kwargs.get('c_param', 1.4)  # UCB探索参数
        self.max_rollout_depth = kwargs.get('max_rollout_depth', 100)
        self.use_rave = kwargs.get('use_rave', False)  # RAVE优化
        
    def get_move(self, board: Board, game_info: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """
        使用MCTS选择最佳落子
        
        Args:
            board: 当前棋盘
            game_info: 游戏信息
        
        Returns:
            最佳落子位置
        """
        start_time = time.time()
        self.nodes_evaluated = 0
        
        # 获取合法着法
        ko_point = game_info.get('ko_point')
        legal_moves = self.get_legal_moves(board, ko_point)
        
        if not legal_moves:
            return None
        
        # 过滤眼位
        candidates = self.filter_obviously_bad_moves(board, legal_moves)
        
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return candidates[0]
        
        # 创建根节点
        root = MCTSNode(board, None, None, self.color)
        root.untried_moves = candidates
        
        simulations_run = 0
        
        # 执行MCTS
        while time.time() - start_time < self.thinking_time and simulations_run < self.simulations:
            node = root
            
            # 1. 选择 (Selection)
            while node.untried_moves == [] and node.children != []:
                node = node.select_child(self.c_param)
            
            # 2. 扩展 (Expansion)
            if node.untried_moves != []:
                move = random.choice(node.untried_moves)
                node = node.add_child(move)
            
            # 3. 模拟 (Simulation)
            result = self._simulate_random_game(node.board, node.current_color)
            
            # 4. 反向传播 (Backpropagation)
            while node is not None:
                # 从当前玩家的角度更新结果
                if node.current_color == self.color:
                    node.update(result)
                else:
                    node.update(1 - result)
                node = node.parent
            
            simulations_run += 1
            self.nodes_evaluated += 1
        
        self.time_spent = time.time() - start_time
        
        # 选择访问次数最多的着法
        if root.children:
            best_child = max(root.children, key=lambda c: c.visits)
            return best_child.move
        
        return None
    
    def _simulate_random_game(self, board: Board, current_color: str) -> float:
        """
        模拟随机对局到终局
        
        Args:
            board: 起始棋盘
            current_color: 当前玩家颜色
        
        Returns:
            结果（1=己方胜，0=对方胜，0.5=平局）
        """
        sim_board = board.copy()
        sim_color = current_color
        pass_count = 0
        moves = 0
        
        while pass_count < 2 and moves < self.max_rollout_depth:
            # 获取合法着法
            legal_moves = []
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if sim_board.is_empty(x, y):
                        # 简单检查，不填眼
                        if not self._is_simple_eye(sim_board, x, y, sim_color):
                            legal_moves.append((x, y))
            
            if legal_moves:
                # 随机选择
                x, y = random.choice(legal_moves)
                sim_board.place_stone(x, y, sim_color)
                pass_count = 0
            else:
                # 虚手
                pass_count += 1
            
            # 切换玩家
            sim_color = 'white' if sim_color == 'black' else 'black'
            moves += 1
        
        # 评估终局
        return self._evaluate_final_position(sim_board)
    
    def _is_simple_eye(self, board: Board, x: int, y: int, color: str) -> bool:
        """简单的眼位检测"""
        # 检查四个正交方向
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                if board.get_stone(nx, ny) != color:
                    return False
        return True
    
    def _evaluate_final_position(self, board: Board) -> float:
        """
        评估终局位置
        
        Returns:
            胜率（0到1之间）
        """
        my_score = 0
        opp_score = 0
        
        # 简单计算领地
        for y in range(self.board_size):
            for x in range(self.board_size):
                stone = board.get_stone(x, y)
                if stone == self.color:
                    my_score += 1
                elif stone == self.opponent_color:
                    opp_score += 1
                else:
                    # 简单判断空点归属
                    neighbors = []
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.board_size and 0 <= ny < self.board_size:
                            neighbor_stone = board.get_stone(nx, ny)
                            if neighbor_stone:
                                neighbors.append(neighbor_stone)
                    
                    if neighbors:
                        if all(s == self.color for s in neighbors):
                            my_score += 1
                        elif all(s == self.opponent_color for s in neighbors):
                            opp_score += 1
        
        # 加上贴目
        if self.color == 'white':
            my_score += 7.5
        else:
            opp_score += 7.5
        
        # 返回胜率
        if my_score > opp_score:
            return 1.0
        elif my_score < opp_score:
            return 0.0
        else:
            return 0.5
    
    def get_analysis(self, board: Board, last_move: Optional[Tuple[int, int]] = None) -> str:
        """获取分析文本"""
        analysis = [
            f"MCTS AI分析:",
            f"模拟对局数: {self.nodes_evaluated}",
            f"思考时间: {self.time_spent:.2f}秒",
            f"平均每秒模拟: {self.nodes_evaluated / max(self.time_spent, 0.01):.0f}"
        ]
        
        return "\n".join(analysis)