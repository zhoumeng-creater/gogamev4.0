"""
多语言翻译系统
支持中文、英文、日文、韩文等多种语言
"""

from typing import Dict, Any, Optional
import json
import os
from pathlib import Path


class Translator:
    """翻译器类"""
    
    # 完整的翻译字典
    TRANSLATIONS = {
        'en': {
            # 基础
            'app_name': 'Go Master',
            'version': 'Version',
            'author': 'Author',
            'description': 'A professional Go game application',
            
            # 菜单
            'file': 'File',
            'edit': 'Edit',
            'view': 'View',
            'game': 'Game',
            'tools': 'Tools',
            'help': 'Help',
            
            # 文件菜单
            'new_game': 'New Game',
            'save_game': 'Save Game',
            'load_game': 'Load Game',
            'save_sgf': 'Save as SGF',
            'load_sgf': 'Load SGF',
            'import_sgf': 'Import SGF',
            'export_sgf': 'Export SGF',
            'exit': 'Exit',
            
            # 编辑菜单
            'undo': 'Undo',
            'redo': 'Redo',
            'pass': 'Pass',
            'resign': 'Resign',
            
            # 视图菜单
            'show_coordinates': 'Show Coordinates',
            'show_move_numbers': 'Show Move Numbers',
            'show_territory': 'Show Territory',
            'show_influence': 'Show Influence',
            'highlight_last_move': 'Highlight Last Move',
            'full_screen': 'Full Screen',
            
            # 游戏菜单
            'analyze': 'Analyze',
            'score': 'Score',
            'estimate': 'Estimate',
            'hint': 'Hint',
            'statistics': 'Statistics',
            
            # 工具菜单
            'settings': 'Settings',
            'joseki_library': 'Joseki Library',
            'game_review': 'Game Review',
            'pattern_search': 'Pattern Search',
            
            # 帮助菜单
            'rules': 'Rules',
            'tutorial': 'Tutorial',
            'about': 'About',
            
            # 游戏相关
            'black': 'Black',
            'white': 'White',
            'players': 'Players',
            'current_player': 'Current Player',
            'black_player': 'Black Player',
            'white_player': 'White Player',
            'move': 'Move',
            'moves': 'Moves',
            'captured': 'Captured',
            'ko': 'Ko',
            'phase': 'Phase',
            'playing': 'Playing',
            'scoring': 'Scoring',
            'ended': 'Ended',
            
            # 游戏信息
            'game_info': 'Game Info',
            'game_mode': 'Game Mode',
            'game_settings': 'Game Settings',
            'game_control': 'Game Control',
            'board_size': 'Board Size',
            'default_board_size': 'Default Board Size',
            'komi': 'Komi',
            'default_komi': 'Default Komi',
            'handicap': 'Handicap',
            'time_control': 'Time Control',
            'main_time': 'Main Time',
            'byoyomi': 'Byoyomi',
            'none': 'None',
            'absolute': 'Absolute',
            'canadian': 'Canadian',
            
            # 规则
            'rules_type': 'Rules',
            'default_rules': 'Default Rules',
            'chinese': 'Chinese',
            'japanese': 'Japanese',
            'aga': 'AGA',
            'ing': 'Ing',
            'new_zealand': 'New Zealand',
            
            # 游戏模式
            'human_vs_human': 'Human vs Human',
            'human_vs_ai': 'Human vs AI',
            'ai_vs_human': 'AI vs Human',
            'ai_vs_ai': 'AI vs AI',
            'player': 'Player',
            'player_1': 'Player 1',
            'player_2': 'Player 2',
            
            # AI相关
            'ai': 'AI',
            'ai_level': 'AI Level',
            'default_ai_level': 'Default AI Level',
            'ai_thinking_time': 'AI Thinking Time',
            'easy': 'Easy',
            'medium': 'Medium',
            'hard': 'Hard',
            'expert': 'Expert',
            'ai_thinking': 'AI is thinking...',
            
            # 分析
            'analysis': 'Analysis',
            'analysis_info': 'Analysis Info',
            'situation': 'Situation',
            'suggestions': 'Suggestions',
            'win_rate': 'Win Rate',
            'visits': 'Visits',
            'thinking_time': 'Thinking Time',
            'nodes_analyzed': 'Nodes Analyzed',
            'search_depth': 'Search Depth',
            'show_ai_analysis': 'Show AI Analysis',
            'show_winrate': 'Show Win Rate',
            'show_best_moves': 'Show Best Moves',
            'auto_analyze': 'Auto Analyze',
            
            # 导航
            'navigation': 'Navigation',
            'branches': 'Branches',
            'auto_play': 'Auto Play',
            'play': 'Play',
            'pause': 'Pause',
            'speed': 'Speed',
            'create': 'Create',
            'delete': 'Delete',
            
            # 显示设置
            'display': 'Display',
            'animation_settings': 'Animation Settings',
            'enable_animations': 'Enable Animations',
            'animation_speed': 'Animation Speed',
            
            # 音效设置
            'sound': 'Sound',
            'sound_enabled': 'Sound Enabled',
            'volume': 'Volume',
            'sound_effects': 'Sound Effects',
            'stone_sound': 'Stone Placement Sound',
            'capture_sound': 'Capture Sound',
            'time_warning_sound': 'Time Warning Sound',
            
            # 高级设置
            'advanced': 'Advanced',
            'sgf_settings': 'SGF Settings',
            'auto_save_sgf': 'Auto Save SGF',
            'sgf_path': 'SGF Save Path',
            'sgf_file': 'SGF File',
            'browse': 'Browse',
            'engine_settings': 'Engine Settings',
            'use_gpu': 'Use GPU',
            'threads': 'Threads',
            'debug_mode': 'Debug Mode',
            
            # 通用设置
            'general': 'General',
            'language': 'Language',
            'theme': 'Theme',
            'auto_save': 'Auto Save',
            'confirm_exit': 'Confirm Exit',
            
            # 按钮
            'ok': 'OK',
            'cancel': 'Cancel',
            'apply': 'Apply',
            'start': 'Start',
            'close': 'Close',
            'save': 'Save',
            'load': 'Load',
            'import': 'Import',
            'export': 'Export',
            'restore_defaults': 'Restore Defaults',
            'customize': 'Customize',
            'choose': 'Choose',
            
            # 对话框
            'confirm': 'Confirm',
            'info': 'Information',
            'warning': 'Warning',
            'error': 'Error',
            'confirm_resign': 'Are you sure you want to resign?',
            'confirm_exit': 'Game in progress. Are you sure you want to exit?',
            'settings_applied': 'Settings have been applied',
            'restore_defaults_confirm': 'Are you sure you want to restore default settings?',
            'delete_game_confirm': 'Are you sure you want to delete this game?',
            'overwrite_current': 'Overwrite Current Game',
            
            # 文件操作
            'filename': 'Filename',
            'date': 'Date',
            'format': 'Format',
            'select_sgf_file': 'Select SGF File',
            'select_sgf_folder': 'Select SGF Folder',
            'import_options': 'Import Options',
            'export_options': 'Export Options',
            'import_comments': 'Import Comments',
            'import_variations': 'Import Variations',
            'include_comments': 'Include Comments',
            'include_variations': 'Include Variations',
            'include_analysis': 'Include Analysis',
            
            # 状态消息
            'ready': 'Ready',
            'game_started': 'Game Started',
            'new_game_started': 'New game started',
            'game_ended': 'Game Ended',
            'game_saved': 'Game Saved',
            'game_loaded': 'Game Loaded',
            'sgf_saved': 'SGF Saved',
            'sgf_loaded': 'SGF Loaded',
            'move_undone': 'Move Undone',
            'move_redone': 'Move Redone',
            'analysis_complete': 'Analysis Complete',
            'calculating_hint': 'Calculating best move...',
            'pass_recommended': 'Pass is recommended',
            'illegal_move': 'Illegal Move',
            'ko_rule': 'Ko Rule Violation',
            'suicide_rule': 'Suicide Move',
            'need_two_passes': 'Two passes needed to enter scoring phase',
            'accept_result': 'Accept this result?',
            'save_failed': 'Save Failed',
            'load_failed': 'Load Failed',
            
            # 游戏结果
            'game_over': 'Game Over',
            'game_result': 'Game Result',
            'black_wins': 'Black Wins',
            'white_wins': 'White Wins',
            'draw': 'Draw',
            'wins_by': 'wins by',
            'wins_by_time': 'wins by time',
            'even': 'Even',
            'even_game': 'Even Game',
            'leading': 'Leading',
            
            # 关于对话框
            'about_description': 'A professional Go/Weiqi/Baduk game application with AI opponents and analysis tools.',
            'features': 'Features',
            'feature_1': 'Multiple board sizes (9x9, 13x13, 19x19)',
            'feature_2': 'Various AI difficulty levels',
            'feature_3': 'Game analysis and review',
            'feature_4': 'SGF import/export',
            'feature_5': 'Multiple rule sets support',
            'developers': 'Developers',
            'license': 'License',
            'website': 'Website',
            'contact': 'Contact',
            
            # 主题
            'theme_name': 'Theme Name',
            'colors': 'Colors',
            'board_background': 'Board Background',
            'grid_color': 'Grid Color',
            'black_stone': 'Black Stone',
            'white_stone': 'White Stone',
            'last_move_marker': 'Last Move Marker',
            'ui_background': 'UI Background',
            'text_color': 'Text Color',
            'customize_theme': 'Customize Theme',
            
            # 统计
            'total_games': 'Total Games',
            'black_wins_count': 'Black Wins',
            'white_wins_count': 'White Wins',
            'draws': 'Draws',
            'average_moves': 'Average Moves',
            'vs_ai_games': 'Games vs AI',
            'vs_human_games': 'Games vs Human',
            
            # 其他
            'feature_coming_soon': 'This feature is coming soon!',
            'rules_description': 'Go is a strategic board game for two players.',
            'tutorial_content': 'Welcome to Go Master tutorial!',
            'passed': 'passed',
            'move_number': 'Move #'
        },
        
        'zh': {
            # 基础
            'app_name': '围棋大师',
            'version': '版本',
            'author': '作者',
            'description': '专业的围棋游戏应用',
            
            # 菜单
            'file': '文件',
            'edit': '编辑',
            'view': '视图',
            'game': '对局',
            'tools': '工具',
            'help': '帮助',
            
            # 文件菜单
            'new_game': '新对局',
            'save_game': '保存对局',
            'load_game': '加载对局',
            'save_sgf': '保存为SGF',
            'load_sgf': '加载SGF',
            'import_sgf': '导入SGF',
            'export_sgf': '导出SGF',
            'exit': '退出',
            
            # 编辑菜单
            'undo': '悔棋',
            'redo': '重做',
            'pass': '虚手',
            'resign': '认输',
            
            # 视图菜单
            'show_coordinates': '显示坐标',
            'show_move_numbers': '显示手数',
            'show_territory': '显示地盘',
            'show_influence': '显示势力',
            'highlight_last_move': '高亮最后一手',
            'full_screen': '全屏',
            
            # 游戏菜单
            'analyze': '分析',
            'score': '点目',
            'estimate': '形势估计',
            'hint': '提示',
            'statistics': '统计',
            
            # 工具菜单
            'settings': '设置',
            'joseki_library': '定式库',
            'game_review': '复盘',
            'pattern_search': '棋型搜索',
            
            # 帮助菜单
            'rules': '规则',
            'tutorial': '教程',
            'about': '关于',
            
            # 游戏相关
            'black': '黑棋',
            'white': '白棋',
            'players': '玩家',
            'current_player': '当前玩家',
            'black_player': '黑方',
            'white_player': '白方',
            'move': '手',
            'moves': '手数',
            'captured': '提子',
            'ko': '劫',
            'phase': '阶段',
            'playing': '对弈中',
            'scoring': '点目中',
            'ended': '已结束',
            
            # 游戏信息
            'game_info': '对局信息',
            'game_mode': '对局模式',
            'game_settings': '对局设置',
            'game_control': '对局控制',
            'board_size': '棋盘大小',
            'default_board_size': '默认棋盘大小',
            'komi': '贴目',
            'default_komi': '默认贴目',
            'handicap': '让子',
            'time_control': '时间控制',
            'main_time': '基本时间',
            'byoyomi': '读秒',
            'none': '无',
            'absolute': '包干',
            'canadian': '加拿大',
            
            # 规则
            'rules_type': '规则',
            'default_rules': '默认规则',
            'chinese': '中国',
            'japanese': '日本',
            'aga': '美国',
            'ing': '应氏',
            'new_zealand': '新西兰',
            
            # 游戏模式
            'human_vs_human': '人人对弈',
            'human_vs_ai': '人机对弈',
            'ai_vs_human': '机人对弈',
            'ai_vs_ai': '机机对弈',
            'player': '玩家',
            'player_1': '玩家1',
            'player_2': '玩家2',
            
            # AI相关
            'ai': '人工智能',
            'ai_level': 'AI难度',
            'default_ai_level': '默认AI难度',
            'ai_thinking_time': 'AI思考时间',
            'easy': '简单',
            'medium': '中等',
            'hard': '困难',
            'expert': '专家',
            'ai_thinking': 'AI正在思考...',
            
            # 分析
            'analysis': '分析',
            'analysis_info': '分析信息',
            'situation': '形势',
            'suggestions': '推荐着法',
            'win_rate': '胜率',
            'visits': '访问数',
            'thinking_time': '思考时间',
            'nodes_analyzed': '分析节点数',
            'search_depth': '搜索深度',
            'show_ai_analysis': '显示AI分析',
            'show_winrate': '显示胜率',
            'show_best_moves': '显示最佳着法',
            'auto_analyze': '自动分析',
            
            # 导航
            'navigation': '导航',
            'branches': '分支',
            'auto_play': '自动播放',
            'play': '播放',
            'pause': '暂停',
            'speed': '速度',
            'create': '创建',
            'delete': '删除',
            
            # 显示设置
            'display': '显示',
            'animation_settings': '动画设置',
            'enable_animations': '启用动画',
            'animation_speed': '动画速度',
            
            # 音效设置
            'sound': '音效',
            'sound_enabled': '启用音效',
            'volume': '音量',
            'sound_effects': '音效',
            'stone_sound': '落子音效',
            'capture_sound': '吃子音效',
            'time_warning_sound': '时间警告音',
            
            # 高级设置
            'advanced': '高级',
            'sgf_settings': 'SGF设置',
            'auto_save_sgf': '自动保存SGF',
            'sgf_path': 'SGF保存路径',
            'sgf_file': 'SGF文件',
            'browse': '浏览',
            'engine_settings': '引擎设置',
            'use_gpu': '使用GPU',
            'threads': '线程数',
            'debug_mode': '调试模式',
            
            # 通用设置
            'general': '通用',
            'language': '语言',
            'theme': '主题',
            'auto_save': '自动保存',
            'confirm_exit': '退出确认',
            
            # 按钮
            'ok': '确定',
            'cancel': '取消',
            'apply': '应用',
            'start': '开始',
            'close': '关闭',
            'save': '保存',
            'load': '加载',
            'import': '导入',
            'export': '导出',
            'restore_defaults': '恢复默认',
            'customize': '自定义',
            'choose': '选择',
            
            # 对话框
            'confirm': '确认',
            'info': '信息',
            'warning': '警告',
            'error': '错误',
            'confirm_resign': '确定要认输吗？',
            'confirm_exit': '对局进行中，确定要退出吗？',
            'settings_applied': '设置已应用',
            'restore_defaults_confirm': '确定要恢复默认设置吗？',
            'delete_game_confirm': '确定要删除这个对局吗？',
            'overwrite_current': '覆盖当前对局',
            
            # 文件操作
            'filename': '文件名',
            'date': '日期',
            'format': '格式',
            'select_sgf_file': '选择SGF文件',
            'select_sgf_folder': '选择SGF文件夹',
            'import_options': '导入选项',
            'export_options': '导出选项',
            'import_comments': '导入注释',
            'import_variations': '导入变化',
            'include_comments': '包含注释',
            'include_variations': '包含变化',
            'include_analysis': '包含分析',
            
            # 状态消息
            'ready': '就绪',
            'game_started': '对局开始',
            'new_game_started': '新对局已开始',
            'game_ended': '对局结束',
            'game_saved': '对局已保存',
            'game_loaded': '对局已加载',
            'sgf_saved': 'SGF已保存',
            'sgf_loaded': 'SGF已加载',
            'move_undone': '已悔棋',
            'move_redone': '已重做',
            'analysis_complete': '分析完成',
            'calculating_hint': '正在计算最佳着法...',
            'pass_recommended': '建议虚手',
            'illegal_move': '非法落子',
            'ko_rule': '违反劫规则',
            'suicide_rule': '自杀手',
            'need_two_passes': '需要两次虚手才能进入点目阶段',
            'accept_result': '接受这个结果吗？',
            'save_failed': '保存失败',
            'load_failed': '加载失败',
            
            # 游戏结果
            'game_over': '对局结束',
            'game_result': '对局结果',
            'black_wins': '黑棋胜',
            'white_wins': '白棋胜',
            'draw': '和棋',
            'wins_by': '胜',
            'wins_by_time': '超时胜',
            'even': '均势',
            'even_game': '势均力敌',
            'leading': '领先方',
            
            # 关于对话框
            'about_description': '专业的围棋游戏应用，支持人工智能对手和分析工具。',
            'features': '功能特点',
            'feature_1': '多种棋盘大小（9x9、13x13、19x19）',
            'feature_2': '多种AI难度级别',
            'feature_3': '对局分析和复盘',
            'feature_4': 'SGF导入/导出',
            'feature_5': '支持多种规则',
            'developers': '开发者',
            'license': '许可证',
            'website': '网站',
            'contact': '联系方式',
            
            # 主题
            'theme_name': '主题名称',
            'colors': '颜色',
            'board_background': '棋盘背景',
            'grid_color': '网格颜色',
            'black_stone': '黑子',
            'white_stone': '白子',
            'last_move_marker': '最后一手标记',
            'ui_background': '界面背景',
            'text_color': '文字颜色',
            'customize_theme': '自定义主题',
            
            # 统计
            'total_games': '总对局数',
            'black_wins_count': '黑棋胜',
            'white_wins_count': '白棋胜',
            'draws': '和棋',
            'average_moves': '平均手数',
            'vs_ai_games': '人机对局',
            'vs_human_games': '人人对局',
            
            # 其他
            'feature_coming_soon': '此功能即将推出！',
            'rules_description': '围棋是一种两人对弈的策略棋盘游戏。',
            'tutorial_content': '欢迎使用围棋大师教程！',
            'passed': '虚手',
            'move_number': '第{}手'
        },
        
        'ja': {
            # 基础日语翻译（示例）
            'app_name': '囲碁マスター',
            'black': '黒',
            'white': '白',
            'new_game': '新規対局',
            'settings': '設定',
            'pass': 'パス',
            'resign': '投了',
            'undo': '待った',
            'score': '地を数える',
            # ... 更多日语翻译
        }
    }
    
    def __init__(self, language: str = 'en', custom_translations: Optional[str] = None):
        """
        初始化翻译器
        
        Args:
            language: 语言代码
            custom_translations: 自定义翻译文件路径
        """
        self.language = language
        self.translations = self.TRANSLATIONS.copy()
        
        # 加载自定义翻译
        if custom_translations:
            self._load_custom_translations(custom_translations)
    
    def _load_custom_translations(self, file_path: str):
        """
        加载自定义翻译文件
        
        Args:
            file_path: JSON翻译文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                custom = json.load(f)
                for lang, trans in custom.items():
                    if lang in self.translations:
                        self.translations[lang].update(trans)
                    else:
                        self.translations[lang] = trans
        except Exception as e:
            print(f"加载自定义翻译失败: {e}")
    
    def get(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        """
        获取翻译文本
        
        Args:
            key: 翻译键
            default: 默认值
            **kwargs: 格式化参数
            
        Returns:
            翻译后的文本
        """
        # 获取当前语言的翻译
        lang_dict = self.translations.get(self.language, {})
        
        # 如果当前语言没有，尝试英语
        if key not in lang_dict:
            lang_dict = self.translations.get('en', {})
        
        # 获取翻译文本
        text = lang_dict.get(key, default or key)
        
        # 格式化文本
        if kwargs:
            try:
                text = text.format(**kwargs)
            except:
                pass
        
        return text
    
    def set_language(self, language: str):
        """
        设置语言
        
        Args:
            language: 语言代码
        """
        if language in self.translations:
            self.language = language
        else:
            print(f"不支持的语言: {language}")
    
    def get_available_languages(self) -> list:
        """
        获取可用语言列表
        
        Returns:
            语言代码列表
        """
        return list(self.translations.keys())
    
    def add_translation(self, language: str, key: str, value: str):
        """
        添加翻译条目
        
        Args:
            language: 语言代码
            key: 翻译键
            value: 翻译值
        """
        if language not in self.translations:
            self.translations[language] = {}
        self.translations[language][key] = value
    
    def export_translations(self, file_path: str, language: Optional[str] = None):
        """
        导出翻译到文件
        
        Args:
            file_path: 导出文件路径
            language: 特定语言，None表示导出所有
        """
        try:
            if language:
                data = {language: self.translations.get(language, {})}
            else:
                data = self.translations
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"导出翻译失败: {e}")
    
    def check_completeness(self, language: str) -> Dict[str, list]:
        """
        检查翻译完整性
        
        Args:
            language: 要检查的语言
            
        Returns:
            {'missing': [...], 'extra': [...]}
        """
        en_keys = set(self.translations.get('en', {}).keys())
        lang_keys = set(self.translations.get(language, {}).keys())
        
        return {
            'missing': list(en_keys - lang_keys),
            'extra': list(lang_keys - en_keys)
        }


# 全局翻译器实例
_global_translator = None


def get_translator() -> Translator:
    """获取全局翻译器实例"""
    global _global_translator
    if _global_translator is None:
        _global_translator = Translator()
    return _global_translator


def set_global_language(language: str):
    """设置全局语言"""
    translator = get_translator()
    translator.set_language(language)


def t(key: str, **kwargs) -> str:
    """
    便捷翻译函数
    
    Args:
        key: 翻译键
        **kwargs: 格式化参数
        
    Returns:
        翻译后的文本
    """
    translator = get_translator()
    return translator.get(key, **kwargs)