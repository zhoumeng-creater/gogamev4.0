"""
地盘计算和死活判定模块
包含地盘识别、死活判定、双活判断等功能
"""

from typing import List, Tuple, Set, Dict, Optional
from enum import Enum
import numpy as np

from .board import Board, StoneColor, Group


class TerritoryStatus(Enum):
    """地盘状态枚举"""
    BLACK = 'black'
    WHITE = 'white'
    NEUTRAL = 'neutral'  # 中立区域
    SEKI = 'seki'  # 双活区域
    DAME = 'dame'  # 单官


class GroupStatus(Enum):
    """棋块死活状态"""
    ALIVE = 'alive'  # 活棋
    DEAD = 'dead'  # 死棋
    UNSETTLED = 'unsettled'  # 未定
    SEKI = 'seki'  # 双活


class Territory:
    """地盘计算类"""
    
    def __init__(self, board: Board):
        """
        初始化地盘计算器
        
        Args:
            board: 棋盘对象
        """
        self.board = board
        self.territory_map = [[TerritoryStatus.NEUTRAL.value for _ in range(board.size)] 
                              for _ in range(board.size)]
        self.influence_map = np.zeros((board.size, board.size), dtype=np.float32)
        
    def calculate_territory(self, dead_stones: Set[Tuple[int, int]] = None) -> Dict[str, int]:
        """
        计算地盘
        
        Args:
            dead_stones: 死子集合
            
        Returns:
            各方地盘数量
        """
        dead_stones = dead_stones or set()
        
        # 创建工作棋盘（移除死子）
        work_board = self.board.copy()
        for x, y in dead_stones:
            work_board.remove_stone(x, y)
        
        # 初始化结果
        result = {
            TerritoryStatus.BLACK.value: 0,
            TerritoryStatus.WHITE.value: 0,
            TerritoryStatus.NEUTRAL.value: 0,
            TerritoryStatus.DAME.value: 0
        }
        
        # 使用洪水填充算法识别地盘
        visited = set()
        
        for y in range(self.board.size):
            for x in range(self.board.size):
                if work_board.is_empty(x, y) and (x, y) not in visited:
                    territory, owner = self._flood_fill_territory(
                        work_board, x, y, visited
                    )
                    
                    # 更新地盘图
                    for tx, ty in territory:
                        self.territory_map[ty][tx] = owner
                        
                    # 更新计数
                    if owner in result:
                        result[owner] += len(territory)
        
        return result
    
    def _flood_fill_territory(self, board: Board, start_x: int, start_y: int,
                             visited: Set[Tuple[int, int]]) -> Tuple[Set[Tuple[int, int]], str]:
        """
        洪水填充算法识别连通的空地
        
        Args:
            board: 工作棋盘
            start_x, start_y: 起始位置
            visited: 已访问集合
            
        Returns:
            (地盘坐标集合, 所有者)
        """
        territory = set()
        borders = set()  # 边界颜色
        queue = [(start_x, start_y)]
        
        while queue:
            x, y = queue.pop(0)
            
            if (x, y) in visited:
                continue
                
            if not board.is_valid_position(x, y):
                continue
            
            if board.is_empty(x, y):
                visited.add((x, y))
                territory.add((x, y))
                
                # 检查四个方向
                for nx, ny in board.get_neighbors(x, y):
                    if (nx, ny) not in visited:
                        color = board.get_color(nx, ny)
                        if color == StoneColor.EMPTY.value:
                            queue.append((nx, ny))
                        else:
                            borders.add(color)
        
        # 判断地盘归属
        if len(borders) == 1:
            owner = borders.pop()
        elif len(borders) == 0:
            owner = TerritoryStatus.NEUTRAL.value
        else:
            # 多种颜色边界，判断是否为单官
            if len(territory) == 1:
                owner = TerritoryStatus.DAME.value
            else:
                owner = TerritoryStatus.NEUTRAL.value
        
        return territory, owner
    
    def calculate_influence(self, decay_factor: float = 0.5) -> np.ndarray:
        """
        计算势力图
        
        使用改进的距离衰减算法
        
        Args:
            decay_factor: 衰减因子
            
        Returns:
            势力图数组（正值为黑方势力，负值为白方势力）
        """
        influence = np.zeros((self.board.size, self.board.size), dtype=np.float32)
        
        # 获取所有棋块
        groups = self.board.get_all_groups()
        
        for group in groups:
            # 棋块强度基于大小和气数
            strength = len(group.stones) * np.sqrt(group.num_liberties())
            
            if group.color == StoneColor.BLACK.value:
                strength = abs(strength)
            else:
                strength = -abs(strength)
            
            # 传播势力
            for stone_x, stone_y in group.stones:
                self._propagate_influence(
                    influence, stone_x, stone_y, strength, decay_factor
                )
        
        self.influence_map = influence
        return influence
    
    def _propagate_influence(self, influence: np.ndarray, x: int, y: int,
                            strength: float, decay_factor: float):
        """
        传播单个位置的势力
        
        Args:
            influence: 势力图数组
            x, y: 源位置
            strength: 势力强度
            decay_factor: 衰减因子
        """
        max_distance = self.board.size // 2
        
        for dy in range(self.board.size):
            for dx in range(self.board.size):
                if dx == x and dy == y:
                    influence[dy, dx] += strength * 2  # 自身位置加倍
                else:
                    # 使用切比雪夫距离
                    distance = max(abs(dx - x), abs(dy - y))
                    
                    if distance <= max_distance:
                        # 指数衰减
                        factor = decay_factor ** distance
                        influence[dy, dx] += strength * factor
    
    def estimate_territory_by_influence(self, threshold: float = 5.0) -> Dict[str, int]:
        """
        基于势力图估算地盘
        
        Args:
            threshold: 判定阈值
            
        Returns:
            估算的地盘数量
        """
        if self.influence_map is None:
            self.calculate_influence()
        
        black_territory = 0
        white_territory = 0
        
        for y in range(self.board.size):
            for x in range(self.board.size):
                if self.board.is_empty(x, y):
                    influence = self.influence_map[y, x]
                    
                    if influence > threshold:
                        black_territory += 1
                    elif influence < -threshold:
                        white_territory += 1
        
        return {
            TerritoryStatus.BLACK.value: black_territory,
            TerritoryStatus.WHITE.value: white_territory
        }


