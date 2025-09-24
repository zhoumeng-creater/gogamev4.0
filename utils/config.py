"""
配置管理模块
处理游戏配置的读取、保存和管理
"""

import os
import json
import copy
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path


class ThemeType(Enum):
    """主题类型"""
    WOOD = "wood"
    MODERN = "modern"
    DARK = "dark"
    CUSTOM = "custom"


class LanguageCode(Enum):
    """语言代码"""
    CHINESE = "zh"
    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"


@dataclass
class DisplayConfig:
    """显示配置"""
    theme: str = "wood"
    show_coordinates: bool = True
    show_move_numbers: bool = False
    show_last_move: bool = True
    highlight_legal_moves: bool = False
    board_opacity: float = 1.0
    stone_style: str = "realistic"  # realistic, simple, cartoon
    animation_enabled: bool = True
    animation_speed: float = 0.5


@dataclass
class SoundConfig:
    """音效配置"""
    enabled: bool = True
    volume: float = 0.7
    stone_sound: bool = True
    capture_sound: bool = True
    clock_sound: bool = True
    warning_sound: bool = True
    button_sound: bool = True
    voice_announce: bool = False


@dataclass
class GameRulesConfig:
    """游戏规则配置"""
    default_rules: str = "chinese"
    default_board_size: int = 19
    default_komi: float = 7.5
    default_handicap: int = 0
    allow_suicide: bool = False
    super_ko_rule: bool = True


@dataclass
class AIConfig:
    """AI配置"""
    default_level: str = "medium"
    thinking_time: float = 1.0
    show_analysis: bool = False
    show_win_rate: bool = False
    show_best_moves: bool = False
    analysis_depth: int = 3
    use_opening_book: bool = True
    use_neural_network: bool = False
    gpu_enabled: bool = False
    threads: int = 4


@dataclass
class NetworkConfig:
    """网络配置"""
    auto_connect: bool = False
    server_address: str = "localhost"
    server_port: int = 9999
    username: str = ""
    auto_match: bool = False
    show_rating: bool = True


@dataclass
class StorageConfig:
    """存储配置"""
    auto_save: bool = True
    auto_save_interval: int = 60  # 秒
    save_path: str = "./saves"
    sgf_path: str = "./sgf"
    cloud_sync: bool = False
    cloud_provider: str = "none"  # none, google, dropbox, onedrive
    max_saves: int = 100
    compress_saves: bool = True


@dataclass
class HotkeyConfig:
    """快捷键配置"""
    new_game: str = "Ctrl+N"
    open_game: str = "Ctrl+O"
    save_game: str = "Ctrl+S"
    undo: str = "Ctrl+Z"
    redo: str = "Ctrl+Y"
    pass_turn: str = "P"
    resign: str = "R"
    hint: str = "H"
    analyze: str = "A"
    settings: str = "Ctrl+,"
    fullscreen: str = "F11"
    quit: str = "Ctrl+Q"


