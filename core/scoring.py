"""
计分系统模块
实现中国规则、日本规则等不同的计分方式
"""

from typing import Dict, List, Tuple, Set, Optional, Any
from abc import ABC, abstractmethod
from .board import Board, StoneColor
from .territory import Territory


class ScoringSystem(ABC):
    """计分系统基类"""
    
    def __init__(self, komi: float = 7.5):
        """
        初始化计分系统
        
        Args:
            komi: 贴目数
        """
        self.komi = komi
    
    @abstractmethod
    def calculate_score(self, board: Board, 
                       captured_black: int, 
                       captured_white: int,
                       dead_stones: Set[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        计算得分
        
        Args:
            board: 棋盘
            captured_black: 黑方被提子数
            captured_white: 白方被提子数
            dead_stones: 死子集合
        
        Returns:
            包含得分信息的字典
        """
        pass
    
    def _calculate_territory(self, board: Board, 
                           dead_stones: Set[Tuple[int, int]] = None) -> Dict[str, int]:
        """
        计算地盘
        
        Args:
            board: 棋盘
            dead_stones: 死子集合
        
        Returns:
            各方地盘数
        """
        territory = Territory(board)
        
        # 如果有死子，先将其从棋盘上移除（仅用于计算）
        temp_board = board.copy()
        if dead_stones:
            for x, y in dead_stones:
                temp_board.remove_stone(x, y)
            territory = Territory(temp_board)
        
        return territory.calculate_territory()
    
    def _count_stones(self, board: Board, 
                     dead_stones: Set[Tuple[int, int]] = None) -> Dict[str, int]:
        """
        数子
        
        Args:
            board: 棋盘
            dead_stones: 死子集合
        
        Returns:
            各方活子数
        """
        black_stones = 0
        white_stones = 0
        
        for y in range(board.size):
            for x in range(board.size):
                stone = board.get_stone(x, y)
                if stone == StoneColor.BLACK.value:
                    if not dead_stones or (x, y) not in dead_stones:
                        black_stones += 1
                elif stone == StoneColor.WHITE.value:
                    if not dead_stones or (x, y) not in dead_stones:
                        white_stones += 1
        
        return {
            'black': black_stones,
            'white': white_stones
        }


class ChineseScoring(ScoringSystem):
    """中国规则计分系统（数子法）"""
    
    def calculate_score(self, board: Board,
                       captured_black: int,
                       captured_white: int,
                       dead_stones: Set[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        中国规则计分
        子空皆地，活子+围空=总得分
        
        Args:
            board: 棋盘
            captured_black: 黑方被提子数（中国规则不使用）
            captured_white: 白方被提子数（中国规则不使用）
            dead_stones: 死子集合
        
        Returns:
            得分信息
        """
        # 计算地盘（包括空点）
        territory = self._calculate_territory(board, dead_stones)
        
        # 数活子
        stones = self._count_stones(board, dead_stones)
        
        # 中国规则：活子数 + 围空数
        black_score = stones['black'] + territory['black']
        white_score = stones['white'] + territory['white']
        
        # 贴目（中国规则通常贴3.75子，相当于7.5目）
        white_score += self.komi / 2  # 转换为子数
        
        # 计算胜负
        if black_score > white_score:
            winner = 'black'
            margin = black_score - white_score
        elif white_score > black_score:
            winner = 'white'
            margin = white_score - black_score
        else:
            winner = 'draw'
            margin = 0
        
        return {
            'black_score': black_score,
            'white_score': white_score,
            'black_territory': territory['black'],
            'white_territory': territory['white'],
            'black_stones': stones['black'],
            'white_stones': stones['white'],
            'winner': winner,
            'margin': margin,
            'scoring_method': 'chinese'
        }


class JapaneseScoring(ScoringSystem):
    """日本规则计分系统（数目法）"""
    
    def calculate_score(self, board: Board,
                       captured_black: int,
                       captured_white: int,
                       dead_stones: Set[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        日本规则计分
        围空+提子=总得分（不计算活子）
        
        Args:
            board: 棋盘
            captured_black: 黑方被提子数
            captured_white: 白方被提子数
            dead_stones: 死子集合
        
        Returns:
            得分信息
        """
        # 计算地盘（仅空点）
        territory = self._calculate_territory(board, dead_stones)
        
        # 计算死子
        dead_black = 0
        dead_white = 0
        if dead_stones:
            for x, y in dead_stones:
                stone = board.get_stone(x, y)
                if stone == StoneColor.BLACK.value:
                    dead_black += 1
                elif stone == StoneColor.WHITE.value:
                    dead_white += 1
        
        # 日本规则：围空 + 提子 + 对方死子
        black_score = territory['black'] + captured_white + dead_white
        white_score = territory['white'] + captured_black + dead_black
        
        # 贴目（日本规则通常贴6.5目）
        white_score += self.komi
        
        # 计算胜负
        if black_score > white_score:
            winner = 'black'
            margin = black_score - white_score
        elif white_score > black_score:
            winner = 'white'
            margin = white_score - black_score
        else:
            winner = 'draw'
            margin = 0
        
        return {
            'black_score': black_score,
            'white_score': white_score,
            'black_territory': territory['black'],
            'white_territory': territory['white'],
            'black_captures': captured_white + dead_white,
            'white_captures': captured_black + dead_black,
            'winner': winner,
            'margin': margin,
            'scoring_method': 'japanese'
        }


class AGAScoring(ScoringSystem):
    """AGA（美国围棋协会）规则计分系统"""
    
    def calculate_score(self, board: Board,
                       captured_black: int,
                       captured_white: int,
                       dead_stones: Set[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        AGA规则计分
        类似中国规则，但白方需要多贴还最后通过的虚手数
        
        Args:
            board: 棋盘
            captured_black: 黑方被提子数
            captured_white: 白方被提子数
            dead_stones: 死子集合
        
        Returns:
            得分信息
        """
        # 基本同中国规则
        territory = self._calculate_territory(board, dead_stones)
        stones = self._count_stones(board, dead_stones)
        
        # AGA规则：活子数 + 围空数
        black_score = stones['black'] + territory['black']
        white_score = stones['white'] + territory['white']
        
        # 贴目（AGA规则通常贴7.5目）
        white_score += self.komi / 2  # 转换为子数
        
        # 计算胜负
        if black_score > white_score:
            winner = 'black'
            margin = black_score - white_score
        elif white_score > black_score:
            winner = 'white'
            margin = white_score - black_score
        else:
            winner = 'draw'
            margin = 0
        
        return {
            'black_score': black_score,
            'white_score': white_score,
            'black_territory': territory['black'],
            'white_territory': territory['white'],
            'black_stones': stones['black'],
            'white_stones': stones['white'],
            'winner': winner,
            'margin': margin,
            'scoring_method': 'aga'
        }


class IngScoring(ScoringSystem):
    """应氏规则计分系统"""
    
    def __init__(self, komi: float = 8.0):
        """应氏规则使用8点贴目"""
        super().__init__(komi)
    
    def calculate_score(self, board: Board,
                       captured_black: int,
                       captured_white: int,
                       dead_stones: Set[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        应氏规则计分
        填满计点，黑184点获胜，白177点获胜
        
        Args:
            board: 棋盘
            captured_black: 黑方被提子数
            captured_white: 白方被提子数
            dead_stones: 死子集合
        
        Returns:
            得分信息
        """
        # 使用中国规则的基本方法
        territory = self._calculate_territory(board, dead_stones)
        stones = self._count_stones(board, dead_stones)
        
        black_score = stones['black'] + territory['black']
        white_score = stones['white'] + territory['white']
        
        # 应氏规则的特殊贴点
        white_score += self.komi / 2
        
        # 应氏规则的胜负判定
        total_points = board.size * board.size
        black_target = (total_points + 1) / 2  # 黑方需要超过一半
        white_target = (total_points - 1) / 2  # 白方需要接近一半
        
        if black_score >= black_target:
            winner = 'black'
            margin = black_score - black_target
        elif white_score >= white_target:
            winner = 'white'
            margin = white_score - white_target
        else:
            winner = 'draw'
            margin = 0
        
        return {
            'black_score': black_score,
            'white_score': white_score,
            'black_territory': territory['black'],
            'white_territory': territory['white'],
            'black_stones': stones['black'],
            'white_stones': stones['white'],
            'winner': winner,
            'margin': margin,
            'scoring_method': 'ing'
        }


class NewZealandScoring(ScoringSystem):
    """新西兰规则计分系统"""
    
    def calculate_score(self, board: Board,
                       captured_black: int,
                       captured_white: int,
                       dead_stones: Set[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        新西兰规则计分
        类似中国规则但贴目方式不同
        
        Args:
            board: 棋盘
            captured_black: 黑方被提子数
            captured_white: 白方被提子数
            dead_stones: 死子集合
        
        Returns:
            得分信息
        """
        # 基本同中国规则
        chinese_scoring = ChineseScoring(self.komi)
        result = chinese_scoring.calculate_score(board, captured_black, captured_white, dead_stones)
        result['scoring_method'] = 'new_zealand'
        
        return result


def create_scoring_system(rule_set: str, komi: float = None) -> ScoringSystem:
    """
    创建计分系统
    
    Args:
        rule_set: 规则集名称
        komi: 贴目数（如果为None则使用默认值）
    
    Returns:
        对应的计分系统实例
    """
    default_komi = {
        'chinese': 7.5,
        'japanese': 6.5,
        'aga': 7.5,
        'ing': 8.0,
        'new_zealand': 7.5
    }
    
    if komi is None:
        komi = default_komi.get(rule_set, 7.5)
    
    if rule_set == 'japanese':
        return JapaneseScoring(komi)
    elif rule_set == 'aga':
        return AGAScoring(komi)
    elif rule_set == 'ing':
        return IngScoring(komi)
    elif rule_set == 'new_zealand':
        return NewZealandScoring(komi)
    else:  # 默认中国规则
        return ChineseScoring(komi)