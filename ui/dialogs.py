"""
对话框组件
包含新游戏、设置、关于等对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any, List
from datetime import datetime

from .translator import Translator
from .themes import Theme, ThemeManager


class BaseDialog(tk.Toplevel):
    """对话框基类"""
    
    def __init__(self, parent, title: str = "", 
                 translator: Optional[Translator] = None,
                 theme: Optional[Theme] = None,
                 modal: bool = True,
                 auto_wait: bool = True,
                 resizable: bool = True):
        super().__init__(parent)
        
        self.title(title)
        self.translator = translator or Translator()
        self.theme = theme or Theme(name='default')
        self.result = None
        self._modal = modal
        
        # 设置模态
        if modal:
            self.transient(parent)
            self.grab_set()

        # 关闭窗口等同取消
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # 配置窗口
        self.resizable(resizable, resizable)
        
        # 应用主题
        self._apply_theme()
        
        # 创建内容
        self._create_widgets()
        
        # 居中窗口
        self._center_window()
        
        # 绑定ESC键
        self.bind('<Escape>', lambda e: self.cancel())

        # 重要：如果是模态对话框，需等待用户操作后再返回，否则调用方读取 result 会永远是 None
        if self._modal and auto_wait:
            self.wait_window()
    
    def _apply_theme(self):
        """应用主题"""
        self.configure(bg=self.theme.ui_background)
        
        style = ttk.Style(self)
        style.configure('Dialog.TFrame', background=self.theme.ui_background)
        style.configure('Dialog.TLabel', 
                       background=self.theme.ui_background,
                       foreground=self.theme.ui_text_primary)
        style.configure('Dialog.TLabelframe',
                       background=self.theme.ui_background,
                       foreground=self.theme.ui_text_primary)
    
    def _center_window(self):
        """居中窗口"""
        self.update_idletasks()
        
        # 获取屏幕尺寸
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # 获取窗口尺寸
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        # 计算位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f'+{x}+{y}')
    
    def _create_widgets(self):
        """创建控件（子类实现）"""
        pass
    
    def ok(self):
        """确定按钮处理"""
        self.result = self._get_result()
        self.destroy()
    
    def cancel(self):
        """取消按钮处理"""
        self.result = None
        self.destroy()
    
    def _get_result(self) -> Any:
        """获取结果（子类实现）"""
        return None


class NewGameDialog(BaseDialog):
    """新游戏对话框"""
    
    def __init__(self, parent,  config=None, **kwargs):
        self.config = config or {}
        
        # 过滤掉 config，只传递 BaseDialog 需要的参数给父类
        # 注意这里不再将 config 包含在 kwargs 中
        super().__init__(parent, 
                        title=kwargs.get('translator', Translator()).get('new_game'),
                        translator=kwargs.get('translator'),
                        theme=kwargs.get('theme'),
                        modal=kwargs.get('modal', True))    

    def _config_get(self, key: str, default=None):
        """兼容 dict 与 dataclass 的配置读取（仅用于新对局对话框默认值）。"""
        try:
            if isinstance(self.config, dict):
                return self.config.get(key, default)
        except Exception:
            pass

        # 支持 GameConfig dataclass：key 形如 'rules.default_rules'
        try:
            parts = str(key).split('.')
            value = self.config
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return default
            return value
        except Exception:
            return default

    def _setup_option_maps(self):
        """初始化下拉框的显示值<->内部 key 映射。"""
        # 规则（对话框目前仅提供三种）
        self._rules_keys = ['chinese', 'japanese', 'aga']
        self._rules_label_by_key = {k: self.translator.get(k) for k in self._rules_keys}
        self._rules_key_by_label = {v: k for k, v in self._rules_label_by_key.items()}

        # 时间控制
        self._time_keys = ['none', 'absolute', 'byoyomi', 'canadian']
        self._time_label_by_key = {k: self.translator.get(k) for k in self._time_keys}
        self._time_key_by_label = {v: k for k, v in self._time_label_by_key.items()}

        # AI 难度
        self._ai_level_keys = ['easy', 'medium', 'hard', 'expert']
        self._ai_level_label_by_key = {k: self.translator.get(k) for k in self._ai_level_keys}
        self._ai_level_key_by_label = {v: k for k, v in self._ai_level_label_by_key.items()}

    def _rules_key(self) -> str:
        """当前规则的内部 key。"""
        try:
            label = self.rules_var.get()
        except Exception:
            label = ''
        return getattr(self, '_rules_key_by_label', {}).get(label, label)

    def _time_control_key(self) -> str:
        """当前时间控制的内部 key。"""
        try:
            label = self.time_control_var.get()
        except Exception:
            label = ''
        return getattr(self, '_time_key_by_label', {}).get(label, label)

    def _ai_level_key(self, label_or_key: str) -> str:
        """AI 难度的内部 key。"""
        return getattr(self, '_ai_level_key_by_label', {}).get(label_or_key, label_or_key)
        
    def _create_widgets(self):
        """创建控件"""
        self._setup_option_maps()
        # 主框架
        main_frame = ttk.Frame(self, style='Dialog.TFrame', padding=10)
        main_frame.pack(fill='both', expand=True)
        
        # 游戏模式
        mode_frame = ttk.LabelFrame(main_frame, text=self.translator.get('game_mode'),
                                   style='Dialog.TLabelframe')
        mode_frame.pack(fill='x', pady=5)
        
        self.mode_var = tk.StringVar(value='human_vs_human')
        
        ttk.Radiobutton(mode_frame, text=self.translator.get('human_vs_human'),
                       variable=self.mode_var, value='human_vs_human',
                       command=self._on_mode_change).pack(anchor='w', padx=10, pady=2)
        
        ttk.Radiobutton(mode_frame, text=self.translator.get('human_vs_ai'),
                       variable=self.mode_var, value='human_vs_ai',
                       command=self._on_mode_change).pack(anchor='w', padx=10, pady=2)
        
        ttk.Radiobutton(mode_frame, text=self.translator.get('ai_vs_human'),
                       variable=self.mode_var, value='ai_vs_human',
                       command=self._on_mode_change).pack(anchor='w', padx=10, pady=2)
        
        ttk.Radiobutton(mode_frame, text=self.translator.get('ai_vs_ai'),
                       variable=self.mode_var, value='ai_vs_ai',
                       command=self._on_mode_change).pack(anchor='w', padx=10, pady=2)
        
        # 玩家设置
        player_frame = ttk.LabelFrame(main_frame, text=self.translator.get('players'),
                                     style='Dialog.TLabelframe')
        player_frame.pack(fill='x', pady=5)
        
        # 黑方
        ttk.Label(player_frame, text=self.translator.get('black_player'),
                 style='Dialog.TLabel').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        
        self.black_name_var = tk.StringVar(value=self.translator.get('player_1'))
        self.black_name_entry = ttk.Entry(player_frame, textvariable=self.black_name_var, width=20)
        self.black_name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.black_ai_level_var = tk.StringVar(
            value=self._ai_level_label_by_key.get('medium', 'medium')
        )
        self.black_ai_combo = ttk.Combobox(player_frame, textvariable=self.black_ai_level_var,
                                          values=[self._ai_level_label_by_key[k] for k in self._ai_level_keys],
                                          state='readonly', width=10)
        self.black_ai_combo.grid(row=0, column=2, padx=5, pady=5)
        self.black_ai_combo.grid_remove()  # 初始隐藏
        
        # 白方
        ttk.Label(player_frame, text=self.translator.get('white_player'),
                 style='Dialog.TLabel').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        
        self.white_name_var = tk.StringVar(value=self.translator.get('player_2'))
        self.white_name_entry = ttk.Entry(player_frame, textvariable=self.white_name_var, width=20)
        self.white_name_entry.grid(row=1, column=1, padx=5, pady=5)
        
        self.white_ai_level_var = tk.StringVar(
            value=self._ai_level_label_by_key.get('medium', 'medium')
        )
        self.white_ai_combo = ttk.Combobox(player_frame, textvariable=self.white_ai_level_var,
                                          values=[self._ai_level_label_by_key[k] for k in self._ai_level_keys],
                                          state='readonly', width=10)
        self.white_ai_combo.grid(row=1, column=2, padx=5, pady=5)
        self.white_ai_combo.grid_remove()  # 初始隐藏
        
        # 游戏设置
        settings_frame = ttk.LabelFrame(main_frame, text=self.translator.get('game_settings'),
                                       style='Dialog.TLabelframe')
        settings_frame.pack(fill='x', pady=5)
        
        # 棋盘大小
        ttk.Label(settings_frame, text=self.translator.get('board_size'),
                 style='Dialog.TLabel').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        
        default_board_size = int(self._config_get('rules.default_board_size', 19) or 19)
        self.board_size_var = tk.IntVar(value=default_board_size)
        board_size_combo = ttk.Combobox(settings_frame, textvariable=self.board_size_var,
                                       values=[9, 13, 19], state='readonly', width=10)
        board_size_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # 规则
        ttk.Label(settings_frame, text=self.translator.get('rules'),
                 style='Dialog.TLabel').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        
        default_rules_key = str(self._config_get('rules.default_rules', 'chinese') or 'chinese')
        self.rules_var = tk.StringVar(
            value=self._rules_label_by_key.get(default_rules_key, self._rules_label_by_key.get('chinese', 'chinese'))
        )
        rules_combo = ttk.Combobox(settings_frame, textvariable=self.rules_var,
                                  values=[self._rules_label_by_key[k] for k in self._rules_keys],
                                  state='readonly', width=10)
        rules_combo.grid(row=1, column=1, padx=5, pady=5)
        rules_combo.bind('<<ComboboxSelected>>', self._on_rules_change)
        
        # 贴目
        ttk.Label(settings_frame, text=self.translator.get('komi'),
                 style='Dialog.TLabel').grid(row=2, column=0, sticky='w', padx=10, pady=5)
        
        default_komi = float(self._config_get('rules.default_komi', 7.5) or 7.5)
        self.komi_var = tk.DoubleVar(value=default_komi)
        komi_spin = ttk.Spinbox(settings_frame, textvariable=self.komi_var,
                               from_=0, to=20, increment=0.5, width=10)
        komi_spin.grid(row=2, column=1, padx=5, pady=5)
        
        # 让子
        ttk.Label(settings_frame, text=self.translator.get('handicap'),
                 style='Dialog.TLabel').grid(row=3, column=0, sticky='w', padx=10, pady=5)
        
        default_handicap = int(self._config_get('rules.default_handicap', 0) or 0)
        self.handicap_var = tk.IntVar(value=default_handicap)
        handicap_spin = ttk.Spinbox(settings_frame, textvariable=self.handicap_var,
                                   from_=0, to=9, width=10)
        handicap_spin.grid(row=3, column=1, padx=5, pady=5)
        
        # 时间设置
        ttk.Label(settings_frame, text=self.translator.get('time_control'),
                 style='Dialog.TLabel').grid(row=4, column=0, sticky='w', padx=10, pady=5)
        
        self.time_control_var = tk.StringVar(value=self._time_label_by_key.get('none', 'none'))
        time_combo = ttk.Combobox(settings_frame, textvariable=self.time_control_var,
                                 values=[self._time_label_by_key[k] for k in self._time_keys],
                                 state='readonly', width=10)
        time_combo.grid(row=4, column=1, padx=5, pady=5)
        time_combo.bind('<<ComboboxSelected>>', self._on_time_change)
        
        # 基本时间
        self.time_label = ttk.Label(settings_frame, text=self.translator.get('main_time'),
                                   style='Dialog.TLabel')
        self.time_label.grid(row=5, column=0, sticky='w', padx=10, pady=5)
        
        self.main_time_var = tk.IntVar(value=1800)
        self.time_spin = ttk.Spinbox(settings_frame, textvariable=self.main_time_var,
                                    from_=60, to=7200, increment=60, width=10)
        self.time_spin.grid(row=5, column=1, padx=5, pady=5)
        
        # 初始隐藏时间设置
        self.time_label.grid_remove()
        self.time_spin.grid_remove()
        
        # 按钮
        button_frame = ttk.Frame(main_frame, style='Dialog.TFrame')
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text=self.translator.get('start'),
                  command=self.ok).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.translator.get('cancel'),
                  command=self.cancel).pack(side='left', padx=5)
    
    def _on_mode_change(self):
        """游戏模式改变处理"""
        mode = self.mode_var.get()
        
        # 更新玩家输入框
        if mode == 'human_vs_human':
            self.black_name_entry.grid()
            self.white_name_entry.grid()
            self.black_ai_combo.grid_remove()
            self.white_ai_combo.grid_remove()
            self.black_name_var.set(self.translator.get('player_1'))
            self.white_name_var.set(self.translator.get('player_2'))
            
        elif mode == 'human_vs_ai':
            self.black_name_entry.grid()
            self.white_name_entry.grid_remove()
            self.black_ai_combo.grid_remove()
            self.white_ai_combo.grid()
            self.black_name_var.set(self.translator.get('player'))
            self.white_name_var.set('AI')
            
        elif mode == 'ai_vs_human':
            self.black_name_entry.grid_remove()
            self.white_name_entry.grid()
            self.black_ai_combo.grid()
            self.white_ai_combo.grid_remove()
            self.black_name_var.set('AI')
            self.white_name_var.set(self.translator.get('player'))
            
        elif mode == 'ai_vs_ai':
            self.black_name_entry.grid_remove()
            self.white_name_entry.grid_remove()
            self.black_ai_combo.grid()
            self.white_ai_combo.grid()
            self.black_name_var.set('AI (Black)')
            self.white_name_var.set('AI (White)')
    
    def _on_rules_change(self, event=None):
        """规则改变处理"""
        rules = self._rules_key()
        
        # 根据规则调整默认贴目
        if rules == 'chinese':
            self.komi_var.set(7.5)
        elif rules == 'japanese':
            self.komi_var.set(6.5)
        elif rules == 'aga':
            self.komi_var.set(7.5)
    
    def _on_time_change(self, event=None):
        """时间控制改变处理"""
        time_control = self._time_control_key()
        
        if time_control == 'none':
            self.time_label.grid_remove()
            self.time_spin.grid_remove()
        else:
            self.time_label.grid()
            self.time_spin.grid()
    
    def _get_result(self) -> Dict[str, Any]:
        """获取对话框结果"""
        mode = self.mode_var.get()
        
        # 获取AI级别
        black_ai_level = (
            self._ai_level_key(self.black_ai_level_var.get())
            if mode in ['ai_vs_human', 'ai_vs_ai']
            else None
        )
        white_ai_level = (
            self._ai_level_key(self.white_ai_level_var.get())
            if mode in ['human_vs_ai', 'ai_vs_ai']
            else None
        )
        
        return {
            'mode': mode,
            'black_player': self.black_name_var.get(),
            'white_player': self.white_name_var.get(),
            'black_ai_level': black_ai_level,
            'white_ai_level': white_ai_level,
            'board_size': self.board_size_var.get(),
            'rules': self._rules_key(),
            'komi': self.komi_var.get(),
            'handicap': self.handicap_var.get(),
            'time_control': self._time_control_key(),
            'main_time': self.main_time_var.get() if self._time_control_key() != 'none' else 0
        }

"""
对话框组件（续）
设置对话框、文件对话框等
"""

# 续接前面的代码...

class SettingsDialog(BaseDialog):
    """设置对话框"""
    
    def __init__(self, parent, config: Dict[str, Any], **kwargs):
        self.config = config.copy()  # 创建配置副本
        super().__init__(parent, title=kwargs.get('translator', Translator()).get('settings'), **kwargs)
    
    def _create_widgets(self):
        """创建控件"""
        # 创建标签页
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 通用设置
        self._create_general_tab()
        
        # 显示设置
        self._create_display_tab()
        
        # AI设置
        self._create_ai_tab()
        
        # 音效设置
        self._create_sound_tab()
        
        # 高级设置
        self._create_advanced_tab()
        
        # 按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text=self.translator.get('ok'),
                  command=self.ok).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.translator.get('cancel'),
                  command=self.cancel).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.translator.get('apply'),
                  command=self.apply_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.translator.get('restore_defaults'),
                  command=self.restore_defaults).pack(side='left', padx=5)
    
    def _create_general_tab(self):
        """创建通用设置标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=self.translator.get('general'))
        
        # 语言设置
        row = 0
        ttk.Label(frame, text=self.translator.get('language')).grid(
            row=row, column=0, sticky='w', padx=10, pady=5
        )
        
        self.language_var = tk.StringVar(value=self.config.get('language', 'en'))
        try:
            available_languages = list(self.translator.get_available_languages())
        except Exception:
            available_languages = ['en', 'zh']

        # 优先排序：中文/英文/日文
        preferred_order = ['zh', 'en', 'ja']
        language_values = [c for c in preferred_order if c in available_languages] + [
            c for c in available_languages if c not in preferred_order
        ]

        language_combo = ttk.Combobox(
            frame,
            textvariable=self.language_var,
            values=language_values,
            state='readonly',
            width=15,
        )
        language_combo.grid(row=row, column=1, padx=10, pady=5)
        
        # 主题设置
        row += 1
        ttk.Label(frame, text=self.translator.get('theme')).grid(
            row=row, column=0, sticky='w', padx=10, pady=5
        )
        
        self.theme_var = tk.StringVar(value=self.config.get('theme', 'classic'))
        theme_combo = ttk.Combobox(frame, textvariable=self.theme_var,
                                  values=['classic', 'modern', 'dark', 'bamboo', 'ocean', 'sakura'],
                                  state='readonly', width=15)
        theme_combo.grid(row=row, column=1, padx=10, pady=5)
        
        ttk.Button(frame, text=self.translator.get('customize'),
                  command=self.customize_theme).grid(row=row, column=2, padx=5, pady=5)
        
        # 默认棋盘大小
        row += 1
        ttk.Label(frame, text=self.translator.get('default_board_size')).grid(
            row=row, column=0, sticky='w', padx=10, pady=5
        )
        
        self.default_board_size_var = tk.IntVar(value=self.config.get('default_board_size', 19))
        board_size_combo = ttk.Combobox(frame, textvariable=self.default_board_size_var,
                                       values=[9, 13, 19], state='readonly', width=15)
        board_size_combo.grid(row=row, column=1, padx=10, pady=5)
        
        # 默认规则
        row += 1
        ttk.Label(frame, text=self.translator.get('default_rules')).grid(
            row=row, column=0, sticky='w', padx=10, pady=5
        )
        
        self.default_rules_var = tk.StringVar(value=self.config.get('default_rules', 'chinese'))
        rules_combo = ttk.Combobox(frame, textvariable=self.default_rules_var,
                                  values=['chinese', 'japanese', 'aga', 'ing', 'new_zealand'],
                                  state='readonly', width=15)
        rules_combo.grid(row=row, column=1, padx=10, pady=5)
        
        # 默认贴目
        row += 1
        ttk.Label(frame, text=self.translator.get('default_komi')).grid(
            row=row, column=0, sticky='w', padx=10, pady=5
        )
        
        self.default_komi_var = tk.DoubleVar(value=self.config.get('default_komi', 7.5))
        komi_spin = ttk.Spinbox(frame, textvariable=self.default_komi_var,
                               from_=0, to=20, increment=0.5, width=15)
        komi_spin.grid(row=row, column=1, padx=10, pady=5)
        
        # 自动保存
        row += 1
        self.auto_save_var = tk.BooleanVar(value=self.config.get('auto_save', True))
        ttk.Checkbutton(frame, text=self.translator.get('auto_save'),
                       variable=self.auto_save_var).grid(
            row=row, column=0, columnspan=2, sticky='w', padx=10, pady=5
        )
        
        # 确认退出
        row += 1
        self.confirm_exit_var = tk.BooleanVar(value=self.config.get('confirm_exit', True))
        ttk.Checkbutton(frame, text=self.translator.get('confirm_exit'),
                       variable=self.confirm_exit_var).grid(
            row=row, column=0, columnspan=2, sticky='w', padx=10, pady=5
        )
    
    def _create_display_tab(self):
        """创建显示设置标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=self.translator.get('display'))
        
        # 显示坐标
        row = 0
        self.show_coordinates_var = tk.BooleanVar(value=self.config.get('show_coordinates', True))
        ttk.Checkbutton(frame, text=self.translator.get('show_coordinates'),
                       variable=self.show_coordinates_var).grid(
            row=row, column=0, sticky='w', padx=10, pady=5
        )
        
        # 显示手数
        row += 1
        self.show_move_numbers_var = tk.BooleanVar(value=self.config.get('show_move_numbers', False))
        ttk.Checkbutton(frame, text=self.translator.get('show_move_numbers'),
                       variable=self.show_move_numbers_var).grid(
            row=row, column=0, sticky='w', padx=10, pady=5
        )
        
        # 高亮最后一手
        row += 1
        self.highlight_last_move_var = tk.BooleanVar(value=self.config.get('highlight_last_move', True))
        ttk.Checkbutton(frame, text=self.translator.get('highlight_last_move'),
                       variable=self.highlight_last_move_var).grid(
            row=row, column=0, sticky='w', padx=10, pady=5
        )
        
        # 显示地盘
        row += 1
        self.show_territory_var = tk.BooleanVar(value=self.config.get('show_territory', False))
        ttk.Checkbutton(frame, text=self.translator.get('show_territory'),
                       variable=self.show_territory_var).grid(
            row=row, column=0, sticky='w', padx=10, pady=5
        )
        
        # 显示势力图
        row += 1
        self.show_influence_var = tk.BooleanVar(value=self.config.get('show_influence', False))
        ttk.Checkbutton(frame, text=self.translator.get('show_influence'),
                       variable=self.show_influence_var).grid(
            row=row, column=0, sticky='w', padx=10, pady=5
        )
        
        # 动画设置
        row += 1
        ttk.Label(frame, text=self.translator.get('animation_settings')).grid(
            row=row, column=0, sticky='w', padx=10, pady=10
        )
        
        row += 1
        self.enable_animations_var = tk.BooleanVar(value=self.config.get('enable_animations', True))
        ttk.Checkbutton(frame, text=self.translator.get('enable_animations'),
                       variable=self.enable_animations_var).grid(
            row=row, column=0, sticky='w', padx=20, pady=5
        )
        
        row += 1
        ttk.Label(frame, text=self.translator.get('animation_speed')).grid(
            row=row, column=0, sticky='w', padx=20, pady=5
        )
        
        self.animation_speed_var = tk.DoubleVar(value=self.config.get('animation_speed', 1.0))
        speed_scale = ttk.Scale(frame, from_=0.5, to=3.0, 
                              variable=self.animation_speed_var,
                              orient='horizontal', length=200)
        speed_scale.grid(row=row, column=1, padx=10, pady=5)
        
        self.speed_label = ttk.Label(frame, text=f"{self.animation_speed_var.get():.1f}x")
        self.speed_label.grid(row=row, column=2, padx=5, pady=5)
        speed_scale.configure(command=lambda v: self.speed_label.configure(text=f"{float(v):.1f}x"))
    
    def _create_ai_tab(self):
        """创建AI设置标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=self.translator.get('ai'))
        
        # 默认AI难度
        row = 0
        ttk.Label(frame, text=self.translator.get('default_ai_level')).grid(
            row=row, column=0, sticky='w', padx=10, pady=5
        )
        
        self.default_ai_level_var = tk.StringVar(value=self.config.get('default_ai_level', 'medium'))
        ai_combo = ttk.Combobox(frame, textvariable=self.default_ai_level_var,
                               values=['easy', 'medium', 'hard', 'expert'],
                               state='readonly', width=15)
        ai_combo.grid(row=row, column=1, padx=10, pady=5)
        
        # AI思考时间
        row += 1
        ttk.Label(frame, text=self.translator.get('ai_thinking_time')).grid(
            row=row, column=0, sticky='w', padx=10, pady=5
        )
        
        self.ai_thinking_time_var = tk.DoubleVar(value=self.config.get('ai_thinking_time', 1.0))
        time_spin = ttk.Spinbox(frame, textvariable=self.ai_thinking_time_var,
                               from_=0.1, to=30.0, increment=0.5, width=15)
        time_spin.grid(row=row, column=1, padx=10, pady=5)
        
        # 显示AI分析
        row += 1
        self.show_ai_analysis_var = tk.BooleanVar(value=self.config.get('show_ai_analysis', False))
        ttk.Checkbutton(frame, text=self.translator.get('show_ai_analysis'),
                       variable=self.show_ai_analysis_var).grid(
            row=row, column=0, columnspan=2, sticky='w', padx=10, pady=5
        )
        
        # 显示胜率
        row += 1
        self.show_winrate_var = tk.BooleanVar(value=self.config.get('show_winrate', False))
        ttk.Checkbutton(frame, text=self.translator.get('show_winrate'),
                       variable=self.show_winrate_var).grid(
            row=row, column=0, columnspan=2, sticky='w', padx=10, pady=5
        )
        
        # 显示最佳着法
        row += 1
        self.show_best_moves_var = tk.BooleanVar(value=self.config.get('show_best_moves', False))
        ttk.Checkbutton(frame, text=self.translator.get('show_best_moves'),
                       variable=self.show_best_moves_var).grid(
            row=row, column=0, columnspan=2, sticky='w', padx=10, pady=5
        )
        
        # 自动分析
        row += 1
        self.auto_analyze_var = tk.BooleanVar(value=self.config.get('auto_analyze', False))
        ttk.Checkbutton(frame, text=self.translator.get('auto_analyze'),
                       variable=self.auto_analyze_var).grid(
            row=row, column=0, columnspan=2, sticky='w', padx=10, pady=5
        )
    
    def _create_sound_tab(self):
        """创建音效设置标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=self.translator.get('sound'))
        
        # 启用音效
        row = 0
        self.sound_enabled_var = tk.BooleanVar(value=self.config.get('sound_enabled', True))
        ttk.Checkbutton(frame, text=self.translator.get('sound_enabled'),
                       variable=self.sound_enabled_var,
                       command=self._on_sound_toggle).grid(
            row=row, column=0, columnspan=2, sticky='w', padx=10, pady=5
        )
        
        # 音量
        row += 1
        self.volume_label = ttk.Label(frame, text=self.translator.get('volume'))
        self.volume_label.grid(row=row, column=0, sticky='w', padx=10, pady=5)
        
        self.volume_var = tk.DoubleVar(value=self.config.get('sound_volume', 0.7))
        self.volume_scale = ttk.Scale(frame, from_=0, to=1,
                                    variable=self.volume_var,
                                    orient='horizontal', length=200)
        self.volume_scale.grid(row=row, column=1, padx=10, pady=5)
        
        self.volume_percent_label = ttk.Label(frame, text=f"{int(self.volume_var.get()*100)}%")
        self.volume_percent_label.grid(row=row, column=2, padx=5, pady=5)
        self.volume_scale.configure(
            command=lambda v: self.volume_percent_label.configure(text=f"{int(float(v)*100)}%")
        )
        
        # 各种音效开关
        row += 1
        ttk.Label(frame, text=self.translator.get('sound_effects')).grid(
            row=row, column=0, sticky='w', padx=10, pady=10
        )
        
        # 落子音效
        row += 1
        self.stone_sound_var = tk.BooleanVar(value=self.config.get('stone_sound', True))
        self.stone_sound_check = ttk.Checkbutton(frame, text=self.translator.get('stone_sound'),
                                                variable=self.stone_sound_var)
        self.stone_sound_check.grid(row=row, column=0, sticky='w', padx=20, pady=2)
        
        # 吃子音效
        row += 1
        self.capture_sound_var = tk.BooleanVar(value=self.config.get('capture_sound', True))
        self.capture_sound_check = ttk.Checkbutton(frame, text=self.translator.get('capture_sound'),
                                                  variable=self.capture_sound_var)
        self.capture_sound_check.grid(row=row, column=0, sticky='w', padx=20, pady=2)
        
        # 计时警告音
        row += 1
        self.time_warning_sound_var = tk.BooleanVar(value=self.config.get('time_warning_sound', True))
        self.time_warning_check = ttk.Checkbutton(frame, text=self.translator.get('time_warning_sound'),
                                                 variable=self.time_warning_sound_var)
        self.time_warning_check.grid(row=row, column=0, sticky='w', padx=20, pady=2)
        
        # 初始化音效控件状态
        self._on_sound_toggle()
    
    def _create_advanced_tab(self):
        """创建高级设置标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=self.translator.get('advanced'))
        
        # SGF设置
        row = 0
        ttk.Label(frame, text=self.translator.get('sgf_settings')).grid(
            row=row, column=0, sticky='w', padx=10, pady=10
        )
        
        # 自动保存SGF
        row += 1
        self.auto_save_sgf_var = tk.BooleanVar(value=self.config.get('auto_save_sgf', False))
        ttk.Checkbutton(frame, text=self.translator.get('auto_save_sgf'),
                       variable=self.auto_save_sgf_var).grid(
            row=row, column=0, sticky='w', padx=20, pady=5
        )
        
        # SGF保存路径
        row += 1
        ttk.Label(frame, text=self.translator.get('sgf_path')).grid(
            row=row, column=0, sticky='w', padx=20, pady=5
        )
        
        self.sgf_path_var = tk.StringVar(value=self.config.get('sgf_path', './sgf'))
        sgf_entry = ttk.Entry(frame, textvariable=self.sgf_path_var, width=30)
        sgf_entry.grid(row=row, column=1, padx=10, pady=5)
        
        ttk.Button(frame, text=self.translator.get('browse'),
                  command=self.browse_sgf_path).grid(row=row, column=2, padx=5, pady=5)
        
        # 引擎设置
        row += 1
        ttk.Label(frame, text=self.translator.get('engine_settings')).grid(
            row=row, column=0, sticky='w', padx=10, pady=10
        )
        
        # 使用GPU
        row += 1
        self.use_gpu_var = tk.BooleanVar(value=self.config.get('use_gpu', False))
        ttk.Checkbutton(frame, text=self.translator.get('use_gpu'),
                       variable=self.use_gpu_var).grid(
            row=row, column=0, sticky='w', padx=20, pady=5
        )
        
        # 线程数
        row += 1
        ttk.Label(frame, text=self.translator.get('threads')).grid(
            row=row, column=0, sticky='w', padx=20, pady=5
        )
        
        self.threads_var = tk.IntVar(value=self.config.get('threads', 4))
        threads_spin = ttk.Spinbox(frame, textvariable=self.threads_var,
                                  from_=1, to=32, width=10)
        threads_spin.grid(row=row, column=1, sticky='w', padx=10, pady=5)
        
        # 调试模式
        row += 1
        self.debug_mode_var = tk.BooleanVar(value=self.config.get('debug_mode', False))
        ttk.Checkbutton(frame, text=self.translator.get('debug_mode'),
                       variable=self.debug_mode_var).grid(
            row=row, column=0, sticky='w', padx=10, pady=10
        )
    
    def _on_sound_toggle(self):
        """音效开关切换处理"""
        enabled = self.sound_enabled_var.get()
        state = 'normal' if enabled else 'disabled'
        
        self.volume_scale.configure(state=state)
        self.stone_sound_check.configure(state=state)
        self.capture_sound_check.configure(state=state)
        self.time_warning_check.configure(state=state)
    
    def customize_theme(self):
        """打开主题自定义对话框"""
        dialog = ThemeCustomizeDialog(self, self.theme_var.get(), self.translator)
        self.wait_window(dialog)
        
        if dialog.result:
            # 添加自定义主题
            self.theme_var.set(dialog.result['name'])
    
    def browse_sgf_path(self):
        """浏览SGF保存路径"""
        path = filedialog.askdirectory(
            title=self.translator.get('select_sgf_folder'),
            initialdir=self.sgf_path_var.get()
        )
        if path:
            self.sgf_path_var.set(path)
    
    def apply_settings(self):
        """应用设置"""
        self._update_config()
        messagebox.showinfo(
            self.translator.get('info'),
            self.translator.get('settings_applied')
        )
    
    def restore_defaults(self):
        """恢复默认设置"""
        if messagebox.askyesno(
            self.translator.get('confirm'),
            self.translator.get('restore_defaults_confirm')
        ):
            # 恢复默认值
            self.language_var.set('en')
            self.theme_var.set('classic')
            self.default_board_size_var.set(19)
            self.default_rules_var.set('chinese')
            self.default_komi_var.set(7.5)
            self.auto_save_var.set(True)
            self.confirm_exit_var.set(True)
            # ... 其他默认值
    
    def _update_config(self):
        """更新配置字典"""
        self.config.update({
            'language': self.language_var.get(),
            'theme': self.theme_var.get(),
            'default_board_size': self.default_board_size_var.get(),
            'default_rules': self.default_rules_var.get(),
            'default_komi': self.default_komi_var.get(),
            'auto_save': self.auto_save_var.get(),
            'confirm_exit': self.confirm_exit_var.get(),
            'show_coordinates': self.show_coordinates_var.get(),
            'show_move_numbers': self.show_move_numbers_var.get(),
            'highlight_last_move': self.highlight_last_move_var.get(),
            'show_territory': self.show_territory_var.get(),
            'show_influence': self.show_influence_var.get(),
            'enable_animations': self.enable_animations_var.get(),
            'animation_speed': self.animation_speed_var.get(),
            'default_ai_level': self.default_ai_level_var.get(),
            'ai_thinking_time': self.ai_thinking_time_var.get(),
            'show_ai_analysis': self.show_ai_analysis_var.get(),
            'show_winrate': self.show_winrate_var.get(),
            'show_best_moves': self.show_best_moves_var.get(),
            'auto_analyze': self.auto_analyze_var.get(),
            'sound_enabled': self.sound_enabled_var.get(),
            'sound_volume': self.volume_var.get(),
            'stone_sound': self.stone_sound_var.get(),
            'capture_sound': self.capture_sound_var.get(),
            'time_warning_sound': self.time_warning_sound_var.get(),
            'auto_save_sgf': self.auto_save_sgf_var.get(),
            'sgf_path': self.sgf_path_var.get(),
            'use_gpu': self.use_gpu_var.get(),
            'threads': self.threads_var.get(),
            'debug_mode': self.debug_mode_var.get()
        })
    
    def _get_result(self) -> Dict[str, Any]:
        """获取结果"""
        self._update_config()
        return self.config


