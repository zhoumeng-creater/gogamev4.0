"""
SGF棋谱处理模块
实现SGF格式的读取、解析和生成
"""

import re
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum


class SGFProperty(Enum):
    """SGF属性枚举"""
    # 根节点属性
    FILE_FORMAT = "FF"  # 文件格式
    GAME_TYPE = "GM"     # 游戏类型（1=围棋）
    CHARSET = "CA"       # 字符集
    APPLICATION = "AP"   # 应用程序
    
    # 游戏信息
    BOARD_SIZE = "SZ"    # 棋盘大小
    KOMI = "KM"          # 贴目
    HANDICAP = "HA"      # 让子数
    RULESET = "RU"       # 规则
    TIME_LIMIT = "TM"    # 时限
    OVERTIME = "OT"      # 读秒
    
    # 对局信息
    PLAYER_BLACK = "PB"  # 黑方姓名
    PLAYER_WHITE = "PW"  # 白方姓名
    BLACK_RANK = "BR"    # 黑方段位
    WHITE_RANK = "WR"    # 白方段位
    BLACK_TEAM = "BT"    # 黑方队伍
    WHITE_TEAM = "WT"    # 白方队伍
    
    # 结果信息
    RESULT = "RE"        # 对局结果
    DATE = "DT"          # 对局日期
    PLACE = "PC"         # 对局地点
    EVENT = "EV"         # 赛事名称
    ROUND = "RO"         # 轮次
    
    # 着手相关
    BLACK_MOVE = "B"     # 黑棋着手
    WHITE_MOVE = "W"     # 白棋着手
    ADD_BLACK = "AB"     # 添加黑子
    ADD_WHITE = "AW"     # 添加白子
    ADD_EMPTY = "AE"     # 清空点位
    
    # 标记和注释
    COMMENT = "C"        # 注释
    NODE_NAME = "N"      # 节点名称
    MARK = "MA"          # X标记
    CIRCLE = "CR"        # 圆圈标记
    SQUARE = "SQ"       # 方块标记
    TRIANGLE = "TR"     # 三角标记
    LABEL = "LB"         # 文字标签
    
    # 时间相关
    BLACK_TIME = "BL"    # 黑方剩余时间
    WHITE_TIME = "WL"    # 白方剩余时间
    BLACK_MOVES = "OB"   # 黑方剩余着数
    WHITE_MOVES = "OW"   # 白方剩余着数


@dataclass
class SGFNode:
    """SGF节点"""
    properties: Dict[str, List[str]] = field(default_factory=dict)
    children: List['SGFNode'] = field(default_factory=list)
    parent: Optional['SGFNode'] = None
    
    def add_property(self, prop: str, value: Union[str, List[str]]) -> None:
        """添加属性"""
        if isinstance(value, str):
            value = [value]
        self.properties[prop] = value
    
    def get_property(self, prop: str, default: Any = None) -> Any:
        """获取属性"""
        values = self.properties.get(prop, [])
        if not values:
            return default
        return values[0] if len(values) == 1 else values
    
    def has_property(self, prop: str) -> bool:
        """检查是否有属性"""
        return prop in self.properties
    
    def add_child(self, child: 'SGFNode') -> None:
        """添加子节点"""
        child.parent = self
        self.children.append(child)
    
    def is_move(self) -> bool:
        """是否是着手节点"""
        return 'B' in self.properties or 'W' in self.properties
    
    def get_move(self) -> Optional[Tuple[str, int, int]]:
        """获取着手信息"""
        if 'B' in self.properties:
            coord = self.properties['B'][0]
            if coord:  # 非虚手
                x, y = self._parse_coordinate(coord)
                return ('black', x, y)
        elif 'W' in self.properties:
            coord = self.properties['W'][0]
            if coord:  # 非虚手
                x, y = self._parse_coordinate(coord)
                return ('white', x, y)
        return None
    
    def _parse_coordinate(self, coord: str) -> Tuple[int, int]:
        """解析SGF坐标"""
        if len(coord) != 2:
            return (-1, -1)
        x = ord(coord[0]) - ord('a')
        y = ord(coord[1]) - ord('a')
        return (x, y)


@dataclass
class SGFGame:
    """SGF棋谱"""
    root: SGFNode = field(default_factory=SGFNode)
    current: SGFNode = None
    
    def __post_init__(self):
        if self.current is None:
            self.current = self.root
    
    def get_info(self) -> Dict[str, Any]:
        """获取棋谱信息"""
        return {
            'board_size': int(self.root.get_property('SZ', 19)),
            'player_black': self.root.get_property('PB', 'Black'),
            'player_white': self.root.get_property('PW', 'White'),
            'black_rank': self.root.get_property('BR', ''),
            'white_rank': self.root.get_property('WR', ''),
            'komi': float(self.root.get_property('KM', 7.5)),
            'handicap': int(self.root.get_property('HA', 0)),
            'result': self.root.get_property('RE', ''),
            'date': self.root.get_property('DT', ''),
            'event': self.root.get_property('EV', ''),
            'place': self.root.get_property('PC', ''),
            'rules': self.root.get_property('RU', 'Chinese'),
        }
    
    def get_moves(self) -> List[Tuple[str, int, int]]:
        """获取主变化的所有着手"""
        moves = []
        node = self.root
        
        while node:
            move = node.get_move()
            if move:
                moves.append(move)
            
            # 沿着第一个分支前进
            if node.children:
                node = node.children[0]
            else:
                break
        
        return moves
    
    def add_move(self, color: str, x: int, y: int, comment: str = "") -> SGFNode:
        """添加着手"""
        node = SGFNode()
        
        # 添加着手属性
        if x < 0 or y < 0:  # 虚手
            coord = ""
        else:
            coord = chr(ord('a') + x) + chr(ord('a') + y)
        
        prop = 'B' if color == 'black' else 'W'
        node.add_property(prop, coord)
        
        # 添加注释
        if comment:
            node.add_property('C', comment)
        
        # 连接到当前节点
        self.current.add_child(node)
        self.current = node
        
        return node
    
    def navigate_to_move(self, move_number: int) -> bool:
        """导航到指定手数"""
        self.current = self.root
        count = 0
        
        while self.current.children and count < move_number:
            self.current = self.current.children[0]
            if self.current.is_move():
                count += 1
        
        return count == move_number


