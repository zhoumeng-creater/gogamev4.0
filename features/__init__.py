"""
功能模块初始化文件
提供复盘、分析、教学等高级功能
"""

from .replay import (
    ReplayManager, 
    ReplayViewer, 
    MoveTree,
    Variation,
    Comment
)

from .analysis import (
    AnalysisEngine,
    PositionAnalyzer,
    MistakeDetector,
    SuggestionEngine,
    WinrateGraph
)

from .joseki import (
    JosekiDatabase,
    JosekiSequence,
    JosekiMatcher,
    JosekiExplorer,
    JosekiTrainer
)

from .teaching import (
    TeachingSystem,
    RulesTutorial,
    BasicTutorial,
    TacticalPuzzles,
    InteractiveLesson,
    ProgressTracker
)

from .network import (
    NetworkGame,
    GameServer,
    GameClient,
    MatchMaker,
    NetworkProtocol
)

__all__ = [
    # 复盘系统
    'ReplayManager', 'ReplayViewer', 'MoveTree', 'Variation', 'Comment',
    
    # 分析引擎
    'AnalysisEngine', 'PositionAnalyzer', 'MistakeDetector', 
    'SuggestionEngine', 'WinrateGraph',
    
    # 定式库
    'JosekiDatabase', 'JosekiSequence', 'JosekiMatcher', 
    'JosekiExplorer', 'JosekiTrainer',
    
    # 教学系统
    'TeachingSystem', 'RulesTutorial', 'BasicTutorial',
    'TacticalPuzzles', 'InteractiveLesson', 'ProgressTracker',
    
    # 网络对战
    'NetworkGame', 'GameServer', 'GameClient', 
    'MatchMaker', 'NetworkProtocol'
]