"""
围棋大师 Go Master 4.0
主程序入口
整合所有模块，提供完整的围棋游戏功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import threading
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from core import (
    Board, Rules, Game, Territory, ScoringSystem,
    GamePhase, MoveResult, GameState
)
from core.board import StoneColor

# 导入UI模块
from ui import (
    BoardCanvas, InfoPanel, ControlPanel, AnalysisPanel,
    NewGameDialog, SettingsDialog, AboutDialog, SaveGameDialog,
    Theme, ThemeManager, AnimationManager, GameTreeWindow,
    RulesHelpDialog, TutorialDialog,
    JosekiDictionaryWindow, PatternSearchWindow, ProblemLibraryWindow
)
from ui.fonts import apply_app_fonts
from ui.widgets import (
    ModernWindow, ModernMenuBar, ModernMenu, ModernScrollbar, 
    ModernTitleBar, ModernButton
)
from ui.translator import Translator, set_global_language

# 导入AI模块
from ai import AIFactory, AIPlayer, AILevel

# 导入功能模块
from features import (
    ReplayManager, AnalysisEngine, JosekiDatabase,
    TeachingSystem, NetworkGame
)

# 导入工具模块
from utils import (
    ConfigManager, SoundManager, SGFParser, Timer,
    Statistics, StorageManager, TimeControl,
    resource_path, GameConfig, TimeSettings, GameStats,
    get_content_db, get_user_db
)
from utils.hotkeys import load_hotkeys, hotkey_to_tk_sequences, hotkey_to_display


class GoMasterApp:
    """围棋大师主应用程序"""
    
    VERSION = "4.3"
    APP_NAME_KEY = "app_name"
    
    def __init__(self, root: tk.Tk):
        """
        初始化应用程序
        
        Args:
            root: Tkinter根窗口
        """
        self.root = root
        
        # 初始化管理器
        self._init_managers()
        
        # 设置窗口
        self._setup_window()
        
        # 游戏状态
        self.game: Optional[Game] = None
        self.ai_black: Optional[AIPlayer] = None
        self.ai_white: Optional[AIPlayer] = None
        self.is_ai_thinking = False
        self.game_paused = False
        self._current_save_path: Optional[str] = None
        
        # UI组件
        self.board_canvas: Optional[BoardCanvas] = None
        self.info_panel: Optional[InfoPanel] = None
        self.control_panel: Optional[ControlPanel] = None
        self.analysis_panel: Optional[AnalysisPanel] = None
        
        # 功能模块
        self.replay_manager: Optional[ReplayManager] = None
        self.analysis_engine: Optional[AnalysisEngine] = None
        self.teaching_system: Optional[TeachingSystem] = None
        self.network_game: Optional[NetworkGame] = None
        
        # 创建UI
        self._create_ui()
        self._create_menu()
        self._bind_shortcuts()
        
        # 加载上次的游戏或开始新游戏
        if not self._load_last_game():
            self._start_default_game()
        
        # 设置关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 启动自动保存
        self._setup_auto_save()
    
    def _init_managers(self):
        """初始化各种管理器"""
        # 配置管理
        self.config_manager = ConfigManager()
        config = self.config_manager.config

        # 内容数据库
        self.content_db = get_content_db()

        # 用户数据库
        self.user_db = get_user_db()
        
        # 翻译系统
        self.translator = Translator(config.language)
        set_global_language(self.translator.language)

        # 快捷键配置
        self.hotkeys = load_hotkeys()
        
        # 音效管理
        self.sound_manager = SoundManager(self.config_manager)
        
        # 统计系统
        self.statistics = Statistics(user_db=self.user_db)
        
        # 存储管理
        self.storage_manager = StorageManager(self.config_manager)
        
        # 主题管理
        self.theme_manager = ThemeManager()
        
        # 设置当前主题
        theme_name = config.display.theme if hasattr(config.display, 'theme') else 'wood'
        self.theme_manager.set_current_theme(theme_name)

        # 字体设置（优先使用项目内字体，其次系统字体）
        try:
            self._font_bundle = apply_app_fonts(
                self.root,
                self.theme_manager,
                language=getattr(config, "language", None),
            )
        except Exception:
            self._font_bundle = None
        
        # 注意：删除了这里的 AnimationManager 创建代码
        # AnimationManager 会在 BoardCanvas 中创建，因为它需要 canvas 对象
        # 我们可以保存动画配置，稍后传递给 BoardCanvas
        self.animation_config = {
            'enabled': config.display.animation_enabled if hasattr(config.display, 'animation_enabled') else True,
            'speed': config.display.animation_speed if hasattr(config.display, 'animation_speed') else 1.0
        }
        
        # 定式数据库
        self.joseki_db = JosekiDatabase()
    
    def _setup_window(self):
        """设置主窗口"""
        # 设置标题和图标
        self.root.title(self.translator.get(self.APP_NAME_KEY))
        
        try:
            icon_path = resource_path(os.path.join("assets", "icons", "app.ico"))
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # 恢复窗口大小和位置
        geometry = self.config_manager.get('window_geometry', '1200x800+100+100')
        self.root.geometry(geometry)
        
        # 设置最小尺寸
        self.root.minsize(800, 600)
        
        # 设置主题
        self.root.tk_setPalette(background='#f0f0f0')
    
    def _create_ui(self):
        """创建用户界面"""
        # 创建主框架
        parent = self.root.content_area if hasattr(self.root, 'content_area') else self.root
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame = main_frame
        
        # 创建分割面板
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧面板（信息/控制/分析）：做成可滚动容器，避免窗口高度不够导致“局势”等区域被挤压不可见
        left_container = ttk.Frame(paned)
        paned.add(left_container, weight=1)

        self._left_sidebar_canvas = tk.Canvas(
            left_container,
            highlightthickness=0,
            borderwidth=0,
            bg=self.theme_manager.get_current_theme().ui_panel_background,
        )
        
        left_scrollbar = ModernScrollbar(
            left_container, 
            orient='vertical', 
            command=self._left_sidebar_canvas.yview,
            theme=self.theme_manager.get_current_theme(),
            match_widget=self._left_sidebar_canvas,
        )
        self._left_sidebar_canvas.configure(yscrollcommand=left_scrollbar.set)
        
        self.left_scrollbar = left_scrollbar # Store for theme updates

        left_scrollbar.pack(side='right', fill='y')
        self._left_sidebar_canvas.pack(side='left', fill='both', expand=True)

        left_frame = ttk.Frame(self._left_sidebar_canvas)
        self._left_sidebar_window = self._left_sidebar_canvas.create_window((0, 0), window=left_frame, anchor='nw')

        def _on_left_frame_configure(event):
            self._left_sidebar_canvas.configure(scrollregion=self._left_sidebar_canvas.bbox('all'))

        def _on_left_canvas_configure(event):
            # 让内部 Frame 宽度跟随 Canvas，避免出现横向滚动条/裁切
            self._left_sidebar_canvas.itemconfigure(self._left_sidebar_window, width=event.width)

        left_frame.bind('<Configure>', _on_left_frame_configure)
        self._left_sidebar_canvas.bind('<Configure>', _on_left_canvas_configure)

        # 鼠标滚轮仅在进入左侧区域时生效
        def _on_mousewheel(event):
            try:
                delta = int(-1 * (event.delta / 120))
            except Exception:
                delta = -1 if getattr(event, 'delta', 0) > 0 else 1
            self._left_sidebar_canvas.yview_scroll(delta, 'units')

        def _bind_mousewheel(_event):
            self._left_sidebar_canvas.bind_all('<MouseWheel>', _on_mousewheel)

        def _unbind_mousewheel(_event):
            self._left_sidebar_canvas.unbind_all('<MouseWheel>')

        self._left_sidebar_canvas.bind('<Enter>', _bind_mousewheel)
        self._left_sidebar_canvas.bind('<Leave>', _unbind_mousewheel)
        
        # 信息面板
        self.info_panel = InfoPanel(
            left_frame,
            translator=self.translator,
            on_settings_click=self.show_settings
        )
        self.info_panel.pack(fill=tk.BOTH, expand=False, pady=(0, 5))
        
        # 控制面板
        self.control_panel = ControlPanel(
            left_frame,
            translator=self.translator,
            on_pass=self.on_pass,
            on_resign=self.on_resign,
            on_undo=self.on_undo,
            on_redo=self.on_redo,
            on_hint=self.on_hint,
            on_analyze=self.on_analyze,
            on_score=self.on_score,
            on_end_game=self.on_end_game,
            on_estimate=self.on_estimate,
            on_pause=self.on_pause,
            on_show_coordinates=self.set_show_coordinates,
            on_show_move_numbers=self.set_show_move_numbers,
            on_show_territory=self.set_show_territory,
            on_show_influence=self.set_show_influence,
            show_coordinates=self.config_manager.get('display.show_coordinates', True),
            show_move_numbers=self.config_manager.get('display.show_move_numbers', False),
            show_territory=self.config_manager.get('display.show_territory', False),
            show_influence=self.config_manager.get('display.show_influence', False),
        )
        self.control_panel.pack(fill=tk.BOTH, expand=False, pady=(0, 5))
        
        # 分析面板
        self.analysis_panel = AnalysisPanel(
            left_frame,
            translator=self.translator
        )
        self.analysis_panel.pack(fill=tk.BOTH, expand=True)
        
        # 中间面板（棋盘）
        center_frame = ttk.Frame(paned)
        paned.add(center_frame, weight=3)
        
        # 获取当前主题
        current_theme = self.theme_manager.get_current_theme()

        # 棋盘画布
        self.board_canvas = BoardCanvas(
            center_frame,
            board_size=19,
            theme=current_theme,
            show_coordinates=self.config_manager.get('display.show_coordinates', True),
        )

        self.board_canvas.on_click = self.on_board_click
        self.board_canvas.on_hover = self.on_board_hover
        
        self.board_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 右侧面板（可选，用于额外功能）
        if self.config_manager.get('display.show_side_panel', False):
            right_frame = ttk.Frame(paned)
            paned.add(right_frame, weight=1)
            # TODO: 添加游戏树、变化图等
        
        # 配置动画管理器（BoardCanvas 内部已创建）
        if hasattr(self, 'animation_config') and hasattr(self.board_canvas, 'animation_manager'):
            am = self.board_canvas.animation_manager
            am.enable_animations = self.animation_config.get('enabled', True)
            am.animation_speed = self.animation_config.get('speed', 1.0)

    def _create_menu(self):
        """创建菜单栏"""
        # remove native menu
        self.root.config(menu="")

        if getattr(self, "menubar", None):
            try:
                self.menubar.destroy()
            except Exception:
                pass
        
        current_theme = self.theme_manager.get_current_theme()
        
        # Create ModernMenuBar
        parent = self.root.content_area if hasattr(self.root, 'content_area') else self.root
        menubar = ModernMenuBar(parent, theme=current_theme)
        if getattr(self, "main_frame", None) is not None:
            menubar.pack(side="top", fill="x", before=self.main_frame)
        else:
            menubar.pack(side="top", fill="x")
        self.menubar = menubar
        
        # 文件菜单
        file_menu = ModernMenu(menubar, theme=current_theme)
        menubar.add_cascade(label=self.translator.get('file'), menu=file_menu)
        
        file_menu.add_command(
            label=self.translator.get('new_game'),
            command=self.new_game,
            shortcut=self._get_hotkey_display("new_game")
        )
        file_menu.add_separator()
        
        file_menu.add_command(
            label=self.translator.get('open'),
            command=self.open_game,
            shortcut=self._get_hotkey_display("open_game")
        )
        file_menu.add_command(
            label=self.translator.get('save'),
            command=self.save_game,
            shortcut=self._get_hotkey_display("save_game")
        )
        file_menu.add_command(
            label=self.translator.get('save_as'),
            command=self.save_game_as,
            shortcut=self._get_hotkey_display("save_game_as")
        )
        file_menu.add_separator()
        
        file_menu.add_command(
            label=self.translator.get('import_sgf'),
            command=self.import_sgf
        )
        file_menu.add_command(
            label=self.translator.get('export_sgf'),
            command=self.export_sgf
        )
        file_menu.add_separator()
        
        # 最近文件
        recent_menu = ModernMenu(file_menu, theme=current_theme)
        file_menu.add_cascade(label=self.translator.get('recent_files'), menu=recent_menu)
        self._update_recent_files_menu(recent_menu)
        self.recent_menu = recent_menu
        
        file_menu.add_separator()
        file_menu.add_command(
            label=self.translator.get('quit'),
            command=self.on_closing,
            shortcut=self._get_hotkey_display("quit")
        )
        
        # 编辑菜单
        edit_menu = ModernMenu(menubar, theme=current_theme)
        menubar.add_cascade(label=self.translator.get('edit'), menu=edit_menu)
        
        edit_menu.add_command(
            label=self.translator.get('undo'),
            command=self.on_undo,
            shortcut=self._get_hotkey_display("undo")
        )
        edit_menu.add_command(
            label=self.translator.get('redo'),
            command=self.on_redo,
            shortcut=self._get_hotkey_display("redo")
        )
        edit_menu.add_separator()
        
        edit_menu.add_command(
            label=self.translator.get('copy_sgf'),
            command=self.copy_sgf,
            shortcut=self._get_hotkey_display("copy_sgf")
        )
        edit_menu.add_command(
            label=self.translator.get('paste_sgf'),
            command=self.paste_sgf,
            shortcut=self._get_hotkey_display("paste_sgf")
        )
        edit_menu.add_separator()
        
        edit_menu.add_command(
            label=self.translator.get('clear_board'),
            command=self.clear_board
        )
        edit_menu.add_command(
            label=self.translator.get('teaching_mode'),
            command=self.toggle_teaching_mode,
            shortcut=self._get_hotkey_display("teaching_mode")
        )
        
        # 游戏菜单
        game_menu = ModernMenu(menubar, theme=current_theme)
        menubar.add_cascade(label=self.translator.get('game'), menu=game_menu)
        
        game_menu.add_command(
            label=self.translator.get('pass'),
            command=self.on_pass,
            shortcut=self._get_hotkey_display("pass")
        )
        game_menu.add_command(
            label=self.translator.get('resign'),
            command=self.on_resign,
            shortcut=self._get_hotkey_display("resign")
        )
        game_menu.add_separator()
        
        game_menu.add_command(
            label=self.translator.get('hint'),
            command=self.on_hint,
            shortcut=self._get_hotkey_display("hint")
        )
        game_menu.add_command(
            label=self.translator.get('analyze'),
            command=self.on_analyze,
            shortcut=self._get_hotkey_display("analyze")
        )
        game_menu.add_command(
            label=self.translator.get('score'),
            command=self.on_score,
            shortcut=self._get_hotkey_display("score")
        )
        game_menu.add_command(
            label=self.translator.get('end_game'),
            command=self.on_end_game,
            shortcut=self._get_hotkey_display("end_game")
        )
        game_menu.add_separator()
        
        game_menu.add_command(
            label=self.translator.get('pause'),
            command=self.on_pause,
            shortcut=self._get_hotkey_display("pause")
        )
        
        # 视图菜单
        view_menu = ModernMenu(menubar, theme=current_theme)
        menubar.add_cascade(label=self.translator.get('view'), menu=view_menu)
        
        # 显示选项
        self.show_coords_var = tk.BooleanVar(
            value=self.config_manager.get('display.show_coordinates', True)
        )
        view_menu.add_checkbutton(
            label=self.translator.get('show_coordinates'),
            variable=self.show_coords_var,
            command=self.toggle_coordinates
        )
        
        self.show_move_nums_var = tk.BooleanVar(
            value=self.config_manager.get('display.show_move_numbers', False)
        )
        view_menu.add_checkbutton(
            label=self.translator.get('show_move_numbers'),
            variable=self.show_move_nums_var,
            command=self.toggle_move_numbers
        )
        
        self.show_last_move_var = tk.BooleanVar(
            value=self.config_manager.get('display.show_last_move', True)
        )
        view_menu.add_checkbutton(
            label=self.translator.get('show_last_move'),
            variable=self.show_last_move_var,
            command=self.toggle_last_move
        )
        
        view_menu.add_separator()
        
        view_menu.add_command(
            label=self.translator.get('fullscreen'),
            command=self.toggle_fullscreen,
            shortcut=self._get_hotkey_display("fullscreen")
        )
        view_menu.add_command(
            label=self.translator.get('zoom_in'),
            command=self.zoom_in,
            shortcut=self._get_hotkey_display("zoom_in")
        )
        view_menu.add_command(
            label=self.translator.get('zoom_out'),
            command=self.zoom_out,
            shortcut=self._get_hotkey_display("zoom_out")
        )
        view_menu.add_command(
            label=self.translator.get('reset_view'),
            command=self.reset_view,
            shortcut=self._get_hotkey_display("reset_view")
        )
        
        # 工具菜单
        tools_menu = ModernMenu(menubar, theme=current_theme)
        menubar.add_cascade(label=self.translator.get('tools'), menu=tools_menu)
        
        tools_menu.add_command(
            label=self.translator.get('game_tree'),
            command=self.show_game_tree
        )
        tools_menu.add_command(
            label=self.translator.get('position_analysis'),
            command=self.show_position_analysis
        )
        tools_menu.add_separator()
        
        tools_menu.add_command(
            label=self.translator.get('joseki_dictionary'),
            command=self.show_joseki_dictionary
        )
        tools_menu.add_command(
            label=self.translator.get('pattern_search'),
            command=self.show_pattern_search
        )
        tools_menu.add_separator()
        
        tools_menu.add_command(
            label=self.translator.get('problem_library'),
            command=self.show_problem_library
        )
        tools_menu.add_command(
            label=self.translator.get('statistics'),
            command=self.show_statistics
        )
        tools_menu.add_separator()

        # 语言切换
        language_menu = ModernMenu(tools_menu, theme=current_theme)
        tools_menu.add_cascade(label=self.translator.get('language'), menu=language_menu)
        self.language_var = tk.StringVar(value=getattr(self.translator, 'language', 'zh'))
        for code in self.translator.get_available_languages():
            language_menu.add_radiobutton(
                label=self.translator.get(f"language_name_{code}", code),
                variable=self.language_var,
                value=code,
                command=lambda c=code: self._apply_language(c),
            )

        tools_menu.add_separator()
        
        tools_menu.add_command(
            label=self.translator.get('settings'),
            command=self.show_settings,
            shortcut=self._get_hotkey_display("settings")
        )
        
        # 帮助菜单
        help_menu = ModernMenu(menubar, theme=current_theme)
        menubar.add_cascade(label=self.translator.get('help'), menu=help_menu)
        
        help_menu.add_command(
            label=self.translator.get('rules_help'),
            command=self.show_rules_help
        )
        help_menu.add_command(
            label=self.translator.get('tutorial'),
            command=self.show_tutorial
        )
        help_menu.add_separator()
        
        help_menu.add_command(
            label=self.translator.get('shortcuts'),
            command=self.show_shortcuts,
            shortcut=self._get_hotkey_display("show_shortcuts")
        )
        help_menu.add_separator()
        
        help_menu.add_command(
            label=self.translator.get('about'),
            command=self.show_about
        )

    def _get_hotkey_display(self, action: str) -> str:
        if not getattr(self, "hotkeys", None):
            return ""
        return hotkey_to_display(self.hotkeys.get(action))

    def _get_hotkey_sequences(self, action: str) -> List[str]:
        if not getattr(self, "hotkeys", None):
            return []
        return hotkey_to_tk_sequences(self.hotkeys.get(action))
    
    def _bind_shortcuts(self):
        """绑定快捷键"""
        actions = {
            "new_game": self.new_game,
            "open_game": self.open_game,
            "save_game": self.save_game,
            "save_game_as": self.save_game_as,
            "quit": self.on_closing,
            "undo": self.on_undo,
            "redo": self.on_redo,
            "copy_sgf": self.copy_sgf,
            "paste_sgf": self.paste_sgf,
            "zoom_in": self.zoom_in,
            "zoom_out": self.zoom_out,
            "reset_view": self.reset_view,
            "settings": self.show_settings,
            "show_shortcuts": self.show_shortcuts,
            "fullscreen": self.toggle_fullscreen,
            "pause": self.on_pause,
            "pass": self.on_pass,
            "resign": self.on_resign,
            "hint": self.on_hint,
            "analyze": self.on_analyze,
            "score": self.on_score,
            "end_game": self.on_end_game,
            "teaching_mode": self.toggle_teaching_mode,
        }

        for action, handler in actions.items():
            for sequence in self._get_hotkey_sequences(action):
                self.root.bind(sequence, lambda _e, h=handler: h())
    
    def _setup_auto_save(self):
        """设置自动保存"""
        if self.config_manager.get('storage.auto_save'):
            def auto_save():
                if self.game and not self.game.is_ended():
                    self.save_game(auto=True)
            
            self.storage_manager.set_auto_save_callback(auto_save)
    
    def new_game(self):
        """开始新游戏"""
        # 如果有正在进行的游戏，询问是否保存
        if self.game and not self.game.is_ended():
            response = messagebox.askyesnocancel(
                self.translator.get('confirm'),
                self.translator.get('save_current_game')
            )
            
            if response is None:  # 取消
                return
            elif response:  # 保存
                self.save_game()
        
        # 显示新游戏对话框
        dialog = NewGameDialog(
            self.root,
            translator=self.translator,
            config=self.config_manager.config,
            theme=self.theme_manager.get_current_theme(),
        )
        
        if dialog.result:
            # 创建新游戏
            self._start_new_game(dialog.result)

    def _start_default_game(self):
        """启动时创建一个默认对局（不弹出新对局对话框）。"""
        settings = {
            'mode': 'human_vs_human',
            'black_player': self.translator.get('black'),
            'white_player': self.translator.get('white'),
            'board_size': self.config_manager.get('rules.default_board_size', 19),
            'rules': self.config_manager.get('rules.default_rules', 'chinese'),
            'komi': self.config_manager.get('rules.default_komi', 7.5),
            'handicap': self.config_manager.get('rules.default_handicap', 0),
            'time_control': 'none',
        }
        self._start_new_game(settings, initial=True)
    
    def _start_new_game(self, settings: Dict[str, Any], initial: bool = False):
        """
        开始新游戏
        
        Args:
            settings: 游戏设置
        """
        # 停止当前游戏的计时器
        if self.game:
            self.game.cleanup()
        self._current_save_path = None
        
        # 创建新游戏
        self.game = Game(
            board_size=settings['board_size'],
            rules=settings['rules'],
            komi=settings['komi'],
            handicap=settings['handicap']
        )
        
        # 设置游戏信息
        black_name = settings.get('black_player') or self.translator.get('black_player')
        white_name = settings.get('white_player') or self.translator.get('white_player')
        self.game.set_player_info(black_name=black_name, white_name=white_name)
        
        # 设置计时器
        if settings.get('time_control') != 'none':
            time_settings = TimeSettings(
                control_type=TimeControl(settings['time_control']),
                main_time=settings.get('main_time', 1800),
                byoyomi_time=settings.get('byoyomi_time', 30),
                byoyomi_periods=settings.get('byoyomi_periods', 3),
                canadian_time=settings.get('canadian_time', 300),
                canadian_stones=settings.get('canadian_stones', 25)
            )
            
            self.game.set_time_control(time_settings)
        
        # 创建AI玩家
        self.ai_black = None
        self.ai_white = None
        
        mode = settings.get('mode', 'human_vs_human')
        
        if mode in ['ai_vs_human', 'ai_vs_ai']:
            level = settings.get('black_ai_level', 'medium')
            self.ai_black = AIFactory.create_ai(level, 'black', settings['board_size'])
        
        if mode in ['human_vs_ai', 'ai_vs_ai']:
            level = settings.get('white_ai_level', 'medium')
            self.ai_white = AIFactory.create_ai(level, 'white', settings['board_size'])
        
        # 更新UI
        self.board_canvas.set_board_size(settings['board_size'])
        self.board_canvas.clear_board()
        self.update_display()
        
        if not initial:
            # 播放开始音效
            self.sound_manager.play('game_start')
            # 记录统计
            self.statistics.record_game_start(settings)
        
        # 如果AI执黑，让AI先下
        if self.ai_black:
            self.root.after(500, self.ai_move)
    
    def on_board_click(self, x: int, y: int):
        """
        处理棋盘点击
        
        Args:
            x: 横坐标
            y: 纵坐标
        """
        if not self.game or self.game.is_ended():
            return

        # 教学/推演模式：交替落子（黑白交替），不走规则，不记录正式历史
        if getattr(self, '_teaching_mode', False):
            try:
                next_color = getattr(self, '_teaching_next_color', StoneColor.BLACK.value)
                # 覆盖原位置
                self.game.board.remove_stone(x, y)
                self._teaching_move_number = getattr(self, '_teaching_move_number', 0) + 1
                self._teaching_move_number = max(1, self._teaching_move_number)
                # 直接放置并附带手数，便于显示手数
                self.game.board.place_stone(x, y, next_color, move_number=self._teaching_move_number)
                self.game.last_move = (x, y)
                self.game.move_number = self._teaching_move_number
                # 交替颜色
                self._teaching_next_color = StoneColor.opposite(next_color)
                self.game.current_player = self._teaching_next_color
                # 重新刷新界面，确保手数/当前玩家同步
                self.update_display()
            except Exception:
                return
            return

        if self.is_ai_thinking:
            return
        
        # 检查是否是当前玩家的回合
        current_player = self.game.get_current_player()
        
        if (current_player == 'black' and self.ai_black) or \
           (current_player == 'white' and self.ai_white):
            return
        
        # 尝试落子
        self.make_move(x, y)
    
    def on_board_hover(self, x: int, y: int):
        """
        处理棋盘悬停
        
        Args:
            x: 横坐标
            y: 纵坐标
        """
        if not self.game or self.game.is_ended():
            return
        
        # 显示落子预览
        if self.config_manager.get('display.show_move_preview', True):
            current_player = self.game.get_current_player()
            self.board_canvas.show_preview(x, y, current_player)
    
    def make_move(self, x: int, y: int):
        """
        执行落子
        
        Args:
            x: 横坐标
            y: 纵坐标
        """
        if not self.game:
            return
        
        # 执行落子
        result = self.game.place_stone(x, y)
        
        if result == MoveResult.SUCCESS:
            # 播放落子音效
            self.sound_manager.play('place_stone')
            
            # 更新显示
            self.update_display()
            
            # 检查是否有吃子
            captures = self.game.get_last_captures()
            if captures:
                self.sound_manager.play('capture')
                # 注：吃子动画由 BoardCanvas/AnimationManager 自身负责；此处不再调用旧接口，避免崩溃
            
            # 检查游戏是否结束
            if self.game.is_ended():
                self.on_game_end()
            else:
                # AI回合
                current_player = self.game.get_current_player()
                if (current_player == 'black' and self.ai_black) or \
                   (current_player == 'white' and self.ai_white):
                    self.root.after(500, self.ai_move)
        
        elif result == MoveResult.ILLEGAL:
            # 非法落子
            self.sound_manager.play('illegal')
            messagebox.showwarning(
                self.translator.get('warning'),
                self.translator.get('invalid_move')
            )
        
        elif result == MoveResult.KO:
            # 劫争
            self.sound_manager.play('illegal')
            messagebox.showwarning(
                self.translator.get('warning'),
                self.translator.get('ko_violation')
            )
        
        elif result == MoveResult.SUICIDE:
            # 自杀
            self.sound_manager.play('illegal')
            messagebox.showwarning(
                self.translator.get('warning'),
                self.translator.get('suicide_move')
            )
    
    def ai_move(self):
        """AI落子"""
        if not self.game or self.game.is_ended():
            return
        
        current_player = self.game.get_current_player()
        ai_player = self.ai_black if current_player == 'black' else self.ai_white
        
        if not ai_player:
            return
        
        self.is_ai_thinking = True
        self.info_panel.show_thinking(True)
        
        # 在线程中执行AI计算
        def ai_think():
            game_info = self.game.get_game_info()
            move = ai_player.get_move(self.game.board, game_info)
            
            # 在主线程中执行落子
            self.root.after(0, lambda: self.ai_move_complete(move))
        
        thread = threading.Thread(target=ai_think, daemon=True)
        thread.start()
    
    def ai_move_complete(self, move: Optional[Tuple[int, int]]):
        """AI落子完成"""
        self.is_ai_thinking = False
        self.info_panel.show_thinking(False)
        
        if move:
            self.make_move(move[0], move[1])
        else:
            # AI虚手
            self.on_pass()
    
    def on_pass(self):
        """虚手"""
        if not self.game or self.game.is_ended():
            return
        
        entered_scoring = self.game.pass_turn()
        self.sound_manager.play('pass')
        
        # 连续虚手：按规则应进入数子/结算，这里直接结束对局并自动数子
        if entered_scoring or getattr(self.game, 'phase', None) == GamePhase.SCORING:
            self.on_end_game(prompt=False)
            return

        self.update_display()
            
        # AI回合
        current_player = self.game.get_current_player()
        if (current_player == 'black' and self.ai_black) or \
           (current_player == 'white' and self.ai_white):
            self.root.after(500, self.ai_move)
    
    def on_resign(self):
        """认输"""
        if not self.game or self.game.is_ended():
            return
        
        # 确认认输
        response = messagebox.askyesno(
            self.translator.get('confirm'),
            self.translator.get('confirm_resign')
        )
        
        if response:
            self.game.resign()
            self.sound_manager.play('resign')
            self.on_game_end()
    
    def on_undo(self):
        """悔棋"""
        if not self.game or self.game.is_ended():
            return
        
        if self.game.undo_move():
            self.sound_manager.play('button_click')
            self.update_display()
    
    def on_redo(self):
        """重做"""
        if not self.game:
            return
        
        if self.game.redo_move():
            self.sound_manager.play('button_click')
            self.update_display()
    
    def on_hint(self):
        """提示"""
        if not self.game or self.game.is_ended():
            return
        
        # 使用AI计算最佳着法
        current_player = self.game.get_current_player()
        hint_ai = AIFactory.create_ai('expert', current_player, self.game.board_size)
        
        def calculate_hint():
            game_info = self.game.get_game_info()
            move = hint_ai.get_move(self.game.board, game_info)
            
            if move:
                # 显示提示
                self.root.after(0, lambda: self.board_canvas.show_hint(move[0], move[1]))
        
        thread = threading.Thread(target=calculate_hint, daemon=True)
        thread.start()
    
    def on_analyze(self):
        """分析局面"""
        if not self.game:
            return
        
        # 创建分析引擎
        if not self.analysis_engine:
            self.analysis_engine = AnalysisEngine()
        
        # 分析当前局面
        analysis = self.analysis_engine.analyze_position(
            self.game.board,
            self.game.get_current_player()
        )

        # 分析：专注于“推荐着法/搜索信息”，不直接覆盖“局势(胜率/地盘)”显示
        if self.analysis_panel:
            # 组装推荐列表
            best_moves = getattr(analysis, 'best_moves', []) or []
            suggestions: List[Dict[str, Any]] = []
            for m in best_moves:
                try:
                    move_text = m.get_coordinate_string() if hasattr(m, 'get_coordinate_string') else f"{m.x},{m.y}"
                except Exception:
                    move_text = ""

                try:
                    wr = float(getattr(m, 'winrate', 0.0) or 0.0)
                except Exception:
                    wr = 0.0
                wr_percent = wr * 100.0 if wr <= 1.0 else wr

                try:
                    visits = int(getattr(m, 'visits', 0) or 0)
                except Exception:
                    visits = 0

                suggestions.append({'move': move_text, 'winrate': wr_percent, 'visits': visits})

            self.analysis_panel.update_suggestions(suggestions)

            try:
                depth = int(getattr(analysis, 'analysis_depth', 0) or 0)
            except Exception:
                depth = 0
            try:
                nodes = int(sum(int(s.get('visits', 0) or 0) for s in suggestions))
            except Exception:
                nodes = 0
            self.analysis_panel.update_analysis_info(thinking_time=0.0, nodes=nodes, depth=depth)

            self._scroll_left_sidebar_to(self.analysis_panel)

    def on_estimate(self):
        """形势估计：快速评估胜率/势力，不做完整搜索。"""
        if not self.game:
            return

        board = self.game.board

        # 1) 快速胜率（以黑方视角），失败则回退到 50%
        winrate_percent = 50.0
        try:
            eval_ai = AIFactory.create_ai('expert', 'black', self.game.board_size)
            eval_result = eval_ai.evaluate_position(board)
            winrate_percent = float(getattr(eval_result, 'winning_probability', 0.5) or 0.5) * 100.0
        except Exception:
            winrate_percent = 50.0

        # 2) 势力/地盘估计
        black_terr = 0
        white_terr = 0
        influence_map = None
        try:
            territory = Territory(board)
            influence_map = territory.calculate_influence()
            terr_est = territory.estimate_territory_by_influence()
            black_terr = int(terr_est.get('black', 0) or 0)
            white_terr = int(terr_est.get('white', 0) or 0)
        except Exception:
            pass

        # 3) 更新左侧“局势”面板（不清空推荐着法，避免覆盖“分析”的输出）
        if self.analysis_panel:
            self.analysis_panel.update_winrate(winrate_percent)
            self.analysis_panel.update_territory(black_terr, white_terr)
            self._scroll_left_sidebar_to(self.analysis_panel)

        # 4) 如果用户开启了显示选项，刷新棋盘叠加层
        if influence_map is not None and self.board_canvas:
            if self.config_manager.get('display.show_influence', False):
                self.board_canvas.show_influence_map(influence_map)
        self._refresh_board_overlays()

    def _scroll_left_sidebar_to(self, widget: Optional[tk.Widget]):
        """让左侧滚动面板滚动到指定控件（用于“分析/形势估计”后自动展示局势区域）。"""
        canvas = getattr(self, '_left_sidebar_canvas', None)
        if not canvas or not widget:
            return

        try:
            canvas.update_idletasks()
            widget.update_idletasks()
        except Exception:
            pass

        # 如果已经可见，就不跳动
        try:
            canvas_top = canvas.winfo_rooty()
            canvas_bottom = canvas_top + canvas.winfo_height()
            widget_top = widget.winfo_rooty()
            widget_bottom = widget_top + widget.winfo_height()
            if widget_top >= canvas_top and widget_bottom <= canvas_bottom:
                return
        except Exception:
            pass

        try:
            # widget.winfo_y() 是相对于其父容器（left_frame）的 y 坐标
            target_y = int(widget.winfo_y())
            bbox = canvas.bbox('all')
            if not bbox:
                return
            total_height = int(bbox[3] - bbox[1])
            view_height = int(canvas.winfo_height())
            denom = max(1, total_height - view_height)
            canvas.yview_moveto(max(0.0, min(1.0, target_y / denom)))
        except Exception:
            return

    def _format_scoring_brief(self, score: Dict[str, Any]) -> str:
        """格式化数子阶段的当前领先信息（用于阶段栏）。"""
        winner = score.get('winner')
        margin = score.get('margin', score.get('difference', 0) or 0) or 0
        try:
            margin_value = float(margin)
        except Exception:
            margin_value = 0.0

        if winner not in ('black', 'white') or margin_value == 0:
            return self.translator.get('jigo')

        return self.translator.get(
            'score_lead_format',
            winner=self.translator.get(winner),
            margin=margin_value,
            points=self.translator.get('points'),
        )

    def _format_final_result_brief(self, result: Dict[str, Any]) -> str:
        """格式化对局结束结果（用于阶段栏）。"""
        winner = result.get('winner')
        diff = result.get('score_difference', 0) or 0
        try:
            diff_value = float(diff)
        except Exception:
            diff_value = 0.0

        if not winner or diff_value == 0:
            return self.translator.get('jigo')

        return self.translator.get(
            'score_result_format',
            winner=self.translator.get(winner),
            wins=self.translator.get('wins'),
            margin=diff_value,
            points=self.translator.get('points'),
        )

    def _update_phase_display(self):
        """在特定阶段（数子/结束）覆盖 InfoPanel 的阶段显示，提供更直观的信息。"""
        if not self.game or not self.info_panel:
            return

        # 教学/推演模式下优先提示当前模式
        if getattr(self, '_teaching_mode', False):
            self.info_panel.set_phase_text(
                f"{self.translator.get('phase')}: {self.translator.get('teaching_mode')}"
            )
            return

        phase = getattr(self.game, 'phase', None)
        if phase == GamePhase.SCORING:
            try:
                score = self.game.calculate_score()
                brief = self._format_scoring_brief(score)
                self.info_panel.set_phase_text(
                    self.translator.get(
                        'phase_detail_format',
                        phase=self.translator.get('phase'),
                        status=self.translator.get('scoring'),
                        detail=brief,
                    )
                )
            except Exception:
                return
        elif phase == GamePhase.ENDED:
            try:
                result = self.game.get_result()
                brief = self._format_final_result_brief(result)
                self.info_panel.set_phase_text(
                    self.translator.get(
                        'phase_detail_format',
                        phase=self.translator.get('phase'),
                        status=self.translator.get('ended'),
                        detail=brief,
                    )
                )
            except Exception:
                return

    def _enter_scoring_mode(self):
        """进入数子模式：点击棋子标记死活，右键或再次点击“数子”完成。"""
        if not self.game:
            return

        # 进入数子阶段
        try:
            self.game.enter_scoring_phase()
        except Exception:
            return

        # 显示死活标记界面
        try:
            self.board_canvas.enter_scoring_mode(
                on_stone_click=self.on_mark_dead_stone,
                on_done=self.on_scoring_done,
            )
        except Exception:
            return

        self.update_display()
    
    def on_score(self):
        """数子（预览）：仅计算当前盘面分数，不结束对局。"""
        if not self.game:
            return

        try:
            score = self.game.calculate_score()
        except Exception:
            messagebox.showerror(self.translator.get('error'), self.translator.get('score_failed'))
            return

        try:
            black_score = float(score.get('black_score', 0) or 0)
        except Exception:
            black_score = 0.0
        try:
            white_score = float(score.get('white_score', 0) or 0)
        except Exception:
            white_score = 0.0

        brief = self._format_scoring_brief(score)
        message = (
            f"{self.translator.get('black')}: {black_score:.1f}\n"
            f"{self.translator.get('white')}: {white_score:.1f}\n"
            f"{self.translator.get('game_result')}: {brief}"
        )

        messagebox.showinfo(self.translator.get('score'), message)

    def on_end_game(self, prompt: bool = True):
        """结束对局：自动数子并显示结果。"""
        if getattr(self, '_teaching_mode', False):
            self.toggle_teaching_mode()
            return
        if not self.game:
            return

        if getattr(self.game, 'phase', None) == GamePhase.ENDED:
            return

        if prompt:
            ok = messagebox.askyesno(
                self.translator.get('confirm'),
                self.translator.get('end_game_confirm'),
            )
            if not ok:
                return

        try:
            # 确保进入数子阶段以便 end_game 写入 result
            self.game.enter_scoring_phase()
            self.game.end_game(accept_score=True)
        except Exception:
            return

        try:
            if self.board_canvas:
                self.board_canvas.exit_scoring_mode()
        except Exception:
            pass

        self.update_display()
        self.on_game_end()
    
    def on_mark_dead_stone(self, x: int, y: int):
        """标记死子"""
        self.game.toggle_dead_stone(x, y)
        self.board_canvas.update_dead_stones(self.game.get_dead_stones())
        self._update_phase_display()
    
    def on_scoring_done(self):
        """完成数子"""
        if not self.game:
            return

        # 结束游戏并固化结果（点目结果写入 game_info.result）
        try:
            self.game.end_game(accept_score=True)
        except Exception:
            pass

        # 退出数子模式
        try:
            self.board_canvas.exit_scoring_mode()
        except Exception:
            pass

        self.update_display()
        self.on_game_end()
    
    def on_pause(self):
        """暂停/继续"""
        if not self.game:
            return
        
        self.game_paused = not self.game_paused
        
        if self.game_paused:
            self.game.pause_timers()
            self.control_panel.set_pause_text(self.translator.get('continue'))
        else:
            self.game.resume_timers()
            self.control_panel.set_pause_text(self.translator.get('pause'))
    
    def on_game_end(self):
        """游戏结束"""
        if not self.game:
            return
        
        # 播放结束音效
        self.sound_manager.play('game_end')
        
        # 记录统计
        game_stats = self.game.get_game_statistics()
        self.statistics.record_game(game_stats)
        
        # 显示结果
        result = self.game.get_result()
        self.show_game_result(result)
        
        # 自动保存棋谱
        if self.config_manager.get('storage.auto_save_sgf'):
            self.export_sgf(auto=True)
    
    def show_game_result(self, result: Dict[str, Any]):
        """显示游戏结果"""
        winner = result.get('winner')
        score_diff = result.get('score_difference', 0)
        reason = result.get('reason', '')
        
        if winner:
            message = f"{self.translator.get(winner)} {self.translator.get('wins')}"
            if score_diff:
                message += f" ({score_diff} {self.translator.get('points')})"
            if reason:
                message += f"\n{self.translator.get(reason)}"
        else:
            message = self.translator.get('jigo')
        
        messagebox.showinfo(
            self.translator.get('game_ended'),
            message
        )
    
    def update_display(self):
        """更新显示"""
        if not self.game:
            return
        
        # 更新棋盘
        try:
            # 供 BoardCanvas.update_board 在必要时从 move_history 推导手数/最后一手（例如悔棋/重做后）
            setattr(self.game.board, 'move_history', list(self.game.move_history))
        except Exception:
            pass
        self.board_canvas.update_board(self.game.board)
        self._refresh_board_overlays()
        
        # 更新信息面板
        game_info = self.game.get_game_info()
        self.info_panel.update_info(game_info)
        self._update_phase_display()
        
        # 更新控制面板状态
        is_scoring = getattr(self.game, 'phase', None) == GamePhase.SCORING
        is_teaching = getattr(self, '_teaching_mode', False)
        self.control_panel.update_buttons(
            can_undo=self.game.can_undo(),
            can_redo=self.game.can_redo(),
            is_playing=not self.game.is_ended(),
            is_scoring=is_scoring,
            is_teaching=is_teaching,
        )
    
    def save_game(self, auto: bool = False):
        """保存游戏"""
        if not self.game:
            return

        if auto:
            # 自动保存
            game_data = self.game.to_dict()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            save_id = self.storage_manager.save_game(
                game_data,
                name=self.translator.get('auto_save_name_format', timestamp=timestamp),
                tags=['auto_save']
            )
        else:
            # 手动保存：优先覆盖上次保存位置，否则进入“另存为”
            if self._current_save_path:
                self._save_sgf_to_path(self._current_save_path, show_message=True)
            else:
                self.save_game_as()
    
    def save_game_as(self):
        """另存为（面向文件保存）"""
        if not self.game:
            return

        current_dir = None
        current_name = None
        if self._current_save_path:
            try:
                current_dir = os.path.dirname(self._current_save_path)
                current_name = os.path.splitext(os.path.basename(self._current_save_path))[0]
            except Exception:
                current_dir = None
                current_name = None

        if not current_dir:
            current_dir = self.config_manager.get('storage.sgf_path', './sgf')

        dialog = SaveGameDialog(
            self.root,
            game_info=self.game.get_game_info() if self.game else {},
            translator=self.translator,
            theme=self.theme_manager.get_current_theme(),
            initial_dir=current_dir,
            initial_name=current_name,
            title=self.translator.get('save_as'),
        )

        result = getattr(dialog, "result", None)
        if not result:
            return

        file_path = result.get('file_path')
        if not file_path:
            return

        file_path = self._normalize_sgf_path(file_path)
        if os.path.exists(file_path):
            if not messagebox.askyesno(
                self.translator.get('confirm'),
                self.translator.get('confirm_overwrite_file'),
            ):
                return

        self._save_sgf_to_path(file_path, show_message=True)

    def _normalize_sgf_path(self, file_path: str) -> str:
        if not file_path:
            return file_path
        root, ext = os.path.splitext(file_path)
        if ext.lower() != ".sgf":
            return f"{root}.sgf"
        return file_path

    def _save_sgf_to_path(
        self,
        file_path: str,
        show_message: bool = False,
        update_current: bool = True,
        record_recent: bool = True,
    ) -> bool:
        if not self.game or not file_path:
            return False
        file_path = self._normalize_sgf_path(file_path)
        try:
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
            sgf_text = self.game.export_to_sgf()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sgf_text)
        except Exception:
            messagebox.showerror(
                self.translator.get('error'),
                self.translator.get('save_failed')
            )
            return False

        if update_current:
            self._current_save_path = file_path
        if record_recent:
            self._record_recent_file(file_path)
        try:
            save_dir = os.path.dirname(file_path) or '.'
            self.config_manager.set('storage.sgf_path', save_dir, save=False)
            self.config_manager.save_config()
        except Exception:
            pass

        if show_message:
            messagebox.showinfo(
                self.translator.get('info'),
                self.translator.get('game_saved')
            )
        return True

    def _record_recent_file(self, file_path: str) -> None:
        if not file_path:
            return
        try:
            normalized = os.path.abspath(file_path)
        except Exception:
            normalized = file_path

        recent_files = self.config_manager.get('recent_files', [])
        if not isinstance(recent_files, list):
            recent_files = []

        recent_files = [p for p in recent_files if p and p != normalized]
        recent_files.insert(0, normalized)
        recent_files = recent_files[:10]
        self.config_manager.set('recent_files', recent_files)

        if getattr(self, "recent_menu", None) is not None:
            self._update_recent_files_menu(self.recent_menu)

    def _normalize_ruleset(self, rules_text: Optional[str]) -> str:
        value = str(rules_text or "").lower()
        if "japan" in value:
            return "japanese"
        if "aga" in value:
            return "aga"
        if "china" in value or "chinese" in value:
            return "chinese"
        return self.config_manager.get('rules.default_rules', 'chinese')

    def _build_game_from_sgf(self, sgf_game: Any) -> Optional[Game]:
        try:
            info = sgf_game.get_info()
        except Exception:
            info = {}
        try:
            board_size = int(info.get('board_size', 19))
        except Exception:
            board_size = 19
        try:
            komi = float(info.get('komi', 7.5))
        except Exception:
            komi = 7.5
        try:
            handicap = int(info.get('handicap', 0))
        except Exception:
            handicap = 0

        rule_set = self._normalize_ruleset(info.get('rules'))
        game = Game(
            board_size=board_size,
            rules=rule_set,
            komi=komi,
            handicap=handicap,
        )
        game.set_player_info(
            black_name=info.get('player_black', 'Black'),
            white_name=info.get('player_white', 'White'),
        )

        try:
            moves = sgf_game.get_moves()
        except Exception:
            moves = []

        for color, x, y in moves:
            if color and color != game.current_player:
                game.current_player = color
            if x < 0 or y < 0:
                game.pass_turn()
            else:
                game.make_move(x, y)

        try:
            game.game_info.result = info.get('result', '')
            game.game_info.date = info.get('date', '')
        except Exception:
            pass
        return game

    def _load_sgf_from_path(self, file_path: str, set_current_path: bool = True) -> bool:
        sgf_game = SGFParser.load_from_file(file_path)
        if not sgf_game:
            messagebox.showerror(
                self.translator.get('error'),
                self.translator.get('invalid_sgf')
            )
            return False

        game = self._build_game_from_sgf(sgf_game)
        if not game:
            messagebox.showerror(
                self.translator.get('error'),
                self.translator.get('invalid_sgf')
            )
            return False
        if self.game:
            try:
                self.game.cleanup()
            except Exception:
                pass
        self.ai_black = None
        self.ai_white = None
        self.is_ai_thinking = False
        self.game_paused = False
        self.game = game
        if self.board_canvas:
            try:
                self.board_canvas.set_board_size(game.board.size)
                self.board_canvas.clear_board()
            except Exception:
                pass
        self.update_display()
        if set_current_path:
            self._current_save_path = file_path
        else:
            self._current_save_path = None
        self._record_recent_file(file_path)
        return True

    def open_game(self):
        """打开SGF文件"""
        file_path = filedialog.askopenfilename(
            defaultextension=".sgf",
            filetypes=[
                (self.translator.get('sgf_files'), "*.sgf"),
                (self.translator.get('all_files'), "*.*")
            ],
            initialdir=self.config_manager.get('storage.sgf_path', './sgf'),
        )

        if file_path:
            if self._load_sgf_from_path(file_path, set_current_path=True):
                messagebox.showinfo(
                    self.translator.get('info'),
                    self.translator.get('game_loaded')
                )
    
    def import_sgf(self):
        """导入SGF"""
        file_path = filedialog.askopenfilename(
            defaultextension=".sgf",
            filetypes=[
                (self.translator.get('sgf_files'), "*.sgf"),
                (self.translator.get('all_files'), "*.*")
            ],
            initialdir=self.config_manager.get('storage.sgf_path', './sgf'),
        )

        if file_path:
            if self._load_sgf_from_path(file_path, set_current_path=False):
                messagebox.showinfo(
                    self.translator.get('info'),
                    self.translator.get('sgf_loaded')
                )
    
    def export_sgf(self, auto: bool = False):
        """导出SGF"""
        if not self.game:
            return
        
        if auto:
            # 自动导出
            sgf_dir = self.config_manager.get('storage.sgf_path')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.translator.get('sgf_default_name_format', timestamp=timestamp)
            if not filename.lower().endswith('.sgf'):
                filename = f"{filename}.sgf"
            file_path = os.path.join(sgf_dir, filename)
        else:
            # 手动导出
            file_path = filedialog.asksaveasfilename(
                defaultextension=".sgf",
                filetypes=[
                    (self.translator.get('sgf_files'), "*.sgf"),
                    (self.translator.get('all_files'), "*.*")
                ],
                initialdir=self.config_manager.get('storage.sgf_path', './sgf'),
            )

        if file_path:
            if self._save_sgf_to_path(
                file_path,
                show_message=False,
                update_current=False,
                record_recent=not auto,
            ):
                if not auto:
                    messagebox.showinfo(
                        self.translator.get('info'),
                        self.translator.get('sgf_saved')
                    )
    
    def copy_sgf(self):
        """复制SGF到剪贴板"""
        if not self.game:
            return

        sgf_text = self.game.export_to_sgf()
        self.root.clipboard_clear()
        self.root.clipboard_append(sgf_text)
        
        messagebox.showinfo(
            self.translator.get('info'),
            self.translator.get('sgf_copied')
        )
    
    def paste_sgf(self):
        """从剪贴板粘贴SGF"""
        try:
            sgf_text = self.root.clipboard_get()
            sgf_game = SGFParser.parse(sgf_text)

            if sgf_game:
                game = self._build_game_from_sgf(sgf_game)
                if game:
                    self.game = game
                    self._current_save_path = None
                    if self.board_canvas:
                        try:
                            self.board_canvas.set_board_size(game.board.size)
                            self.board_canvas.clear_board()
                        except Exception:
                            pass
                    self.update_display()

                    messagebox.showinfo(
                        self.translator.get('info'),
                        self.translator.get('sgf_pasted')
                    )
        except:
            messagebox.showerror(
                self.translator.get('error'),
                self.translator.get('invalid_sgf')
            )
    
    def clear_board(self):
        """清空棋盘"""
        response = messagebox.askyesno(
            self.translator.get('confirm'),
            self.translator.get('confirm_clear_board')
        )
        
        if response and self.game:
            if hasattr(self.game, 'clear_board'):
                self.game.clear_board()
            else:
                try:
                    # 兼容缺少 clear_board 方法的旧 Game 实例
                    size = getattr(self.game, 'board_size', 19)
                    rules = getattr(self.game.game_info, 'rules', 'chinese')
                    komi = getattr(self.game.game_info, 'komi', 7.5)
                    handicap = getattr(self.game.game_info, 'handicap', 0)
                    self.game = Game(board_size=size, rules=rules, komi=komi, handicap=handicap)
                except Exception:
                    return
            self.update_display()
    
    def toggle_teaching_mode(self):
        """切换教学/推演模式：进入后可随意摆子，退出后不保留改动。"""
        if not self.game:
            return

        if getattr(self, '_teaching_mode', False):
            # 退出：还原备份
            backup = getattr(self, '_teaching_backup', None)
            if backup:
                try:
                    self.game = Game.from_dict(backup)
                    self.ai_black = None
                    self.ai_white = None
                except Exception:
                    pass
            self._teaching_mode = False
            self._teaching_backup = None
            self._teaching_move_number = 0
            self._teaching_next_color = StoneColor.BLACK.value
            # 恢复阶段显示
            self.update_display()
            return

        # 进入编辑模式前确认
        ui_pref = self.config_manager.get('ui', {})
        skip_prompt = ui_pref.get('skip_teaching_mode_prompt', ui_pref.get('skip_edit_mode_prompt', False))
        dont_show_again = False
        proceed = True
        if not skip_prompt:
            proceed, dont_show_again = self._confirm_teaching_mode()
            if dont_show_again:
                ui_pref['skip_teaching_mode_prompt'] = True
                self.config_manager.set('ui', ui_pref, save=False)
        if not proceed:
            return

        # 备份当前对局
        try:
            self._teaching_backup = self.game.to_dict()
        except Exception:
            return

        self._teaching_mode = True
        self._teaching_move_number = 0
        self._teaching_next_color = StoneColor.BLACK.value
        # 阶段栏提示
        try:
            if self.info_panel:
                self.info_panel.set_phase_text(f"{self.translator.get('phase')}: {self.translator.get('teaching_mode')}")
        except Exception:
            pass
        # 清除提示点等
        if self.board_canvas:
            self.board_canvas.delete('hint')
        # 刷新界面以应用禁用状态和按钮文本
        self.update_display()

    def _confirm_teaching_mode(self) -> Tuple[bool, bool]:
        """弹窗确认进入教学模式，返回 (是否进入, 是否不再提示)。"""
        top = tk.Toplevel(self.root)
        top.title(self.translator.get('teaching_mode'))
        top.grab_set()
        top.transient(self.root)
        ttk.Label(top, text=self.translator.get('teaching_mode_prompt'), wraplength=320).pack(padx=12, pady=10)
        dont_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text=self.translator.get('dont_show_again'), variable=dont_var).pack(anchor='w', padx=12, pady=(0, 10))

        result = {'ok': False}
        def on_ok():
            result['ok'] = True
            top.destroy()
        def on_cancel():
            result['ok'] = False
            top.destroy()

        btn_frame = ttk.Frame(top)
        btn_frame.pack(fill='x', pady=8)
        ttk.Button(btn_frame, text=self.translator.get('ok'), command=on_ok).pack(side='left', expand=True, padx=8)
        ttk.Button(btn_frame, text=self.translator.get('cancel'), command=on_cancel).pack(side='right', expand=True, padx=8)

        top.update_idletasks()
        top.geometry(f"+{self.root.winfo_rootx()+80}+{self.root.winfo_rooty()+80}")
        top.wait_window()
        return result['ok'], dont_var.get()

    def set_show_coordinates(self, show: bool):
        """设置坐标显示（供菜单/左侧面板共用）。"""
        self.config_manager.set('display.show_coordinates', bool(show))
        try:
            if hasattr(self, 'show_coords_var'):
                self.show_coords_var.set(bool(show))
        except Exception:
            pass
        if self.board_canvas:
            self.board_canvas.set_show_coordinates(bool(show))

    def set_show_move_numbers(self, show: bool):
        """设置手数显示（供菜单/左侧面板共用）。"""
        self.config_manager.set('display.show_move_numbers', bool(show))
        try:
            if hasattr(self, 'show_move_nums_var'):
                self.show_move_nums_var.set(bool(show))
        except Exception:
            pass
        if self.board_canvas and self.game:
            # 先同步棋盘以刷新 move_numbers 映射
            self.board_canvas.update_board(self.game.board)
            self.board_canvas.set_show_move_numbers(bool(show))

    def set_show_territory(self, show: bool):
        """设置地盘显示（需要有当前对局）。"""
        self.config_manager.set('display.show_territory', bool(show))
        if not self.game or not self.board_canvas:
            return
        if show:
            self._refresh_territory_overlay()
        else:
            self.board_canvas.hide_territory_map()

    def set_show_influence(self, show: bool):
        """设置势力显示（需要有当前对局）。"""
        self.config_manager.set('display.show_influence', bool(show))
        if not self.game or not self.board_canvas:
            return
        if show:
            self._refresh_influence_overlay()
        else:
            self.board_canvas.hide_influence_map()

    def _refresh_territory_overlay(self):
        if not self.game or not self.board_canvas:
            return
        try:
            dead = set(self.game.get_dead_stones()) if hasattr(self.game, 'get_dead_stones') else set()
            territory = Territory(self.game.board)
            territory.calculate_territory(dead_stones=dead)
            self.board_canvas.show_territory_map(territory.territory_map)
        except Exception:
            return

    def _refresh_influence_overlay(self):
        if not self.game or not self.board_canvas:
            return
        try:
            territory = Territory(self.game.board)
            influence_map = territory.calculate_influence()
            self.board_canvas.show_influence_map(influence_map)
        except Exception:
            return

    def _refresh_board_overlays(self):
        """根据当前开关刷新棋盘叠加层（地盘/势力）。"""
        if not self.game or not self.board_canvas:
            return
        if getattr(self.board_canvas, 'show_territory', False):
            self._refresh_territory_overlay()
        if getattr(self.board_canvas, 'show_influence', False):
            self._refresh_influence_overlay()
    
    def toggle_coordinates(self):
        """切换坐标显示"""
        self.set_show_coordinates(self.show_coords_var.get())
    
    def toggle_move_numbers(self):
        """切换手数显示"""
        self.set_show_move_numbers(self.show_move_nums_var.get())
    
    def toggle_last_move(self):
        """切换最后一手显示"""
        show = self.show_last_move_var.get()
        self.config_manager.set('display.show_last_move', show)
        self.board_canvas.set_highlight_last_move(show)
    
    def toggle_fullscreen(self):
        """切换全屏"""
        current = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current)
    
    def zoom_in(self):
        """放大"""
        self.board_canvas.zoom(1.1)
    
    def zoom_out(self):
        """缩小"""
        self.board_canvas.zoom(0.9)
    
    def reset_view(self):
        """重置视图"""
        self.board_canvas.reset_zoom()

    def _build_settings_dialog_config(self, config: GameConfig) -> Dict[str, Any]:
        """将 GameConfig 转为 SettingsDialog 需要的扁平字典。"""
        theme_name = getattr(config.display, "theme", "wood")
        if theme_name not in getattr(self.theme_manager, 'themes', {}):
            theme_name = self.theme_manager.get_current_theme().name

        return {
            'language': getattr(config, "language", "zh"),
            'theme': theme_name,
            'default_board_size': getattr(config.rules, "default_board_size", 19),
            'default_rules': getattr(config.rules, "default_rules", "chinese"),
            'default_komi': getattr(config.rules, "default_komi", 7.5),
            'auto_save': getattr(config.storage, "auto_save", True),
            'confirm_exit': getattr(config, "confirm_exit", True),
            'show_coordinates': getattr(config.display, "show_coordinates", True),
            'show_move_numbers': getattr(config.display, "show_move_numbers", False),
            'highlight_last_move': getattr(config.display, "show_last_move", True),
            'show_territory': getattr(config.display, "show_territory", False),
            'show_influence': getattr(config.display, "show_influence", False),
            'enable_animations': getattr(config.display, "animation_enabled", True),
            'animation_speed': getattr(config.display, "animation_speed", 1.0),
            'default_ai_level': getattr(config.ai, "default_level", "medium"),
            'ai_thinking_time': getattr(config.ai, "thinking_time", 1.0),
            'show_ai_analysis': getattr(config.ai, "show_analysis", False),
            'show_winrate': getattr(config.ai, "show_win_rate", False),
            'show_best_moves': getattr(config.ai, "show_best_moves", False),
            'auto_analyze': getattr(config.ai, "auto_analyze", False),
            'sound_enabled': getattr(config.sound, "enabled", True),
            'sound_volume': getattr(config.sound, "volume", 0.7),
            'stone_sound': getattr(config.sound, "stone_sound", True),
            'capture_sound': getattr(config.sound, "capture_sound", True),
            'time_warning_sound': getattr(config.sound, "warning_sound", True),
            'auto_save_sgf': getattr(config.storage, "auto_save_sgf", False),
            'sgf_path': getattr(config.storage, "sgf_path", "./sgf"),
            'use_gpu': getattr(config.ai, "gpu_enabled", False),
            'threads': getattr(config.ai, "threads", 4),
            'debug_mode': getattr(config, "debug_mode", False),
        }

    def _get_settings_dialog_config(self) -> Dict[str, Any]:
        return self._build_settings_dialog_config(self.config_manager.config)

    def _apply_language(self, language: str):
        """切换语言并刷新 UI 文本（菜单/左侧面板）。"""
        if not language:
            return

        self.translator.set_language(language)
        set_global_language(language)
        self.config_manager.set('language', language, save=True)

        # 语言切换时更新字体（日文优先使用日文字体）
        try:
            self._font_bundle = apply_app_fonts(
                self.root,
                self.theme_manager,
                language=language,
            )
        except Exception:
            pass

        if self.info_panel:
            self.info_panel.update_translator(self.translator)
        if self.control_panel:
            self.control_panel.update_translator(self.translator)
        if self.analysis_panel:
            self.analysis_panel.update_translator(self.translator)

        self._create_menu()
        if self.game:
            self.update_display()

        # 避免语言切换后窗口跑到后台
        self._ensure_window_foreground()

    def _apply_theme(self, theme_name: str):
        """切换主题并刷新 UI 样式。"""
        if not theme_name:
            return

        self.config_manager.set('display.theme', theme_name, save=False)
        self.theme_manager.set_current_theme(theme_name)
        theme = self.theme_manager.get_current_theme()

        # 重新应用字体和 Tk 默认样式
        try:
            self._font_bundle = apply_app_fonts(
                self.root,
                self.theme_manager,
                language=getattr(self.translator, "language", None),
            )
        except Exception:
            pass

        if self.board_canvas:
            self.board_canvas.set_theme(theme)
        if self.info_panel:
            self.info_panel.update_theme(theme)
        if self.control_panel:
            self.control_panel.update_theme(theme)
        if self.analysis_panel:
            self.analysis_panel.update_theme(theme)
        if getattr(self, "menubar", None):
            self.menubar.update_theme(theme)
        if getattr(self, "left_scrollbar", None):
            self.left_scrollbar.update_theme(theme)
        if getattr(self, "_left_sidebar_canvas", None):
            try:
                self._left_sidebar_canvas.configure(bg=theme.ui_panel_background)
            except Exception:
                pass
        if hasattr(self.root, "update_theme") and callable(getattr(self.root, "update_theme")):
            self.root.update_theme(theme)

    def _ensure_window_foreground(self):
        """将主窗口抬到前台，避免被系统窗口遮挡。"""
        def _bring():
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                # Windows 上使用 topmost 切换确保前台
                if sys.platform.startswith("win"):
                    self.root.attributes("-topmost", True)
                    self.root.after(80, lambda: self.root.attributes("-topmost", False))
            except Exception:
                pass
        _bring()
        try:
            self.root.after(10, _bring)
        except Exception:
            pass

    def show_settings(self):
        """显示设置对话框"""
        theme_names = sorted(
            [item.get("name") for item in self.theme_manager.list_themes() if item.get("name")]
        )
        default_config = self.config_manager.get_default_config()
        default_values = self._build_settings_dialog_config(default_config)
        dialog = SettingsDialog(
            self.root,
            config=self._get_settings_dialog_config(),
            translator=self.translator,
            theme_names=theme_names,
            defaults=default_values,
        )
        
        if dialog.result:
            result = dialog.result

            old_language = self.config_manager.get('language', 'zh')
            old_theme = self.config_manager.get('display.theme', 'wood')

            # 写入配置（尽量不影响其它功能：未知字段会被 ConfigManager 忽略）
            mappings = {
                'language': result.get('language'),
                'display.theme': result.get('theme'),
                'rules.default_board_size': result.get('default_board_size'),
                'rules.default_rules': result.get('default_rules'),
                'rules.default_komi': result.get('default_komi'),
                'storage.auto_save': result.get('auto_save'),
                'confirm_exit': result.get('confirm_exit'),
                'display.show_coordinates': result.get('show_coordinates'),
                'display.show_move_numbers': result.get('show_move_numbers'),
                'display.show_last_move': result.get('highlight_last_move'),
                'display.show_territory': result.get('show_territory'),
                'display.show_influence': result.get('show_influence'),
                'display.animation_enabled': result.get('enable_animations'),
                'display.animation_speed': result.get('animation_speed'),
                'ai.default_level': result.get('default_ai_level'),
                'ai.thinking_time': result.get('ai_thinking_time'),
                'ai.show_analysis': result.get('show_ai_analysis'),
                'ai.show_win_rate': result.get('show_winrate'),
                'ai.show_best_moves': result.get('show_best_moves'),
                'ai.auto_analyze': result.get('auto_analyze'),
                'sound.enabled': result.get('sound_enabled'),
                'sound.volume': result.get('sound_volume'),
                'sound.stone_sound': result.get('stone_sound'),
                'sound.capture_sound': result.get('capture_sound'),
                'sound.warning_sound': result.get('time_warning_sound'),
                'storage.auto_save_sgf': result.get('auto_save_sgf'),
                'storage.sgf_path': result.get('sgf_path'),
                'ai.gpu_enabled': result.get('use_gpu'),
                'ai.threads': result.get('threads'),
                'debug_mode': result.get('debug_mode'),
            }
            for key, value in mappings.items():
                if value is None:
                    continue
                self.config_manager.set(key, value, save=False)

            self.config_manager.save_config()

            # 应用语言/主题
            new_language = self.config_manager.get('language', old_language)
            new_theme = self.config_manager.get('display.theme', old_theme)

            if new_language != old_language:
                self._apply_language(new_language)
            if new_theme != old_theme:
                self._apply_theme(new_theme)

            # 应用显示选项（尽量复用现有开关，避免状态不同步）
            self.set_show_coordinates(bool(result.get('show_coordinates', True)))
            self.set_show_move_numbers(bool(result.get('show_move_numbers', False)))
            self.set_show_territory(bool(result.get('show_territory', False)))
            self.set_show_influence(bool(result.get('show_influence', False)))

            # 最后一手标记
            show_last = bool(result.get('highlight_last_move', True))
            self.config_manager.set('display.show_last_move', show_last, save=False)
            try:
                if hasattr(self, 'show_last_move_var'):
                    self.show_last_move_var.set(show_last)
            except Exception:
                pass
            if self.board_canvas:
                self.board_canvas.set_highlight_last_move(show_last)

            # 动画设置（BoardCanvas 内部已创建 animation_manager）
            if self.board_canvas and hasattr(self.board_canvas, 'animation_manager'):
                am = self.board_canvas.animation_manager
                am.enable_animations = bool(result.get('enable_animations', True))
                am.animation_speed = float(result.get('animation_speed', 1.0))

            messagebox.showinfo(self.translator.get('info'), self.translator.get('settings_applied'))
    
    def show_game_tree(self):
        """显示游戏树"""
        if not self.game:
            return

        try:
            if getattr(self, '_game_tree_window', None) and self._game_tree_window.winfo_exists():
                self._game_tree_window.lift()
                self._game_tree_window.focus_force()
                return
        except Exception:
            pass

        theme = self.theme_manager.get_current_theme()
        self._game_tree_window = GameTreeWindow(
            self.root,
            game=self.game,
            translator=self.translator,
            theme=theme,
            show_coordinates=self.config_manager.get('display.show_coordinates', True),
            show_move_numbers=self.config_manager.get('display.show_move_numbers', False),
        )
    
    def show_position_analysis(self):
        """显示局面分析"""
        if not self.game:
            return

        # 作为“备用入口”：一键运行【形势估计 + 分析】
        self.on_estimate()
        self.on_analyze()
    
    def show_joseki_dictionary(self):
        """显示定式词典"""
        try:
            if getattr(self, '_joseki_window', None) and self._joseki_window.winfo_exists():
                self._joseki_window.lift()
                self._joseki_window.focus_force()
                return
        except Exception:
            pass

        theme = self.theme_manager.get_current_theme()
        self._joseki_window = JosekiDictionaryWindow(
            self.root,
            database=self.joseki_db,
            translator=self.translator,
            theme=theme,
            board_size=19,
            show_coordinates=self.config_manager.get('display.show_coordinates', True),
            show_move_numbers=self.config_manager.get('display.show_move_numbers', False),
        )
    
    def show_pattern_search(self):
        """显示模式搜索"""
        try:
            if getattr(self, '_pattern_window', None) and self._pattern_window.winfo_exists():
                self._pattern_window.lift()
                self._pattern_window.focus_force()
                return
        except Exception:
            pass

        theme = self.theme_manager.get_current_theme()
        self._pattern_window = PatternSearchWindow(
            self.root,
            get_game=lambda: self.game,
            translator=self.translator,
            theme=theme,
            show_coordinates=self.config_manager.get('display.show_coordinates', True),
            show_move_numbers=self.config_manager.get('display.show_move_numbers', False),
        )
    
    def show_problem_library(self):
        """显示死活题库"""
        try:
            if getattr(self, '_problem_library_window', None) and self._problem_library_window.winfo_exists():
                self._problem_library_window.lift()
                self._problem_library_window.focus_force()
                return
        except Exception:
            pass

        if not self.teaching_system:
            self.teaching_system = TeachingSystem(
                self.translator,
                content_db=self.content_db,
                user_db=self.user_db,
            )

        theme = self.theme_manager.get_current_theme()
        self._problem_library_window = ProblemLibraryWindow(
            self.root,
            teaching_system=self.teaching_system,
            translator=self.translator,
            theme=theme,
            show_coordinates=self.config_manager.get('display.show_coordinates', True),
            show_move_numbers=self.config_manager.get('display.show_move_numbers', False),
        )
    
    def show_statistics(self):
        """显示统计信息"""
        summary = self.statistics.get_statistics_summary()
        
        message = f"""
        {self.translator.get('total_games')}: {summary['total_games']}
        {self.translator.get('total_players')}: {summary['total_players']}
        {self.translator.get('average_game_length')}: {summary['average_moves']:.1f}
        {self.translator.get('most_active_player')}: {summary['most_active_player'] or self.translator.get('not_available')}
        """
        
        messagebox.showinfo(
            self.translator.get('statistics'),
            message.strip()
        )
    
    def show_rules_help(self):
        """显示规则说明"""
        RulesHelpDialog(
            self.root,
            translator=self.translator,
            theme=self.theme_manager.get_current_theme()
        )
    
    def show_tutorial(self):
        """显示教程"""
        if not self.teaching_system:
            self.teaching_system = TeachingSystem(
                self.translator,
                content_db=self.content_db,
                user_db=self.user_db,
            )
        
        TutorialDialog(
            self.root,
            teaching_system=self.teaching_system,
            translator=self.translator,
            theme=self.theme_manager.get_current_theme()
        )
    
    def show_shortcuts(self):
        """显示快捷键"""
        label_map = {
            "new_game": self.translator.get("new_game"),
            "open_game": self.translator.get("open"),
            "save_game": self.translator.get("save"),
            "save_game_as": self.translator.get("save_as"),
            "quit": self.translator.get("quit"),
            "undo": self.translator.get("undo"),
            "redo": self.translator.get("redo"),
            "copy_sgf": self.translator.get("copy_sgf"),
            "paste_sgf": self.translator.get("paste_sgf"),
            "teaching_mode": self.translator.get("teaching_mode"),
            "pass": self.translator.get("pass"),
            "resign": self.translator.get("resign"),
            "hint": self.translator.get("hint"),
            "analyze": self.translator.get("analyze"),
            "score": self.translator.get("score"),
            "end_game": self.translator.get("end_game"),
            "pause": self.translator.get("pause"),
            "fullscreen": self.translator.get("fullscreen"),
            "zoom_in": self.translator.get("zoom_in"),
            "zoom_out": self.translator.get("zoom_out"),
            "reset_view": self.translator.get("reset_view"),
            "settings": self.translator.get("settings"),
            "show_shortcuts": self.translator.get("shortcuts"),
        }

        groups = [
            ["new_game", "open_game", "save_game", "save_game_as", "quit"],
            ["undo", "redo", "copy_sgf", "paste_sgf", "teaching_mode"],
            ["pass", "resign", "hint", "analyze", "score", "end_game", "pause"],
            ["fullscreen", "zoom_in", "zoom_out", "reset_view", "settings", "show_shortcuts"],
        ]

        lines = []
        for group in groups:
            group_lines = []
            for action in group:
                hotkey = self._get_hotkey_display(action)
                if not hotkey:
                    continue
                label = label_map.get(action, action)
                group_lines.append(f"{hotkey} - {label}")
            if group_lines:
                lines.extend(group_lines)
                lines.append("")

        shortcuts = "\n".join(lines).strip()
        messagebox.showinfo(
            self.translator.get('shortcuts'),
            shortcuts.strip()
        )
    
    def show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(
            self.root,
            version=self.VERSION,
            author=self.translator.get("author_default"),
            contact="violentadvance@proton.me",
            translator=self.translator
        )
    
    def _update_recent_files_menu(self, menu: tk.Menu):
        """更新最近文件菜单"""
        if hasattr(menu, "clear_items"):
            try:
                menu.clear_items()
            except Exception:
                pass

        recent_files = self.config_manager.get('recent_files', [])
        if not isinstance(recent_files, list):
            recent_files = []

        cleaned = []
        for path in recent_files:
            if isinstance(path, str) and path.strip():
                cleaned.append(path)

        if cleaned != recent_files:
            self.config_manager.set('recent_files', cleaned)

        if not cleaned:
            menu.add_command(
                label=self.translator.get('none'),
                command=None,
                state="disabled",
                font_style="italic",
            )
            return
        
        for file_path in cleaned[:10]:
            menu.add_command(
                label=os.path.basename(file_path) or file_path,
                command=lambda f=file_path: self.open_recent_file(f)
            )
    
    def open_recent_file(self, file_path: str):
        """打开最近的文件"""
        if not file_path:
            return
        if os.path.exists(file_path):
            self._load_sgf_from_path(file_path, set_current_path=True)
        else:
            # 清理不存在的路径
            recent_files = self.config_manager.get('recent_files', [])
            if isinstance(recent_files, list):
                cleaned = [p for p in recent_files if p and p != file_path]
                if cleaned != recent_files:
                    self.config_manager.set('recent_files', cleaned)
                    if getattr(self, "recent_menu", None) is not None:
                        self._update_recent_files_menu(self.recent_menu)
    
    def _load_last_game(self) -> bool:
        """加载上次的游戏"""
        # TODO: 实现加载上次游戏
        return False
    
    def on_closing(self):
        """关闭应用程序"""
        # 如果有正在进行的游戏，询问是否保存
        if self.game and not self.game.is_ended():
            if self.config_manager.get('confirm_exit', True):
                response = messagebox.askyesnocancel(
                    self.translator.get('confirm'),
                    self.translator.get('save_current_game'),
                )

                if response is None:  # 取消
                    return
                elif response:  # 保存
                    self.save_game()
        
        # 保存窗口大小和位置
        geometry = self.root.geometry()
        self.config_manager.set('window_geometry', geometry)
        
        # 清理资源
        if self.game:
            self.game.cleanup()
        
        self.sound_manager.cleanup()
        self.storage_manager.cleanup()
        self.statistics.save_statistics()
        
        # 关闭窗口
        self.root.destroy()


def main():
    """主函数"""
    # 创建根窗口
    root = ModernWindow(title="围棋大师 Go Master 4.0")
    
    # 创建应用程序
    app = GoMasterApp(root)
    
    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()
