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

# 导入UI模块
from ui import (
    BoardCanvas, InfoPanel, ControlPanel, AnalysisPanel,
    NewGameDialog, SettingsDialog, AboutDialog,
    Theme, ThemeManager, AnimationManager
)

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
    Translator, Statistics, StorageManager, TimeControl,
    resource_path, GameConfig, TimeSettings, GameStats
)


class GoMasterApp:
    """围棋大师主应用程序"""
    
    VERSION = "2.0.0"
    APP_NAME = "围棋大师 Go Master"
    
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
            self.new_game()
        
        # 设置关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 启动自动保存
        self._setup_auto_save()
    
    def _init_managers(self):
        """初始化各种管理器"""
        # 配置管理
        self.config_manager = ConfigManager()
        config = self.config_manager.config
        
        # 翻译系统
        self.translator = Translator(config.language)
        
        # 音效管理
        self.sound_manager = SoundManager(self.config_manager)
        
        # 统计系统
        self.statistics = Statistics()
        
        # 存储管理
        self.storage_manager = StorageManager(self.config_manager)
        
        # 主题管理
        self.theme_manager = ThemeManager(config.display.theme)
        
        # 注意：删除了这里的 AnimationManager 创建代码
        # AnimationManager 会在 BoardCanvas 中创建，因为它需要 canvas 对象
        # 我们可以保存动画配置，稍后传递给 BoardCanvas
        self.animation_config = {
            'enabled': config.display.animation_enabled,
            'speed': config.display.animation_speed
        }
        
        # 定式数据库
        self.joseki_db = JosekiDatabase()
    
    def _setup_window(self):
        """设置主窗口"""
        # 设置标题和图标
        self.root.title(self.APP_NAME)
        
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
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建分割面板
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧面板（信息和控制）
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
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
            on_pause=self.on_pause
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
        
        # 棋盘画布
        self.board_canvas = BoardCanvas(
            center_frame,
            board_size=19,
            theme_manager=self.theme_manager,
            animation_manager=self.animation_manager,
            on_click=self.on_board_click,
            on_hover=self.on_board_hover
        )
        self.board_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 右侧面板（可选，用于额外功能）
        if self.config_manager.get('display.show_side_panel', False):
            right_frame = ttk.Frame(paned)
            paned.add(right_frame, weight=1)
            # TODO: 添加游戏树、变化图等
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.translator.get('file'), menu=file_menu)
        
        file_menu.add_command(
            label=self.translator.get('new_game'),
            command=self.new_game,
            accelerator="Ctrl+N"
        )
        file_menu.add_separator()
        
        file_menu.add_command(
            label=self.translator.get('open'),
            command=self.open_game,
            accelerator="Ctrl+O"
        )
        file_menu.add_command(
            label=self.translator.get('save'),
            command=self.save_game,
            accelerator="Ctrl+S"
        )
        file_menu.add_command(
            label=self.translator.get('save_as'),
            command=self.save_game_as,
            accelerator="Ctrl+Shift+S"
        )
        file_menu.add_separator()
        
        file_menu.add_command(
            label=self.translator.get('import') + " SGF",
            command=self.import_sgf
        )
        file_menu.add_command(
            label=self.translator.get('export') + " SGF",
            command=self.export_sgf
        )
        file_menu.add_separator()
        
        # 最近文件
        recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label=self.translator.get('recent_files'), menu=recent_menu)
        self._update_recent_files_menu(recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(
            label=self.translator.get('quit'),
            command=self.on_closing,
            accelerator="Ctrl+Q"
        )
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.translator.get('edit'), menu=edit_menu)
        
        edit_menu.add_command(
            label=self.translator.get('undo'),
            command=self.on_undo,
            accelerator="Ctrl+Z"
        )
        edit_menu.add_command(
            label=self.translator.get('redo'),
            command=self.on_redo,
            accelerator="Ctrl+Y"
        )
        edit_menu.add_separator()
        
        edit_menu.add_command(
            label=self.translator.get('copy') + " SGF",
            command=self.copy_sgf,
            accelerator="Ctrl+C"
        )
        edit_menu.add_command(
            label=self.translator.get('paste') + " SGF",
            command=self.paste_sgf,
            accelerator="Ctrl+V"
        )
        edit_menu.add_separator()
        
        edit_menu.add_command(
            label=self.translator.get('clear_board'),
            command=self.clear_board
        )
        edit_menu.add_command(
            label=self.translator.get('edit_mode'),
            command=self.toggle_edit_mode
        )
        
        # 游戏菜单
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.translator.get('game'), menu=game_menu)
        
        game_menu.add_command(
            label=self.translator.get('pass'),
            command=self.on_pass,
            accelerator="P"
        )
        game_menu.add_command(
            label=self.translator.get('resign'),
            command=self.on_resign,
            accelerator="R"
        )
        game_menu.add_separator()
        
        game_menu.add_command(
            label=self.translator.get('hint'),
            command=self.on_hint,
            accelerator="H"
        )
        game_menu.add_command(
            label=self.translator.get('analyze'),
            command=self.on_analyze,
            accelerator="A"
        )
        game_menu.add_command(
            label=self.translator.get('score'),
            command=self.on_score,
            accelerator="S"
        )
        game_menu.add_separator()
        
        game_menu.add_command(
            label=self.translator.get('pause'),
            command=self.on_pause,
            accelerator="Space"
        )
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
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
            accelerator="F11"
        )
        view_menu.add_command(
            label=self.translator.get('zoom_in'),
            command=self.zoom_in,
            accelerator="Ctrl++"
        )
        view_menu.add_command(
            label=self.translator.get('zoom_out'),
            command=self.zoom_out,
            accelerator="Ctrl+-"
        )
        view_menu.add_command(
            label=self.translator.get('reset_view'),
            command=self.reset_view,
            accelerator="Ctrl+0"
        )
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
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
        
        tools_menu.add_command(
            label=self.translator.get('settings'),
            command=self.show_settings,
            accelerator="Ctrl+,"
        )
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
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
            accelerator="F1"
        )
        help_menu.add_separator()
        
        help_menu.add_command(
            label=self.translator.get('about'),
            command=self.show_about
        )
    
    def _bind_shortcuts(self):
        """绑定快捷键"""
        shortcuts = {
            '<Control-n>': lambda e: self.new_game(),
            '<Control-o>': lambda e: self.open_game(),
            '<Control-s>': lambda e: self.save_game(),
            '<Control-S>': lambda e: self.save_game_as(),
            '<Control-q>': lambda e: self.on_closing(),
            '<Control-z>': lambda e: self.on_undo(),
            '<Control-y>': lambda e: self.on_redo(),
            '<Control-c>': lambda e: self.copy_sgf(),
            '<Control-v>': lambda e: self.paste_sgf(),
            '<Control-plus>': lambda e: self.zoom_in(),
            '<Control-minus>': lambda e: self.zoom_out(),
            '<Control-0>': lambda e: self.reset_view(),
            '<Control-comma>': lambda e: self.show_settings(),
            '<F1>': lambda e: self.show_shortcuts(),
            '<F11>': lambda e: self.toggle_fullscreen(),
            '<space>': lambda e: self.on_pause(),
            'p': lambda e: self.on_pass(),
            'r': lambda e: self.on_resign(),
            'h': lambda e: self.on_hint(),
            'a': lambda e: self.on_analyze(),
            's': lambda e: self.on_score(),
        }
        
        for key, handler in shortcuts.items():
            self.root.bind(key, handler)
    
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
            config=self.config_manager.config
        )
        
        if dialog.result:
            # 创建新游戏
            self._start_new_game(dialog.result)
    
    def _start_new_game(self, settings: Dict[str, Any]):
        """
        开始新游戏
        
        Args:
            settings: 游戏设置
        """
        # 停止当前游戏的计时器
        if self.game:
            self.game.cleanup()
        
        # 创建新游戏
        self.game = Game(
            board_size=settings['board_size'],
            rules=settings['rules'],
            komi=settings['komi'],
            handicap=settings['handicap']
        )
        
        # 设置游戏信息
        self.game.set_player_info(
            black_name=settings.get('black_player', 'Black'),
            white_name=settings.get('white_player', 'White')
        )
        
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
                # 播放吃子动画
                self.animation_manager.play_capture_animation(
                    self.board_canvas, captures
                )
            
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
        
        self.game.pass_turn()
        self.sound_manager.play('pass')
        
        # 检查是否连续虚手（游戏结束）
        if self.game.is_ended():
            self.on_game_end()
        else:
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
        
        # 更新分析面板
        self.analysis_panel.update_analysis(analysis)
    
    def on_score(self):
        """数子"""
        if not self.game:
            return
        
        # 进入数子阶段
        self.game.enter_scoring_phase()
        
        # 显示死活标记界面
        self.board_canvas.enter_scoring_mode(
            on_stone_click=self.on_mark_dead_stone,
            on_done=self.on_scoring_done
        )
    
    def on_mark_dead_stone(self, x: int, y: int):
        """标记死子"""
        self.game.toggle_dead_stone(x, y)
        self.board_canvas.update_dead_stones(self.game.get_dead_stones())
    
    def on_scoring_done(self):
        """完成数子"""
        # 计算最终得分
        result = self.game.calculate_final_score()
        
        # 显示结果
        self.show_game_result(result)
        
        # 退出数子模式
        self.board_canvas.exit_scoring_mode()
    
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
        self.board_canvas.update_board(self.game.board)
        
        # 更新信息面板
        game_info = self.game.get_game_info()
        self.info_panel.update_info(game_info)
        
        # 更新控制面板状态
        self.control_panel.update_buttons(
            can_undo=self.game.can_undo(),
            can_redo=self.game.can_redo(),
            is_playing=not self.game.is_ended()
        )
    
    def save_game(self, auto: bool = False):
        """保存游戏"""
        if not self.game:
            return
        
        game_data = self.game.to_dict()
        
        if auto:
            # 自动保存
            save_id = self.storage_manager.save_game(
                game_data,
                name=f"Auto Save {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                tags=['auto_save']
            )
        else:
            # 手动保存
            name = tk.simpledialog.askstring(
                self.translator.get('save'),
                self.translator.get('enter_save_name')
            )
            
            if name:
                save_id = self.storage_manager.save_game(game_data, name)
                
                if save_id:
                    messagebox.showinfo(
                        self.translator.get('info'),
                        self.translator.get('game_saved')
                    )
    
    def save_game_as(self):
        """另存为"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pkl",
            filetypes=[
                (self.translator.get('game_files'), "*.pkl"),
                (self.translator.get('all_files'), "*.*")
            ]
        )
        
        if file_path:
            # TODO: 实现另存为功能
            pass
    
    def open_game(self):
        """打开游戏"""
        # 显示存档列表
        saves = self.storage_manager.list_saves()
        
        if not saves:
            messagebox.showinfo(
                self.translator.get('info'),
                self.translator.get('no_saved_games')
            )
            return
        
        # TODO: 显示存档选择对话框
        # 暂时使用第一个存档
        if saves:
            save = self.storage_manager.load_game(saves[0].save_id)
            
            if save:
                self.game = Game.from_dict(save.game_data)
                self.update_display()
                
                messagebox.showinfo(
                    self.translator.get('info'),
                    self.translator.get('game_loaded')
                )
    
    def import_sgf(self):
        """导入SGF"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                (self.translator.get('sgf_files'), "*.sgf"),
                (self.translator.get('all_files'), "*.*")
            ]
        )
        
        if file_path:
            save_id = self.storage_manager.import_sgf(file_path)
            
            if save_id:
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
            file_path = os.path.join(sgf_dir, f"game_{timestamp}.sgf")
        else:
            # 手动导出
            file_path = filedialog.asksaveasfilename(
                defaultextension=".sgf",
                filetypes=[
                    (self.translator.get('sgf_files'), "*.sgf"),
                    (self.translator.get('all_files'), "*.*")
                ]
            )
        
        if file_path:
            # 生成SGF
            sgf_game = self.game.to_sgf()
            
            if SGFParser.save_to_file(sgf_game, file_path):
                if not auto:
                    messagebox.showinfo(
                        self.translator.get('info'),
                        self.translator.get('sgf_saved')
                    )
    
    def copy_sgf(self):
        """复制SGF到剪贴板"""
        if not self.game:
            return
        
        sgf_game = self.game.to_sgf()
        sgf_text = SGFParser.generate(sgf_game)
        
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
                self.game = Game.from_sgf(sgf_game)
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
            self.game.clear_board()
            self.update_display()
    
    def toggle_edit_mode(self):
        """切换编辑模式"""
        # TODO: 实现编辑模式
        pass
    
    def toggle_coordinates(self):
        """切换坐标显示"""
        show = self.show_coords_var.get()
        self.config_manager.set('display.show_coordinates', show)
        self.board_canvas.set_show_coordinates(show)
    
    def toggle_move_numbers(self):
        """切换手数显示"""
        show = self.show_move_nums_var.get()
        self.config_manager.set('display.show_move_numbers', show)
        self.board_canvas.set_show_move_numbers(show)
    
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
    
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(
            self.root,
            config=self.config_manager.config,
            translator=self.translator
        )
        
        if dialog.result:
            # 应用设置
            self.config_manager.config = dialog.result
            self.config_manager.save_config()
            
            # 更新翻译
            if dialog.result.language != self.translator.language:
                self.translator.set_language(dialog.result.language)
                # TODO: 重新创建UI以应用新语言
            
            # 更新主题
            if dialog.result.display.theme != self.theme_manager.current_theme:
                self.theme_manager.set_theme(dialog.result.display.theme)
                self.board_canvas.update_theme()
            
            messagebox.showinfo(
                self.translator.get('info'),
                self.translator.get('settings_applied')
            )
    
    def show_game_tree(self):
        """显示游戏树"""
        if self.game:
            # TODO: 实现游戏树窗口
            messagebox.showinfo(
                self.translator.get('info'),
                "游戏树功能开发中..."
            )
    
    def show_position_analysis(self):
        """显示局面分析"""
        if self.game:
            # TODO: 实现局面分析窗口
            messagebox.showinfo(
                self.translator.get('info'),
                "局面分析功能开发中..."
            )
    
    def show_joseki_dictionary(self):
        """显示定式词典"""
        # TODO: 实现定式词典窗口
        messagebox.showinfo(
            self.translator.get('info'),
            "定式词典功能开发中..."
        )
    
    def show_pattern_search(self):
        """显示模式搜索"""
        # TODO: 实现模式搜索窗口
        messagebox.showinfo(
            self.translator.get('info'),
            "模式搜索功能开发中..."
        )
    
    def show_problem_library(self):
        """显示死活题库"""
        # TODO: 实现死活题库窗口
        messagebox.showinfo(
            self.translator.get('info'),
            "死活题库功能开发中..."
        )
    
    def show_statistics(self):
        """显示统计信息"""
        summary = self.statistics.get_statistics_summary()
        
        message = f"""
        {self.translator.get('total_games')}: {summary['total_games']}
        {self.translator.get('total_players')}: {summary['total_players']}
        {self.translator.get('average_game_length')}: {summary['average_moves']:.1f}
        {self.translator.get('most_active_player')}: {summary['most_active_player'] or 'N/A'}
        """
        
        messagebox.showinfo(
            self.translator.get('statistics'),
            message.strip()
        )
    
    def show_rules_help(self):
        """显示规则说明"""
        # TODO: 实现规则说明窗口
        messagebox.showinfo(
            self.translator.get('info'),
            "规则说明功能开发中..."
        )
    
    def show_tutorial(self):
        """显示教程"""
        if not self.teaching_system:
            self.teaching_system = TeachingSystem(self.translator)
        
        # TODO: 实现教程窗口
        messagebox.showinfo(
            self.translator.get('info'),
            "教程功能开发中..."
        )
    
    def show_shortcuts(self):
        """显示快捷键"""
        shortcuts = """
        Ctrl+N - 新游戏
        Ctrl+O - 打开
        Ctrl+S - 保存
        Ctrl+Q - 退出
        Ctrl+Z - 悔棋
        Ctrl+Y - 重做
        
        P - 虚手
        R - 认输
        H - 提示
        A - 分析
        S - 数子
        
        F1 - 帮助
        F11 - 全屏
        Space - 暂停
        """
        
        messagebox.showinfo(
            self.translator.get('shortcuts'),
            shortcuts.strip()
        )
    
    def show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(
            self.root,
            version=self.VERSION,
            translator=self.translator
        )
    
    def _update_recent_files_menu(self, menu: tk.Menu):
        """更新最近文件菜单"""
        recent_files = self.config_manager.get('recent_files', [])
        
        for file_path in recent_files[:10]:
            menu.add_command(
                label=os.path.basename(file_path),
                command=lambda f=file_path: self.open_recent_file(f)
            )
    
    def open_recent_file(self, file_path: str):
        """打开最近的文件"""
        # TODO: 实现打开最近文件
        pass
    
    def _load_last_game(self) -> bool:
        """加载上次的游戏"""
        # TODO: 实现加载上次游戏
        return False
    
    def on_closing(self):
        """关闭应用程序"""
        # 如果有正在进行的游戏，询问是否保存
        if self.game and not self.game.is_ended():
            response = messagebox.askyesnocancel(
                self.translator.get('confirm'),
                self.translator.get('confirm_exit')
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
    root = tk.Tk()
    
    # 创建应用程序
    app = GoMasterApp(root)
    
    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()