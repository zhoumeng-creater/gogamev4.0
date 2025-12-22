"""
定式库模块
实现完整的定式序列、查询、学习等功能
"""

import json
import os
import hashlib
from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from pathlib import Path

# 导入核心模块
from core import Board


class JosekiType(Enum):
    """定式类型"""
    CORNER = 'corner'  # 角部定式
    SIDE = 'side'  # 边定式
    INVASION = 'invasion'  # 打入定式
    REDUCTION = 'reduction'  # 消减定式
    SPECIAL = 'special'  # 特殊定式
    OPENING = 'opening'  # 布局定式
    FIGHTING = 'fighting'  # 战斗定式


class JosekiResult(Enum):
    """定式结果评价"""
    EVEN = 'even'  # 两分
    SLIGHTLY_BETTER_BLACK = 'slightly_better_black'  # 黑略好
    SLIGHTLY_BETTER_WHITE = 'slightly_better_white'  # 白略好
    BETTER_BLACK = 'better_black'  # 黑好
    BETTER_WHITE = 'better_white'  # 白好
    COMPLICATED = 'complicated'  # 复杂
    DEPENDS = 'depends'  # 视情况而定


@dataclass
class JosekiMove:
    """定式中的一手棋"""
    x: int
    y: int
    color: str
    order: int  # 手数顺序
    is_main_line: bool = True  # 是否主线
    comment: str = ""
    comment_key: str = ""
    next_moves: List['JosekiMove'] = field(default_factory=list)
    
    def to_coords(self) -> Tuple[int, int]:
        """转换为坐标"""
        return (self.x, self.y)
    
    def matches(self, x: int, y: int) -> bool:
        """检查是否匹配"""
        return self.x == x and self.y == y


@dataclass
class JosekiSequence:
    """定式序列"""
    name: str
    type: JosekiType
    first_move: JosekiMove
    result: JosekiResult
    key: str = ""
    popularity: int = 0  # 流行度(0-100)
    difficulty: int = 1  # 难度(1-5)
    era: str = ""  # 流行年代
    comment: str = ""
    tags: List[str] = field(default_factory=list)

    def get_main_line(self) -> List[JosekiMove]:
        """获取主线变化"""
        moves = []
        current = self.first_move
        
        while current:
            moves.append(current)
            # 找主线的下一手
            next_move = None
            for move in current.next_moves:
                if move.is_main_line:
                    next_move = move
                    break
            current = next_move
        
        return moves
    
    def get_all_moves(self) -> List[JosekiMove]:
        """获取所有着法（包括分支）"""
        all_moves = []
        visited = set()
        
        def traverse(move: JosekiMove):
            if id(move) in visited:
                return
            visited.add(id(move))
            all_moves.append(move)
            for next_move in move.next_moves:
                traverse(next_move)
        
        traverse(self.first_move)
        return all_moves
    
    def find_position(self, moves: List[Tuple[int, int, str]]) -> Optional[JosekiMove]:
        """查找匹配的位置"""
        if not moves:
            return self.first_move
        
        current = self.first_move
        for x, y, color in moves:
            found = False
            for next_move in current.next_moves:
                if next_move.matches(x, y) and next_move.color == color:
                    current = next_move
                    found = True
                    break
            
            if not found:
                return None
        
        return current


JOSEKI_KEY_BY_NAME = {
    "三三定式-基本型": "san_san_basic",
    "星位定式-小飞挂": "star_point_small_approach_joseki",
    "小目定式-高挂": "komoku_high_approach_joseki",
    "高目定式-基本型": "takamoku_basic",
    "3-3点入侵": "three_three_invasion",
    "星位小飞挂": "star_point_small_approach",
    "小目一间高挂": "komoku_one_space_high_approach",
    "中国流布局": "chinese_fuseki",
    "三连星布局": "three_star_fuseki",
    "小林流布局": "kobayashi_fuseki",
    "雪崩定式": "avalanche_joseki",
    "大斜定式": "taisha_joseki",
    "双飞燕定式": "double_flying_goose_joseki",
    "镇神头": "zhen_shen_tou",
}


