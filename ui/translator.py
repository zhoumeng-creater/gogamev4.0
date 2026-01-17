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
            'teaching_mode': 'Teaching Mode',
            'teaching_mode_prompt': 'Enter teaching/sandbox mode? Changes will NOT be saved when you exit.',
            'exit_teaching': 'Exit Teaching',
            'dont_show_again': 'Do not show again',
            
            # 菜单
            'file': 'File',
            'edit': 'Edit',
            'view': 'View',
            'game': 'Game',
            'tools': 'Tools',
            'help': 'Help',
            
            # 文件菜单
            'new_game': 'New Game',
            'open': 'Open',
            'save_game': 'Save Game',
            'save_as': 'Save As',
            'load_game': 'Load Game',
            'save_sgf': 'Save as SGF',
            'load_sgf': 'Load SGF',
            'import_sgf': 'Import SGF',
            'export_sgf': 'Export SGF',
            'recent_files': 'Recent Files',
            'exit': 'Exit',
            'quit': 'Exit',
            
            # 编辑菜单
            'undo': 'Undo',
            'redo': 'Redo',
            'pass': 'Pass',
            'resign': 'Resign',
            'copy': 'Copy',
            'paste': 'Paste',
            'clear_board': 'Clear Board',
            # 兼容旧键：保持 edit_mode 映射到教学模式
            'edit_mode': 'Teaching Mode',
            
            # 视图菜单
            'show_coordinates': 'Show Coordinates',
            'show_move_numbers': 'Show Move Numbers',
            'show_territory': 'Show Territory',
            'show_influence': 'Show Influence',
            'highlight_last_move': 'Highlight Last Move',
            'show_last_move': 'Highlight Last Move',
            'full_screen': 'Full Screen',
            'fullscreen': 'Full Screen',
            'zoom_in': 'Zoom In',
            'zoom_out': 'Zoom Out',
            'reset_view': 'Reset View',
            
            # 游戏菜单
            'analyze': 'Analyze',
            'score': 'Score',
            'end_game': 'End Game',
            'estimate': 'Estimate',
            'hint': 'Hint',
            'statistics': 'Statistics',
            'finish_scoring': 'Confirm Result',
            
            # 工具菜单
            'settings': 'Settings',
            'game_tree': 'Game Tree',
            'position_analysis': 'Position Analysis',
            'joseki_dictionary': 'Joseki Dictionary',
            'joseki_library': 'Joseki Library',
            'game_review': 'Game Review',
            'pattern_search': 'Pattern Search',
            'problem_library': 'Problem Library',
            'problem_list': 'Problem List',
            'problem_info': 'Problem Info',
            'problem_objective': 'Objective',
            'problem_show_solution': 'Show Solution',
            'problem_reset_board': 'Reset Board',
            'problem_resources': 'Problem Resources',
            'problem_solution': 'Solution',
            'problem_status_ready': 'Select a problem and click the board to try.',
            'problem_status_correct': 'Correct!',
            'problem_status_incorrect': 'Try again.',
            'problem_status_continue': 'Correct, continue.',
            'problem_status_completed': 'Correct, problem solved.',
            'problem_import_hint': 'Supported: SGF / JSON',
            'problem_import_strategy': 'Merge',
            'problem_import_strategy_overwrite': 'Overwrite',
            'problem_import_strategy_skip': 'Skip',
            'problem_import_strategy_copy': 'New Copy',
            'problem_import_guide': 'Formats',
            'problem_import_guide_title': 'Problem Import Formats',
            'problem_import_guide_body': 'Supported formats:\n'
                                         '1) SGF (.sgf): uses AB/AW for setup and the main line as the solution.\n'
                                         '2) JSON (.json): a list or {"puzzles": [...]}.\n'
                                         'JSON supports board_state (2D list) or stones list.\n'
                                         'Example:\n'
                                         '{\n'
                                         '  "puzzles": [\n'
                                         '    {\n'
                                         '      "title": "Sample Puzzle",\n'
                                         '      "difficulty": 2,\n'
                                         '      "board_size": 9,\n'
                                         '      "stones": [{"x": 4, "y": 4, "color": "white"}],\n'
                                         '      "player_color": "black",\n'
                                         '      "objective": "Capture the white stone",\n'
                                         '      "solution": [[4, 5]]\n'
                                         '    }\n'
                                         '  ]\n'
                                         '}\n',
            'problem_import_success': 'Imported {count} problems.',
            'problem_import_failed': 'No valid problems found.',
            'problem_rebuild': 'Rebuild',
            'problem_rebuild_title': 'Rebuild Puzzle Library',
            'problem_rebuild_confirm': 'Rebuild the default puzzle pack now? Imported puzzles will be kept.',
            'problem_rebuild_done': 'Rebuilt {count} puzzles from the default pack.',
            'search': 'Search',
            'keyword': 'Keyword',
            'search_web': 'Search Web',
            'no_results': 'No local results',
            'joseki_list': 'Joseki List',
            'joseki_info': 'Joseki Info',
            'board_preview': 'Board Preview',
            'comment': 'Comment',
            'pattern_library': 'Pattern Library',
            'pattern_category': 'Category',
            'pattern_color': 'Color',
            'pattern_scan': 'Scan Board',
            'pattern_matches': 'Matches',
            'pattern_details': 'Pattern Details',
            'pattern_anchor': 'Anchor',
            'pattern_next_moves': 'Next Moves',
            'pattern_stones': 'Stones',
            'pattern_empty_points': 'Empty Points',
            'pattern_context': 'Context',
            'pattern_filter_all': 'All',
            'pattern_category_joseki': 'Joseki',
            'pattern_category_tactical': 'Tactical',
            'pattern_category_life_death': 'Life & Death',
            'pattern_category_tesuji': 'Tesuji',
            'color_auto': 'Auto',
            'name': 'Name',
            'type': 'Type',
            'difficulty': 'Difficulty',
            'result': 'Result',
            'popularity': 'Popularity',
            'joseki_type_corner': 'Corner',
            'joseki_type_side': 'Side',
            'joseki_type_invasion': 'Invasion',
            'joseki_type_reduction': 'Reduction',
            'joseki_type_special': 'Special',
            'joseki_type_opening': 'Opening',
            'joseki_type_fighting': 'Fighting',
            'joseki_result_even': 'Even',
            'joseki_result_slightly_better_black': 'Slightly better for Black',
            'joseki_result_slightly_better_white': 'Slightly better for White',
            'joseki_result_better_black': 'Better for Black',
            'joseki_result_better_white': 'Better for White',
            'joseki_result_complicated': 'Complicated',
            'joseki_result_depends': 'Depends',
            'joseki_name_san_san_basic': '3-3 Joseki - Basic',
            'joseki_comment_san_san_basic': 'Basic 3-3 joseki: Black takes corner territory, White gets outside influence.',
            'joseki_name_star_point_small_approach_joseki': 'Star Point Joseki - Small Approach',
            'joseki_comment_star_point_small_approach_joseki': 'One of the most common star point joseki.',
            'joseki_name_komoku_high_approach_joseki': 'Komoku Joseki - High Approach',
            'joseki_comment_komoku_high_approach_joseki': 'Komoku high approach joseki with rich variations.',
            'joseki_name_takamoku_basic': 'Takamoku Joseki - Basic',
            'joseki_comment_takamoku_basic': 'Takamoku joseki emphasizes outside influence.',
            'joseki_name_three_three_invasion': '3-3 Invasion',
            'joseki_comment_three_three_invasion': 'Basic 3-3 invasion joseki; position is even.',
            'joseki_name_star_point_small_approach': 'Star Point Small Approach',
            'joseki_comment_star_point_small_approach': 'Basic response to the star point small approach.',
            'joseki_name_komoku_one_space_high_approach': 'Komoku One-space High Approach',
            'joseki_comment_komoku_one_space_high_approach': 'Common variations of the komoku one-space high approach.',
            'joseki_name_chinese_fuseki': 'Chinese Fuseki',
            'joseki_comment_chinese_fuseki': 'Chinese opening where Black builds a large framework.',
            'joseki_name_three_star_fuseki': 'Three-Star Fuseki',
            'joseki_comment_three_star_fuseki': 'Three-star opening emphasizing central influence.',
            'joseki_name_kobayashi_fuseki': 'Kobayashi Fuseki',
            'joseki_comment_kobayashi_fuseki': 'Kobayashi opening balancing territory and influence.',
            'joseki_name_avalanche_joseki': 'Avalanche Joseki',
            'joseki_comment_avalanche_joseki': 'Complex avalanche joseki requiring precise reading.',
            'joseki_name_taisha_joseki': 'Taisha Joseki',
            'joseki_comment_taisha_joseki': 'Basic form of the Taisha joseki.',
            'joseki_name_double_flying_goose_joseki': 'Double Flying Goose Joseki',
            'joseki_comment_double_flying_goose_joseki': 'Double flying goose formation emphasizing outside influence.',
            'joseki_name_zhen_shen_tou': 'Zhen Shen Tou',
            'joseki_comment_zhen_shen_tou': 'Zhen Shen Tou tesuji used for attack.',
            'joseki_move_comment_star_point_small_approach_joseki_one_space_pincer': 'One-space pincer, play actively.',
            'joseki_move_comment_star_point_small_approach_joseki_two_space_pincer': 'Two-space pincer, emphasize outside influence.',
            'joseki_move_comment_star_point_small_approach_joseki_small_knight_reply': 'Small knight response, simple and solid.',
            'pattern_name_san_san_invasion': '3-3 Invasion',
            'pattern_context_san_san_invasion': 'Responding to a 3-3 invasion',
            'pattern_name_star_point_approach': 'Star Point Approach',
            'pattern_context_star_point_approach': 'Star point small approach',
            'pattern_name_komoku_approach': 'Komoku Approach',
            'pattern_context_komoku_approach': 'Komoku one-space high approach',
            'pattern_name_cut_point': 'Cut Point',
            'pattern_context_cut_point': 'Cut to break the connection',
            'pattern_name_double_atari': 'Double Atari',
            'pattern_context_double_atari': 'Double atari',
            'pattern_name_hane': 'Hane',
            'pattern_context_hane': 'Hane at the head',
            'pattern_name_tiger_mouth': "Tiger's Mouth",
            'pattern_context_tiger_mouth': "Reinforce the tiger's mouth",
            'pattern_name_straight_three_eyes': 'Straight Three',
            'pattern_context_straight_three_eyes': 'Make an eye with straight three',
            'pattern_name_bent_three_eyes': 'Bent Three',
            'pattern_context_bent_three_eyes': 'Make an eye with bent three',
            
            # 帮助菜单
            'rules': 'Rules',
            'rules_help': 'Rules',
            'tutorial': 'Tutorial',
            'shortcuts': 'Shortcuts',
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
            'done': 'Done',
            'continue': 'Continue',
            
            # 对话框
            'confirm': 'Confirm',
            'info': 'Information',
            'warning': 'Warning',
            'error': 'Error',
            'confirm_resign': 'Are you sure you want to resign?',
            'confirm_exit_message': 'Game in progress. Are you sure you want to exit?',
            'settings_applied': 'Settings have been applied',
            'restore_defaults_confirm': 'Are you sure you want to restore default settings?',
            'delete_game_confirm': 'Are you sure you want to delete this game?',
            'overwrite_current': 'Overwrite Current Game',
            'confirm_clear_board': 'Are you sure you want to clear the board?',
            'save_current_game': 'Do you want to save the current game?',
            'end_game_confirm': 'End the game and auto-score? Continue?',
            'enter_save_name': 'Enter save name',
            
            # 文件操作
            'filename': 'Filename',
            'date': 'Date',
            'format': 'Format',
            'game_files': 'Game Files',
            'sgf_files': 'SGF Files',
            'all_files': 'All Files',
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
            'sgf_copied': 'SGF copied to clipboard',
            'sgf_pasted': 'SGF loaded from clipboard',
            'invalid_sgf': 'Invalid SGF data',
            'no_saved_games': 'No saved games found',
            'move_undone': 'Move Undone',
            'move_redone': 'Move Redone',
            'analyzing': 'Analyzing',
            'analysis_complete': 'Analysis Complete',
            'calculating_hint': 'Calculating best move...',
            'pass_recommended': 'Pass is recommended',
            'illegal_move': 'Illegal Move',
            'ko_rule': 'Ko Rule Violation',
            'suicide_rule': 'Suicide Move',
            'invalid_move': 'Invalid Move',
            'ko_violation': 'Ko Rule Violation',
            'suicide_move': 'Suicide Move',
            'need_two_passes': 'Two passes needed to enter scoring phase',
            'accept_result': 'Accept this result?',
            'save_failed': 'Save Failed',
            'score_failed': 'Failed to calculate score',
            'load_failed': 'Load Failed',
            
            # 游戏结果
            'game_over': 'Game Over',
            'game_result': 'Game Result',
            'black_wins': 'Black Wins',
            'white_wins': 'White Wins',
            'draw': 'Draw',
            'jigo': 'Draw',
            'wins': 'wins',
            'points': 'points',
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
            'total_players': 'Total Players',
            'black_wins_count': 'Black Wins',
            'white_wins_count': 'White Wins',
            'draws': 'Draws',
            'average_moves': 'Average Moves',
            'average_game_length': 'Average Game Length',
            'vs_ai_games': 'Games vs AI',
            'most_active_player': 'Most Active Player',
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
            'teaching_mode': '教学模式',
            'teaching_mode_prompt': '进入教学/推演模式？退出时所做改动不会被保存。',
            'exit_teaching': '退出教学模式',
            'dont_show_again': '不再提示',
            
            # 菜单
            'file': '文件',
            'edit': '编辑',
            'view': '视图',
            'game': '对局',
            'tools': '工具',
            'help': '帮助',
            
            # 文件菜单
            'new_game': '新对局',
            'open': '打开',
            'save_game': '保存对局',
            'save_as': '另存为',
            'load_game': '加载对局',
            'save_sgf': '保存为SGF',
            'load_sgf': '加载SGF',
            'import_sgf': '导入SGF',
            'export_sgf': '导出SGF',
            'recent_files': '最近文件',
            'exit': '退出',
            'quit': '退出',
            
            # 编辑菜单
            'undo': '悔棋',
            'redo': '重做',
            'pass': '虚手',
            'resign': '认输',
            'copy': '复制',
            'paste': '粘贴',
            'clear_board': '清空棋盘',
            # 兼容旧键：保持 edit_mode 映射到教学模式
            'edit_mode': '教学模式',
            
            # 视图菜单
            'show_coordinates': '显示坐标',
            'show_move_numbers': '显示手数',
            'show_territory': '显示地盘',
            'show_influence': '显示势力',
            'highlight_last_move': '高亮最后一手',
            'show_last_move': '高亮最后一手',
            'full_screen': '全屏',
            'fullscreen': '全屏',
            'zoom_in': '放大',
            'zoom_out': '缩小',
            'reset_view': '重置视图',
            
            # 游戏菜单
            'analyze': '分析',
            'score': '数子',
            'end_game': '结束对局',
            'estimate': '形势估计',
            'hint': '提示',
            'statistics': '统计',
            'finish_scoring': '确认结果',
            
            # 工具菜单
            'settings': '设置',
            'game_tree': '棋谱树',
            'position_analysis': '局面分析',
            'joseki_dictionary': '定式词典',
            'joseki_library': '定式库',
            'game_review': '复盘',
            'pattern_search': '棋型搜索',
            'problem_library': '题库',
            'problem_list': '题目列表',
            'problem_info': '题目信息',
            'problem_objective': '目标',
            'problem_show_solution': '查看答案',
            'problem_reset_board': '重置棋盘',
            'problem_resources': '题库资源',
            'problem_solution': '答案',
            'problem_status_ready': '请选择题目并在棋盘上尝试。',
            'problem_status_correct': '正确！',
            'problem_status_incorrect': '再试试。',
            'problem_status_continue': '正确，继续下一手。',
            'problem_status_completed': '正确，题目完成。',
            'problem_import_hint': '支持格式：SGF / JSON',
            'problem_import_strategy': '合并',
            'problem_import_strategy_overwrite': '覆盖',
            'problem_import_strategy_skip': '跳过',
            'problem_import_strategy_copy': '新副本',
            'problem_import_guide': '导入格式',
            'problem_import_guide_title': '题库导入格式',
            'problem_import_guide_body': '支持格式：\n'
                                         '1) SGF (.sgf)：使用 AB/AW 作为初始摆子，主线作为答案。\n'
                                         '2) JSON (.json)：列表或 {"puzzles": [...]}。\n'
                                         'JSON 可用 board_state（二维列表）或 stones 列表描述初始局面。\n'
                                         '示例：\n'
                                         '{\n'
                                         '  "puzzles": [\n'
                                         '    {\n'
                                         '      "title": "示例题",\n'
                                         '      "difficulty": 2,\n'
                                         '      "board_size": 9,\n'
                                         '      "stones": [{"x": 4, "y": 4, "color": "white"}],\n'
                                         '      "player_color": "black",\n'
                                         '      "objective": "吃掉白子",\n'
                                         '      "solution": [[4, 5]]\n'
                                         '    }\n'
                                         '  ]\n'
                                         '}\n',
            'problem_import_success': '已导入 {count} 道题目。',
            'problem_import_failed': '未找到可导入的题目。',
            'problem_rebuild': '重建题库',
            'problem_rebuild_title': '重建题库',
            'problem_rebuild_confirm': '现在重建默认题库吗？已导入的题目会保留。',
            'problem_rebuild_done': '已从默认题库重建 {count} 道题目。',
            'search': '搜索',
            'keyword': '关键词',
            'search_web': '搜索网页',
            'no_results': '未找到本地结果',
            'joseki_list': '定式列表',
            'joseki_info': '定式信息',
            'board_preview': '棋盘预览',
            'comment': '评注',
            'pattern_library': '棋型词典',
            'pattern_category': '类别',
            'pattern_color': '颜色',
            'pattern_scan': '扫描棋盘',
            'pattern_matches': '匹配结果',
            'pattern_details': '棋型详情',
            'pattern_anchor': '锚点',
            'pattern_next_moves': '后续着法',
            'pattern_stones': '棋子',
            'pattern_empty_points': '空点',
            'pattern_context': '场景',
            'pattern_filter_all': '全部',
            'pattern_category_joseki': '定式',
            'pattern_category_tactical': '战术',
            'pattern_category_life_death': '死活',
            'pattern_category_tesuji': '手筋',
            'color_auto': '自动',
            'name': '名称',
            'type': '类型',
            'difficulty': '难度',
            'result': '结果',
            'popularity': '流行度',
            'joseki_type_corner': '角部定式',
            'joseki_type_side': '边部定式',
            'joseki_type_invasion': '打入定式',
            'joseki_type_reduction': '消减定式',
            'joseki_type_special': '特殊定式',
            'joseki_type_opening': '布局定式',
            'joseki_type_fighting': '战斗定式',
            'joseki_result_even': '均势',
            'joseki_result_slightly_better_black': '黑略好',
            'joseki_result_slightly_better_white': '白略好',
            'joseki_result_better_black': '黑优',
            'joseki_result_better_white': '白优',
            'joseki_result_complicated': '复杂',
            'joseki_result_depends': '视情况而定',
            'joseki_name_san_san_basic': '三三定式-基本型',
            'joseki_comment_san_san_basic': '最基本的三三定式，黑角实地，白获外势',
            'joseki_name_star_point_small_approach_joseki': '星位定式-小飞挂',
            'joseki_comment_star_point_small_approach_joseki': '星位小飞挂是最常见的定式之一',
            'joseki_name_komoku_high_approach_joseki': '小目定式-高挂',
            'joseki_comment_komoku_high_approach_joseki': '小目高挂定式，变化丰富',
            'joseki_name_takamoku_basic': '高目定式-基本型',
            'joseki_comment_takamoku_basic': '高目定式强调外势',
            'joseki_name_three_three_invasion': '3-3点入侵',
            'joseki_comment_three_three_invasion': '基础的3-3点入侵定式，双方均势',
            'joseki_name_star_point_small_approach': '星位小飞挂',
            'joseki_comment_star_point_small_approach': '星位小飞挂角的基本应对',
            'joseki_name_komoku_one_space_high_approach': '小目一间高挂',
            'joseki_comment_komoku_one_space_high_approach': '小目一间高挂的常见变化',
            'joseki_name_chinese_fuseki': '中国流布局',
            'joseki_comment_chinese_fuseki': '中国流开局，黑棋构筑大模样',
            'joseki_name_three_star_fuseki': '三连星布局',
            'joseki_comment_three_star_fuseki': '三连星布局，重视中央势力',
            'joseki_name_kobayashi_fuseki': '小林流布局',
            'joseki_comment_kobayashi_fuseki': '小林流布局，平衡实地与外势',
            'joseki_name_avalanche_joseki': '雪崩定式',
            'joseki_comment_avalanche_joseki': '复杂的雪崩定式，需要精确计算',
            'joseki_name_taisha_joseki': '大斜定式',
            'joseki_comment_taisha_joseki': '大斜定式的基本型',
            'joseki_name_double_flying_goose_joseki': '双飞燕定式',
            'joseki_comment_double_flying_goose_joseki': '双飞燕阵型，强调外势',
            'joseki_name_zhen_shen_tou': '镇神头',
            'joseki_comment_zhen_shen_tou': '镇神头战术，用于攻击',
            'joseki_move_comment_star_point_small_approach_joseki_one_space_pincer': '一间夹，积极作战',
            'joseki_move_comment_star_point_small_approach_joseki_two_space_pincer': '二间夹，重视外势',
            'joseki_move_comment_star_point_small_approach_joseki_small_knight_reply': '小飞应，简明',
            'pattern_name_san_san_invasion': '三三入侵',
            'pattern_context_san_san_invasion': '三三入侵应对',
            'pattern_name_star_point_approach': '星位小飞挂',
            'pattern_context_star_point_approach': '星位小飞挂',
            'pattern_name_komoku_approach': '小目一间高挂',
            'pattern_context_komoku_approach': '小目一间高挂',
            'pattern_name_cut_point': '断点',
            'pattern_context_cut_point': '切断对方连接',
            'pattern_name_double_atari': '双叫吃',
            'pattern_context_double_atari': '双叫吃',
            'pattern_name_hane': '扳',
            'pattern_context_hane': '扳头',
            'pattern_name_tiger_mouth': '虎口',
            'pattern_context_tiger_mouth': '虎口补强',
            'pattern_name_straight_three_eyes': '直三做眼',
            'pattern_context_straight_three_eyes': '直三做眼',
            'pattern_name_bent_three_eyes': '曲三做眼',
            'pattern_context_bent_three_eyes': '曲三做眼',
            
            # 帮助菜单
            'rules': '规则',
            'rules_help': '规则说明',
            'tutorial': '教程',
            'shortcuts': '快捷键',
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
            'scoring': '数子确认中',
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
            'situation': '局势',
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
            'done': '完成',
            'continue': '继续',
            
            # 对话框
            'confirm': '确认',
            'info': '信息',
            'warning': '警告',
            'error': '错误',
            'confirm_resign': '确定要认输吗？',
            'confirm_exit_message': '对局进行中，确定要退出吗？',
            'settings_applied': '设置已应用',
            'restore_defaults_confirm': '确定要恢复默认设置吗？',
            'delete_game_confirm': '确定要删除这个对局吗？',
            'overwrite_current': '覆盖当前对局',
            'confirm_clear_board': '确定要清空棋盘吗？',
            'save_current_game': '是否保存当前对局？',
            'end_game_confirm': '结束对局将自动数子并显示结果，确定继续吗？',
            'enter_save_name': '请输入存档名称',
            
            # 文件操作
            'filename': '文件名',
            'date': '日期',
            'format': '格式',
            'game_files': '对局文件',
            'sgf_files': 'SGF文件',
            'all_files': '所有文件',
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
            'sgf_copied': 'SGF已复制到剪贴板',
            'sgf_pasted': '已从剪贴板导入SGF',
            'invalid_sgf': '无效的SGF数据',
            'no_saved_games': '没有找到存档',
            'move_undone': '已悔棋',
            'move_redone': '已重做',
            'analyzing': '分析中',
            'analysis_complete': '分析完成',
            'calculating_hint': '正在计算最佳着法...',
            'pass_recommended': '建议虚手',
            'illegal_move': '非法落子',
            'ko_rule': '违反劫规则',
            'suicide_rule': '自杀手',
            'invalid_move': '非法落子',
            'ko_violation': '违反劫规则',
            'suicide_move': '自杀禁手',
            'need_two_passes': '需要两次虚手才能进入点目阶段',
            'accept_result': '接受这个结果吗？',
            'save_failed': '保存失败',
            'score_failed': '计算分数失败',
            'load_failed': '加载失败',
            
            # 游戏结果
            'game_over': '对局结束',
            'game_result': '对局结果',
            'black_wins': '黑棋胜',
            'white_wins': '白棋胜',
            'draw': '和棋',
            'jigo': '平局',
            'wins': '胜',
            'points': '目',
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
            'total_players': '总玩家数',
            'black_wins_count': '黑棋胜',
            'white_wins_count': '白棋胜',
            'draws': '和棋',
            'average_moves': '平均手数',
            'average_game_length': '平均对局长度',
            'vs_ai_games': '人机对局',
            'vs_human_games': '人人对局',
            'most_active_player': '最活跃玩家',
            
            # 其他
            'feature_coming_soon': '此功能即将推出！',
            'rules_description': '围棋是一种两人对弈的策略棋盘游戏。',
            'tutorial_content': '欢迎使用围棋大师教程！',
            'passed': '虚手',
            'move_number': '第{}手'
        },
        
        'ja': {
            # 日本語
            # 基础
            'app_name': '囲碁マスター',
            'version': 'バージョン',
            'author': '作者',
            'description': 'AI対戦と解析ツールを備えた囲碁アプリ',
            'teaching_mode': '練習モード',
            'teaching_mode_prompt': '練習/検討モードに入りますか？終了時に変更は保存されません。',
            'exit_teaching': '練習モードを終了',
            'dont_show_again': '次回から表示しない',

            # 菜单
            'file': 'ファイル',
            'edit': '編集',
            'view': '表示',
            'game': '対局',
            'tools': 'ツール',
            'help': 'ヘルプ',

            # 文件菜单
            'new_game': '新規対局',
            'open': '開く',
            'save_game': '対局を保存',
            'save_as': '名前を付けて保存',
            'load_game': '対局を読み込み',
            'save_sgf': 'SGFとして保存',
            'load_sgf': 'SGFを読み込み',
            'import_sgf': 'SGFをインポート',
            'export_sgf': 'SGFをエクスポート',
            'recent_files': '最近使ったファイル',
            'exit': '終了',
            'quit': '終了',

            # 编辑菜单
            'undo': '戻す',
            'redo': 'やり直し',
            'pass': 'パス',
            'resign': '投了',
            'copy': 'コピー',
            'paste': '貼り付け',
            'clear_board': '盤面をクリア',
            # 互換キー：edit_mode を練習モードに揃える
            'edit_mode': '練習モード',

            # 视图菜单
            'show_coordinates': '座標を表示',
            'show_move_numbers': '手数を表示',
            'show_territory': '地を表示',
            'show_influence': '勢力を表示',
            'highlight_last_move': '最終手を強調',
            'show_last_move': '最終手を強調',
            'full_screen': '全画面',
            'fullscreen': '全画面',
            'zoom_in': '拡大',
            'zoom_out': '縮小',
            'reset_view': '表示をリセット',

            # 游戏菜单
            'analyze': '解析',
            'score': '採点',
            'end_game': '対局終了',
            'estimate': '形勢推定',
            'hint': 'ヒント',
            'statistics': '統計',
            'finish_scoring': '結果を確定',

            # 工具菜单
            'settings': '設定',
            'game_tree': '棋譜ツリー',
            'position_analysis': '局面解析',
            'joseki_dictionary': '定石辞典',
            'joseki_library': '定石ライブラリ',
            'game_review': '検討',
            'pattern_search': '棋形検索',
            'problem_library': '問題集',
            'problem_list': '問題一覧',
            'problem_info': '問題情報',
            'problem_objective': '目的',
            'problem_show_solution': '解答を見る',
            'problem_reset_board': '盤面をリセット',
            'problem_resources': '問題リソース',
            'problem_solution': '解答',
            'problem_status_ready': '問題を選択して盤面で試してください。',
            'problem_status_correct': '正解！',
            'problem_status_incorrect': 'もう一度。',
            'problem_status_continue': '正解、続けてください。',
            'problem_status_completed': '正解、完了。',
            'problem_import_hint': '対応形式: SGF / JSON',
            'problem_import_strategy': '統合',
            'problem_import_strategy_overwrite': '上書き',
            'problem_import_strategy_skip': 'スキップ',
            'problem_import_strategy_copy': '新しいコピー',
            'problem_import_guide': '形式',
            'problem_import_guide_title': '問題集のインポート形式',
            'problem_import_guide_body': '対応形式：\n'
                                         '1) SGF (.sgf)：AB/AW を初期配置、主線を解答として読み込みます。\n'
                                         '2) JSON (.json)：リストまたは {"puzzles": [...]}。\n'
                                         'JSON は board_state（2次元配列）または stones を使用できます。\n'
                                         '例：\n'
                                         '{\n'
                                         '  "puzzles": [\n'
                                         '    {\n'
                                         '      "title": "サンプル",\n'
                                         '      "difficulty": 2,\n'
                                         '      "board_size": 9,\n'
                                         '      "stones": [{"x": 4, "y": 4, "color": "white"}],\n'
                                         '      "player_color": "black",\n'
                                         '      "objective": "白石を取る",\n'
                                         '      "solution": [[4, 5]]\n'
                                         '    }\n'
                                         '  ]\n'
                                         '}\n',
            'problem_import_success': '{count} 問をインポートしました。',
            'problem_import_failed': 'インポートできる問題がありません。',
            'problem_rebuild': '再構築',
            'problem_rebuild_title': '問題集の再構築',
            'problem_rebuild_confirm': '標準問題集を再構築しますか？インポート済みの問題は保持されます。',
            'problem_rebuild_done': '標準問題集から {count} 問を再構築しました。',
            'search': '検索',
            'keyword': 'キーワード',
            'search_web': 'Web検索',
            'no_results': 'ローカル結果なし',
            'joseki_list': '定石一覧',
            'joseki_info': '定石情報',
            'board_preview': '盤面プレビュー',
            'comment': 'コメント',
            'pattern_library': '棋形辞典',
            'pattern_category': 'カテゴリ',
            'pattern_color': '色',
            'pattern_scan': '盤面をスキャン',
            'pattern_matches': '一致結果',
            'pattern_details': '棋形詳細',
            'pattern_anchor': '基準点',
            'pattern_next_moves': '次の手',
            'pattern_stones': '石',
            'pattern_empty_points': '空点',
            'pattern_context': '状況',
            'pattern_filter_all': 'すべて',
            'pattern_category_joseki': '定石',
            'pattern_category_tactical': '戦術',
            'pattern_category_life_death': '死活',
            'pattern_category_tesuji': '手筋',
            'color_auto': '自動',
            'name': '名称',
            'type': '種類',
            'difficulty': '難度',
            'result': '結果',
            'popularity': '人気度',
            'joseki_type_corner': '隅の定石',
            'joseki_type_side': '辺の定石',
            'joseki_type_invasion': '侵入定石',
            'joseki_type_reduction': '減らし定石',
            'joseki_type_special': '特殊定石',
            'joseki_type_opening': '布石定石',
            'joseki_type_fighting': '戦闘定石',
            'joseki_result_even': '互角',
            'joseki_result_slightly_better_black': '黒がやや良い',
            'joseki_result_slightly_better_white': '白がやや良い',
            'joseki_result_better_black': '黒が良い',
            'joseki_result_better_white': '白が良い',
            'joseki_result_complicated': '複雑',
            'joseki_result_depends': '状況次第',
            'joseki_name_san_san_basic': '三三定石・基本形',
            'joseki_comment_san_san_basic': '基本的な三三定石。黒は角の実地、白は外勢。',
            'joseki_name_star_point_small_approach_joseki': '星位定石・小ゲ掛かり',
            'joseki_comment_star_point_small_approach_joseki': '星位小ゲ掛かりは最も一般的な定石の一つ。',
            'joseki_name_komoku_high_approach_joseki': '小目定石・高掛かり',
            'joseki_comment_komoku_high_approach_joseki': '小目高掛かり定石。変化が豊富。',
            'joseki_name_takamoku_basic': '高目定石・基本形',
            'joseki_comment_takamoku_basic': '高目定石は外勢を重視。',
            'joseki_name_three_three_invasion': '三三侵入',
            'joseki_comment_three_three_invasion': '基本的な三三侵入定石。形勢は互角。',
            'joseki_name_star_point_small_approach': '星位小ゲ掛かり',
            'joseki_comment_star_point_small_approach': '星位小ゲ掛かりへの基本応手。',
            'joseki_name_komoku_one_space_high_approach': '小目一間高掛かり',
            'joseki_comment_komoku_one_space_high_approach': '小目一間高掛かりの一般的な変化。',
            'joseki_name_chinese_fuseki': '中国流布石',
            'joseki_comment_chinese_fuseki': '中国流の布石。黒が大模様を築く。',
            'joseki_name_three_star_fuseki': '三連星布石',
            'joseki_comment_three_star_fuseki': '三連星の布石。中央勢力を重視。',
            'joseki_name_kobayashi_fuseki': '小林流布石',
            'joseki_comment_kobayashi_fuseki': '小林流布石。実地と外勢のバランス。',
            'joseki_name_avalanche_joseki': '雪崩定石',
            'joseki_comment_avalanche_joseki': '複雑な雪崩定石。正確な読みが必要。',
            'joseki_name_taisha_joseki': '大斜定石',
            'joseki_comment_taisha_joseki': '大斜定石の基本形。',
            'joseki_name_double_flying_goose_joseki': '双飛燕定石',
            'joseki_comment_double_flying_goose_joseki': '双飛燕の形。外勢を強調。',
            'joseki_name_zhen_shen_tou': '鎮神頭',
            'joseki_comment_zhen_shen_tou': '鎮神頭の戦術。攻めに用いる。',
            'joseki_move_comment_star_point_small_approach_joseki_one_space_pincer': '一間挟みで積極的に戦う。',
            'joseki_move_comment_star_point_small_approach_joseki_two_space_pincer': '二間挟みで外勢を重視。',
            'joseki_move_comment_star_point_small_approach_joseki_small_knight_reply': '小ゲ受けで簡明。',
            'pattern_name_san_san_invasion': '三三侵入',
            'pattern_context_san_san_invasion': '三三侵入への応手',
            'pattern_name_star_point_approach': '星位小ゲ掛かり',
            'pattern_context_star_point_approach': '星位小ゲ掛かり',
            'pattern_name_komoku_approach': '小目一間高掛かり',
            'pattern_context_komoku_approach': '小目一間高掛かり',
            'pattern_name_cut_point': '切断点',
            'pattern_context_cut_point': '相手の連結を切る',
            'pattern_name_double_atari': 'ダブルアタリ',
            'pattern_context_double_atari': 'ダブルアタリ',
            'pattern_name_hane': 'ハネ',
            'pattern_context_hane': '頭をハネる',
            'pattern_name_tiger_mouth': '虎口',
            'pattern_context_tiger_mouth': '虎口を補強',
            'pattern_name_straight_three_eyes': '直三',
            'pattern_context_straight_three_eyes': '直三の眼作り',
            'pattern_name_bent_three_eyes': '曲三',
            'pattern_context_bent_three_eyes': '曲三の眼作り',

            # 帮助菜单
            'rules': 'ルール',
            'rules_help': 'ルール',
            'tutorial': 'チュートリアル',
            'shortcuts': 'ショートカット',
            'about': 'このアプリについて',

            # 游戏相关
            'black': '黒',
            'white': '白',
            'players': 'プレイヤー',
            'current_player': '手番',
            'black_player': '黒番',
            'white_player': '白番',
            'move': '手',
            'moves': '手数',
            'captured': '取った石',
            'ko': 'コウ',
            'phase': '状態',
            'playing': '対局中',
            'scoring': '採点中',
            'ended': '終了',

            # 游戏信息
            'game_info': '対局情報',
            'game_mode': '対局モード',
            'game_settings': '対局設定',
            'game_control': '対局操作',
            'board_size': '盤サイズ',
            'default_board_size': '既定の盤サイズ',
            'komi': 'コミ',
            'default_komi': '既定のコミ',
            'handicap': '置石',
            'time_control': '時間設定',
            'main_time': '持ち時間',
            'byoyomi': '秒読み',
            'none': 'なし',
            'absolute': '持ち時間のみ',
            'canadian': 'カナダ式',

            # 规则
            'rules_type': 'ルール',
            'default_rules': '既定のルール',
            'chinese': '中国ルール',
            'japanese': '日本ルール',
            'aga': 'AGAルール',
            'ing': 'Ingルール',
            'new_zealand': 'ニュージーランドルール',

            # 游戏模式
            'human_vs_human': '人 vs 人',
            'human_vs_ai': '人 vs AI',
            'ai_vs_human': 'AI vs 人',
            'ai_vs_ai': 'AI vs AI',
            'player': 'プレイヤー',
            'player_1': 'プレイヤー1',
            'player_2': 'プレイヤー2',

            # AI相关
            'ai': 'AI',
            'ai_level': 'AI難易度',
            'default_ai_level': '既定のAI難易度',
            'ai_thinking_time': 'AI思考時間',
            'easy': '易しい',
            'medium': '普通',
            'hard': '難しい',
            'expert': '上級',
            'ai_thinking': 'AI思考中...',

            # 分析
            'analysis': '解析',
            'analysis_info': '解析情報',
            'situation': '形勢',
            'suggestions': '候補手',
            'win_rate': '勝率',
            'visits': '探索回数',
            'thinking_time': '思考時間',
            'nodes_analyzed': '解析ノード数',
            'search_depth': '探索深度',
            'show_ai_analysis': 'AI解析を表示',
            'show_winrate': '勝率を表示',
            'show_best_moves': '最善手を表示',
            'auto_analyze': '自動解析',

            # 导航
            'navigation': 'ナビゲーション',
            'branches': '分岐',
            'auto_play': '自動再生',
            'play': '再生',
            'pause': '一時停止',
            'speed': '速度',
            'create': '作成',
            'delete': '削除',

            # 显示设置
            'display': '表示',
            'animation_settings': 'アニメーション設定',
            'enable_animations': 'アニメーションを有効化',
            'animation_speed': 'アニメーション速度',

            # 音效设置
            'sound': 'サウンド',
            'sound_enabled': 'サウンドを有効化',
            'volume': '音量',
            'sound_effects': '効果音',
            'stone_sound': '着手音',
            'capture_sound': '取る音',
            'time_warning_sound': '時間警告音',

            # 高级设置
            'advanced': '詳細',
            'sgf_settings': 'SGF設定',
            'auto_save_sgf': 'SGFを自動保存',
            'sgf_path': 'SGF保存先',
            'sgf_file': 'SGFファイル',
            'browse': '参照',
            'engine_settings': 'エンジン設定',
            'use_gpu': 'GPUを使用',
            'threads': 'スレッド数',
            'debug_mode': 'デバッグモード',

            # 通用设置
            'general': '一般',
            'language': '言語',
            'theme': 'テーマ',
            'auto_save': '自動保存',
            'confirm_exit': '終了確認',

            # 按钮
            'ok': 'OK',
            'cancel': 'キャンセル',
            'apply': '適用',
            'start': '開始',
            'close': '閉じる',
            'save': '保存',
            'load': '読み込み',
            'import': 'インポート',
            'export': 'エクスポート',
            'restore_defaults': '既定値に戻す',
            'customize': 'カスタマイズ',
            'choose': '選択',
            'done': '完了',
            'continue': '続行',

            # 对话框
            'confirm': '確認',
            'info': '情報',
            'warning': '警告',
            'error': 'エラー',
            'confirm_resign': '投了しますか？',
            'confirm_exit_message': '対局中です。終了しますか？',
            'settings_applied': '設定を適用しました',
            'restore_defaults_confirm': '既定値に戻しますか？',
            'delete_game_confirm': 'この対局を削除しますか？',
            'overwrite_current': '現在の対局を上書き',
            'confirm_clear_board': '盤面をクリアしますか？',
            'save_current_game': '現在の対局を保存しますか？',
            'end_game_confirm': '対局を終了して自動採点します。続行しますか？',
            'enter_save_name': '保存名を入力してください',

            # 文件操作
            'filename': 'ファイル名',
            'date': '日付',
            'format': '形式',
            'game_files': '対局ファイル',
            'sgf_files': 'SGFファイル',
            'all_files': 'すべてのファイル',
            'select_sgf_file': 'SGFファイルを選択',
            'select_sgf_folder': 'SGFフォルダーを選択',
            'import_options': 'インポート設定',
            'export_options': 'エクスポート設定',
            'import_comments': 'コメントを取り込む',
            'import_variations': '変化を取り込む',
            'include_comments': 'コメントを含める',
            'include_variations': '変化を含める',
            'include_analysis': '解析を含める',

            # 状态消息
            'ready': '準備完了',
            'game_started': '対局開始',
            'new_game_started': '新しい対局を開始しました',
            'game_ended': '対局終了',
            'game_saved': '対局を保存しました',
            'game_loaded': '対局を読み込みました',
            'sgf_saved': 'SGFを保存しました',
            'sgf_loaded': 'SGFを読み込みました',
            'sgf_copied': 'SGFをクリップボードにコピーしました',
            'sgf_pasted': 'クリップボードからSGFを読み込みました',
            'invalid_sgf': '無効なSGFデータ',
            'no_saved_games': '保存された対局がありません',
            'move_undone': '手を戻しました',
            'move_redone': '手をやり直しました',
            'analyzing': '解析中',
            'analysis_complete': '解析完了',
            'calculating_hint': '最善手を計算中...',
            'pass_recommended': 'パスがおすすめです',
            'illegal_move': '不正な手',
            'ko_rule': 'コウ違反',
            'suicide_rule': '自殺手',
            'invalid_move': '不正な手',
            'ko_violation': 'コウ違反',
            'suicide_move': '自殺手',
            'need_two_passes': '採点に入るには連続2回パスが必要です',
            'accept_result': 'この結果を採用しますか？',
            'save_failed': '保存に失敗しました',
            'score_failed': '採点に失敗しました',
            'load_failed': '読み込みに失敗しました',

            # 游戏结果
            'game_over': '対局終了',
            'game_result': '対局結果',
            'black_wins': '黒勝ち',
            'white_wins': '白勝ち',
            'draw': '引き分け',
            'jigo': '引き分け',
            'wins': '勝ち',
            'points': '目',
            'wins_by': '勝ち',
            'wins_by_time': '時間切れ勝ち',
            'even': '互角',
            'even_game': '互角',
            'leading': '優勢',

            # 关于对话框
            'about_description': 'AI対戦と解析ツールを備えた囲碁（Go/Weiqi/Baduk）アプリです。',
            'features': '機能',
            'feature_1': '盤サイズ（9x9、13x13、19x19）に対応',
            'feature_2': '複数のAI難易度',
            'feature_3': '対局解析と検討',
            'feature_4': 'SGFのインポート/エクスポート',
            'feature_5': '複数ルールに対応',
            'developers': '開発者',
            'license': 'ライセンス',
            'website': 'ウェブサイト',
            'contact': '連絡先',

            # 主题
            'theme_name': 'テーマ名',
            'colors': '色',
            'board_background': '盤面背景',
            'grid_color': '格子線の色',
            'black_stone': '黒石',
            'white_stone': '白石',
            'last_move_marker': '最終手マーカー',
            'ui_background': 'UI背景',
            'text_color': '文字色',
            'customize_theme': 'テーマをカスタマイズ',

            # 统计
            'total_games': '総対局数',
            'total_players': '総プレイヤー数',
            'black_wins_count': '黒勝ち数',
            'white_wins_count': '白勝ち数',
            'draws': '引き分け数',
            'average_moves': '平均手数',
            'average_game_length': '平均対局時間',
            'vs_ai_games': 'AI対局数',
            'vs_human_games': '対人対局数',
            'most_active_player': '最も活躍したプレイヤー',

            # 其他
            'feature_coming_soon': 'この機能は近日公開です！',
            'rules_description': '囲碁は二人で対局する戦略的なボードゲームです。',
            'tutorial_content': '囲碁マスターへようこそ！',
            'passed': 'パス',
            'move_number': '第{}手',
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

        # 从内容数据库加载翻译（作为最高优先级）
        self._load_content_db_translations()
    
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

    def _load_content_db_translations(self):
        """从内容数据库加载翻译"""
        try:
            from utils.content_db import get_content_db

            db_translations = get_content_db().list_translations()
        except Exception:
            return

        if not isinstance(db_translations, dict):
            return
        for lang_code, mapping in db_translations.items():
            if not isinstance(mapping, dict):
                continue
            if lang_code in self.translations:
                self.translations[lang_code].update(mapping)
            else:
                self.translations[lang_code] = mapping
    
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
