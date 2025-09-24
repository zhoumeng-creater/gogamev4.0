"""
翻译系统模块
提供多语言支持和国际化功能
"""

import os
import json
from typing import Dict, Optional, Any, List
from pathlib import Path


class Translator:
    """翻译器类"""
    
    # 内置翻译
    TRANSLATIONS = {
        'zh': {
            # 游戏基础
            'app_name': '围棋大师',
            'new_game': '新对局',
            'continue': '继续',
            'settings': '设置',
            'quit': '退出',
            'black': '黑方',
            'white': '白方',
            'pass': '虚手',
            'resign': '认输',
            'undo': '悔棋',
            'redo': '重做',
            'hint': '提示',
            'analyze': '分析',
            'score': '数子',
            
            # 游戏模式
            'game_mode': '游戏模式',
            'human_vs_human': '人类对战',
            'human_vs_ai': '人机对战',
            'ai_vs_human': 'AI先手',
            'ai_vs_ai': 'AI对战',
            'online': '网络对战',
            'replay': '复盘模式',
            'tutorial': '教学模式',
            'puzzle': '死活题',
            
            # AI难度
            'ai_level': 'AI难度',
            'beginner': '初学者',
            'easy': '简单',
            'medium': '中等',
            'hard': '困难',
            'expert': '专家',
            'master': '大师',
            
            # 规则设置
            'rules': '规则',
            'chinese_rules': '中国规则',
            'japanese_rules': '日本规则',
            'aga_rules': 'AGA规则',
            'board_size': '棋盘大小',
            'komi': '贴目',
            'handicap': '让子',
            'time_control': '计时方式',
            'no_time_limit': '无限时',
            'absolute_time': '包干时间',
            'byoyomi': '读秒',
            'canadian': '加拿大计时',
            'fischer': '费舍尔计时',
            'main_time': '基本时间',
            'overtime': '加时',
            
            # 游戏状态
            'game_info': '对局信息',
            'current_player': '当前玩家',
            'move_number': '手数',
            'captures': '提子',
            'territory': '地盘',
            'time_left': '剩余时间',
            'status': '状态',
            'playing': '对局中',
            'paused': '已暂停',
            'ended': '已结束',
            'counting': '数子中',
            
            # 结果
            'result': '结果',
            'black_wins': '黑胜',
            'white_wins': '白胜',
            'jigo': '和棋',
            'wins_by_resignation': '中盘胜',
            'wins_by_time': '超时胜',
            'wins_by_points': '目胜',
            
            # 文件操作
            'file': '文件',
            'open': '打开',
            'save': '保存',
            'save_as': '另存为',
            'import': '导入',
            'export': '导出',
            'recent_files': '最近文件',
            'sgf_files': 'SGF棋谱',
            'all_files': '所有文件',
            
            # 编辑
            'edit': '编辑',
            'copy': '复制',
            'paste': '粘贴',
            'clear_board': '清空棋盘',
            'edit_mode': '编辑模式',
            'add_black_stone': '添加黑子',
            'add_white_stone': '添加白子',
            'remove_stone': '移除棋子',
            'mark_territory': '标记地盘',
            
            # 视图
            'view': '视图',
            'show_coordinates': '显示坐标',
            'show_move_numbers': '显示手数',
            'show_last_move': '显示最后一手',
            'show_variations': '显示变化',
            'show_analysis': '显示分析',
            'fullscreen': '全屏',
            'zoom_in': '放大',
            'zoom_out': '缩小',
            'reset_view': '重置视图',
            
            # 工具
            'tools': '工具',
            'game_tree': '游戏树',
            'position_analysis': '局面分析',
            'pattern_search': '模式搜索',
            'joseki_dictionary': '定式词典',
            'problem_library': '死活题库',
            'statistics': '统计信息',
            'game_record': '对局记录',
            
            # 帮助
            'help': '帮助',
            'rules_help': '规则说明',
            'tutorial': '教程',
            'shortcuts': '快捷键',
            'about': '关于',
            'check_updates': '检查更新',
            'report_bug': '报告问题',
            'online_manual': '在线手册',
            
            # 设置界面
            'general_settings': '通用设置',
            'display_settings': '显示设置',
            'sound_settings': '音效设置',
            'game_settings': '游戏设置',
            'ai_settings': 'AI设置',
            'network_settings': '网络设置',
            'advanced_settings': '高级设置',
            
            # 显示设置
            'theme': '主题',
            'wood_theme': '木纹主题',
            'modern_theme': '现代主题',
            'dark_theme': '暗黑主题',
            'custom_theme': '自定义主题',
            'board_style': '棋盘样式',
            'stone_style': '棋子样式',
            'grid_style': '网格样式',
            'coordinate_style': '坐标样式',
            'animation': '动画效果',
            'animation_speed': '动画速度',
            
            # 音效设置
            'sound': '音效',
            'sound_enabled': '启用音效',
            'volume': '音量',
            'sound_effects': '音效设置',
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
            'settings_saved': '设置已保存',
            'calculating': '计算中...',
            'thinking': '思考中...',
            'analyzing': '分析中...',
            
            # 错误消息
            'invalid_move': '无效落子',
            'ko_violation': '劫争违规',
            'suicide_move': '自杀着手',
            'already_occupied': '该位置已有棋子',
            'file_not_found': '文件未找到',
            'invalid_sgf': '无效的SGF文件',
            'network_error': '网络错误',
            'connection_lost': '连接丢失',
            'save_failed': '保存失败',
            'load_failed': '加载失败',
            
            # 提示信息
            'click_to_place': '点击落子',
            'your_turn': '轮到您了',
            'opponent_thinking': '对手思考中',
            'select_dead_stones': '请选择死子',
            'mark_territory': '请标记地盘',
            'choose_variation': '选择变化',
            'enter_comment': '输入注释',
            
            # 教学相关
            'lesson': '课程',
            'exercise': '练习',
            'solution': '答案',
            'correct': '正确',
            'incorrect': '错误',
            'try_again': '再试一次',
            'show_solution': '显示答案',
            'next_problem': '下一题',
            'previous_problem': '上一题',
            'problem_solved': '题目已解决',
            
            # 网络对战
            'connect': '连接',
            'disconnect': '断开',
            'host_game': '创建房间',
            'join_game': '加入房间',
            'room_name': '房间名',
            'player_name': '玩家名',
            'waiting_for_opponent': '等待对手',
            'opponent_connected': '对手已连接',
            'opponent_disconnected': '对手已断开',
            'chat': '聊天',
            'send_message': '发送消息',
            
            # 统计信息
            'total_games': '总对局数',
            'wins': '胜',
            'losses': '负',
            'win_rate': '胜率',
            'average_game_length': '平均手数',
            'favorite_opening': '常用开局',
            'time_played': '游戏时长',
            'achievements': '成就',
            
            # 成就
            'first_win': '首胜',
            'winning_streak': '连胜',
            'perfect_game': '完美对局',
            'joseki_master': '定式大师',
            'problem_solver': '解题高手',
            'speed_player': '快棋高手',
            
            # 其他
            'welcome': '欢迎',
            'goodbye': '再见',
            'thank_you': '谢谢',
            'loading': '加载中',
            'please_wait': '请稍候',
            'done': '完成',
            'version': '版本',
            'author': '作者',
            'license': '许可',
            'website': '网站',
            'email': '邮箱',
            'feedback': '反馈',
            'donate': '捐赠'
        },
        
        'en': {
            # 游戏基础
            'app_name': 'Go Master',
            'new_game': 'New Game',
            'continue': 'Continue',
            'settings': 'Settings',
            'quit': 'Quit',
            'black': 'Black',
            'white': 'White',
            'pass': 'Pass',
            'resign': 'Resign',
            'undo': 'Undo',
            'redo': 'Redo',
            'hint': 'Hint',
            'analyze': 'Analyze',
            'score': 'Score',
            
            # 游戏模式
            'game_mode': 'Game Mode',
            'human_vs_human': 'Human vs Human',
            'human_vs_ai': 'Human vs AI',
            'ai_vs_human': 'AI vs Human',
            'ai_vs_ai': 'AI vs AI',
            'online': 'Online',
            'replay': 'Replay',
            'tutorial': 'Tutorial',
            'puzzle': 'Puzzle',
            
            # AI难度
            'ai_level': 'AI Level',
            'beginner': 'Beginner',
            'easy': 'Easy',
            'medium': 'Medium',
            'hard': 'Hard',
            'expert': 'Expert',
            'master': 'Master',
            
            # 规则设置
            'rules': 'Rules',
            'chinese_rules': 'Chinese Rules',
            'japanese_rules': 'Japanese Rules',
            'aga_rules': 'AGA Rules',
            'board_size': 'Board Size',
            'komi': 'Komi',
            'handicap': 'Handicap',
            'time_control': 'Time Control',
            'no_time_limit': 'No Time Limit',
            'absolute_time': 'Absolute Time',
            'byoyomi': 'Byo-yomi',
            'canadian': 'Canadian',
            'fischer': 'Fischer',
            'main_time': 'Main Time',
            'overtime': 'Overtime',
            
            # 游戏状态
            'game_info': 'Game Info',
            'current_player': 'Current Player',
            'move_number': 'Move',
            'captures': 'Captures',
            'territory': 'Territory',
            'time_left': 'Time Left',
            'status': 'Status',
            'playing': 'Playing',
            'paused': 'Paused',
            'ended': 'Ended',
            'counting': 'Counting',
            
            # 结果
            'result': 'Result',
            'black_wins': 'Black Wins',
            'white_wins': 'White Wins',
            'jigo': 'Draw',
            'wins_by_resignation': 'Wins by Resignation',
            'wins_by_time': 'Wins on Time',
            'wins_by_points': 'Wins by Points',
            
            # 文件操作
            'file': 'File',
            'open': 'Open',
            'save': 'Save',
            'save_as': 'Save As',
            'import': 'Import',
            'export': 'Export',
            'recent_files': 'Recent Files',
            'sgf_files': 'SGF Files',
            'all_files': 'All Files',
            
            # 编辑
            'edit': 'Edit',
            'copy': 'Copy',
            'paste': 'Paste',
            'clear_board': 'Clear Board',
            'edit_mode': 'Edit Mode',
            'add_black_stone': 'Add Black Stone',
            'add_white_stone': 'Add White Stone',
            'remove_stone': 'Remove Stone',
            'mark_territory': 'Mark Territory',
            
            # 视图
            'view': 'View',
            'show_coordinates': 'Show Coordinates',
            'show_move_numbers': 'Show Move Numbers',
            'show_last_move': 'Show Last Move',
            'show_variations': 'Show Variations',
            'show_analysis': 'Show Analysis',
            'fullscreen': 'Fullscreen',
            'zoom_in': 'Zoom In',
            'zoom_out': 'Zoom Out',
            'reset_view': 'Reset View',
            
            # 显示设置
            'theme': 'Theme',
            'wood_theme': 'Wood Theme',
            'modern_theme': 'Modern Theme',
            'dark_theme': 'Dark Theme',
            'custom_theme': 'Custom Theme',
            'board_style': 'Board Style',
            'stone_style': 'Stone Style',
            'grid_style': 'Grid Style',
            'coordinate_style': 'Coordinate Style',
            'animation': 'Animation',
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
            'overwrite_current': 'Overwrite current game',
            
            # 其他（继续英文翻译...）
        },
        
        'ja': {
            # 游戏基础（日语翻译）
            'app_name': '囲碁マスター',
            'new_game': '新規対局',
            'black': '黒',
            'white': '白',
            'pass': 'パス',
            'resign': '投了',
            # ... 继续日语翻译
        }
    }
    
    def __init__(self, language: str = 'zh', custom_translations: Optional[str] = None):
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
        
        # 尝试从文件加载额外翻译
        self._load_translation_files()
    
    def _load_translation_files(self):
        """从文件加载翻译"""
        from . import resource_path
        trans_dir = resource_path(os.path.join("assets", "translations"))
        
        if os.path.exists(trans_dir):
            for file_name in os.listdir(trans_dir):
                if file_name.endswith('.json'):
                    lang_code = file_name[:-5]  # 移除.json
                    file_path = os.path.join(trans_dir, file_name)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            translations = json.load(f)
                            
                            if lang_code in self.translations:
                                self.translations[lang_code].update(translations)
                            else:
                                self.translations[lang_code] = translations
                                
                    except Exception as e:
                        print(f"加载翻译文件 {file_name} 失败: {e}")
    
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
        
        # 如果英语也没有，尝试中文
        if key not in lang_dict:
            lang_dict = self.translations.get('zh', {})
        
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
            raise ValueError(f"不支持的语言: {language}")
    
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
        zh_keys = set(self.translations.get('zh', {}).keys())
        lang_keys = set(self.translations.get(language, {}).keys())
        
        return {
            'missing': list(zh_keys - lang_keys),
            'extra': list(lang_keys - zh_keys)
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