class DeadStoneAnalyzer:
    """死活分析器"""
    
    def __init__(self, board: Board):
        """
        初始化死活分析器
        
        Args:
            board: 棋盘对象
        """
        self.board = board
        self.group_status: Dict[int, GroupStatus] = {}  # group_id -> status
        
    def analyze_all_groups(self) -> Dict[int, GroupStatus]:
        """
        分析所有棋块的死活状态
        
        Returns:
            棋块ID到状态的映射
        """
        groups = self.board.get_all_groups()
        
        for group in groups:
            group_id = id(group)
            status = self._analyze_group(group)
            self.group_status[group_id] = status
        
        return self.group_status
    
    def _analyze_group(self, group: Group) -> GroupStatus:
        """
        分析单个棋块的死活
        
        Args:
            group: 棋块对象
            
        Returns:
            棋块状态
        """
        # 简单的死活判定规则
        
        # 1. 气数判断
        if group.num_liberties() == 0:
            return GroupStatus.DEAD
        
        if group.num_liberties() >= 2:
            # 2. 眼位判断
            eyes = self._count_eyes(group)
            if eyes >= 2:
                return GroupStatus.ALIVE
            elif eyes == 1 and group.num_liberties() >= 4:
                return GroupStatus.ALIVE
        
        # 3. 逃跑潜力判断
        if self._can_escape(group):
            return GroupStatus.UNSETTLED
        
        # 4. 是否可以做活
        if self._can_make_eyes(group):
            return GroupStatus.UNSETTLED
        
        # 默认判定
        if group.num_liberties() >= 5:
            return GroupStatus.ALIVE
        elif group.num_liberties() <= 1:
            return GroupStatus.DEAD
        else:
            return GroupStatus.UNSETTLED
    
    def _count_eyes(self, group: Group) -> int:
        """
        计算棋块的眼数
        
        Args:
            group: 棋块对象
            
        Returns:
            眼数
        """
        eyes = []
        checked = set()
        
        # 检查棋块内部和周围的空点
        for stone_x, stone_y in group.stones:
            for nx, ny in self.board.get_neighbors(stone_x, stone_y):
                if (nx, ny) in checked:
                    continue
                    
                if self.board.is_empty(nx, ny):
                    if self._is_eye(nx, ny, group.color):
                        eyes.append((nx, ny))
                    checked.add((nx, ny))
        
        # 过滤假眼
        real_eyes = []
        for eye_x, eye_y in eyes:
            if self._is_real_eye(eye_x, eye_y, group):
                real_eyes.append((eye_x, eye_y))
        
        return len(real_eyes)
    
    def _is_eye(self, x: int, y: int, color: str) -> bool:
        """
        判断是否为眼位
        
        Args:
            x, y: 空点位置
            color: 棋块颜色
            
        Returns:
            是否为眼位
        """
        if not self.board.is_empty(x, y):
            return False
        
        # 四个正交方向必须都是己方颜色或边界
        for nx, ny in self.board.get_neighbors(x, y):
            if self.board.get_color(nx, ny) != color:
                return False
        
        # 对角线检查
        diagonal_positions = [
            (x - 1, y - 1), (x - 1, y + 1),
            (x + 1, y - 1), (x + 1, y + 1)
        ]
        
        diagonal_friendly = 0
        diagonal_total = 0
        
        for dx, dy in diagonal_positions:
            if self.board.is_valid_position(dx, dy):
                diagonal_total += 1
                if self.board.get_color(dx, dy) == color:
                    diagonal_friendly += 1
        
        # 需要足够的对角支持
        if diagonal_total == 4:
            return diagonal_friendly >= 3
        else:
            return diagonal_friendly >= diagonal_total - 1
    
    def _is_real_eye(self, x: int, y: int, group: Group) -> bool:
        """
        判断是否为真眼（不是假眼）
        
        Args:
            x, y: 眼位坐标
            group: 所属棋块
            
        Returns:
            是否为真眼
        """
        # 简化判断：如果眼位周围都是同一个棋块的棋子，则为真眼
        for nx, ny in self.board.get_neighbors(x, y):
            if not self.board.is_empty(nx, ny):
                if (nx, ny) not in group.stones:
                    return False
        
        return True
    
    def _can_escape(self, group: Group) -> bool:
        """
        判断棋块是否有逃跑潜力
        
        Args:
            group: 棋块对象
            
        Returns:
            是否可以逃跑
        """
        # 简化判断：如果棋块较大且有足够的气，可能可以逃跑
        if len(group.stones) >= 4 and group.num_liberties() >= 3:
            return True
        
        # 检查是否靠近边角（边角更难逃跑）
        min_x = min(x for x, y in group.stones)
        max_x = max(x for x, y in group.stones)
        min_y = min(y for x, y in group.stones)
        max_y = max(y for x, y in group.stones)
        
        edge_distance = min(min_x, min_y, 
                           self.board.size - 1 - max_x,
                           self.board.size - 1 - max_y)
        
        if edge_distance == 0 and group.num_liberties() <= 2:
            return False
        
        return group.num_liberties() >= 3
    
    def _can_make_eyes(self, group: Group) -> bool:
        """
        判断棋块是否可以做眼
        
        Args:
            group: 棋块对象
            
        Returns:
            是否可以做眼活棋
        """
        # 需要足够的空间做眼
        internal_space = self._count_internal_space(group)
        
        # 一般需要至少6-7个点的空间才能做出两个眼
        return internal_space >= 6
    
    def _count_internal_space(self, group: Group) -> int:
        """
        计算棋块内部空间
        
        Args:
            group: 棋块对象
            
        Returns:
            内部空间大小
        """
        # 使用凸包算法估算内部空间
        if len(group.stones) < 4:
            return 0
        
        # 简化：计算棋块的边界框内的空点数
        min_x = min(x for x, y in group.stones)
        max_x = max(x for x, y in group.stones)
        min_y = min(y for x, y in group.stones)
        max_y = max(y for x, y in group.stones)
        
        internal_empty = 0
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if self.board.is_empty(x, y):
                    # 检查是否被包围
                    if self._is_surrounded_by_group(x, y, group):
                        internal_empty += 1
        
        return internal_empty
    
    def _is_surrounded_by_group(self, x: int, y: int, group: Group) -> bool:
        """
        检查空点是否被棋块包围
        
        Args:
            x, y: 空点位置
            group: 棋块对象
            
        Returns:
            是否被包围
        """
        # 简化判断：四个方向至少有3个是该棋块的棋子
        group_neighbors = 0
        
        for nx, ny in self.board.get_neighbors(x, y):
            if (nx, ny) in group.stones:
                group_neighbors += 1
        
        return group_neighbors >= 3
    
    def find_dead_stones(self, threshold: float = 0.3) -> Set[Tuple[int, int]]:
        """
        查找可能的死子
        
        Args:
            threshold: 判定阈值（0-1之间，越小越严格）
            
        Returns:
            死子坐标集合
        """
        dead_stones = set()
        
        # 分析所有棋块
        self.analyze_all_groups()
        
        # 收集死棋的所有棋子
        groups = self.board.get_all_groups()
        for group in groups:
            group_id = id(group)
            if group_id in self.group_status:
                status = self.group_status[group_id]
                
                # 严格判定为死棋的
                if status == GroupStatus.DEAD:
                    dead_stones.update(group.stones)
                # 可能死棋的（根据阈值）
                elif status == GroupStatus.UNSETTLED and group.num_liberties() <= 1:
                    dead_stones.update(group.stones)
        
        return dead_stones
    
    def analyze_seki(self) -> List[Set[Tuple[int, int]]]:
        """
        分析双活（seki）情况
        
        Returns:
            双活区域列表
        """
        seki_regions = []
        
        # 查找相邻的不同颜色棋块
        groups = self.board.get_all_groups()
        
        for i, group1 in enumerate(groups):
            for group2 in groups[i + 1:]:
                if group1.color != group2.color:
                    if self._is_seki(group1, group2):
                        # 合并双活区域
                        region = set()
                        region.update(group1.stones)
                        region.update(group2.stones)
                        region.update(group1.liberties & group2.liberties)
                        seki_regions.append(region)
        
        return seki_regions
    
    def _is_seki(self, group1: Group, group2: Group) -> bool:
        """
        判断两个棋块是否形成双活
        
        Args:
            group1: 第一个棋块
            group2: 第二个棋块
            
        Returns:
            是否为双活
        """
        # 双活的条件：
        # 1. 共享气
        shared_liberties = group1.liberties & group2.liberties
        if not shared_liberties:
            return False
        
        # 2. 双方都无法吃掉对方
        # 简化判断：如果共享的气无法被任一方占据
        for x, y in shared_liberties:
            # 模拟黑方落子
            if group1.color == StoneColor.BLACK.value:
                test_board = self.board.copy()
                test_board.place_stone(x, y, StoneColor.BLACK.value)
                # 检查是否会被吃
                test_group = test_board.get_group(x, y)
                if test_group and test_group.num_liberties() == 0:
                    continue
            
            # 模拟白方落子
            if group2.color == StoneColor.WHITE.value:
                test_board = self.board.copy()
                test_board.place_stone(x, y, StoneColor.WHITE.value)
                # 检查是否会被吃
                test_group = test_board.get_group(x, y)
                if test_group and test_group.num_liberties() == 0:
                    continue
            
            # 如果双方都无法安全占据共享的气
            return False
        
        # 3. 双方都有足够的眼位潜力
        return len(shared_liberties) >= 2