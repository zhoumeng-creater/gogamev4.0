"""
棋盘管理模块
负责棋盘状态管理、棋子操作、棋块连接等
"""

import hashlib
from typing import List, Tuple, Set, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


class StoneColor(Enum):
    """棋子颜色枚举"""
    EMPTY = ''
    BLACK = 'black'
    WHITE = 'white'

    @classmethod
    def opposite(cls, color: str) -> str:
        """获取对手颜色"""
        if color == cls.BLACK.value:
            return cls.WHITE.value
        elif color == cls.WHITE.value:
            return cls.BLACK.value
        return cls.EMPTY.value


@dataclass
class Stone:
    """棋子数据类"""
    x: int
    y: int
    color: str
    move_number: int = 0  # 手数
    
    def __hash__(self):
        return hash((self.x, self.y, self.color))
    
    def __eq__(self, other):
        if not isinstance(other, Stone):
            return False
        return self.x == other.x and self.y == other.y and self.color == other.color


@dataclass
class Group:
    """棋块数据类 - 连接的同色棋子组"""
    stones: Set[Tuple[int, int]] = field(default_factory=set)
    color: str = ''
    liberties: Set[Tuple[int, int]] = field(default_factory=set)
    
    def add_stone(self, x: int, y: int):
        """添加棋子到棋块"""
        self.stones.add((x, y))
    
    def remove_liberty(self, x: int, y: int):
        """移除气"""
        self.liberties.discard((x, y))
    
    def add_liberty(self, x: int, y: int):
        """添加气"""
        self.liberties.add((x, y))
    
    def num_liberties(self) -> int:
        """获取气数"""
        return len(self.liberties)
    
    def merge(self, other: 'Group'):
        """合并另一个棋块"""
        if self.color != other.color:
            raise ValueError("Cannot merge groups of different colors")
        self.stones.update(other.stones)
        self.liberties.update(other.liberties)
        # 移除内部位置（不再是气）
        self.liberties -= self.stones