class SGFParser:
    """SGF解析器"""
    
    @staticmethod
    def parse(sgf_text: str) -> SGFGame:
        """
        解析SGF文本
        
        Args:
            sgf_text: SGF格式文本
        
        Returns:
            SGFGame对象
        """
        # 移除空白和换行
        sgf_text = sgf_text.strip()
        
        # 基本验证
        if not sgf_text.startswith('(') or not sgf_text.endswith(')'):
            raise ValueError("Invalid SGF format")
        
        # 移除外层括号
        sgf_text = sgf_text[1:-1]
        
        game = SGFGame()
        current_node = game.root
        
        # 解析节点
        nodes = SGFParser._split_nodes(sgf_text)
        
        for node_text in nodes:
            if node_text.startswith(';'):
                node_text = node_text[1:]  # 移除分号
                
                node = SGFNode()
                SGFParser._parse_node_properties(node_text, node)
                
                if current_node == game.root and not game.root.properties:
                    # 第一个节点，更新根节点
                    game.root.properties = node.properties
                else:
                    # 添加为子节点
                    current_node.add_child(node)
                    current_node = node
        
        return game
    
    @staticmethod
    def _split_nodes(text: str) -> List[str]:
        """分割节点"""
        nodes = []
        current = []
        bracket_depth = 0
        
        for char in text:
            if char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
            elif char == ';' and bracket_depth == 0:
                if current:
                    nodes.append(''.join(current))
                    current = []
            
            current.append(char)
        
        if current:
            nodes.append(''.join(current))
        
        return nodes
    
    @staticmethod
    def _parse_node_properties(text: str, node: SGFNode) -> None:
        """解析节点属性"""
        # 属性正则表达式
        prop_pattern = r'([A-Z]+)(\[[^\]]*\])+'
        
        for match in re.finditer(prop_pattern, text):
            prop_name = match.group(1)
            
            # 提取所有值
            value_pattern = r'\[([^\]]*)\]'
            values = re.findall(value_pattern, match.group(0))
            
            node.properties[prop_name] = values
    
    @staticmethod
    def generate(game: SGFGame) -> str:
        """
        生成SGF文本
        
        Args:
            game: SGFGame对象
        
        Returns:
            SGF格式文本
        """
        sgf = "("
        sgf += SGFParser._node_to_sgf(game.root)
        
        # 添加所有着手
        node = game.root
        while node.children:
            node = node.children[0]
            sgf += SGFParser._node_to_sgf(node)
        
        sgf += ")"
        return sgf
    
    @staticmethod
    def _node_to_sgf(node: SGFNode) -> str:
        """节点转SGF文本"""
        if not node.properties:
            return ""
        
        sgf = ";"
        
        for prop, values in node.properties.items():
            for value in values:
                sgf += f"{prop}[{value}]"
        
        return sgf
    
    @staticmethod
    def save_to_file(game: SGFGame, file_path: str) -> bool:
        """
        保存到文件
        
        Args:
            game: SGFGame对象
            file_path: 文件路径
        
        Returns:
            是否成功
        """
        try:
            sgf_text = SGFParser.generate(game)
            
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sgf_text)
            
            return True
            
        except Exception as e:
            print(f"保存SGF失败: {e}")
            return False
    
    @staticmethod
    def load_from_file(file_path: str) -> Optional[SGFGame]:
        """
        从文件加载
        
        Args:
            file_path: 文件路径
        
        Returns:
            SGFGame对象或None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sgf_text = f.read()
            
            return SGFParser.parse(sgf_text)
            
        except Exception as e:
            print(f"加载SGF失败: {e}")
            return None
    
    @staticmethod
    def create_from_moves(moves: List[Tuple[int, int, str]],
                         board_size: int = 19,
                         player_black: str = "Black",
                         player_white: str = "White",
                         komi: float = 7.5,
                         **kwargs) -> SGFGame:
        """
        从着手列表创建SGF
        
        Args:
            moves: 着手列表 [(x, y, color), ...]
            board_size: 棋盘大小
            player_black: 黑方姓名
            player_white: 白方姓名
            komi: 贴目
            **kwargs: 其他属性
        
        Returns:
            SGFGame对象
        """
        game = SGFGame()
        
        # 设置根节点属性
        game.root.add_property('FF', '4')  # SGF版本
        game.root.add_property('GM', '1')  # 围棋
        game.root.add_property('SZ', str(board_size))
        game.root.add_property('PB', player_black)
        game.root.add_property('PW', player_white)
        game.root.add_property('KM', str(komi))
        game.root.add_property('AP', 'GoMaster:2.0')
        
        # 添加日期
        if 'date' not in kwargs:
            kwargs['date'] = datetime.now().strftime('%Y-%m-%d')
        game.root.add_property('DT', kwargs['date'])
        
        # 添加其他属性
        for key, value in kwargs.items():
            if key.upper() in [e.value for e in SGFProperty]:
                game.root.add_property(key.upper(), str(value))
        
        # 添加着手
        for x, y, color in moves:
            game.add_move(color, x, y)
        
        # 重置当前节点到根
        game.current = game.root
        
        return game