class JosekiDatabase:
    """定式数据库"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化定式数据库
        
        Args:
            db_path: 数据库文件路径，None则使用内存数据库
        """
        self.db_path = db_path or ":memory:"
        self.connection = None
        self.joseki_dict: Dict[str, JosekiSequence] = {}
        
        self._init_database()
        self._load_basic_joseki()
        self._load_joseki_from_json()
    
    def _init_database(self):
        """初始化数据库"""
        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()
        
        # 创建表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS joseki (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                data TEXT NOT NULL,
                popularity INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS joseki_stats (
                joseki_id INTEGER,
                times_played INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.5,
                last_played TIMESTAMP,
                FOREIGN KEY (joseki_id) REFERENCES joseki(id)
            )
        """)
        
        self.connection.commit()
    
    def _load_basic_joseki(self):
        """加载基础定式"""
        # 三三定式
        san_san = self._create_san_san_joseki()
        self.add_joseki(san_san)
        
        # 星位定式
        star_point = self._create_star_point_joseki()
        self.add_joseki(star_point)
        
        # 小目定式
        komoku = self._create_komoku_joseki()
        self.add_joseki(komoku)
        
        # 高目定式
        takamoku = self._create_takamoku_joseki()
        self.add_joseki(takamoku)

    def _load_joseki_from_json(self):
        """从JSON文件加载定式数据"""
        base_dir = Path(__file__).resolve().parents[1]
        json_path = base_dir / 'assets' / 'joseki' / 'joseki_db.json'

        if not json_path.exists():
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return

        sequences = data.get('joseki_sequences', [])
        category_labels = data.get('categories', {})
        difficulty_labels = data.get('difficulty_levels', {})

        difficulty_map = {
            'basic': 1,
            'intermediate': 3,
            'advanced': 4
        }
        popularity_map = {
            'basic': 85,
            'intermediate': 65,
            'advanced': 45
        }
        type_map = {
            'corner': JosekiType.CORNER,
            'side': JosekiType.SIDE,
            'opening': JosekiType.OPENING,
            'fighting': JosekiType.FIGHTING,
            'invasion': JosekiType.INVASION,
            'reduction': JosekiType.REDUCTION
        }
        result_map = {
            'equal': JosekiResult.EVEN,
            'favorable_black': JosekiResult.BETTER_BLACK,
            'favorable_white': JosekiResult.BETTER_WHITE,
            'complex': JosekiResult.COMPLICATED,
            'fighting': JosekiResult.COMPLICATED
        }

        for item in sequences:
            name = item.get('name', '').strip()
            moves = item.get('moves', []) or []
            if not name or not moves:
                continue

            first_move = self._build_main_line(moves)
            if not first_move:
                continue

            category_key = str(item.get('category', 'special')).lower()
            difficulty_key = str(item.get('difficulty', 'basic')).lower()
            result_key = str(item.get('result', 'equal')).lower()
            joseki_key = self._get_joseki_key(name)

            tags = [
                category_labels.get(category_key, category_key),
                difficulty_labels.get(difficulty_key, difficulty_key)
            ]
            tags = [tag for tag in tags if tag]

            joseki = JosekiSequence(
                name=name,
                type=type_map.get(category_key, JosekiType.SPECIAL),
                first_move=first_move,
                result=result_map.get(result_key, JosekiResult.DEPENDS),
                key=joseki_key,
                popularity=popularity_map.get(difficulty_key, 50),
                difficulty=difficulty_map.get(difficulty_key, 2),
                comment=item.get('description', '') or "",
                tags=tags
            )
            self.add_joseki(joseki)

    def _get_joseki_key(self, name: str) -> str:
        key = JOSEKI_KEY_BY_NAME.get(name)
        if key:
            return key
        digest = hashlib.md5(name.encode('utf-8')).hexdigest()[:8]
        return f"joseki_{digest}"

    def _build_main_line(self, moves: List[Dict[str, Any]]) -> Optional[JosekiMove]:
        """根据顺序着法构建主线"""
        first_move = None
        prev_move = None
        order = 1

        for move in moves:
            try:
                x = int(move.get('x'))
                y = int(move.get('y'))
            except Exception:
                continue
            color = str(move.get('color', '')).strip() or 'black'
            if color not in ('black', 'white'):
                continue

            current = JosekiMove(x, y, color, order)
            if prev_move:
                prev_move.next_moves.append(current)
            else:
                first_move = current
            prev_move = current
            order += 1

        return first_move
    
    def _create_san_san_joseki(self) -> JosekiSequence:
        """创建三三定式"""
        # 黑占三三
        first = JosekiMove(2, 2, 'black', 1)
        
        # 白小飞挂
        w2 = JosekiMove(4, 2, 'white', 2)
        first.next_moves.append(w2)
        
        # 黑扳
        b3 = JosekiMove(4, 3, 'black', 3)
        w2.next_moves.append(b3)
        
        # 白长
        w4 = JosekiMove(5, 2, 'white', 4)
        b3.next_moves.append(w4)
        
        # 黑虎
        b5 = JosekiMove(3, 3, 'black', 5)
        w4.next_moves.append(b5)
        
        return JosekiSequence(
            name="三三定式-基本型",
            type=JosekiType.CORNER,
            first_move=first,
            result=JosekiResult.EVEN,
            key="san_san_basic",
            popularity=90,
            difficulty=2,
            comment="最基本的三三定式，黑角实地，白获外势",
            tags=['三三', '实地', '基本定式']
        )
    
    def _create_star_point_joseki(self) -> JosekiSequence:
        """创建星位定式"""
        # 黑占星位
        first = JosekiMove(3, 3, 'black', 1)
        
        # 白小飞挂
        w2 = JosekiMove(5, 2, 'white', 2)
        first.next_moves.append(w2)
        
        # 黑一间夹
        b3_a = JosekiMove(
            2,
            4,
            'black',
            3,
            comment="一间夹，积极作战",
            comment_key="joseki_move_comment_star_point_small_approach_joseki_one_space_pincer",
        )
        w2.next_moves.append(b3_a)
        
        # 黑二间夹
        b3_b = JosekiMove(
            2,
            5,
            'black',
            3,
            is_main_line=False,
            comment="二间夹，重视外势",
            comment_key="joseki_move_comment_star_point_small_approach_joseki_two_space_pincer",
        )
        w2.next_moves.append(b3_b)
        
        # 黑小飞应
        b3_c = JosekiMove(
            2,
            5,
            'black',
            3,
            comment="小飞应，简明",
            comment_key="joseki_move_comment_star_point_small_approach_joseki_small_knight_reply",
        )
        w2.next_moves.append(b3_c)
        
        # 继续主线（一间夹后）
        # 白三三
        w4 = JosekiMove(2, 2, 'white', 4)
        b3_a.next_moves.append(w4)
        
        return JosekiSequence(
            name="星位定式-小飞挂",
            type=JosekiType.CORNER,
            first_move=first,
            result=JosekiResult.EVEN,
            key="star_point_small_approach_joseki",
            popularity=85,
            difficulty=3,
            comment="星位小飞挂是最常见的定式之一",
            tags=['星位', '小飞挂', '夹攻']
        )
    
    def _create_komoku_joseki(self) -> JosekiSequence:
        """创建小目定式"""
        # 黑占小目
        first = JosekiMove(3, 4, 'black', 1)
        
        # 白高挂
        w2 = JosekiMove(5, 2, 'white', 2)
        first.next_moves.append(w2)
        
        # 黑尖顶
        b3 = JosekiMove(4, 2, 'black', 3)
        w2.next_moves.append(b3)
        
        return JosekiSequence(
            name="小目定式-高挂",
            type=JosekiType.CORNER,
            first_move=first,
            result=JosekiResult.EVEN,
            key="komoku_high_approach_joseki",
            popularity=75,
            difficulty=3,
            comment="小目高挂定式，变化丰富",
            tags=['小目', '高挂']
        )
    
    def _create_takamoku_joseki(self) -> JosekiSequence:
        """创建高目定式"""
        # 黑占高目
        first = JosekiMove(3, 5, 'black', 1)
        
        # 白挂角
        w2 = JosekiMove(5, 3, 'white', 2)
        first.next_moves.append(w2)
        
        return JosekiSequence(
            name="高目定式-基本型",
            type=JosekiType.CORNER,
            first_move=first,
            result=JosekiResult.EVEN,
            key="takamoku_basic",
            popularity=60,
            difficulty=4,
            comment="高目定式强调外势",
            tags=['高目', '外势']
        )
    
    def add_joseki(self, joseki: JosekiSequence):
        """添加定式"""
        self.joseki_dict[joseki.name] = joseki
        
        # 保存到数据库
        cursor = self.connection.cursor()
        
        # 创建一个可序列化的字典
        def make_serializable(obj):
            """递归转换对象为可序列化格式"""
            if isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, (JosekiMove, JosekiSequence)):
                # 对于 dataclass，先转换为字典再递归处理
                return make_serializable(asdict(obj))
            else:
                return obj
        
        # 序列化定式数据
        serializable_data = make_serializable(joseki)
        json_data = json.dumps(serializable_data)
        
        cursor.execute("""
            INSERT OR REPLACE INTO joseki (name, type, data, popularity)
            VALUES (?, ?, ?, ?)
        """, (joseki.name, joseki.type.value, json_data, joseki.popularity))
        
        self.connection.commit()
    
    def get_joseki(self, name: str) -> Optional[JosekiSequence]:
        """获取定式"""
        return self.joseki_dict.get(name)
    
    def search_joseki(self, keyword: Optional[str] = None, **criteria) -> List[JosekiSequence]:
        """
        搜索定式
        
        Args:
            keyword: 关键字（名称/标签/评注）
            type: 定式类型
            min_popularity: 最低流行度
            max_difficulty: 最高难度
            tags: 标签列表
        
        Returns:
            符合条件的定式列表
        """
        results = []
        
        for joseki in self.joseki_dict.values():
            if keyword and not self._match_keyword(joseki, keyword):
                continue
            # 检查类型
            if 'type' in criteria and joseki.type != criteria['type']:
                continue
            
            # 检查流行度
            if 'min_popularity' in criteria and joseki.popularity < criteria['min_popularity']:
                continue
            
            # 检查难度
            if 'max_difficulty' in criteria and joseki.difficulty > criteria['max_difficulty']:
                continue
            
            # 检查标签
            if 'tags' in criteria:
                required_tags = set(criteria['tags'])
                if not required_tags.issubset(set(joseki.tags)):
                    continue
            
            results.append(joseki)
        
        # 按流行度排序
        results.sort(key=lambda j: j.popularity, reverse=True)
        
        return results

    def _match_keyword(self, joseki: JosekiSequence, keyword: str) -> bool:
        value = keyword.strip().lower()
        if not value:
            return True

        name = (joseki.name or '').lower()
        comment = (joseki.comment or '').lower()
        tags = [str(tag).lower() for tag in joseki.tags]
        return value in name or value in comment or any(value in tag for tag in tags)
    
    def update_statistics(self, joseki_name: str, success: bool):
        """更新定式统计"""
        cursor = self.connection.cursor()
        
        # 获取定式ID
        cursor.execute("SELECT id FROM joseki WHERE name = ?", (joseki_name,))
        row = cursor.fetchone()
        
        if row:
            joseki_id = row[0]
            
            # 更新统计
            cursor.execute("""
                INSERT INTO joseki_stats (joseki_id, times_played, success_rate, last_played)
                VALUES (?, 1, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(joseki_id) DO UPDATE SET
                    times_played = times_played + 1,
                    success_rate = (success_rate * times_played + ?) / (times_played + 1),
                    last_played = CURRENT_TIMESTAMP
            """, (joseki_id, 1.0 if success else 0.0, 1.0 if success else 0.0))
            
            self.connection.commit()


class JosekiMatcher:
    """定式匹配器"""
    
    def __init__(self, database: JosekiDatabase):
        self.database = database
        self.board_size = 19
    
    def find_matching_joseki(self, board: Board, moves: List[Tuple[int, int, str]]) -> List[JosekiSequence]:
        """
        查找匹配的定式
        
        Args:
            board: 当前棋盘
            moves: 已下的棋步序列
        
        Returns:
            匹配的定式列表
        """
        matches = []
        
        # 检查四个角
        corners = [
            (0, 0, 1, 1),  # 左上
            (0, 18, 1, -1),  # 左下  
            (18, 0, -1, 1),  # 右上
            (18, 18, -1, -1)  # 右下
        ]
        
        for corner_x, corner_y, dx, dy in corners:
            # 转换坐标到标准形式（左上角）
            transformed_moves = self._transform_moves(moves, corner_x, corner_y, dx, dy)
            
            # 在数据库中查找匹配
            for joseki in self.database.joseki_dict.values():
                if self._matches_joseki(transformed_moves, joseki):
                    matches.append(joseki)
        
        return matches
    
    def get_next_moves(self, joseki: JosekiSequence, moves: List[Tuple[int, int, str]]) -> List[JosekiMove]:
        """
        获取定式的下一手
        
        Args:
            joseki: 定式序列
            moves: 已下的棋
        
        Returns:
            可能的下一手列表
        """
        current_position = joseki.find_position(moves)
        
        if current_position:
            return current_position.next_moves
        
        return []
    
    def _transform_moves(self, moves: List[Tuple[int, int, str]], 
                        corner_x: int, corner_y: int, dx: int, dy: int) -> List[Tuple[int, int, str]]:
        """转换坐标系"""
        transformed = []
        
        for x, y, color in moves:
            # 相对于角的坐标
            rel_x = abs(x - corner_x)
            rel_y = abs(y - corner_y)
            
            # 只考虑角附近的棋子（7x7范围）
            if rel_x < 7 and rel_y < 7:
                transformed.append((rel_x, rel_y, color))
        
        return transformed
    
    def _matches_joseki(self, moves: List[Tuple[int, int, str]], joseki: JosekiSequence) -> bool:
        """检查是否匹配定式"""
        if not moves:
            return False
        
        main_line = joseki.get_main_line()
        
        # 检查前几手是否匹配
        for i, (x, y, color) in enumerate(moves):
            if i >= len(main_line):
                break
            
            joseki_move = main_line[i]
            if not joseki_move.matches(x, y) or joseki_move.color != color:
                return False
        
        return True


class JosekiExplorer(tk.Frame):
    """定式浏览器UI组件"""
    
    def __init__(self, parent, database: JosekiDatabase, **kwargs):
        super().__init__(parent, **kwargs)
        self.database = database
        self.current_joseki: Optional[JosekiSequence] = None
        self.current_move_index = 0
        
        self._create_widgets()
        self._load_joseki_list()
    
    def _create_widgets(self):
        """创建控件"""
        # 左侧：定式列表
        left_frame = ttk.Frame(self)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        # 搜索框
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(search_frame, text="搜索:").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.search_entry.bind('<Return>', lambda e: self._on_search())
        
        ttk.Button(search_frame, text="搜索", command=self._on_search).pack(side='left')
        
        # 定式列表
        list_frame = ttk.LabelFrame(left_frame, text="定式列表")
        list_frame.pack(fill='both', expand=True)
        
        # 列表框和滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.joseki_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.joseki_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.joseki_listbox.yview)
        
        self.joseki_listbox.bind('<<ListboxSelect>>', self._on_joseki_select)
        
        # 右侧：定式详情
        right_frame = ttk.Frame(self)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # 定式信息
        info_frame = ttk.LabelFrame(right_frame, text="定式信息")
        info_frame.pack(fill='x', pady=(0, 5))
        
        self.info_text = tk.Text(info_frame, height=5, wrap='word')
        self.info_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 控制按钮
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(fill='x', pady=5)
        
        ttk.Button(control_frame, text="<<", command=self._first_move, width=3).pack(side='left', padx=2)
        ttk.Button(control_frame, text="<", command=self._prev_move, width=3).pack(side='left', padx=2)
        ttk.Button(control_frame, text=">", command=self._next_move, width=3).pack(side='left', padx=2)
        ttk.Button(control_frame, text=">>", command=self._last_move, width=3).pack(side='left', padx=2)
        
        self.move_label = ttk.Label(control_frame, text="0 / 0")
        self.move_label.pack(side='left', padx=10)
        
        # 变化列表
        variation_frame = ttk.LabelFrame(right_frame, text="变化")
        variation_frame.pack(fill='both', expand=True)
        
        self.variation_listbox = tk.Listbox(variation_frame, height=6)
        self.variation_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 评注
        comment_frame = ttk.LabelFrame(right_frame, text="评注")
        comment_frame.pack(fill='both', expand=True)
        
        self.comment_text = tk.Text(comment_frame, height=4, wrap='word')
        self.comment_text.pack(fill='both', expand=True, padx=5, pady=5)
    
    def _load_joseki_list(self):
        """加载定式列表"""
        self.joseki_listbox.delete(0, 'end')
        
        for joseki in self.database.joseki_dict.values():
            display_text = f"{joseki.name} ({joseki.popularity}%)"
            self.joseki_listbox.insert('end', display_text)
    
    def _on_search(self):
        """搜索定式"""
        keyword = self.search_var.get().strip()
        
        if not keyword:
            self._load_joseki_list()
            return
        
        # 搜索匹配的定式
        self.joseki_listbox.delete(0, 'end')
        
        for joseki in self.database.joseki_dict.values():
            if keyword.lower() in joseki.name.lower() or \
               any(keyword.lower() in tag.lower() for tag in joseki.tags):
                display_text = f"{joseki.name} ({joseki.popularity}%)"
                self.joseki_listbox.insert('end', display_text)
    
    def _on_joseki_select(self, event):
        """选择定式"""
        selection = self.joseki_listbox.curselection()
        if not selection:
            return
        
        # 获取选中的定式名称
        display_text = self.joseki_listbox.get(selection[0])
        joseki_name = display_text.split(' (')[0]
        
        # 加载定式
        self.current_joseki = self.database.get_joseki(joseki_name)
        self.current_move_index = 0
        
        if self.current_joseki:
            self._update_display()
    
    def _update_display(self):
        """更新显示"""
        if not self.current_joseki:
            return
        
        # 更新信息
        self.info_text.delete('1.0', 'end')
        info = f"名称: {self.current_joseki.name}\n"
        info += f"类型: {self.current_joseki.type.value}\n"
        info += f"难度: {'★' * self.current_joseki.difficulty}\n"
        info += f"流行度: {self.current_joseki.popularity}%\n"
        info += f"结果: {self.current_joseki.result.value}"
        self.info_text.insert('1.0', info)
        
        # 更新手数
        main_line = self.current_joseki.get_main_line()
        self.move_label.config(text=f"{self.current_move_index} / {len(main_line)}")
        
        # 更新变化（如果有）
        self.variation_listbox.delete(0, 'end')
        if self.current_move_index < len(main_line):
            current_move = main_line[self.current_move_index]
            for i, next_move in enumerate(current_move.next_moves):
                if not next_move.is_main_line:
                    self.variation_listbox.insert('end', f"变化{i+1}")
        
        # 更新评注
        self.comment_text.delete('1.0', 'end')
        if self.current_move_index < len(main_line):
            current_move = main_line[self.current_move_index]
            if current_move.comment:
                self.comment_text.insert('1.0', current_move.comment)
        
        # 触发棋盘更新（如果有回调）
        self.on_position_changed()
    
    def _first_move(self):
        """第一手"""
        self.current_move_index = 0
        self._update_display()
    
    def _last_move(self):
        """最后一手"""
        if self.current_joseki:
            main_line = self.current_joseki.get_main_line()
            self.current_move_index = len(main_line) - 1
            self._update_display()
    
    def _next_move(self):
        """下一手"""
        if self.current_joseki:
            main_line = self.current_joseki.get_main_line()
            if self.current_move_index < len(main_line) - 1:
                self.current_move_index += 1
                self._update_display()
    
    def _prev_move(self):
        """上一手"""
        if self.current_move_index > 0:
            self.current_move_index -= 1
            self._update_display()
    
    def get_current_moves(self) -> List[Tuple[int, int, str]]:
        """获取当前的棋步序列"""
        if not self.current_joseki:
            return []
        
        moves = []
        main_line = self.current_joseki.get_main_line()
        
        for i in range(self.current_move_index + 1):
            if i < len(main_line):
                move = main_line[i]
                moves.append((move.x, move.y, move.color))
        
        return moves
    
    def on_position_changed(self):
        """位置改变回调（供外部调用）"""
        pass


class JosekiTrainer:
    """定式训练器"""
    
    def __init__(self, database: JosekiDatabase):
        self.database = database
        self.current_joseki: Optional[JosekiSequence] = None
        self.current_position = 0
        self.score = 0
        self.total_attempts = 0
    
    def start_training(self, difficulty: Optional[int] = None, 
                      joseki_type: Optional[JosekiType] = None):
        """
        开始训练
        
        Args:
            difficulty: 难度限制
            joseki_type: 定式类型限制
        """
        # 搜索符合条件的定式
        criteria = {}
        if difficulty:
            criteria['max_difficulty'] = difficulty
        if joseki_type:
            criteria['type'] = joseki_type
        
        joseki_list = self.database.search_joseki(**criteria)
        
        if joseki_list:
            import random
            self.current_joseki = random.choice(joseki_list)
            self.current_position = 0
            return True
        
        return False
    
    def check_move(self, x: int, y: int, color: str) -> Tuple[bool, str]:
        """
        检查着法是否正确
        
        Args:
            x, y: 落子位置
            color: 颜色
        
        Returns:
            (是否正确, 反馈信息)
        """
        if not self.current_joseki:
            return False, "没有正在学习的定式"
        
        main_line = self.current_joseki.get_main_line()
        
        if self.current_position >= len(main_line):
            return False, "定式已完成"
        
        expected_move = main_line[self.current_position]
        
        self.total_attempts += 1
        
        if expected_move.matches(x, y) and expected_move.color == color:
            self.current_position += 1
            self.score += 1
            
            if self.current_position >= len(main_line):
                return True, "恭喜！定式完成"
            else:
                return True, "正确！请继续下一手"
        else:
            # 检查是否是变化
            for variation in expected_move.next_moves:
                if variation.matches(x, y) and variation.color == color:
                    return True, f"这是一个变化手，主线是({expected_move.x}, {expected_move.y})"
            
            return False, f"错误。正确的位置是({expected_move.x}, {expected_move.y})"
    
    def get_hint(self) -> Optional[Tuple[int, int]]:
        """获取提示"""
        if not self.current_joseki:
            return None
        
        main_line = self.current_joseki.get_main_line()
        
        if self.current_position < len(main_line):
            move = main_line[self.current_position]
            return (move.x, move.y)
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取训练统计"""
        accuracy = self.score / self.total_attempts if self.total_attempts > 0 else 0
        
        return {
            'score': self.score,
            'total_attempts': self.total_attempts,
            'accuracy': accuracy,
            'current_joseki': self.current_joseki.name if self.current_joseki else None,
            'progress': f"{self.current_position} / {len(self.current_joseki.get_main_line())}" if self.current_joseki else "0 / 0"
        }