class AboutDialog(BaseDialog):
    """关于对话框"""
    
    def __init__(
        self,
        parent,
        version: Optional[str] = None,
        app_name: Optional[str] = None,
        author: Optional[str] = None,
        contact: Optional[str] = None,
        **kwargs,
    ):
        # AboutDialog 额外参数不应透传给 BaseDialog（否则会触发 TypeError）
        self.version = version
        self.app_name = app_name
        self.author = author or "周盟"
        self.contact = contact

        translator = kwargs.get('translator') or Translator()
        super().__init__(
            parent,
            title=translator.get('about'),
            translator=kwargs.get('translator'),
            theme=kwargs.get('theme'),
            modal=kwargs.get('modal', True),
            auto_wait=False,  # 延后 wait_window，避免窗口被销毁后再几何设置
        )
        self.geometry('420x520')
        if self._modal:
            self.transient(parent)
            self.grab_set()
            self.wait_window()
    
    def _create_widgets(self):
        """创建控件"""
        # Logo区域
        logo_frame = ttk.Frame(self)
        logo_frame.pack(pady=20)
        
        # 绘制围棋图标
        logo_canvas = tk.Canvas(logo_frame, width=100, height=100,
                              bg=self.theme.ui_background, highlightthickness=0)
        logo_canvas.pack()
        
        # 绘制棋盘图案
        for i in range(3):
            for j in range(3):
                x, y = 20 + j * 30, 20 + i * 30
                logo_canvas.create_line(x, 10, x, 90, fill='#8B4513')
                logo_canvas.create_line(10, y, 90, y, fill='#8B4513')
        
        # 绘制几个棋子
        logo_canvas.create_oval(15, 15, 25, 25, fill='black')
        logo_canvas.create_oval(45, 45, 55, 55, fill='white', outline='gray')
        logo_canvas.create_oval(75, 15, 85, 25, fill='black')
        logo_canvas.create_oval(15, 75, 25, 85, fill='white', outline='gray')
        
        # 标题 / 版本 / 作者
        title_text = (
            self.app_name
            or (self.master.title() if hasattr(self, 'master') and hasattr(self.master, 'title') else None)
            or self.translator.get('app_name')
        )
        title_label = ttk.Label(self, text=title_text, font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        version_text = self.version or ""
        ttk.Label(
            self,
            text=f"{self.translator.get('version')}: {version_text}" if version_text else self.translator.get('version'),
            font=('Arial', 12),
        ).pack()
        ttk.Label(
            self,
            text=f"{self.translator.get('author')}: {self.author}",
            font=('Arial', 10),
        ).pack(pady=(2, 0))
        
        # 信息文本
        info_frame = ttk.Frame(self)
        info_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        info_text = tk.Text(info_frame, height=15, width=50, wrap='word',
                          bg=self.theme.ui_panel_background,
                          fg=self.theme.ui_text_primary)
        info_text.pack(fill='both', expand=True)
        
        # 添加信息（避免使用特殊项目符号，减少编码环境下的显示问题）
        info_content = "\n".join(
            [
                self.translator.get('about_description'),
                "",
                f"{self.translator.get('features')}:",
                f"- {self.translator.get('feature_1')}",
                f"- {self.translator.get('feature_2')}",
                f"- {self.translator.get('feature_3')}",
                f"- {self.translator.get('feature_4')}",
                f"- {self.translator.get('feature_5')}",
                "",
                f"{self.translator.get('developers')}:",
                self.author,
                "",
                f"{self.translator.get('license')}:",
                "MIT License",
                "",
                f"{self.translator.get('contact')}:",
                self.contact or "",
                "",
            ]
        )
        info_text.insert('1.0', info_content)
        info_text.configure(state='disabled')
        
        # 按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text=self.translator.get('close'),
                  command=self.destroy).pack()


