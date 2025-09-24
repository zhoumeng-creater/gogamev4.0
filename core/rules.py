"""
围棋规则引擎模块
负责规则判定、合法性检查、吃子逻辑等
"""

from typing import List, Tuple, Set, Optional, Dict
from enum import Enum
from .board import Board, StoneColor, Group


class MoveResult(Enum):
    """落子结果枚举"""
    SUCCESS = 'success'
    ILLEGAL = 'illegal'
    KO = 'ko'
    SUICIDE = 'suicide'
    OCCUPIED = 'occupied'
    OUT_OF_BOUNDS = 'out_of_bounds'
    SUPERKO = 'superko'  # 超级劫


class RuleSet(Enum):
    """规则集枚举"""
    CHINESE = 'chinese'
    JAPANESE = 'japanese'
    AGA = 'aga'  # American Go Association
    NEW_ZEALAND = 'new_zealand'
    ING = 'ing'  # Ing rules


class Rules:
    """规则判定类"""
    
    def __init__(self, rule_set: str = 'chinese', komi: float = 7.5):
        """
        初始化规则引擎
        
        Args:
            rule_set: 规则集（chinese/japanese/aga）
            komi: 贴目数
        """
        self.rule_set = rule_set
        self.komi = komi
        
        # 规则特性配置
        self.features = self._get_rule_features(rule_set)
        
        # 历史记录（用于超级劫检测）
        self.position_history: List[str] = []
        self.max_history_check = 8  # 检查最近8个局面避免循环
        
    def _get_rule_features(self, rule_set: str) -> Dict[str, any]:
        """
        获取规则集特性配置
        """
        features = {
            'chinese': {
                'scoring': 'area',  # 数子法
                'suicide_allowed': False,  # 禁止自杀
                'superko_rule': 'positional',  # 禁止全局同形
                'pass_stones': 0,  # 虚手不需要交子
                'territory_in_seki': False,  # 双活无目
                'komi': 7.5  # 标准贴目
            },
            'japanese': {
                'scoring': 'territory',  # 数目法
                'suicide_allowed': False,
                'superko_rule': 'situational',  # 禁止全局同形再现
                'pass_stones': 1,  # 虚手需要交子
                'territory_in_seki': False,
                'komi': 6.5
            },
            'aga': {
                'scoring': 'area',
                'suicide_allowed': False,
                'superko_rule': 'situational',
                'pass_stones': 1,
                'territory_in_seki': False,
                'komi': 7.5
            }
        }
        
        return features.get(rule_set, features['chinese'])
    
    def is_legal_move(self, board: Board, x: int, y: int, color: str, 
                     ko_point: Optional[Tuple[int, int]] = None,
                     check_history: bool = True) -> MoveResult:
        """
        判断落子是否合法
        
        Args:
            board: 棋盘对象
            x, y: 落子位置
            color: 落子颜色
            ko_point: 劫点位置（如果有）
            check_history: 是否检查历史（超级劫）
            
        Returns:
            落子结果
        """
        # 检查位置是否有效
        if not board.is_valid_position(x, y):
            return MoveResult.OUT_OF_BOUNDS
        
        # 检查位置是否已有棋子
        if not board.is_empty(x, y):
            return MoveResult.OCCUPIED
        
        # 检查是否为劫点
        if ko_point and (x, y) == ko_point:
            return MoveResult.KO
        
        # 模拟落子
        test_board = board.copy()
        test_board.place_stone(x, y, color)
        
        # 执行吃子
        opponent_color = StoneColor.opposite(color)
        captured_groups = self._get_captured_groups(test_board, x, y, opponent_color)
        captured_count = 0
        
        for group in captured_groups:
            captured_count += len(group.stones)
            test_board.remove_group(group)
        
        # 检查自杀规则
        if not self.features.get('suicide_allowed', False):
            if self._is_suicide(test_board, x, y, color) and captured_count == 0:
                return MoveResult.SUICIDE
        
        # 检查超级劫（如果启用）
        if check_history and self.features.get('superko_rule'):
            board_hash = test_board.get_hash()
            if board_hash in self.position_history[-self.max_history_check:]:
                return MoveResult.SUPERKO
        
        return MoveResult.SUCCESS
    
    def _get_captured_groups(self, board: Board, x: int, y: int, 
                            opponent_color: str) -> List[Group]:
        """
        获取会被吃掉的对方棋块
        
        Args:
            board: 棋盘对象
            x, y: 刚落子的位置
            opponent_color: 对方颜色
            
        Returns:
            被吃掉的棋块列表
        """
        captured = []
        checked = set()
        
        for nx, ny in board.get_neighbors(x, y):
            if (nx, ny) in checked:
                continue
                
            if board.get_color(nx, ny) == opponent_color:
                group = board.get_group(nx, ny)
                if group and group.num_liberties() == 0:
                    captured.append(group)
                    checked.update(group.stones)
        
        return captured
    
    def _is_suicide(self, board: Board, x: int, y: int, color: str) -> bool:
        """
        检查是否为自杀手
        
        Args:
            board: 已落子的棋盘
            x, y: 落子位置
            color: 落子颜色
            
        Returns:
            是否为自杀
        """
        group = board.get_group(x, y)
        return group and group.num_liberties() == 0
    
    def execute_move(self, board: Board, x: int, y: int, color: str,
                    move_number: int = 0) -> Tuple[bool, List[Tuple[int, int]], Optional[Tuple[int, int]]]:
        """
        执行落子（包括吃子）
        
        Args:
            board: 棋盘对象
            x, y: 落子位置
            color: 落子颜色
            move_number: 手数
            
        Returns:
            (是否成功, 被吃子列表, 新的劫点)
        """
        # 放置棋子
        if not board.place_stone(x, y, color, move_number):
            return False, [], None
        
        # 处理吃子
        opponent_color = StoneColor.opposite(color)
        captured_groups = self._get_captured_groups(board, x, y, opponent_color)
        captured_stones = []
        
        for group in captured_groups:
            removed = board.remove_group(group)
            captured_stones.extend(removed)
        
        # 计算劫点
        ko_point = self.calculate_ko_point(board, x, y, captured_stones)
        
        # 记录棋盘状态
        self.position_history.append(board.get_hash())
        
        # 限制历史记录长度
        if len(self.position_history) > 50:
            self.position_history = self.position_history[-50:]
        
        return True, captured_stones, ko_point
    
    def calculate_ko_point(self, board: Board, x: int, y: int,
                          captured_stones: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """
        计算劫点
        
        如果恰好吃了一个子，且落子位置只形成了一个子的棋块，
        则被吃子的位置成为劫点
        
        Args:
            board: 棋盘对象
            x, y: 刚落子的位置
            captured_stones: 被吃掉的棋子列表
            
        Returns:
            劫点位置，如果没有则返回None
        """
        if len(captured_stones) == 1:
            group = board.get_group(x, y)
            if group and len(group.stones) == 1 and group.num_liberties() == 1:
                # 被吃子的位置成为劫点
                return captured_stones[0]
        
        return None
    
    def check_group_status(self, board: Board, x: int, y: int) -> Dict[str, any]:
        """
        检查棋块状态
        
        Args:
            board: 棋盘对象
            x, y: 棋子位置
            
        Returns:
            包含棋块状态信息的字典
        """
        group = board.get_group(x, y)
        if not group:
            return {
                'exists': False,
                'color': None,
                'size': 0,
                'liberties': 0,
                'in_atari': False,
                'eyes': []
            }
        
        return {
            'exists': True,
            'color': group.color,
            'size': len(group.stones),
            'liberties': group.num_liberties(),
            'in_atari': group.num_liberties() == 1,
            'eyes': self._find_eyes(board, group)
        }
    
    def _find_eyes(self, board: Board, group: Group) -> List[Tuple[int, int]]:
        """
        查找棋块的眼位
        
        Args:
            board: 棋盘对象
            group: 棋块对象
            
        Returns:
            眼位列表
        """
        eyes = []
        checked = set()
        
        # 检查棋块周围的空点
        for stone_x, stone_y in group.stones:
            for nx, ny in board.get_neighbors(stone_x, stone_y):
                if (nx, ny) in checked:
                    continue
                
                if board.is_empty(nx, ny):
                    if self._is_eye(board, nx, ny, group.color):
                        eyes.append((nx, ny))
                    checked.add((nx, ny))
        
        return eyes
    
    def _is_eye(self, board: Board, x: int, y: int, color: str) -> bool:
        """
        判断空点是否为眼位
        
        眼位的定义：
        1. 四周（上下左右）都是己方棋子或边界
        2. 四个对角至少有3个是己方棋子或边界
        
        Args:
            board: 棋盘对象
            x, y: 空点位置
            color: 己方颜色
            
        Returns:
            是否为眼位
        """
        if not board.is_empty(x, y):
            return False
        
        # 检查四周
        for nx, ny in board.get_neighbors(x, y):
            if board.get_color(nx, ny) != color:
                return False
        
        # 检查对角
        diagonal_friends = 0
        diagonal_positions = [
            (x - 1, y - 1), (x - 1, y + 1),
            (x + 1, y - 1), (x + 1, y + 1)
        ]
        
        for dx, dy in diagonal_positions:
            if not board.is_valid_position(dx, dy):
                # 边界算作友好
                diagonal_friends += 1
            elif board.get_color(dx, dy) == color:
                diagonal_friends += 1
            elif board.get_color(dx, dy) == StoneColor.EMPTY.value:
                # 空点不算敌对也不算友好
                pass
        
        # 需要至少3个对角是友好的
        return diagonal_friends >= 3
    
    def find_capturing_moves(self, board: Board, color: str) -> List[Tuple[int, int, int]]:
        """
        查找所有可以吃子的落子点
        
        Args:
            board: 棋盘对象
            color: 落子方颜色
            
        Returns:
            [(x, y, 吃子数)] 列表
        """
        capturing_moves = []
        opponent_color = StoneColor.opposite(color)
        
        # 找出所有气数为1的对方棋块
        vulnerable_groups = []
        checked_stones = set()
        
        for y in range(board.size):
            for x in range(board.size):
                if (x, y) in checked_stones:
                    continue
                
                if board.get_color(x, y) == opponent_color:
                    group = board.get_group(x, y)
                    if group and group.num_liberties() == 1:
                        vulnerable_groups.append(group)
                        checked_stones.update(group.stones)
        
        # 检查每个脆弱棋块的气位
        checked_liberties = set()
        for group in vulnerable_groups:
            for lx, ly in group.liberties:
                if (lx, ly) in checked_liberties:
                    continue
                
                # 检查这个位置是否可以落子
                if self.is_legal_move(board, lx, ly, color) == MoveResult.SUCCESS:
                    # 计算会吃掉多少子
                    test_board = board.copy()
                    test_board.place_stone(lx, ly, color)
                    captured_count = 0
                    
                    for nx, ny in board.get_neighbors(lx, ly):
                        if board.get_color(nx, ny) == opponent_color:
                            test_group = board.get_group(nx, ny)
                            if test_group and test_group.num_liberties() == 1:
                                captured_count += len(test_group.stones)
                    
                    if captured_count > 0:
                        capturing_moves.append((lx, ly, captured_count))
                
                checked_liberties.add((lx, ly))
        
        # 按吃子数排序
        capturing_moves.sort(key=lambda x: x[2], reverse=True)
        
        return capturing_moves
    
    def find_atari_moves(self, board: Board, color: str) -> List[Tuple[int, int, int]]:
        """
        查找所有可以打吃（atari）的落子点
        
        Args:
            board: 棋盘对象
            color: 落子方颜色
            
        Returns:
            [(x, y, 被打吃的棋块大小)] 列表
        """
        atari_moves = []
        opponent_color = StoneColor.opposite(color)
        checked_groups = set()
        
        for y in range(board.size):
            for x in range(board.size):
                if board.get_color(x, y) == opponent_color:
                    group = board.get_group(x, y)
                    if not group or id(group) in checked_groups:
                        continue
                    
                    checked_groups.add(id(group))
                    
                    # 检查是否可以将这个棋块打吃
                    if group.num_liberties() == 2:
                        for lx, ly in group.liberties:
                            if self.is_legal_move(board, lx, ly, color) == MoveResult.SUCCESS:
                                # 模拟落子后检查是否真的打吃
                                test_board = board.copy()
                                test_board.place_stone(lx, ly, color)
                                test_group = test_board.get_group(x, y)
                                
                                if test_group and test_group.num_liberties() == 1:
                                    atari_moves.append((lx, ly, len(group.stones)))
        
        # 按被打吃棋块大小排序
        atari_moves.sort(key=lambda x: x[2], reverse=True)
        
        return atari_moves
    
    def clear_history(self):
        """清除历史记录（用于新游戏）"""
        self.position_history.clear()