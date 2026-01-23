"""
UI面板组件
包含信息面板、控制面板、分析面板等
"""
"""
UI面板组件
包含信息面板、控制面板、分析面板等
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Dict, Any, List, Tuple
from dataclasses import dataclass

from .translator import Translator
from .themes import Theme
from .widgets import ModernButton, ModernCard, ModernLabel, ModernProgressBar, ModernScrollbar


class BasePanel(ttk.Frame):
    """面板基类"""
    
    def __init__(self, parent, translator: Optional[Translator] = None, 
                 theme: Optional[Theme] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.translator = translator or Translator()
        self.theme = theme or Theme(name='default')
        
        # 应用主题样式
        self._apply_theme()
    
    def _apply_theme(self):
        """应用主题样式"""
        style = ttk.Style(self)
        font_family = (self.theme.font_family or "Arial").split(',')[0].strip()
        
        # 统一面板样式（只影响使用 Panel.* 样式名的控件）
        # 外层：更浅的背景；卡片/分组：更深一些的背景，形成层次。
        style.configure(
            'Panel.TFrame',
            background=self.theme.ui_background,
            relief='flat',
            borderwidth=0,
        )

        style.configure(
            'PanelCard.TFrame',
            background=self.theme.ui_panel_background,
            relief='flat',
            borderwidth=0,
        )
        
        style.configure('Panel.TLabel',
                       background=self.theme.ui_panel_background,
                       foreground=self.theme.ui_text_primary)
        
        style.configure('Panel.TLabelframe',
                       background=self.theme.ui_panel_background,
                       foreground=self.theme.ui_text_primary,
                       relief='solid',
                       borderwidth=1)
        
        style.configure('Panel.TLabelframe.Label',
                       background=self.theme.ui_panel_background,
                       foreground=self.theme.ui_text_primary,
                       font=(font_family, max(10, int(self.theme.font_size_normal)), 'bold'))

        style.configure(
            'Panel.TButton',
            padding=(10, 6),
            font=(font_family, max(10, int(self.theme.font_size_normal))),
            background=self.theme.button_bg,
            foreground=self.theme.button_fg,
            relief='flat',
            borderwidth=0,
        )
        style.map(
            'Panel.TButton',
            background=[('active', self.theme.button_hover_bg)],
            foreground=[('active', self.theme.button_hover_fg),
                        ('disabled', self.theme.ui_text_disabled)],
        )

        style.configure(
            'Panel.TCheckbutton',
            background=self.theme.ui_panel_background,
            foreground=self.theme.ui_text_primary,
            padding=(6, 3),
        )
        style.map(
            'Panel.TCheckbutton',
            background=[('active', self.theme.ui_panel_background)],
            foreground=[('disabled', self.theme.ui_text_disabled)],
        )

        style.configure(
            'Panel.Treeview',
            background=self.theme.input_background,
            fieldbackground=self.theme.input_background,
            foreground=self.theme.ui_text_primary,
            rowheight=22,
        )
        style.configure(
            'Panel.Treeview.Heading',
            background=self.theme.ui_panel_background,
            foreground=self.theme.ui_text_primary,
            font=(font_family, max(10, int(self.theme.font_size_small)), 'bold'),
            relief='flat',
        )
        
        self.configure(style='Panel.TFrame')
    
    def update_translator(self, translator: Translator):
        """更新翻译器"""
        self.translator = translator
        self._update_texts()
    
    def update_theme(self, theme: Theme):
        """更新主题"""
        self.theme = theme
        self._apply_theme()
        self._propagate_theme(self)

    def _propagate_theme(self, widget: tk.Widget):
        for child in widget.winfo_children():
            if hasattr(child, 'update_theme') and callable(getattr(child, 'update_theme')):
                child.update_theme(self.theme)
            elif isinstance(child, tk.Canvas):
                try:
                    child.configure(bg=self.theme.ui_panel_background)
                except Exception:
                    pass
            self._propagate_theme(child)
    
    def _update_texts(self):
        """更新所有文本（子类实现）"""
        pass


class InfoPanel(BasePanel):
    """信息显示面板"""
    
    def __init__(self, parent, on_settings_click=None, **kwargs):
        # 先提取出自定义参数，避免传递给父类
        self.on_settings_click = on_settings_click
        
        # 只传递有效的 kwargs 给父类
        super().__init__(parent, **kwargs)
        
        self._create_widgets()
        self._update_texts()
    
    def _create_widgets(self):
        """创建控件"""
        # 玩家信息框架 (使用 ModernCard)
        self.players_card = ModernCard(self, theme=self.theme, padding=12)
        self.players_card.pack(fill='x', padx=10, pady=(10, 6))

        self.players_header = ttk.Frame(self.players_card, style='PanelCard.TFrame')
        self.players_header.pack(fill='x', padx=2, pady=(0, 6))

        self.players_title = ModernLabel(self.players_header, theme=self.theme, font_style='section')
        self.players_title.pack(side='left')

        self.settings_button = None
        if self.on_settings_click:
            self.settings_button = ModernButton(
                self.players_header,
                theme=self.theme,
                width=90,
                height=26,
                command=self.on_settings_click,
            )
            self.settings_button.pack(side='right')
        
        # 黑方信息
        self.black_frame = ttk.Frame(self.players_card, style='PanelCard.TFrame')
        self.black_frame.pack(fill='x', padx=4, pady=2)
        
        # 黑方图标
        self.black_stone_icon = tk.Canvas(self.black_frame, width=20, height=20,
                                         bg=self.theme.ui_panel_background,
                                         highlightthickness=0)
        self.black_stone_icon.pack(side='left', padx=(0, 5))
        self.black_stone_icon.create_oval(2, 2, 18, 18, fill='black', outline='#333')
        
        self.black_name_label = ttk.Label(self.black_frame, style='Panel.TLabel')
        self.black_name_label.pack(side='left')
        
        self.black_info_frame = ttk.Frame(self.black_frame, style='PanelCard.TFrame')
        self.black_info_frame.pack(side='right')
        
        self.black_time_label = ttk.Label(self.black_info_frame, style='Panel.TLabel')
        self.black_time_label.pack(side='right')
        
        self.black_captured_label = ttk.Label(self.black_info_frame, style='Panel.TLabel')
        self.black_captured_label.pack(side='right', padx=(0, 10))
        
        # 白方信息
        self.white_frame = ttk.Frame(self.players_card, style='PanelCard.TFrame')
        self.white_frame.pack(fill='x', padx=4, pady=2)
        
        # 白方图标
        self.white_stone_icon = tk.Canvas(self.white_frame, width=20, height=20,
                                         bg=self.theme.ui_panel_background,
                                         highlightthickness=0)
        self.white_stone_icon.pack(side='left', padx=(0, 5))
        self.white_stone_icon.create_oval(2, 2, 18, 18, fill='white', outline='#ccc')
        
        self.white_name_label = ttk.Label(self.white_frame, style='Panel.TLabel')
        self.white_name_label.pack(side='left')
        
        self.white_info_frame = ttk.Frame(self.white_frame, style='PanelCard.TFrame')
        self.white_info_frame.pack(side='right')
        
        self.white_time_label = ttk.Label(self.white_info_frame, style='Panel.TLabel')
        self.white_time_label.pack(side='right')
        
        self.white_captured_label = ttk.Label(self.white_info_frame, style='Panel.TLabel')
        self.white_captured_label.pack(side='right', padx=(0, 10))
        
        # 游戏信息框架 (使用 ModernCard)
        self.game_card = ModernCard(self, theme=self.theme, padding=12)
        self.game_card.pack(fill='x', padx=10, pady=(0, 6))

        self.game_header = ttk.Frame(self.game_card, style='PanelCard.TFrame')
        self.game_header.pack(fill='x', padx=2, pady=(0, 6))

        self.game_title = ModernLabel(self.game_header, theme=self.theme, font_style='section')
        self.game_title.pack(side='left')
        
        self.current_player_frame = ttk.Frame(self.game_card, style='PanelCard.TFrame')
        self.current_player_frame.pack(fill='x', padx=4, pady=2)
        
        self.current_player_label = ttk.Label(self.current_player_frame, style='Panel.TLabel')
        self.current_player_label.pack(side='left')
        
        # 当前玩家指示器
        self.current_indicator = tk.Canvas(self.current_player_frame, 
                                          width=16, height=16,
                                          bg=self.theme.ui_panel_background,
                                          highlightthickness=0)
        self.current_indicator.pack(side='left', padx=5)
        
        self.move_number_label = ttk.Label(self.game_card, style='Panel.TLabel')
        self.move_number_label.pack(padx=5, pady=2)
        
        self.ko_label = ttk.Label(self.game_card, style='Panel.TLabel')
        self.ko_label.pack(padx=5, pady=2)
        
        self.phase_label = ttk.Label(self.game_card, style='Panel.TLabel')
        self.phase_label.pack(padx=5, pady=2)
        
        # 设置默认值
        self.update_player_info(
            self.translator.get('black_player'),
            self.translator.get('white_player'),
        )
        self.update_game_info('black', 0)
    
    def _update_texts(self):
        """更新文本"""
        # LabelFrame 的 text 属性在这里失效了，因为我们换成了 ModernCard
        # 如果需要标题，可以在 ModernCard 顶部加一个 ModernLabel
        self.players_title.configure(text=self.translator.get('players'))
        self.game_title.configure(text=self.translator.get('game_info'))
        if self.settings_button:
            self.settings_button.configure_text(self.translator.get('settings'))
        self.current_player_label.configure(
            text=f"{self.translator.get('current_player')}:"
        )
        self.phase_label.configure(
            text=f"{self.translator.get('phase')}: {self.translator.get('playing')}"
        )
    
    def update_player_info(self, black_name: str, white_name: str,
                          black_time: Optional[str] = None, white_time: Optional[str] = None,
                          black_captured: int = 0, white_captured: int = 0):
        """更新玩家信息"""
        if black_time is None:
            black_time = self.translator.get('infinite_time_symbol')
        if white_time is None:
            white_time = self.translator.get('infinite_time_symbol')
        self.black_name_label.configure(text=black_name)
        self.white_name_label.configure(text=white_name)

        self.black_time_label.configure(
            text=self.translator.get('time_left_format', time=black_time)
        )
        self.white_time_label.configure(
            text=self.translator.get('time_left_format', time=white_time)
        )
        
        self.black_captured_label.configure(
            text=f"{self.translator.get('captured')}: {black_captured}"
        )
        self.white_captured_label.configure(
            text=f"{self.translator.get('captured')}: {white_captured}"
        )
    
    def update_game_info(self, current_player: str, move_number: int,
                        ko_point: Optional[Tuple[int, int]] = None,
                        phase: str = 'playing'):
        """更新游戏信息"""
        # 更新当前玩家指示
        self.current_indicator.delete('all')
        if current_player == 'black':
            self.current_indicator.create_oval(2, 2, 14, 14, fill='black', outline='#333')
        else:
            self.current_indicator.create_oval(2, 2, 14, 14, fill='white', outline='#ccc')
        
        # 更新手数
        self.move_number_label.configure(
            text=f"{self.translator.get('move')}: {move_number}"
        )
        
        # 更新劫点
        if ko_point:
            letters = 'ABCDEFGHJKLMNOPQRST'
            ko_text = f"{self.translator.get('ko')}: {letters[ko_point[0]]}{19 - ko_point[1]}"
            self.ko_label.configure(text=ko_text)
        else:
            self.ko_label.configure(text="")
        
        # 更新阶段
        phase_text = self.translator.get(phase)
        self.phase_label.configure(
            text=f"{self.translator.get('phase')}: {phase_text}"
        )

    def set_phase_text(self, text: str):
        """直接设置阶段显示文本（用于动态信息，如数子预览结果）。"""
        self.phase_label.configure(text=text)

    # --- 兼容 main.py 的方法（旧版 UI 调用） ---

    def update_info(self, game_info: Dict[str, Any]):
        """
        兼容旧接口：根据 game_info 字典刷新信息面板。
        期望字段：player_black/player_white/current_player/move_number/captured_black/captured_white/ko_point/phase 等。
        """
        black_name = (
            game_info.get('player_black')
            or game_info.get('black_player')
            or self.translator.get('black_player')
        )
        white_name = (
            game_info.get('player_white')
            or game_info.get('white_player')
            or self.translator.get('white_player')
        )

        black_time = game_info.get('black_time', self.translator.get('infinite_time_symbol'))
        white_time = game_info.get('white_time', self.translator.get('infinite_time_symbol'))

        black_captured = int(game_info.get('captured_black', 0) or 0)
        white_captured = int(game_info.get('captured_white', 0) or 0)

        self.update_player_info(
            black_name=black_name,
            white_name=white_name,
            black_time=black_time,
            white_time=white_time,
            black_captured=black_captured,
            white_captured=white_captured,
        )

        self.update_game_info(
            current_player=game_info.get('current_player', 'black'),
            move_number=int(game_info.get('move_number', 0) or 0),
            ko_point=game_info.get('ko_point'),
            phase=game_info.get('phase', 'playing'),
        )

    def show_thinking(self, thinking: bool = True):
        """兼容旧接口：AI思考提示（当前为轻量占位）。"""
        if thinking:
            self.phase_label.configure(
                text=f"{self.translator.get('phase')}: {self.translator.get('analyzing')}"
            )
        else:
            # 恢复为默认显示（由 update_info/update_game_info 再次覆盖）
            return


class ControlPanel(BasePanel):
    """控制面板"""
    
    def __init__(self, parent, 
                 on_pass=None,
                 on_resign=None,
                 on_undo=None,
                 on_redo=None,
                 on_hint=None,
                 on_analyze=None,
                 on_score=None,
                 on_end_game=None,
                 on_estimate=None,
                 on_pause=None,
                 on_show_coordinates=None,
                 on_show_move_numbers=None,
                 on_show_territory=None,
                 on_show_influence=None,
                 show_coordinates: bool = True,
                 show_move_numbers: bool = False,
                 show_territory: bool = False,
                 show_influence: bool = False,
                 **kwargs):
        # 保存回调函数
        self.callbacks = {
            'pass': on_pass,
            'resign': on_resign,
            'undo': on_undo,
            'redo': on_redo,
            'hint': on_hint,
            'analyze': on_analyze,
            'score': on_score,
            'end_game': on_end_game,
            'estimate': on_estimate,
            'pause': on_pause
        }

        # 显示选项回调（用于左侧 display 勾选项）
        self.callbacks.update(
            {
                'show_coordinates': on_show_coordinates,
                'show_move_numbers': on_show_move_numbers,
                'show_territory': on_show_territory,
                'show_influence': on_show_influence,
            }
        )

        # 初始显示状态
        self._display_defaults = {
            'show_coordinates': bool(show_coordinates),
            'show_move_numbers': bool(show_move_numbers),
            'show_territory': bool(show_territory),
            'show_influence': bool(show_influence),
        }
        
        # 只传递有效的 kwargs 给父类
        super().__init__(parent, **kwargs)
        
        self._create_widgets()
        self._update_texts()
    
    def _create_widgets(self):
        """创建控件"""
        # 游戏控制 (使用 ModernCard)
        self.game_control_card = ModernCard(self, theme=self.theme, padding=12)
        self.game_control_card.pack(fill='x', padx=10, pady=(0, 10))
        
        # 按钮网格
        self.game_control_card.columnconfigure(0, weight=1)
        self.game_control_card.columnconfigure(1, weight=1)

        self.game_control_title = ModernLabel(
            self.game_control_card, theme=self.theme, font_style='section'
        )
        self.game_control_title.grid(
            row=0, column=0, columnspan=2, sticky='w', padx=4, pady=(0, 6)
        )
        
        self.pass_button = ModernButton(self.game_control_card, theme=self.theme, width=120)
        self.pass_button.grid(row=1, column=0, padx=6, pady=6, sticky='ew')
        
        self.resign_button = ModernButton(self.game_control_card, theme=self.theme, width=120)
        self.resign_button.grid(row=1, column=1, padx=6, pady=6, sticky='ew')
        
        self.undo_button = ModernButton(self.game_control_card, theme=self.theme, width=120)
        self.undo_button.grid(row=2, column=0, padx=6, pady=6, sticky='ew')
        
        self.redo_button = ModernButton(self.game_control_card, theme=self.theme, width=120)
        self.redo_button.grid(row=2, column=1, padx=6, pady=6, sticky='ew')
 
        self.end_game_button = ModernButton(self.game_control_card, theme=self.theme, width=250)
        self.end_game_button.grid(row=3, column=0, columnspan=2, padx=6, pady=(12, 6), sticky='ew')
        
        # 分析控制 (使用 ModernCard)
        self.analysis_control_card = ModernCard(self, theme=self.theme, padding=12)
        self.analysis_control_card.pack(fill='x', padx=10, pady=(0, 10))
 
        self.analysis_control_card.columnconfigure(0, weight=1)
        self.analysis_control_card.columnconfigure(1, weight=1)

        self.analysis_control_title = ModernLabel(
            self.analysis_control_card, theme=self.theme, font_style='section'
        )
        self.analysis_control_title.grid(
            row=0, column=0, columnspan=2, sticky='w', padx=4, pady=(0, 6)
        )
        
        self.analyze_button = ModernButton(self.analysis_control_card, theme=self.theme, width=120)
        self.analyze_button.grid(row=1, column=0, padx=6, pady=6, sticky='ew')
        
        self.score_button = ModernButton(self.analysis_control_card, theme=self.theme, width=120)
        self.score_button.grid(row=1, column=1, padx=6, pady=6, sticky='ew')
        
        self.hint_button = ModernButton(self.analysis_control_card, theme=self.theme, width=120)
        self.hint_button.grid(row=2, column=0, padx=6, pady=6, sticky='ew')
        
        self.estimate_button = ModernButton(self.analysis_control_card, theme=self.theme, width=120)
        self.estimate_button.grid(row=2, column=1, padx=6, pady=6, sticky='ew')
        
        # 显示选项 (使用 ModernCard)
        self.display_card = ModernCard(self, theme=self.theme, padding=12)
        self.display_card.pack(fill='x', padx=10, pady=(0, 10))

        self.display_title = ModernLabel(self.display_card, theme=self.theme, font_style='section')
        self.display_title.pack(anchor='w', padx=2, pady=(0, 6))
        
        self.show_coordinates_var = tk.BooleanVar(value=self._display_defaults['show_coordinates'])
        self.show_coordinates_check = ttk.Checkbutton(
            self.display_card, variable=self.show_coordinates_var, style='Panel.TCheckbutton'
        )
        self.show_coordinates_check.pack(anchor='w', padx=2, pady=2)
        
        self.show_move_numbers_var = tk.BooleanVar(value=self._display_defaults['show_move_numbers'])
        self.show_move_numbers_check = ttk.Checkbutton(
            self.display_card, variable=self.show_move_numbers_var, style='Panel.TCheckbutton'
        )
        self.show_move_numbers_check.pack(anchor='w', padx=2, pady=2)
        
        self.show_territory_var = tk.BooleanVar(value=self._display_defaults['show_territory'])
        self.show_territory_check = ttk.Checkbutton(
            self.display_card, variable=self.show_territory_var, style='Panel.TCheckbutton'
        )
        self.show_territory_check.pack(anchor='w', padx=2, pady=2)
        
        self.show_influence_var = tk.BooleanVar(value=self._display_defaults['show_influence'])
        self.show_influence_check = ttk.Checkbutton(
            self.display_card, variable=self.show_influence_var, style='Panel.TCheckbutton'
        )
        self.show_influence_check.pack(anchor='w', padx=2, pady=2)
        
        # 绑定事件
        self._bind_events()
    
    def _bind_events(self):
        """绑定事件"""
        # ModernButton 是 Canvas，其 command 已经通过构造函数绑定了，
        # 但这里为了保持逻辑一致，也可以手动修改回调
        self.pass_button.command = lambda: self._callback('pass')
        self.resign_button.command = lambda: self._callback('resign')
        self.undo_button.command = lambda: self._callback('undo')
        self.redo_button.command = lambda: self._callback('redo')
        self.end_game_button.command = lambda: self._callback('end_game')
        self.analyze_button.command = lambda: self._callback('analyze')
        self.score_button.command = lambda: self._callback('score')
        self.hint_button.command = lambda: self._callback('hint')
        self.estimate_button.command = lambda: self._callback('estimate')
        
        self.show_coordinates_var.trace('w', 
            lambda *args: self._callback('show_coordinates', self.show_coordinates_var.get()))
        self.show_move_numbers_var.trace('w',
            lambda *args: self._callback('show_move_numbers', self.show_move_numbers_var.get()))
        self.show_territory_var.trace('w',
            lambda *args: self._callback('show_territory', self.show_territory_var.get()))
        self.show_influence_var.trace('w',
            lambda *args: self._callback('show_influence', self.show_influence_var.get()))
    
    # 修改 _callback 方法来使用已保存的回调
    def _callback(self, name: str, *args):
        """执行回调"""
        if name in self.callbacks and self.callbacks[name]:
            self.callbacks[name](*args)
    
    def _update_texts(self):
        """更新文本"""
        self.game_control_title.configure(text=self.translator.get('game_control'))
        self.analysis_control_title.configure(text=self.translator.get('analysis'))
        self.display_title.configure(text=self.translator.get('display'))

        self.pass_button.configure_text(self.translator.get('pass'))
        self.resign_button.configure_text(self.translator.get('resign'))
        self.undo_button.configure_text(self.translator.get('undo'))
        self.redo_button.configure_text(self.translator.get('redo'))
        self.end_game_button.configure_text(self.translator.get('end_game'))
        
        self.analyze_button.configure_text(self.translator.get('analyze'))
        self.score_button.configure_text(self.translator.get('score'))
        self.hint_button.configure_text(self.translator.get('hint'))
        self.estimate_button.configure_text(self.translator.get('estimate'))
        
        self.show_coordinates_check.configure(text=self.translator.get('show_coordinates'))
        self.show_move_numbers_check.configure(text=self.translator.get('show_move_numbers'))
        self.show_territory_check.configure(text=self.translator.get('show_territory'))
        self.show_influence_check.configure(text=self.translator.get('show_influence'))
    
    def set_callbacks(self, callbacks: Dict[str, Callable]):
        """设置回调函数"""
        self.callbacks.update(callbacks)
    
    def enable_controls(self, enabled: bool = True):
        """启用/禁用控件"""
        state = 'normal' if enabled else 'disabled'
        
        self.pass_button.set_state(state)
        self.resign_button.set_state(state)
        self.undo_button.set_state(state)
        self.redo_button.set_state(state)
        self.end_game_button.set_state(state)
        self.analyze_button.set_state(state)
        self.score_button.set_state(state)
        self.hint_button.set_state(state)
        self.estimate_button.set_state(state)

    # --- 兼容 main.py 的方法（旧版 UI 调用） ---

    def update_buttons(
        self,
        can_undo: bool = True,
        can_redo: bool = True,
        is_playing: bool = True,
        is_scoring: bool = False,
        is_teaching: bool = False,
    ):
        """根据游戏状态更新按钮可用性。"""
        play_state = 'normal' if is_playing else 'disabled'

        if is_scoring:
            # 进入数子阶段（通常由连续虚手触发）：仅保留“确认结果”以结束对局
            self.pass_button.set_state('disabled')
            self.resign_button.set_state('disabled')
            self.undo_button.set_state('disabled')
            self.redo_button.set_state('disabled')
            self.end_game_button.set_state('normal')
            self.analyze_button.set_state('disabled')
            self.score_button.set_state('disabled')
            self.hint_button.set_state('disabled')
            self.estimate_button.set_state('disabled')
            self.end_game_button.configure_text(self.translator.get('finish_scoring', self.translator.get('done')))
        elif is_teaching:
            self.pass_button.set_state(play_state)
            self.resign_button.set_state('disabled')
            self.undo_button.set_state('disabled')
            self.redo_button.set_state('disabled')
            self.end_game_button.set_state('normal')
            self.analyze_button.set_state(play_state)
            self.score_button.set_state(play_state)
            self.hint_button.set_state(play_state)
            self.estimate_button.set_state(play_state)
            self.end_game_button.configure_text(self.translator.get('exit_teaching', self.translator.get('done')))
        else:
            self.pass_button.set_state(play_state)
            self.resign_button.set_state(play_state)
            self.end_game_button.set_state(play_state)
            self.analyze_button.set_state(play_state)
            self.score_button.set_state(play_state)
            self.hint_button.set_state(play_state)
            self.estimate_button.set_state(play_state)
            self.score_button.configure_text(self.translator.get('score'))
            self.end_game_button.configure_text(self.translator.get('end_game'))
 
        if not is_scoring and not is_teaching:
            self.undo_button.set_state('normal' if can_undo else 'disabled')
            self.redo_button.set_state('normal' if can_redo else 'disabled')

    def set_pause_text(self, text: str):
        """兼容旧接口：部分UI版本包含暂停按钮；当前版本无该按钮，保留接口避免崩溃。"""
        if hasattr(self, 'pause_button'):
            self.pause_button.configure(text=text)

"""
UI面板组件（续）
分析面板和导航面板
"""

# 续接前面的代码...

class AnalysisPanel(BasePanel):
    """分析面板 - 显示AI分析、形势判断等"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._last_winrate = 50.0
        self._last_territory = (0, 0)
        self._last_analysis_info = (0.0, 0, 0)
        
        self._create_widgets()
        self._update_texts()
    
    def _create_widgets(self):
        """创建控件"""
        # 形势判断卡片
        self.situation_card = ModernCard(self, theme=self.theme, padding=12)
        self.situation_card.pack(fill='x', padx=10, pady=(0, 10))

        self.situation_title = ModernLabel(
            self.situation_card, theme=self.theme, font_style='section'
        )
        self.situation_title.pack(anchor='w', padx=2, pady=(0, 6))
        
        # 胜率条
        self.winrate_frame = ttk.Frame(self.situation_card, style='PanelCard.TFrame')
        self.winrate_frame.pack(fill='x', padx=2, pady=4)
        
        self.winrate_label = ttk.Label(self.winrate_frame, style='Panel.TLabel')
        self.winrate_label.pack()
        
        self.winrate_bar = ModernProgressBar(
            self.winrate_frame, theme=self.theme, height=25
        )
        self.winrate_bar.pack(fill='x', padx=5, pady=2)
        
        # 地盘估算
        self.territory_frame = ttk.Frame(self.situation_card, style='PanelCard.TFrame')
        self.territory_frame.pack(fill='x', padx=2, pady=4)
        
        self.black_territory_label = ttk.Label(self.territory_frame, style='Panel.TLabel')
        self.black_territory_label.pack(side='left', padx=5)
        
        self.white_territory_label = ttk.Label(self.territory_frame, style='Panel.TLabel')
        self.white_territory_label.pack(side='right', padx=5)
        
        self.territory_diff_label = ttk.Label(self.territory_frame, style='Panel.TLabel')
        self.territory_diff_label.pack()

        # 推荐着法
        self.suggestions_card = ModernCard(self, theme=self.theme, padding=12)
        self.suggestions_card.pack(fill='x', padx=10, pady=(0, 10))

        self.suggestions_title = ModernLabel(
            self.suggestions_card, theme=self.theme, font_style='section'
        )
        self.suggestions_title.pack(anchor='w', padx=2, pady=(0, 6))

        suggestions_frame = ttk.Frame(self.suggestions_card, style='PanelCard.TFrame')
        suggestions_frame.pack(fill='x')

        columns = ('move', 'winrate', 'visits')
        self.suggestions_tree = ttk.Treeview(
            suggestions_frame,
            columns=columns,
            show='tree headings',
            height=6,
            style='Panel.Treeview',
        )
        self.suggestions_tree.heading('#0', text='#')
        self.suggestions_tree.heading('move', text=self.translator.get('move'))
        self.suggestions_tree.heading('winrate', text=self.translator.get('win_rate'))
        self.suggestions_tree.heading('visits', text=self.translator.get('visits'))
        self.suggestions_tree.column('#0', width=30, anchor='center', stretch=False)
        self.suggestions_tree.column('move', width=60, anchor='center', stretch=True)
        self.suggestions_tree.column('winrate', width=70, anchor='center', stretch=False)
        self.suggestions_tree.column('visits', width=70, anchor='center', stretch=False)

        suggestions_scrollbar = ModernScrollbar(
            suggestions_frame, orient='vertical', command=self.suggestions_tree.yview, theme=self.theme
        )
        self.suggestions_tree.configure(yscrollcommand=suggestions_scrollbar.set)

        self.suggestions_tree.pack(side='left', fill='x', expand=True)
        suggestions_scrollbar.pack(side='right', fill='y')
        
        # Store for theme updates
        self.suggestions_scrollbar = suggestions_scrollbar

        # 分析信息
        self.analysis_info_card = ModernCard(self, theme=self.theme, padding=12)
        self.analysis_info_card.pack(fill='x', padx=10, pady=(0, 10))

        self.analysis_info_title = ModernLabel(
            self.analysis_info_card, theme=self.theme, font_style='section'
        )
        self.analysis_info_title.pack(anchor='w', padx=2, pady=(0, 6))

        info_frame = ttk.Frame(self.analysis_info_card, style='PanelCard.TFrame')
        info_frame.pack(fill='x')

        self.thinking_time_label = ttk.Label(info_frame, style='Panel.TLabel')
        self.thinking_time_label.pack(anchor='w', padx=2, pady=1)

        self.nodes_label = ttk.Label(info_frame, style='Panel.TLabel')
        self.nodes_label.pack(anchor='w', padx=2, pady=1)

        self.depth_label = ttk.Label(info_frame, style='Panel.TLabel')
        self.depth_label.pack(anchor='w', padx=2, pady=1)

    def _update_texts(self):
        """更新文本"""
        self.situation_title.configure(text=self.translator.get('situation'))
        self.suggestions_title.configure(text=self.translator.get('suggestions'))
        self.analysis_info_title.configure(text=self.translator.get('analysis_info'))

        self.suggestions_tree.heading('#0', text='#')
        self.suggestions_tree.heading('move', text=self.translator.get('move'))
        self.suggestions_tree.heading('winrate', text=self.translator.get('win_rate'))
        self.suggestions_tree.heading('visits', text=self.translator.get('visits'))

        self.update_winrate(self._last_winrate)
        self.update_territory(*self._last_territory)
        self.update_analysis_info(*self._last_analysis_info)

    def update_winrate(self, winrate: float):
        """更新胜率显示（黑方视角，0~100）。"""
        try:
            value = float(winrate)
        except Exception:
            value = 0.0
        if value <= 1.0:
            value *= 100.0
        value = max(0.0, min(100.0, value))
        self._last_winrate = value

        self.winrate_bar.set_value(value)
        label_value = f"{value:.1f}%"
        self.winrate_label.configure(
            text=self.translator.get('win_rate_format', value=label_value)
        )

    def update_territory(self, black: int, white: int):
        """更新地盘估算显示。"""
        try:
            black_value = int(black)
        except Exception:
            black_value = 0
        try:
            white_value = int(white)
        except Exception:
            white_value = 0

        self._last_territory = (black_value, white_value)

        points_label = self.translator.get('points')
        self.black_territory_label.configure(
            text=f"{self.translator.get('black')}: {black_value} {points_label}"
        )
        self.white_territory_label.configure(
            text=f"{self.translator.get('white')}: {white_value} {points_label}"
        )

        diff = black_value - white_value
        if diff == 0:
            diff_text = self.translator.get('even')
        else:
            leader = self.translator.get('black') if diff > 0 else self.translator.get('white')
            diff_text = self.translator.get(
                'score_lead_format',
                winner=leader,
                margin=float(abs(diff)),
                points=points_label,
            )
        self.territory_diff_label.configure(text=diff_text)

    def update_suggestions(self, suggestions: List[Dict[str, Any]]):
        """
        更新推荐着法
        
        Args:
            suggestions: 推荐列表，每项包含 {move, winrate, visits, pv}
        """
        # 清空列表
        for item in self.suggestions_tree.get_children():
            self.suggestions_tree.delete(item)
        
        # 添加新建议
        for i, suggestion in enumerate(suggestions[:10]):  # 最多显示10个
            move = suggestion.get('move', '')
            winrate = suggestion.get('winrate', 0.0)
            visits = suggestion.get('visits', 0)
            
            self.suggestions_tree.insert(
                '', 'end',
                text=str(i + 1),
                values=(move, f"{winrate:.1f}%", visits)
            )
    
    def update_analysis_info(self, thinking_time: float = 0.0,
                            nodes: int = 0, depth: int = 0):
        """更新分析信息"""
        try:
            thinking_time_value = float(thinking_time)
        except Exception:
            thinking_time_value = 0.0
        try:
            nodes_value = int(nodes)
        except Exception:
            nodes_value = 0
        try:
            depth_value = int(depth)
        except Exception:
            depth_value = 0

        self._last_analysis_info = (thinking_time_value, nodes_value, depth_value)

        self.thinking_time_label.configure(
            text=self.translator.get('analysis_thinking_time_format', value=thinking_time_value)
        )
        self.nodes_label.configure(
            text=self.translator.get('analysis_nodes_format', value=nodes_value)
        )
        self.depth_label.configure(
            text=self.translator.get('analysis_depth_format', value=depth_value)
        )

    # --- 兼容 main.py 的方法（旧版 UI 调用） ---

    def update_analysis(self, analysis: Any) -> None:
        """
        兼容旧接口：根据 analysis 对象刷新分析面板。

        支持 `features.analysis.PositionAnalysis`（推荐）或字典结构。
        """
        if not analysis:
            return

        # 兼容 dict / dataclass
        if isinstance(analysis, dict):
            winrate = analysis.get('winrate', 0.5)
            territory = analysis.get('territory_estimate', {}) or {}
            best_moves = analysis.get('best_moves', []) or []
            depth = analysis.get('analysis_depth', 0) or 0
        else:
            winrate = getattr(analysis, 'winrate', 0.5)
            territory = getattr(analysis, 'territory_estimate', {}) or {}
            best_moves = getattr(analysis, 'best_moves', []) or []
            depth = getattr(analysis, 'analysis_depth', 0) or 0

        # 胜率：PositionAnalysis 为 0~1；面板显示使用 0~100
        try:
            winrate_value = float(winrate)
        except Exception:
            winrate_value = 0.5
        winrate_percent = winrate_value * 100 if winrate_value <= 1.0 else winrate_value
        self.update_winrate(winrate_percent)

        # 领地估算
        try:
            black_terr = int(territory.get('black', 0) or 0)
            white_terr = int(territory.get('white', 0) or 0)
        except Exception:
            black_terr, white_terr = 0, 0
        self.update_territory(black_terr, white_terr)

        # 推荐着法
        suggestions: List[Dict[str, Any]] = []
        for move in best_moves:
            if isinstance(move, dict):
                move_text = move.get('move')
                if not move_text:
                    x, y = move.get('x', -1), move.get('y', -1)
                    move_text = f"{x},{y}"
                move_winrate = move.get('winrate', 0.0)
                visits = int(move.get('visits', 0) or 0)
            else:
                if hasattr(move, 'get_coordinate_string'):
                    move_text = move.get_coordinate_string()
                else:
                    x, y = getattr(move, 'x', -1), getattr(move, 'y', -1)
                    move_text = f"{x},{y}"
                move_winrate = getattr(move, 'winrate', 0.0)
                visits = int(getattr(move, 'visits', 0) or 0)

            try:
                move_winrate_value = float(move_winrate)
            except Exception:
                move_winrate_value = 0.0
            move_winrate_percent = move_winrate_value * 100 if move_winrate_value <= 1.0 else move_winrate_value

            suggestions.append(
                {
                    'move': move_text,
                    'winrate': move_winrate_percent,
                    'visits': visits,
                }
            )
        # 始终刷新（空列表也会清空旧内容，避免显示过期建议）
        self.update_suggestions(suggestions)

        # 分析信息：当前分析结果不包含真实 nodes/time，做轻量展示
        try:
            nodes = int(sum((m.get('visits', 0) if isinstance(m, dict) else getattr(m, 'visits', 0) or 0) for m in best_moves))
        except Exception:
            nodes = 0
        self.update_analysis_info(thinking_time=0.0, nodes=nodes, depth=int(depth or 0))