class Board:
    """棋盘类 - 管理棋盘状态和操作"""
    
    # 标准棋盘星位位置
    STAR_POINTS = {
        19: [(3, 3), (3, 9), (3, 15), (9, 3), (9, 9), 
             (9, 15), (15, 3), (15, 9), (15, 15)],
        13: [(3, 3), (3, 9), (9, 3), (9, 9), (6, 6)],
        9: [(2, 2), (2, 6), (6, 2), (6, 6), (4, 4)]
    }
    
    # 让子标准位置
    HANDICAP_POSITIONS = {
        19: {
            2: [(3, 15), (15, 3)],
            3: [(3, 15), (15, 3), (3, 3)],
            4: [(3, 15), (15, 3), (3, 3), (15, 15)],
            5: [(3, 15), (15, 3), (3, 3), (15, 15), (9, 9)],
            6: [(3, 15), (15, 3), (3, 3), (15, 15), (3, 9), (15, 9)],
            7: [(3, 15), (15, 3), (3, 3), (15, 15), (3, 9), (15, 9), (9, 9)],
            8: [(3, 15), (15, 3), (3, 3), (15, 15), (3, 9), (15, 9), (9, 3), (9, 15)],
            9: [(3, 15), (15, 3), (3, 3), (15, 15), (3, 9), (15, 9), (9, 3), (9, 15), (9, 9)]
        },
        13: {
            2: [(3, 9), (9, 3)],
            3: [(3, 9), (9, 3), (3, 3)],
            4: [(3, 9), (9, 3), (3, 3), (9, 9)],
            5: [(3, 9), (9, 3), (3, 3), (9, 9), (6, 6)],
            6: [(3, 9), (9, 3), (3, 3), (9, 9), (3, 6), (9, 6)],
            7: [(3, 9), (9, 3), (3, 3), (9, 9), (3, 6), (9, 6), (6, 6)],
            8: [(3, 9), (9, 3), (3, 3), (9, 9), (3, 6), (9, 6), (6, 3), (6, 9)],
            9: [(3, 9), (9, 3), (3, 3), (9, 9), (3, 6), (9, 6), (6, 3), (6, 9), (6, 6)]
        },
        9: {
            2: [(2, 6), (6, 2)],
            3: [(2, 6), (6, 2), (2, 2)],
            4: [(2, 6), (6, 2), (2, 2), (6, 6)],
            5: [(2, 6), (6, 2), (2, 2), (6, 6), (4, 4)]
        }
    }
    
    def __init__(self, size: int = 19):
        """
        初始化棋盘
        
        Args:
            size: 棋盘大小（9, 13, 或 19）
        """
        if size not in [9, 13, 19]:
            raise ValueError(f"Invalid board size: {size}. Must be 9, 13, or 19.")
        
        self.size = size
        self.grid = [[StoneColor.EMPTY.value for _ in range(size)] for _ in range(size)]
        self.groups: Dict[Tuple[int, int], Group] = {}  # 缓存棋块信息
        self.stone_history: List[Stone] = []  # 棋子历史，用于手数显示
        
    def copy(self) -> 'Board':
        """深拷贝棋盘"""
        import copy
        new_board = Board(self.size)
        new_board.grid = [row[:] for row in self.grid]
        new_board.groups = copy.deepcopy(self.groups)
        new_board.stone_history = copy.deepcopy(self.stone_history)
        return new_board
    
    def is_empty(self, x: int, y: int) -> bool:
        """检查位置是否为空"""
        return self.grid[y][x] == StoneColor.EMPTY.value
    
    def is_valid_position(self, x: int, y: int) -> bool:
        """检查位置是否有效"""
        return 0 <= x < self.size and 0 <= y < self.size
    
    def get_color(self, x: int, y: int) -> str:
        """获取指定位置的颜色"""
        if self.is_valid_position(x, y):
            return self.grid[y][x]
        return StoneColor.EMPTY.value

    def get_stone(self, x: int, y: int) -> str:
        """
        兼容旧接口：获取指定位置的棋子颜色。

        许多 AI/分析模块使用 `get_stone(x, y)` 读取棋盘；当前实现统一返回颜色字符串：
        - 空：''
        - 黑：'black'
        - 白：'white'
        """
        return self.get_color(x, y)
    
    def place_stone(self, x: int, y: int, color: str, move_number: int = 0) -> bool:
        """
        放置棋子
        
        Args:
            x, y: 坐标
            color: 颜色
            move_number: 手数
            
        Returns:
            是否成功放置
        """
        if not self.is_valid_position(x, y):
            return False
        if not self.is_empty(x, y):
            return False
        
        self.grid[y][x] = color
        self.stone_history.append(Stone(x, y, color, move_number))
        self._invalidate_group_cache(x, y)
        return True
    
    def remove_stone(self, x: int, y: int) -> bool:
        """
        移除棋子
        
        Returns:
            是否成功移除
        """
        if not self.is_valid_position(x, y):
            return False
        
        if not self.is_empty(x, y):
            self.grid[y][x] = StoneColor.EMPTY.value
            self._invalidate_group_cache(x, y)
            # 从历史中移除
            self.stone_history = [s for s in self.stone_history 
                                 if not (s.x == x and s.y == y)]
            return True
        return False
    
    def remove_group(self, group: Group) -> List[Tuple[int, int]]:
        """
        移除整个棋块
        
        Returns:
            被移除的棋子位置列表
        """
        removed = []
        for x, y in group.stones:
            if self.remove_stone(x, y):
                removed.append((x, y))
        return removed
    
    def get_group(self, x: int, y: int) -> Optional[Group]:
        """
        获取棋块信息
        
        Args:
            x, y: 棋子坐标
            
        Returns:
            棋块对象，如果位置为空则返回None
        """
        if not self.is_valid_position(x, y):
            return None
        if self.is_empty(x, y):
            return None
        
        # 检查缓存
        if (x, y) in self.groups:
            return self.groups[(x, y)]
        
        # 计算棋块
        group = self._calculate_group(x, y)
        
        # 更新缓存
        for stone_pos in group.stones:
            self.groups[stone_pos] = group
        
        return group

    def get_group_at(self, x: int, y: int) -> Optional[Group]:
        """
        兼容旧接口：`get_group_at(x, y)`。

        旧版 AI/分析代码使用该方法获取当前位置所属棋块，等价于 `get_group(x, y)`。
        """
        return self.get_group(x, y)
    
    def _calculate_group(self, x: int, y: int) -> Group:
        """
        计算连通的棋块（使用BFS）
        """
        color = self.get_color(x, y)
        if color == StoneColor.EMPTY.value:
            return Group()
        
        group = Group(color=color)
        visited = set()
        queue = [(x, y)]
        
        while queue:
            cx, cy = queue.pop(0)
            
            if (cx, cy) in visited:
                continue
            
            if not self.is_valid_position(cx, cy):
                continue
            
            visited.add((cx, cy))
            current_color = self.get_color(cx, cy)
            
            if current_color == color:
                group.add_stone(cx, cy)
                
                # 检查四个方向
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = cx + dx, cy + dy
                    
                    if not self.is_valid_position(nx, ny):
                        continue
                    
                    if (nx, ny) in visited:
                        continue
                    
                    neighbor_color = self.get_color(nx, ny)
                    
                    if neighbor_color == StoneColor.EMPTY.value:
                        group.add_liberty(nx, ny)
                    elif neighbor_color == color:
                        queue.append((nx, ny))
        
        return group
    
    def _invalidate_group_cache(self, x: int, y: int):
        """
        使相关位置的棋块缓存失效
        """
        positions_to_clear = set()
        
        # 清除自身和周围位置的缓存
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if self.is_valid_position(nx, ny):
                    if (nx, ny) in self.groups:
                        # 获取整个棋块的所有位置
                        group = self.groups[(nx, ny)]
                        positions_to_clear.update(group.stones)
        
        # 清除缓存
        for pos in positions_to_clear:
            if pos in self.groups:
                del self.groups[pos]
    
    def get_liberties(self, x: int, y: int) -> int:
        """获取棋子或棋块的气数"""
        group = self.get_group(x, y)
        return group.num_liberties() if group else 0
    
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """获取邻接位置（上下左右）"""
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if self.is_valid_position(nx, ny):
                neighbors.append((nx, ny))
        return neighbors
    
    def get_star_points(self) -> List[Tuple[int, int]]:
        """获取星位坐标"""
        return self.STAR_POINTS.get(self.size, [])
    
    def get_handicap_positions(self, handicap: int) -> List[Tuple[int, int]]:
        """获取让子位置"""
        if self.size in self.HANDICAP_POSITIONS:
            return self.HANDICAP_POSITIONS[self.size].get(handicap, [])
        return []
    
    def to_string(self) -> str:
        """转换为字符串表示（用于调试）"""
        result = []
        letters = 'ABCDEFGHJKLMNOPQRST'[:self.size]
        
        # 添加列标
        result.append('   ' + ' '.join(letters))
        
        # 添加行
        for i, row in enumerate(self.grid):
            row_num = str(self.size - i).rjust(2)
            row_str = ' '.join(
                '.' if cell == '' else 
                'X' if cell == 'black' else 
                'O' for cell in row
            )
            result.append(f'{row_num} {row_str} {row_num}')
        
        # 添加底部列标
        result.append('   ' + ' '.join(letters))
        
        return '\n'.join(result)
    
    def get_hash(self) -> str:
        """
        获取棋盘的哈希值（用于检测重复局面）
        使用Zobrist hashing会更高效，但这里简化实现
        """
        board_str = ''.join(''.join(row) for row in self.grid)
        return hashlib.sha256(board_str.encode()).hexdigest()
    
    def get_all_groups(self) -> List[Group]:
        """获取棋盘上所有的棋块"""
        groups_found = []
        visited = set()
        
        for y in range(self.size):
            for x in range(self.size):
                if (x, y) not in visited and not self.is_empty(x, y):
                    group = self.get_group(x, y)
                    if group:
                        groups_found.append(group)
                        visited.update(group.stones)
        
        return groups_found
    
    def count_stones(self) -> Dict[str, int]:
        """统计棋盘上各色棋子数量"""
        counts = {
            StoneColor.BLACK.value: 0,
            StoneColor.WHITE.value: 0,
            StoneColor.EMPTY.value: 0
        }
        
        for row in self.grid:
            for cell in row:
                if cell in counts:
                    counts[cell] += 1
        
        return counts
