"""
围棋游戏UI模块
"""

from .board_canvas import BoardCanvas, BoardRenderer
from .panels import InfoPanel, ControlPanel, AnalysisPanel, NavigationPanel
from .dialogs import (
    NewGameDialog, SettingsDialog, AboutDialog,
    SaveGameDialog, LoadGameDialog, SGFDialog
)
from .themes import Theme, ThemeManager
from .animations import AnimationManager, StoneAnimation, CaptureAnimation
from .game_tree import GameTreeWindow
from .help import RulesHelpDialog, TutorialDialog
from .joseki_dictionary import JosekiDictionaryWindow
from .pattern_search import PatternSearchWindow
from .problem_library import ProblemLibraryWindow

__all__ = [
    # 棋盘
    'BoardCanvas', 'BoardRenderer',
    
    # 面板
    'InfoPanel', 'ControlPanel', 'AnalysisPanel', 'NavigationPanel',
    
    # 对话框
    'NewGameDialog', 'SettingsDialog', 'AboutDialog',
    'SaveGameDialog', 'LoadGameDialog', 'SGFDialog',
    
    # 主题
    'Theme', 'ThemeManager',
    
    # 动画
    'AnimationManager', 'StoneAnimation', 'CaptureAnimation',

    # 棋谱树
    'GameTreeWindow',

    # 帮助/教程
    'RulesHelpDialog', 'TutorialDialog',

    # 定式/棋型
    'JosekiDictionaryWindow', 'PatternSearchWindow', 'ProblemLibraryWindow'
]