class SaveGameDialog(BaseDialog):
    """保存游戏对话框"""
    
    def __init__(self, parent, game_info: Dict[str, Any], **kwargs):
        self.game_info = game_info
        super().__init__(parent, title=kwargs.get('translator', Translator()).get('save_game'), **kwargs)
    
    def _create_widgets(self):
        """创建控件"""
        # 文件名
        ttk.Label(self, text=self.translator.get('filename')).grid(
            row=0, column=0, sticky='w', padx=10, pady=5
        )
        
        # 生成默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"game_{timestamp}"
        
        self.filename_var = tk.StringVar(value=default_name)
        filename_entry = ttk.Entry(self, textvariable=self.filename_var, width=30)
        filename_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # 描述
        ttk.Label(self, text=self.translator.get('description')).grid(
            row=1, column=0, sticky='nw', padx=10, pady=5
        )
        
        self.description_text = tk.Text(self, height=5, width=40)
        self.description_text.grid(row=1, column=1, padx=10, pady=5)
        
        # 游戏信息
        info_frame = ttk.LabelFrame(self, text=self.translator.get('game_info'))
        info_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
        
        info_text = f"{self.translator.get('black')}: {self.game_info.get('black_player', 'Unknown')}\n"
        info_text += f"{self.translator.get('white')}: {self.game_info.get('white_player', 'Unknown')}\n"
        info_text += f"{self.translator.get('moves')}: {self.game_info.get('moves', 0)}\n"
        info_text += f"{self.translator.get('date')}: {self.game_info.get('date', '')}"
        
        ttk.Label(info_frame, text=info_text).pack(padx=10, pady=5)
        
        # 保存格式
        ttk.Label(self, text=self.translator.get('format')).grid(
            row=3, column=0, sticky='w', padx=10, pady=5
        )
        
        self.format_var = tk.StringVar(value='sgf')
        format_combo = ttk.Combobox(self, textvariable=self.format_var,
                                   values=['sgf', 'pkl', 'json'],
                                   state='readonly', width=10)
        format_combo.grid(row=3, column=1, sticky='w', padx=10, pady=5)
        
        # 按钮
        button_frame = ttk.Frame(self)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text=self.translator.get('save'),
                  command=self.ok).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.translator.get('cancel'),
                  command=self.cancel).pack(side='left', padx=5)
    
    def _get_result(self) -> Dict[str, Any]:
        """获取结果"""
        return {
            'filename': self.filename_var.get(),
            'description': self.description_text.get('1.0', 'end-1c'),
            'format': self.format_var.get()
        }


