"""
AI模块初始化文件
提供统一的AI接口和工厂类
"""

from .base import AIPlayer, Move, AILevel
from .simple_ai import RandomAI, GreedyAI
from .search_ai import MinimaxAI, MonteCarloAI, MCTSNode
from .pattern_ai import PatternAI, JosekiAI, TacticalAI
from .neural_ai import NeuralNetAI, NeuralNetConfig

class AIFactory:
    """AI工厂类 - 用于创建不同类型和难度的AI"""
    
    # AI级别映射
    AI_MAPPING = {
        'easy': RandomAI,
        'medium': GreedyAI,
        'hard': MinimaxAI,
        'expert': PatternAI,
        'joseki': JosekiAI,
        'tactical': TacticalAI,
        'mcts': MonteCarloAI,
        'neural': NeuralNetAI
    }
    
    @classmethod
    def create_ai(cls, level: str, color: str, board_size: int = 19, **kwargs) -> AIPlayer:
        """
        创建AI实例
        
        Args:
            level: AI难度级别
            color: 棋子颜色 (black/white)
            board_size: 棋盘大小
            **kwargs: 额外参数
        
        Returns:
            AIPlayer: AI实例
        """
        ai_class = cls.AI_MAPPING.get(level, GreedyAI)
        
        # 特殊参数处理
        if level == 'hard':
            kwargs.setdefault('max_depth', 3)
        elif level == 'mcts':
            kwargs.setdefault('simulations', 1000)
        elif level == 'neural':
            kwargs.setdefault('model_path', None)
        
        return ai_class(color=color, board_size=board_size, **kwargs)
    
    @classmethod
    def get_available_levels(cls) -> list:
        """获取可用的AI级别列表"""
        return list(cls.AI_MAPPING.keys())
    
    @classmethod
    def get_level_description(cls, level: str) -> str:
        """获取AI级别描述"""
        descriptions = {
            'easy': '随机AI - 适合初学者',
            'medium': '贪心AI - 基础战术',
            'hard': '极小极大AI - 深度搜索',
            'expert': '模式AI - 定式与战术结合',
            'joseki': '定式AI - 专注于开局定式',
            'tactical': '战术AI - 专注于局部战斗',
            'mcts': '蒙特卡洛AI - 强力搜索',
            'neural': '神经网络AI - 深度学习'
        }
        return descriptions.get(level, '未知难度')


__all__ = [
    'AIPlayer', 'Move', 'AILevel',
    'RandomAI', 'GreedyAI',
    'MinimaxAI', 'MonteCarloAI', 'MCTSNode',
    'PatternAI', 'JosekiAI', 'TacticalAI',
    'NeuralNetAI', 'NeuralNetConfig',
    'AIFactory'
]