@dataclass
class GameConfig:
    """完整游戏配置"""
    version: str = "2.0.0"
    language: str = "zh"
    
    # 子配置
    display: DisplayConfig = field(default_factory=DisplayConfig)
    sound: SoundConfig = field(default_factory=SoundConfig)
    rules: GameRulesConfig = field(default_factory=GameRulesConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    
    # 用户偏好
    recent_files: List[str] = field(default_factory=list)
    favorite_openings: List[str] = field(default_factory=list)
    window_geometry: str = "1200x800+100+100"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameConfig':
        """从字典创建"""
        # 处理子配置
        if 'display' in data and isinstance(data['display'], dict):
            data['display'] = DisplayConfig(**data['display'])
        if 'sound' in data and isinstance(data['sound'], dict):
            data['sound'] = SoundConfig(**data['sound'])
        if 'rules' in data and isinstance(data['rules'], dict):
            data['rules'] = GameRulesConfig(**data['rules'])
        if 'ai' in data and isinstance(data['ai'], dict):
            data['ai'] = AIConfig(**data['ai'])
        if 'network' in data and isinstance(data['network'], dict):
            data['network'] = NetworkConfig(**data['network'])
        if 'storage' in data and isinstance(data['storage'], dict):
            data['storage'] = StorageConfig(**data['storage'])
        if 'hotkeys' in data and isinstance(data['hotkeys'], dict):
            data['hotkeys'] = HotkeyConfig(**data['hotkeys'])
        
        return cls(**data)


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG_FILE = "config.json"
    USER_CONFIG_DIR = ".go_master"
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file or self._get_default_config_path()
        self.config = self.load_config()
        self._observers = []
        self._backup_config = None
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 优先使用用户目录
        user_dir = Path.home() / self.USER_CONFIG_DIR
        user_dir.mkdir(exist_ok=True)
        return str(user_dir / self.DEFAULT_CONFIG_FILE)
    
    def load_config(self) -> GameConfig:
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return GameConfig.from_dict(data)
            except Exception as e:
                print(f"加载配置失败: {e}")
        
        # 返回默认配置
        return GameConfig()
    
    def save_config(self, backup: bool = True) -> bool:
        """
        保存配置
        
        Args:
            backup: 是否备份旧配置
        
        Returns:
            是否成功
        """
        try:
            # 备份
            if backup and os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.bak"
                with open(self.config_file, 'r') as src:
                    with open(backup_file, 'w') as dst:
                        dst.write(src.read())
            
            # 保存
            os.makedirs(os.path.dirname(self.config_file) or '.', exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            
            self._notify_observers('config_saved')
            return True
            
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键（支持点号分隔的嵌套键）
            value: 配置值
            save: 是否立即保存
        
        Returns:
            是否成功
        """
        try:
            keys = key.split('.')
            target = self.config
            
            # 导航到目标属性的父对象
            for k in keys[:-1]:
                if hasattr(target, k):
                    target = getattr(target, k)
                else:
                    return False
            
            # 设置值
            final_key = keys[-1]
            if hasattr(target, final_key):
                setattr(target, final_key, value)
                
                if save:
                    self.save_config()
                
                self._notify_observers(f'config_changed:{key}', value)
                return True
                
        except Exception as e:
            print(f"设置配置失败: {e}")
        
        return False
    
    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        self._backup_config = copy.deepcopy(self.config)
        self.config = GameConfig()
        self.save_config()
        self._notify_observers('config_reset')
    
    def restore_backup(self) -> bool:
        """恢复备份配置"""
        if self._backup_config:
            self.config = copy.deepcopy(self._backup_config)
            self.save_config()
            self._notify_observers('config_restored')
            return True
        return False
    
    def export_config(self, file_path: str) -> bool:
        """导出配置到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """从文件导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.config = GameConfig.from_dict(data)
                self.save_config()
                self._notify_observers('config_imported')
                return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
    
    def add_observer(self, observer) -> None:
        """添加配置变更观察者"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer) -> None:
        """移除观察者"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_observers(self, event: str, data: Any = None) -> None:
        """通知所有观察者"""
        for observer in self._observers:
            if hasattr(observer, 'on_config_change'):
                observer.on_config_change(event, data)
    
    def validate_config(self) -> List[str]:
        """
        验证配置合法性
        
        Returns:
            错误信息列表
        """
        errors = []
        
        # 验证音量范围
        if not 0 <= self.config.sound.volume <= 1:
            errors.append("音量必须在0到1之间")
        
        # 验证棋盘大小
        if self.config.rules.default_board_size not in [9, 13, 19]:
            errors.append("棋盘大小必须是9、13或19")
        
        # 验证贴目
        if self.config.rules.default_komi < 0:
            errors.append("贴目不能为负数")
        
        # 验证让子数
        if not 0 <= self.config.rules.default_handicap <= 9:
            errors.append("让子数必须在0到9之间")
        
        return errors