class LoadGameDialog(BaseDialog):
    """加载游戏对话框"""
    
    def __init__(self, parent, saved_games: List[Dict[str, Any]], **kwargs):
        self.saved_games = saved_games
        super().__init__(parent, title=kwargs.get('translator', Translator()).get('load_game'), **kwargs)
        self.geometry('600x400')
    
    def _create_widgets(self):
        """创建控件"""
        # 游戏列表
        list_frame = ttk.Frame(self)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建列表
        columns = ('name', 'date', 'players', 'moves')
        self.game_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # 设置列标题
        self.game_tree.heading('name', text=self.translator.get('filename'))
        self.game_tree.heading('date', text=self.translator.get('date'))
        self.game_tree.heading('players', text=self.translator.get('players'))
        self.game_tree.heading('moves', text=self.translator.get('moves'))
        
        # 设置列宽
        self.game_tree.column('name', width=200)
        self.game_tree.column('date', width=150)
        self.game_tree.column('players', width=150)
        self.game_tree.column('moves', width=80)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.game_tree.yview)
        self.game_tree.configure(yscrollcommand=scrollbar.set)
        
        self.game_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 填充数据
        for game in self.saved_games:
            players = f"{game.get('black_player', '')} vs {game.get('white_player', '')}"
            self.game_tree.insert('', 'end', values=(
                game.get('filename', ''),
                game.get('date', ''),
                players,
                game.get('moves', 0)
            ))
        
        # 双击加载
        self.game_tree.bind('<Double-1>', lambda e: self.ok())
        
        # 按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text=self.translator.get('load'),
                  command=self.ok).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.translator.get('cancel'),
                  command=self.cancel).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.translator.get('delete'),
                  command=self.delete_game).pack(side='left', padx=5)
    
    def delete_game(self):
        """删除选中的游戏"""
        selection = self.game_tree.selection()
        if selection:
            if messagebox.askyesno(
                self.translator.get('confirm'),
                self.translator.get('delete_game_confirm')
            ):
                item = self.game_tree.item(selection[0])
                # 删除操作需要在主程序中实现
                self.game_tree.delete(selection[0])
    
    def _get_result(self) -> Optional[str]:
        """获取选中的游戏文件名"""
        selection = self.game_tree.selection()
        if selection:
            item = self.game_tree.item(selection[0])
            return item['values'][0]  # 返回文件名
        return None


