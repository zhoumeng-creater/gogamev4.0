"""
围棋游戏核心模块
"""

from .board import Board, Stone, Group
from .rules import Rules, MoveResult
from .game import Game, GamePhase, GameState, Move, MoveSequence
from .territory import Territory, DeadStoneAnalyzer
from .scoring import ScoringSystem, ChineseScoring, JapaneseScoring

__all__ = [
    'Board', 'Stone', 'Group',
    'Rules', 'MoveResult', 
    'Game', 'GamePhase', 'GameState','Move', 'MoveSequence',
    'Territory', 'DeadStoneAnalyzer',
    'ScoringSystem', 'ChineseScoring', 'JapaneseScoring'
]