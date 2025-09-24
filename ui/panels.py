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
        
        # 配置面板样式
        style.configure('Panel.TFrame', 
                       background=self.theme.ui_panel_background,
                       relief='raised',
                       borderwidth=1)
        
        style.configure('Panel.TLabel',
                       background=self.theme.ui_panel_background,
                       foreground=self.theme.ui_text_primary)
        
        style.configure('Panel.TLabelframe',
                       background=self.theme.ui_panel_background,
                       foreground=self.theme.ui_text_primary)
        
        style.configure('Panel.TLabelframe.Label',
                       background=self.theme.ui_panel_background,
                       foreground=self.theme.ui_text_primary)
        
        self.configure(style='Panel.TFrame')
    
    def update_translator(self, translator: Translator):
        """更新翻译器"""
        self.translator = translator
        self._update_texts()
    
    def update_theme(self, theme: Theme):
        """更新主题"""
        self.theme = theme
        self._apply_theme()
    
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
        # 玩家信息框架
        self.players_frame = ttk.LabelFrame(
            self, style='Panel.TLabelframe'
        )
        self.players_frame.pack(fill='x', padx=5, pady=5)
        
        # 黑方信息
        self.black_frame = ttk.Frame(self.players_frame)
        self.black_frame.pack(fill='x', padx=5, pady=2)
        
        # 黑方图标
        self.black_stone_icon = tk.Canvas(self.black_frame, width=20, height=20,
                                         bg=self.theme.ui_panel_background,
                                         highlightthickness=0)
        self.black_stone_icon.pack(side='left', padx=(0, 5))
        self.black_stone_icon.create_oval(2, 2, 18, 18, fill='black', outline='#333')
        
        self.black_name_label = ttk.Label(self.black_frame, style='Panel.TLabel')
        self.black_name_label.pack(side='left')
        
        self.black_info_frame = ttk.Frame(self.black_frame)
        self.black_info_frame.pack(side='right')
        
        self.black_time_label = ttk.Label(self.black_info_frame, style='Panel.TLabel')
        self.black_time_label.pack(side='right')
        
        self.black_captured_label = ttk.Label(self.black_info_frame, style='Panel.TLabel')
        self.black_captured_label.pack(side='right', padx=(0, 10))
        
        # 白方信息
        self.white_frame = ttk.Frame(self.players_frame)
        self.white_frame.pack(fill='x', padx=5, pady=2)
        
        # 白方图标
        self.white_stone_icon = tk.Canvas(self.white_frame, width=20, height=20,
                                         bg=self.theme.ui_panel_background,
                                         highlightthickness=0)
        self.white_stone_icon.pack(side='left', padx=(0, 5))
        self.white_stone_icon.create_oval(2, 2, 18, 18, fill='white', outline='#ccc')
        
        self.white_name_label = ttk.Label(self.white_frame, style='Panel.TLabel')
        self.white_name_label.pack(side='left')
        
        self.white_info_frame = ttk.Frame(self.white_frame)
        self.white_info_frame.pack(side='right')
        
        self.white_time_label = ttk.Label(self.white_info_frame, style='Panel.TLabel')
        self.white_time_label.pack(side='right')
        
        self.white_captured_label = ttk.Label(self.white_info_frame, style='Panel.TLabel')
        self.white_captured_label.pack(side='right', padx=(0, 10))
        
        # 游戏信息框架
        self.game_frame = ttk.LabelFrame(
            self, style='Panel.TLabelframe'
        )
        self.game_frame.pack(fill='x', padx=5, pady=5)
        
        self.current_player_frame = ttk.Frame(self.game_frame)
        self.current_player_frame.pack(fill='x', padx=5, pady=2)
        
        self.current_player_label = ttk.Label(self.current_player_frame, style='Panel.TLabel')
        self.current_player_label.pack(side='left')
        
        # 当前玩家指示器
        self.current_indicator = tk.Canvas(self.current_player_frame, 
                                          width=16, height=16,
                                          bg=self.theme.ui_panel_background,
                                          highlightthickness=0)
        self.current_indicator.pack(side='left', padx=5)
        
        self.move_number_label = ttk.Label(self.game_frame, style='Panel.TLabel')
        self.move_number_label.pack(padx=5, pady=2)
        
        self.ko_label = ttk.Label(self.game_frame, style='Panel.TLabel')
        self.ko_label.pack(padx=5, pady=2)
        
        self.phase_label = ttk.Label(self.game_frame, style='Panel.TLabel')
        self.phase_label.pack(padx=5, pady=2)
        
        # 设置默认值
        self.update_player_info('Black', 'White')
        self.update_game_info('black', 0)
    
    def _update_texts(self):
        """更新文本"""
        self.players_frame.configure(text=self.translator.get('players'))
        self.game_frame.configure(text=self.translator.get('game_info'))
        self.current_player_label.configure(
            text=f"{self.translator.get('current_player')}:"
        )
        self.phase_label.configure(
            text=f"{self.translator.get('phase')}: {self.translator.get('playing')}"
        )
    
    def update_player_info(self, black_name: str, white_name: str,
                          black_time: str = "∞", white_time: str = "∞",
                          black_captured: int = 0, white_captured: int = 0):
        """更新玩家信息"""
        self.black_name_label.configure(text=black_name)
        self.white_name_label.configure(text=white_name)
        
        self.black_time_label.configure(text=f"⏱ {black_time}")
        self.white_time_label.configure(text=f"⏱ {white_time}")
        
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
                 on_pause=None,
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
            'pause': on_pause
        }
        
        # 只传递有效的 kwargs 给父类
        super().__init__(parent, **kwargs)
        
        self._create_widgets()
        self._update_texts()
    
    def _create_widgets(self):
        """创建控件"""
        # 游戏控制
        self.game_control_frame = ttk.LabelFrame(
            self, style='Panel.TLabelframe'
        )
        self.game_control_frame.pack(fill='x', padx=5, pady=5)
        
        # 按钮网格
        button_style = {'width': 8}
        
        self.pass_button = ttk.Button(self.game_control_frame, **button_style)
        self.pass_button.grid(row=0, column=0, padx=2, pady=2)
        
        self.resign_button = ttk.Button(self.game_control_frame, **button_style)
        self.resign_button.grid(row=0, column=1, padx=2, pady=2)
        
        self.undo_button = ttk.Button(self.game_control_frame, **button_style)
        self.undo_button.grid(row=1, column=0, padx=2, pady=2)
        
        self.redo_button = ttk.Button(self.game_control_frame, **button_style)
        self.redo_button.grid(row=1, column=1, padx=2, pady=2)
        
        # 分析控制
        self.analysis_control_frame = ttk.LabelFrame(
            self, style='Panel.TLabelframe'
        )
        self.analysis_control_frame.pack(fill='x', padx=5, pady=5)
        
        self.analyze_button = ttk.Button(self.analysis_control_frame, **button_style)
        self.analyze_button.grid(row=0, column=0, padx=2, pady=2)
        
        self.score_button = ttk.Button(self.analysis_control_frame, **button_style)
        self.score_button.grid(row=0, column=1, padx=2, pady=2)
        
        self.hint_button = ttk.Button(self.analysis_control_frame, **button_style)
        self.hint_button.grid(row=1, column=0, padx=2, pady=2)
        
        self.estimate_button = ttk.Button(self.analysis_control_frame, **button_style)
        self.estimate_button.grid(row=1, column=1, padx=2, pady=2)
        
        # 显示选项
        self.display_frame = ttk.LabelFrame(
            self, style='Panel.TLabelframe'
        )
        self.display_frame.pack(fill='x', padx=5, pady=5)
        
        self.show_coordinates_var = tk.BooleanVar(value=True)
        self.show_coordinates_check = ttk.Checkbutton(
            self.display_frame, variable=self.show_coordinates_var
        )
        self.show_coordinates_check.pack(anchor='w', padx=5, pady=2)
        
        self.show_move_numbers_var = tk.BooleanVar(value=False)
        self.show_move_numbers_check = ttk.Checkbutton(
            self.display_frame, variable=self.show_move_numbers_var
        )
        self.show_move_numbers_check.pack(anchor='w', padx=5, pady=2)
        
        self.show_territory_var = tk.BooleanVar(value=False)
        self.show_territory_check = ttk.Checkbutton(
            self.display_frame, variable=self.show_territory_var
        )
        self.show_territory_check.pack(anchor='w', padx=5, pady=2)
        
        self.show_influence_var = tk.BooleanVar(value=False)
        self.show_influence_check = ttk.Checkbutton(
            self.display_frame, variable=self.show_influence_var
        )
        self.show_influence_check.pack(anchor='w', padx=5, pady=2)
        
        # 绑定事件
        self._bind_events()
    
    def _bind_events(self):
        """绑定事件"""
        self.pass_button.configure(command=lambda: self._callback('pass'))
        self.resign_button.configure(command=lambda: self._callback('resign'))
        self.undo_button.configure(command=lambda: self._callback('undo'))
        self.redo_button.configure(command=lambda: self._callback('redo'))
        self.analyze_button.configure(command=lambda: self._callback('analyze'))
        self.score_button.configure(command=lambda: self._callback('score'))
        self.hint_button.configure(command=lambda: self._callback('hint'))
        self.estimate_button.configure(command=lambda: self._callback('estimate'))
        
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
        self.game_control_frame.configure(text=self.translator.get('game_control'))
        self.pass_button.configure(text=self.translator.get('pass'))
        self.resign_button.configure(text=self.translator.get('resign'))
        self.undo_button.configure(text=self.translator.get('undo'))
        self.redo_button.configure(text=self.translator.get('redo'))
        
        self.analysis_control_frame.configure(text=self.translator.get('analysis'))
        self.analyze_button.configure(text=self.translator.get('analyze'))
        self.score_button.configure(text=self.translator.get('score'))
        self.hint_button.configure(text=self.translator.get('hint'))
        self.estimate_button.configure(text=self.translator.get('estimate'))
        
        self.display_frame.configure(text=self.translator.get('display'))
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
        
        self.pass_button.configure(state=state)
        self.resign_button.configure(state=state)
        self.undo_button.configure(state=state)
        self.redo_button.configure(state=state)
        self.analyze_button.configure(state=state)
        self.score_button.configure(state=state)
        self.hint_button.configure(state=state)
        self.estimate_button.configure(state=state)