class SGFDialog(BaseDialog):
    """SGF导入/导出对话框"""
    
    def __init__(self, parent, mode: str = 'import', **kwargs):
        self.mode = mode  # 'import' or 'export'
        title = kwargs.get('translator', Translator()).get('import_sgf' if mode == 'import' else 'export_sgf')
        super().__init__(parent, title=title, **kwargs)
    
    def _create_widgets(self):
        """创建控件"""
        if self.mode == 'import':
            self._create_import_widgets()
        else:
            self._create_export_widgets()
    
    def _create_import_widgets(self):
        """创建导入控件"""
        # 文件选择
        ttk.Label(self, text=self.translator.get('sgf_file')).grid(
            row=0, column=0, sticky='w', padx=10, pady=5
        )
        
        self.file_var = tk.StringVar()
        file_entry = ttk.Entry(self, textvariable=self.file_var, width=40)
        file_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Button(self, text=self.translator.get('browse'),
                  command=self.browse_file).grid(row=0, column=2, padx=5, pady=5)
        
        # 选项
        options_frame = ttk.LabelFrame(self, text=self.translator.get('import_options'))
        options_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky='ew')
        
        self.overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text=self.translator.get('overwrite_current'),
                       variable=self.overwrite_var).pack(anchor='w', padx=10, pady=5)
        
        self.import_comments_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text=self.translator.get('import_comments'),
                       variable=self.import_comments_var).pack(anchor='w', padx=10, pady=5)
        
        self.import_variations_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text=self.translator.get('import_variations'),
                       variable=self.import_variations_var).pack(anchor='w', padx=10, pady=5)
        
        # 按钮
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text=self.translator.get('import'),
                  command=self.ok).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.translator.get('cancel'),
                  command=self.cancel).pack(side='left', padx=5)
    
    def _create_export_widgets(self):
        """创建导出控件"""
        # 文件名
        ttk.Label(self, text=self.translator.get('filename')).grid(
            row=0, column=0, sticky='w', padx=10, pady=5
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename_var = tk.StringVar(value=f"game_{timestamp}.sgf")
        filename_entry = ttk.Entry(self, textvariable=self.filename_var, width=30)
        filename_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # 选项
        options_frame = ttk.LabelFrame(self, text=self.translator.get('export_options'))
        options_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
        
        self.include_comments_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text=self.translator.get('include_comments'),
                       variable=self.include_comments_var).pack(anchor='w', padx=10, pady=5)
        
        self.include_variations_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text=self.translator.get('include_variations'),
                       variable=self.include_variations_var).pack(anchor='w', padx=10, pady=5)
        
        self.include_analysis_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text=self.translator.get('include_analysis'),
                       variable=self.include_analysis_var).pack(anchor='w', padx=10, pady=5)
        
        # 按钮
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text=self.translator.get('export'),
                  command=self.ok).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.translator.get('cancel'),
                  command=self.cancel).pack(side='left', padx=5)
    
    def browse_file(self):
        """浏览文件"""
        filename = filedialog.askopenfilename(
            title=self.translator.get('select_sgf_file'),
            filetypes=[('SGF Files', '*.sgf'), ('All Files', '*.*')]
        )
        if filename:
            self.file_var.set(filename)
    
    def _get_result(self) -> Dict[str, Any]:
        """获取结果"""
        if self.mode == 'import':
            return {
                'file': self.file_var.get(),
                'overwrite': self.overwrite_var.get(),
                'import_comments': self.import_comments_var.get(),
                'import_variations': self.import_variations_var.get()
            }
        else:
            return {
                'filename': self.filename_var.get(),
                'include_comments': self.include_comments_var.get(),
                'include_variations': self.include_variations_var.get(),
                'include_analysis': self.include_analysis_var.get()
            }