class NavigationPanel(BasePanel):
    """导航面板 - 用于浏览棋谱"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.callbacks: Dict[str, Callable] = {}
        self.total_moves = 0
        self.current_move = 0
        
        self._create_widgets()
        self._update_texts()
    
    def _create_widgets(self):
        """创建控件"""
        # 导航按钮框架
        self.nav_frame = ttk.LabelFrame(
            self, style='Panel.TLabelframe', padding=(8, 6)
        )
        self.nav_frame.pack(fill='x', padx=8, pady=(8, 6))
        
        # 按钮行
        button_frame = ttk.Frame(self.nav_frame, style='PanelCard.TFrame')
        button_frame.pack(pady=4)
        
        # 导航按钮
        self.first_button = ttk.Button(
            button_frame, text='|◀', width=4, style='Panel.TButton',
            command=lambda: self._callback('first')
        )
        self.first_button.pack(side='left', padx=1)
        
        self.prev10_button = ttk.Button(
            button_frame, text='◀◀', width=4, style='Panel.TButton',
            command=lambda: self._callback('prev10')
        )
        self.prev10_button.pack(side='left', padx=1)
        
        self.prev_button = ttk.Button(
            button_frame, text='◀', width=4, style='Panel.TButton',
            command=lambda: self._callback('prev')
        )
        self.prev_button.pack(side='left', padx=1)
        
        self.next_button = ttk.Button(
            button_frame, text='▶', width=4, style='Panel.TButton',
            command=lambda: self._callback('next')
        )
        self.next_button.pack(side='left', padx=1)
        
        self.next10_button = ttk.Button(
            button_frame, text='▶▶', width=4, style='Panel.TButton',
            command=lambda: self._callback('next10')
        )
        self.next10_button.pack(side='left', padx=1)
        
        self.last_button = ttk.Button(
            button_frame, text='▶|', width=4, style='Panel.TButton',
            command=lambda: self._callback('last')
        )
        self.last_button.pack(side='left', padx=1)
        
        # 进度条
        self.progress_frame = ttk.Frame(self.nav_frame, style='PanelCard.TFrame')
        self.progress_frame.pack(fill='x', padx=2, pady=4)
        
        self.progress_label = ttk.Label(self.progress_frame, style='Panel.TLabel')
        self.progress_label.pack(side='left', padx=5)
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_scale = ttk.Scale(
            self.progress_frame,
            from_=0, to=100,
            variable=self.progress_var,
            orient='horizontal',
            command=self._on_scale_change
        )
        self.progress_scale.pack(side='left', fill='x', expand=True, padx=5)
        
        self.move_label = ttk.Label(self.progress_frame, style='Panel.TLabel')
        self.move_label.pack(side='left', padx=5)
        
        # 分支控制框架
        self.branch_frame = ttk.LabelFrame(
            self, style='Panel.TLabelframe', padding=(8, 6)
        )
        self.branch_frame.pack(fill='x', padx=8, pady=(0, 6))
        
        # 分支选择
        self.branch_combo = ttk.Combobox(
            self.branch_frame, state='readonly', width=20
        )
        self.branch_combo.pack(padx=5, pady=5)
        
        # 分支操作按钮
        branch_button_frame = ttk.Frame(self.branch_frame, style='PanelCard.TFrame')
        branch_button_frame.pack()
        
        self.create_branch_button = ttk.Button(
            branch_button_frame, width=10, style='Panel.TButton',
            command=lambda: self._callback('create_branch')
        )
        self.create_branch_button.pack(side='left', padx=2, pady=2)
        
        self.delete_branch_button = ttk.Button(
            branch_button_frame, width=10, style='Panel.TButton',
            command=lambda: self._callback('delete_branch')
        )
        self.delete_branch_button.pack(side='left', padx=2, pady=2)
        
        # 自动播放框架
        self.autoplay_frame = ttk.LabelFrame(
            self, style='Panel.TLabelframe', padding=(8, 6)
        )
        self.autoplay_frame.pack(fill='x', padx=8, pady=(0, 8))
        
        self.autoplay_button = ttk.Button(
            self.autoplay_frame, width=10, style='Panel.TButton',
            command=lambda: self._callback('toggle_autoplay')
        )
        self.autoplay_button.pack(side='left', padx=5, pady=5)
        
        self.speed_label = ttk.Label(self.autoplay_frame, style='Panel.TLabel')
        self.speed_label.pack(side='left', padx=5)
        
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = ttk.Scale(
            self.autoplay_frame,
            from_=0.5, to=5.0,
            variable=self.speed_var,
            orient='horizontal',
            length=100
        )
        self.speed_scale.pack(side='left', padx=5)
        
        # 初始化状态
        self.update_position(0, 0)
    
    def _update_texts(self):
        """更新文本"""
        self.nav_frame.configure(text=self.translator.get('navigation'))
        self.branch_frame.configure(text=self.translator.get('branches'))
        self.autoplay_frame.configure(text=self.translator.get('auto_play'))
        
        self.create_branch_button.configure(text=self.translator.get('create'))
        self.delete_branch_button.configure(text=self.translator.get('delete'))
        self.autoplay_button.configure(text=self.translator.get('play'))
        self.speed_label.configure(text=self.translator.get('speed'))
    
    def _callback(self, name: str, *args):
        """执行回调"""
        if name in self.callbacks:
            self.callbacks[name](*args)
    
    def _on_scale_change(self, value):
        """处理进度条变化"""
        move_num = int(float(value) * self.total_moves / 100)
        self._callback('goto', move_num)
    
    def set_callbacks(self, callbacks: Dict[str, Callable]):
        """设置回调函数"""
        self.callbacks.update(callbacks)
    
    def update_position(self, current: int, total: int):
        """更新位置显示"""
        self.current_move = current
        self.total_moves = total
        
        # 更新标签
        self.move_label.configure(text=f"{current}/{total}")
        
        # 更新进度条
        if total > 0:
            progress = int(current * 100 / total)
            self.progress_var.set(progress)
        else:
            self.progress_var.set(0)
        
        # 更新按钮状态
        self.first_button.configure(state='normal' if current > 0 else 'disabled')
        self.prev10_button.configure(state='normal' if current > 0 else 'disabled')
        self.prev_button.configure(state='normal' if current > 0 else 'disabled')
        self.next_button.configure(state='normal' if current < total else 'disabled')
        self.next10_button.configure(state='normal' if current < total else 'disabled')
        self.last_button.configure(state='normal' if current < total else 'disabled')
    
    def update_branches(self, branches: List[str], current_branch: str = None):
        """更新分支列表"""
        self.branch_combo['values'] = branches
        if current_branch:
            self.branch_combo.set(current_branch)
    
    def set_autoplay_state(self, is_playing: bool):
        """设置自动播放状态"""
        if is_playing:
            self.autoplay_button.configure(text=self.translator.get('pause'))
        else:
            self.autoplay_button.configure(text=self.translator.get('play'))


# 导出所有面板类
__all__ = ['InfoPanel', 'ControlPanel', 'AnalysisPanel', 'NavigationPanel']