"""
UI面板组件（续）
分析面板和导航面板
"""

# 续接前面的代码...

class AnalysisPanel(BasePanel):
    """分析面板 - 显示AI分析、形势判断等"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self._create_widgets()
        self._update_texts()
    
    def _create_widgets(self):
        """创建控件"""
        # 形势判断框架
        self.situation_frame = ttk.LabelFrame(
            self, style='Panel.TLabelframe'
        )
        self.situation_frame.pack(fill='x', padx=5, pady=5)
        
        # 胜率条
        self.winrate_frame = ttk.Frame(self.situation_frame)
        self.winrate_frame.pack(fill='x', padx=5, pady=5)
        
        self.winrate_label = ttk.Label(self.winrate_frame, style='Panel.TLabel')
        self.winrate_label.pack()
        
        self.winrate_canvas = tk.Canvas(
            self.winrate_frame, height=30,
            bg=self.theme.ui_panel_background,
            highlightthickness=1,
            highlightbackground=self.theme.ui_panel_border
        )
        self.winrate_canvas.pack(fill='x', padx=5, pady=2)
        
        # 地盘估算
        self.territory_frame = ttk.Frame(self.situation_frame)
        self.territory_frame.pack(fill='x', padx=5, pady=5)
        
        self.black_territory_label = ttk.Label(self.territory_frame, style='Panel.TLabel')
        self.black_territory_label.pack(side='left', padx=5)
        
        self.white_territory_label = ttk.Label(self.territory_frame, style='Panel.TLabel')
        self.white_territory_label.pack(side='right', padx=5)
        
        self.territory_diff_label = ttk.Label(self.territory_frame, style='Panel.TLabel')
        self.territory_diff_label.pack()
        
        # 推荐着法框架
        self.suggestions_frame = ttk.LabelFrame(
            self, style='Panel.TLabelframe'
        )
        self.suggestions_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 着法列表
        self.suggestions_tree = ttk.Treeview(
            self.suggestions_frame,
            columns=('move', 'winrate', 'visits'),
            show='tree headings',
            height=6
        )
        
        self.suggestions_tree.heading('#0', text='#')
        self.suggestions_tree.heading('move', text=self.translator.get('move'))
        self.suggestions_tree.heading('winrate', text=self.translator.get('win_rate'))
        self.suggestions_tree.heading('visits', text=self.translator.get('visits'))
        
        self.suggestions_tree.column('#0', width=30, stretch=False)
        self.suggestions_tree.column('move', width=60)
        self.suggestions_tree.column('winrate', width=80)
        self.suggestions_tree.column('visits', width=80)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(self.suggestions_frame, orient='vertical',
                                 command=self.suggestions_tree.yview)
        self.suggestions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.suggestions_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 分析信息框架
        self.info_frame = ttk.LabelFrame(
            self, style='Panel.TLabelframe'
        )
        self.info_frame.pack(fill='x', padx=5, pady=5)
        
        self.thinking_time_label = ttk.Label(self.info_frame, style='Panel.TLabel')
        self.thinking_time_label.pack(padx=5, pady=2)
        
        self.nodes_label = ttk.Label(self.info_frame, style='Panel.TLabel')
        self.nodes_label.pack(padx=5, pady=2)
        
        self.depth_label = ttk.Label(self.info_frame, style='Panel.TLabel')
        self.depth_label.pack(padx=5, pady=2)
        
        # 初始化显示
        self.update_winrate(50.0)
    
    def _update_texts(self):
        """更新文本"""
        self.situation_frame.configure(text=self.translator.get('situation'))
        self.suggestions_frame.configure(text=self.translator.get('suggestions'))
        self.info_frame.configure(text=self.translator.get('analysis_info'))
        
        self.suggestions_tree.heading('move', text=self.translator.get('move'))
        self.suggestions_tree.heading('winrate', text=self.translator.get('win_rate'))
        self.suggestions_tree.heading('visits', text=self.translator.get('visits'))
    
    def update_winrate(self, winrate: float):
        """
        更新胜率显示
        
        Args:
            winrate: 黑方胜率（0-100）
        """
        self.winrate_label.configure(
            text=f"{self.translator.get('black')}: {winrate:.1f}% | "
                 f"{self.translator.get('white')}: {100-winrate:.1f}%"
        )
        
        # 绘制胜率条
        self.winrate_canvas.delete('all')
        width = self.winrate_canvas.winfo_width()
        if width <= 1:
            width = 200  # 默认宽度
        
        height = 30
        black_width = int(width * winrate / 100)
        
        # 黑方部分
        self.winrate_canvas.create_rectangle(
            0, 0, black_width, height,
            fill='#2c2c2c', outline=''
        )
        
        # 白方部分
        self.winrate_canvas.create_rectangle(
            black_width, 0, width, height,
            fill='#e0e0e0', outline=''
        )
        
        # 中线
        self.winrate_canvas.create_line(
            width // 2, 0, width // 2, height,
            fill='red', width=1
        )
        
        # 显示数值
        if winrate > 50:
            text_x = black_width // 2
            text_color = 'white'
            text = f"{winrate:.1f}%"
        else:
            text_x = black_width + (width - black_width) // 2
            text_color = 'black'
            text = f"{100-winrate:.1f}%"
        
        self.winrate_canvas.create_text(
            text_x, height // 2,
            text=text, fill=text_color,
            font=('Arial', 10, 'bold')
        )
    
    def update_territory(self, black_territory: int, white_territory: int):
        """更新地盘估算"""
        self.black_territory_label.configure(
            text=f"{self.translator.get('black')}: {black_territory}"
        )
        self.white_territory_label.configure(
            text=f"{self.translator.get('white')}: {white_territory}"
        )
        
        diff = black_territory - white_territory
        if diff > 0:
            diff_text = f"{self.translator.get('black')} +{diff}"
        elif diff < 0:
            diff_text = f"{self.translator.get('white')} +{-diff}"
        else:
            diff_text = self.translator.get('even')
        
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
        self.thinking_time_label.configure(
            text=f"{self.translator.get('thinking_time')}: {thinking_time:.1f}s"
        )
        self.nodes_label.configure(
            text=f"{self.translator.get('nodes_analyzed')}: {nodes:,}"
        )
        self.depth_label.configure(
            text=f"{self.translator.get('search_depth')}: {depth}"
        )


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
            self, style='Panel.TLabelframe'
        )
        self.nav_frame.pack(fill='x', padx=5, pady=5)
        
        # 按钮行
        button_frame = ttk.Frame(self.nav_frame)
        button_frame.pack(pady=5)
        
        # 导航按钮
        self.first_button = ttk.Button(
            button_frame, text='|◀', width=4,
            command=lambda: self._callback('first')
        )
        self.first_button.pack(side='left', padx=1)
        
        self.prev10_button = ttk.Button(
            button_frame, text='◀◀', width=4,
            command=lambda: self._callback('prev10')
        )
        self.prev10_button.pack(side='left', padx=1)
        
        self.prev_button = ttk.Button(
            button_frame, text='◀', width=4,
            command=lambda: self._callback('prev')
        )
        self.prev_button.pack(side='left', padx=1)
        
        self.next_button = ttk.Button(
            button_frame, text='▶', width=4,
            command=lambda: self._callback('next')
        )
        self.next_button.pack(side='left', padx=1)
        
        self.next10_button = ttk.Button(
            button_frame, text='▶▶', width=4,
            command=lambda: self._callback('next10')
        )
        self.next10_button.pack(side='left', padx=1)
        
        self.last_button = ttk.Button(
            button_frame, text='▶|', width=4,
            command=lambda: self._callback('last')
        )
        self.last_button.pack(side='left', padx=1)
        
        # 进度条
        self.progress_frame = ttk.Frame(self.nav_frame)
        self.progress_frame.pack(fill='x', padx=5, pady=5)
        
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
            self, style='Panel.TLabelframe'
        )
        self.branch_frame.pack(fill='x', padx=5, pady=5)
        
        # 分支选择
        self.branch_combo = ttk.Combobox(
            self.branch_frame, state='readonly', width=20
        )
        self.branch_combo.pack(padx=5, pady=5)
        
        # 分支操作按钮
        branch_button_frame = ttk.Frame(self.branch_frame)
        branch_button_frame.pack()
        
        self.create_branch_button = ttk.Button(
            branch_button_frame, width=10,
            command=lambda: self._callback('create_branch')
        )
        self.create_branch_button.pack(side='left', padx=2, pady=2)
        
        self.delete_branch_button = ttk.Button(
            branch_button_frame, width=10,
            command=lambda: self._callback('delete_branch')
        )
        self.delete_branch_button.pack(side='left', padx=2, pady=2)
        
        # 自动播放框架
        self.autoplay_frame = ttk.LabelFrame(
            self, style='Panel.TLabelframe'
        )
        self.autoplay_frame.pack(fill='x', padx=5, pady=5)
        
        self.autoplay_button = ttk.Button(
            self.autoplay_frame, width=10,
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