class ThemeCustomizeDialog(BaseDialog):
    """主题自定义对话框"""
    
    def __init__(self, parent, base_theme: str, translator: Translator, **kwargs):
        self.base_theme = base_theme
        super().__init__(parent, title=translator.get('customize_theme'), translator=translator, **kwargs)
        self.geometry('500x600')
    
    def _create_widgets(self):
        """创建控件"""
        # 主题名称
        name_frame = ttk.Frame(self)
        name_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(name_frame, text=self.translator.get('theme_name')).pack(side='left', padx=5)
        self.name_var = tk.StringVar(value=f"{self.base_theme}_custom")
        ttk.Entry(name_frame, textvariable=self.name_var, width=30).pack(side='left', padx=5)
        
        # 颜色设置
        colors_frame = ttk.LabelFrame(self, text=self.translator.get('colors'))
        colors_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 创建颜色选择器
        self.colors = {}
        color_items = [
            ('board_background', self.translator.get('board_background')),
            ('board_grid_color', self.translator.get('grid_color')),
            ('stone_black_color', self.translator.get('black_stone')),
            ('stone_white_color', self.translator.get('white_stone')),
            ('last_move_marker', self.translator.get('last_move_marker')),
            ('ui_background', self.translator.get('ui_background')),
            ('ui_text_primary', self.translator.get('text_color'))
        ]
        
        for i, (key, label) in enumerate(color_items):
            ttk.Label(colors_frame, text=label).grid(row=i, column=0, sticky='w', padx=10, pady=5)
            
            color_var = tk.StringVar(value='#FFFFFF')
            self.colors[key] = color_var
            
            color_frame = ttk.Frame(colors_frame)
            color_frame.grid(row=i, column=1, padx=10, pady=5)
            
            color_label = tk.Label(color_frame, width=10, bg=color_var.get())
            color_label.pack(side='left', padx=5)
            
            ttk.Button(color_frame, text=self.translator.get('choose'),
                      command=lambda l=color_label, v=color_var: self.choose_color(l, v)).pack(side='left')
        
        # 按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text=self.translator.get('create'),
                  command=self.ok).pack(side='left', padx=5)
        ttk.Button(button_frame, text=self.translator.get('cancel'),
                  command=self.cancel).pack(side='left', padx=5)
    
    def choose_color(self, label: tk.Label, var: tk.StringVar):
        """选择颜色"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(initialcolor=var.get())
        if color[1]:  # color[1]是十六进制颜色值
            var.set(color[1])
            label.configure(bg=color[1])
    
    def _get_result(self) -> Dict[str, Any]:
        """获取结果"""
        result = {'name': self.name_var.get()}
        result.update({k: v.get() for k, v in self.colors.items()})
        return result


# 导出所有对话框类
__all__ = [
    'NewGameDialog', 'SettingsDialog', 'AboutDialog',
    'SaveGameDialog', 'LoadGameDialog', 'SGFDialog',
    'ThemeCustomizeDialog'
]
