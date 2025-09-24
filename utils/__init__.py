"""
工具模块初始化文件
整合所有工具类，提供统一的接口
"""

from .config import ConfigManager, GameConfig
from .sound import SoundManager
from .sgf import SGFParser, SGFGame
from .timer import Timer, TimeControl, TimeSystem, TimeSettings
from .translator import Translator, get_translator, set_global_language, t
from .storage import StorageManager, GameSave, CloudStorage
from .statistics import Statistics, GameStats, PlayerStats

# 工具函数
import os
import sys


def resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径，支持开发环境和打包后的环境"""
    try:
        # PyInstaller创建临时文件夹并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


# 版本信息
__version__ = '2.0.0'
__author__ = 'Go Master Team'


__all__ = [
    # 配置管理
    'ConfigManager', 'GameConfig',
    
    # 音效管理
    'SoundManager',
    
    # SGF处理
    'SGFParser', 'SGFGame',
    
    # 计时器
    'Timer', 'TimeControl', 'TimeSystem', 'TimeSettings',
    
    # 翻译系统
    'Translator', 'get_translator', 'set_global_language', 't',
    
    # 存储管理
    'StorageManager', 'GameSave', 'CloudStorage',
    
    # 统计系统
    'Statistics', 'GameStats', 'PlayerStats',
    
    # 工具函数
    'resource_path'
]