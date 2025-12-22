"""
教学系统模块
提供规则教程、战术训练、互动课程等功能
"""

import json
import time
from typing import List, Dict, Optional, Tuple, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from pathlib import Path

# 导入核心模块
from core import Board, Rules, MoveResult


class LessonType(Enum):
    """课程类型"""
    RULES = 'rules'  # 规则
    BASICS = 'basics'  # 基础
    TACTICS = 'tactics'  # 战术
    STRATEGY = 'strategy'  # 战略
    LIFE_DEATH = 'life_death'  # 死活
    TESUJI = 'tesuji'  # 手筋
    ENDGAME = 'endgame'  # 收官


class DifficultyLevel(Enum):
    """难度级别"""
    BEGINNER = 1  # 初学者
    ELEMENTARY = 2  # 初级
    INTERMEDIATE = 3  # 中级
    ADVANCED = 4  # 高级
    EXPERT = 5  # 专家


@dataclass
class Lesson:
    """课程"""
    id: str
    title: str
    type: LessonType
    difficulty: DifficultyLevel
    description: str
    content: List['LessonContent']
    prerequisites: List[str] = field(default_factory=list)  # 先修课程
    objectives: List[str] = field(default_factory=list)  # 学习目标
    estimated_time: int = 15  # 预计时间（分钟）
    
    def get_progress(self, completed_steps: Set[int]) -> float:
        """获取进度"""
        if not self.content:
            return 1.0
        return len(completed_steps) / len(self.content)


@dataclass
class LessonContent:
    """课程内容"""
    step: int
    type: str  # 'text', 'demo', 'puzzle', 'quiz'
    title: str
    content: Dict[str, Any]
    
    def is_interactive(self) -> bool:
        """是否为互动内容"""
        return self.type in ['puzzle', 'quiz']


@dataclass
class Puzzle:
    """棋题"""
    id: str
    title: str
    difficulty: int
    board_state: List[List[str]]  # 棋盘状态
    player_color: str
    objective: str  # 目标描述
    solution: List[Tuple[int, int]]  # 正解序列
    wrong_moves: Dict[Tuple[int, int], str]  # 错误着法及提示
    hint: str = ""
    explanation: str = ""
    
    def check_move(self, x: int, y: int) -> Tuple[bool, str]:
        """检查着法"""
        move = (x, y)
        
        # 检查是否为正解
        if self.solution and move == self.solution[0]:
            return True, "正确！"
        
        # 检查是否为已知错误
        if move in self.wrong_moves:
            return False, self.wrong_moves[move]
        
        return False, "这不是最佳着法，请再想想。"


class TeachingSystem:
    """教学系统"""
    
    def __init__(self, translator=None):
        # translator 目前仅作占位，便于未来本地化提示
        self.translator = translator
        self.lessons: Dict[str, Lesson] = {}
        self.puzzles: Dict[str, Puzzle] = {}
        self.user_progress: Dict[str, Any] = {
            'completed_lessons': [],
            'completed_puzzles': [],
            'current_lesson': None,
            'total_score': 0,
            'statistics': {}
        }
        
        self._load_lessons()
        self._load_puzzles()
    
    def _load_lessons(self):
        """加载课程"""
        # 规则课程
        self.lessons['rules_basic'] = self._create_rules_lesson()
        
        # 基础课程
        self.lessons['basics_capture'] = self._create_capture_lesson()
        self.lessons['basics_territory'] = self._create_territory_lesson()
        
        # 战术课程
        self.lessons['tactics_ladder'] = self._create_ladder_lesson()
        self.lessons['tactics_net'] = self._create_net_lesson()
    
    def _create_rules_lesson(self) -> Lesson:
        """创建规则课程"""
        content = [
            LessonContent(
                step=1,
                type='text',
                title='围棋简介',
                content={
                    'text': """围棋是一种两人对弈的策略棋盘游戏，起源于中国，已有4000多年历史。

围棋的基本规则非常简单：
1. 黑白双方轮流下子
2. 棋子下在交叉点上
3. 被围住的棋子会被吃掉
4. 占地多的一方获胜

但是，简单的规则蕴含着无穷的变化，这正是围棋的魅力所在。""",
                    'image': None
                }
            ),
            LessonContent(
                step=2,
                type='demo',
                title='如何落子',
                content={
                    'text': '棋子下在交叉点上，不是格子里。点击交叉点即可落子。',
                    'demo_moves': [(9, 9, 'black'), (9, 10, 'white')]
                }
            ),
            LessonContent(
                step=3,
                type='text',
                title='气的概念',
                content={
                    'text': """气是围棋中最重要的概念之一。

一个棋子的"气"是指与它直接相邻的空交叉点。
- 中央的棋子最多有4口气
- 边上的棋子最多有3口气
- 角上的棋子最多有2口气

当一个棋子或一块棋的气全部被对方占据时，就会被提取。"""
                }
            ),
            LessonContent(
                step=4,
                type='puzzle',
                title='练习：提子',
                content={
                    'puzzle_id': 'capture_basic_1'
                }
            )
        ]
        
        return Lesson(
            id='rules_basic',
            title='围棋基本规则',
            type=LessonType.RULES,
            difficulty=DifficultyLevel.BEGINNER,
            description='学习围棋的基本规则和概念',
            content=content,
            objectives=[
                '了解围棋的基本规则',
                '掌握气的概念',
                '学会基本的提子'
            ],
            estimated_time=20
        )
    
    def _create_capture_lesson(self) -> Lesson:
        """创建吃子课程"""
        content = [
            LessonContent(
                step=1,
                type='text',
                title='吃子的基本方法',
                content={
                    'text': """吃子是围棋的基本技术之一。常见的吃子方法包括：

1. **直接吃**：当对方棋子只剩一口气时，直接占据最后一口气
2. **征子**：利用连续叫吃，将对方棋子驱赶到边角吃掉
3. **门吃**：堵住对方棋子的逃路，使其无法逃脱
4. **双吃**：同时威胁两块棋，对方只能救一块"""
                }
            ),
            LessonContent(
                step=2,
                type='demo',
                title='征子演示',
                content={
                    'text': '征子是一种连续叫吃的技术，观察黑棋如何追击白子。',
                    'demo_moves': [
                        (9, 9, 'white'),
                        (10, 9, 'black'),
                        (9, 10, 'white'),
                        (10, 10, 'black'),
                        (9, 11, 'white'),
                        (10, 11, 'black')
                    ]
                }
            ),
            LessonContent(
                step=3,
                type='puzzle',
                title='练习：征子',
                content={
                    'puzzle_id': 'ladder_basic_1'
                }
            )
        ]
        
        return Lesson(
            id='basics_capture',
            title='基本吃子技术',
            type=LessonType.BASICS,
            difficulty=DifficultyLevel.BEGINNER,
            description='学习各种基本的吃子方法',
            content=content,
            prerequisites=['rules_basic'],
            objectives=[
                '掌握直接吃子',
                '学会征子技术',
                '理解门吃和双吃'
            ],
            estimated_time=30
        )
    
    def _create_territory_lesson(self) -> Lesson:
        """创建围地课程"""
        return Lesson(
            id='basics_territory',
            title='围地基础',
            type=LessonType.BASICS,
            difficulty=DifficultyLevel.ELEMENTARY,
            description='学习如何围地和计算地盘',
            content=[],
            prerequisites=['rules_basic'],
            objectives=['理解地盘概念', '学会基本围地'],
            estimated_time=25
        )
    
    def _create_ladder_lesson(self) -> Lesson:
        """创建征子课程"""
        return Lesson(
            id='tactics_ladder',
            title='征子战术',
            type=LessonType.TACTICS,
            difficulty=DifficultyLevel.ELEMENTARY,
            description='深入学习征子及其变化',
            content=[],
            prerequisites=['basics_capture'],
            objectives=['掌握征子判断', '学会征子相关战术'],
            estimated_time=40
        )
    
    def _create_net_lesson(self) -> Lesson:
        """创建网罩课程"""
        return Lesson(
            id='tactics_net',
            title='网罩战术',
            type=LessonType.TACTICS,
            difficulty=DifficultyLevel.INTERMEDIATE,
            description='学习网罩的技巧',
            content=[],
            prerequisites=['basics_capture'],
            objectives=['理解网罩原理', '掌握网罩技巧'],
            estimated_time=35
        )
    
    def _load_puzzles(self):
        """加载棋题"""
        # 基础提子题
        self.puzzles['capture_basic_1'] = Puzzle(
            id='capture_basic_1',
            title='提子练习1',
            difficulty=1,
            board_state=self._create_puzzle_board_1(),
            player_color='black',
            objective='吃掉白子',
            solution=[(10, 9)],
            wrong_moves={
                (8, 10): '这里不能直接吃掉白子',
                (10, 10): '这里也不对，想想白子的气在哪里'
            },
            hint='白子只有一口气了',
            explanation='白子只剩最后一口气，黑子落子即可提取白子。'
        )
        
        # 征子题
        self.puzzles['ladder_basic_1'] = Puzzle(
            id='ladder_basic_1',
            title='征子练习1',
            difficulty=2,
            board_state=self._create_ladder_board_1(),
            player_color='black',
            objective='用征子追击白子',
            solution=[(2, 2), (1, 3), (2, 3)],
            wrong_moves={
                (1, 3): '这是白棋的应对点',
                (2, 1): '方向不对'
            },
            hint='从正确的方向追击',
            explanation='征子需要沿着边线持续追击，迫使白子没有活路。'
        )
    
    def _create_puzzle_board_1(self) -> List[List[str]]:
        """创建棋题棋盘1"""
        board = [[''] * 19 for _ in range(19)]
        # 设置棋子
        board[9][9] = 'white'
        board[9][8] = 'black'
        board[8][9] = 'black'
        board[9][10] = 'black'
        return board
    
    def _create_ladder_board_1(self) -> List[List[str]]:
        """创建征子棋盘1"""
        board = [[''] * 19 for _ in range(19)]
        # 设置征子局面（靠近边线，便于形成征子）
        board[2][1] = 'white'
        board[2][0] = 'black'
        board[1][1] = 'black'
        return board
    
    def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """获取课程"""
        return self.lessons.get(lesson_id)
    
    def get_puzzle(self, puzzle_id: str) -> Optional[Puzzle]:
        """获取棋题"""
        return self.puzzles.get(puzzle_id)
    
    def start_lesson(self, lesson_id: str) -> bool:
        """开始课程"""
        lesson = self.get_lesson(lesson_id)
        if not lesson:
            return False
        
        # 检查先修课程
        for prereq in lesson.prerequisites:
            if prereq not in self.user_progress['completed_lessons']:
                return False
        
        self.user_progress['current_lesson'] = lesson_id
        return True
    
    def complete_lesson_step(self, lesson_id: str, step: int):
        """完成课程步骤"""
        if lesson_id not in self.user_progress:
            self.user_progress[lesson_id] = {'completed_steps': set()}
        
        self.user_progress[lesson_id]['completed_steps'].add(step)
        
        # 检查是否完成整个课程
        lesson = self.get_lesson(lesson_id)
        if lesson:
            progress = lesson.get_progress(self.user_progress[lesson_id]['completed_steps'])
            if progress >= 1.0:
                self.complete_lesson(lesson_id)
    
    def complete_lesson(self, lesson_id: str):
        """完成课程"""
        if lesson_id not in self.user_progress['completed_lessons']:
            self.user_progress['completed_lessons'].append(lesson_id)
            self.user_progress['total_score'] += 100
    
    def check_puzzle_solution(self, puzzle_id: str, x: int, y: int) -> Tuple[bool, str]:
        """检查棋题答案"""
        puzzle = self.get_puzzle(puzzle_id)
        if not puzzle:
            return False, "棋题不存在"
        
        return puzzle.check_move(x, y)
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """获取用户统计"""
        total_lessons = len(self.lessons)
        completed_lessons = len(self.user_progress['completed_lessons'])
        
        return {
            'total_score': self.user_progress['total_score'],
            'lessons_completed': completed_lessons,
            'lessons_total': total_lessons,
            'completion_rate': completed_lessons / total_lessons if total_lessons > 0 else 0,
            'puzzles_solved': len(self.user_progress['completed_puzzles'])
        }


class InteractiveLesson(tk.Frame):
    """互动课程UI组件"""
    
    def __init__(self, parent, teaching_system: TeachingSystem, **kwargs):
        super().__init__(parent, **kwargs)
        self.teaching_system = teaching_system
        self.current_lesson: Optional[Lesson] = None
        self.current_step = 0
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 标题
        self.title_label = ttk.Label(self, text="互动课程", font=('Arial', 14, 'bold'))
        self.title_label.pack(pady=10)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, length=400)
        self.progress_bar.pack(pady=5)
        
        # 内容区域
        content_frame = ttk.Frame(self)
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 文本内容
        self.content_text = tk.Text(content_frame, wrap='word', height=15)
        self.content_text.pack(fill='both', expand=True)
        
        # 控制按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        self.prev_button = ttk.Button(button_frame, text="上一步", command=self.prev_step)
        self.prev_button.pack(side='left', padx=5)
        
        self.next_button = ttk.Button(button_frame, text="下一步", command=self.next_step)
        self.next_button.pack(side='left', padx=5)
        
        self.check_button = ttk.Button(button_frame, text="检查答案", command=self.check_answer)
        self.check_button.pack(side='left', padx=5)
        self.check_button.pack_forget()  # 初始隐藏
    
    def load_lesson(self, lesson_id: str):
        """加载课程"""
        self.current_lesson = self.teaching_system.get_lesson(lesson_id)
        if not self.current_lesson:
            messagebox.showerror("错误", "课程不存在")
            return
        
        # 检查先修课程
        if not self.teaching_system.start_lesson(lesson_id):
            messagebox.showwarning("提示", "请先完成先修课程")
            return
        
        self.current_step = 0
        self._update_display()
    
    def _update_display(self):
        """更新显示"""
        if not self.current_lesson:
            return
        
        # 更新标题
        self.title_label.config(text=self.current_lesson.title)
        
        # 更新进度
        total_steps = len(self.current_lesson.content)
        if total_steps > 0:
            progress = (self.current_step + 1) / total_steps * 100
            self.progress_var.set(progress)
        
        # 更新内容
        if self.current_step < len(self.current_lesson.content):
            content = self.current_lesson.content[self.current_step]
            self._display_content(content)
        
        # 更新按钮状态
        self.prev_button.config(state='normal' if self.current_step > 0 else 'disabled')
        self.next_button.config(state='normal' if self.current_step < total_steps - 1 else 'disabled')
    
    def _display_content(self, content: LessonContent):
        """显示内容"""
        self.content_text.delete('1.0', 'end')
        
        # 显示标题
        self.content_text.insert('end', f"{content.title}\n\n", 'title')
        
        # 根据类型显示内容
        if content.type == 'text':
            self.content_text.insert('end', content.content.get('text', ''))
            self.check_button.pack_forget()
            
        elif content.type == 'demo':
            self.content_text.insert('end', content.content.get('text', ''))
            self.content_text.insert('end', "\n\n点击棋盘查看演示")
            self.check_button.pack_forget()
            
        elif content.type == 'puzzle':
            puzzle_id = content.content.get('puzzle_id')
            puzzle = self.teaching_system.get_puzzle(puzzle_id)
            if puzzle:
                self.content_text.insert('end', f"目标：{puzzle.objective}\n")
                if puzzle.hint:
                    self.content_text.insert('end', f"\n提示：{puzzle.hint}")
            self.check_button.pack(side='left', padx=5)
            
        elif content.type == 'quiz':
            self.content_text.insert('end', "请回答以下问题...")
            self.check_button.pack(side='left', padx=5)
        
        # 配置文本标签样式
        self.content_text.tag_config('title', font=('Arial', 12, 'bold'))
    
    def prev_step(self):
        """上一步"""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_display()
    
    def next_step(self):
        """下一步"""
        if self.current_lesson and self.current_step < len(self.current_lesson.content) - 1:
            # 标记当前步骤完成
            self.teaching_system.complete_lesson_step(self.current_lesson.id, self.current_step)
            
            self.current_step += 1
            self._update_display()
        elif self.current_lesson and self.current_step == len(self.current_lesson.content) - 1:
            # 课程完成
            self.teaching_system.complete_lesson(self.current_lesson.id)
            messagebox.showinfo("恭喜", "课程完成！")
    
    def check_answer(self):
        """检查答案（用于互动内容）"""
        # 这里需要与棋盘交互
        messagebox.showinfo("提示", "请在棋盘上落子")


class TacticalPuzzles(tk.Frame):
    """战术训练UI组件"""
    
    def __init__(self, parent, teaching_system: TeachingSystem, **kwargs):
        super().__init__(parent, **kwargs)
        self.teaching_system = teaching_system
        self.current_puzzle: Optional[Puzzle] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 标题
        title_label = ttk.Label(self, text="战术训练", font=('Arial', 14, 'bold'))
        title_label.pack(pady=10)
        
        # 难度选择
        difficulty_frame = ttk.Frame(self)
        difficulty_frame.pack(pady=5)
        
        ttk.Label(difficulty_frame, text="难度:").pack(side='left')
        
        self.difficulty_var = tk.IntVar(value=1)
        for i in range(1, 6):
            ttk.Radiobutton(difficulty_frame, text=f"★{'★' * (i-1)}", 
                          variable=self.difficulty_var, value=i).pack(side='left')
        
        # 题目信息
        info_frame = ttk.LabelFrame(self, text="题目")
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.puzzle_title = ttk.Label(info_frame, text="", font=('Arial', 12))
        self.puzzle_title.pack(anchor='w', padx=5, pady=2)
        
        self.objective_label = ttk.Label(info_frame, text="")
        self.objective_label.pack(anchor='w', padx=5, pady=2)
        
        self.hint_label = ttk.Label(info_frame, text="", foreground='blue')
        self.hint_label.pack(anchor='w', padx=5, pady=2)
        
        # 控制按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="新题目", command=self.new_puzzle).pack(side='left', padx=5)
        ttk.Button(button_frame, text="显示提示", command=self.show_hint).pack(side='left', padx=5)
        ttk.Button(button_frame, text="显示答案", command=self.show_solution).pack(side='left', padx=5)
        
        # 统计信息
        stats_frame = ttk.LabelFrame(self, text="统计")
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="已解决: 0 | 正确率: 0%")
        self.stats_label.pack(padx=5, pady=5)
    
    def new_puzzle(self):
        """加载新题目"""
        # 根据难度筛选题目
        difficulty = self.difficulty_var.get()
        
        # 找到符合难度的题目
        puzzles = [p for p in self.teaching_system.puzzles.values() 
                  if p.difficulty == difficulty]
        
        if puzzles:
            import random
            self.current_puzzle = random.choice(puzzles)
            self._update_display()
            self.on_puzzle_loaded(self.current_puzzle)
    
    def _update_display(self):
        """更新显示"""
        if not self.current_puzzle:
            return
        
        self.puzzle_title.config(text=self.current_puzzle.title)
        self.objective_label.config(text=f"目标: {self.current_puzzle.objective}")
        self.hint_label.config(text="")
    
    def show_hint(self):
        """显示提示"""
        if self.current_puzzle and self.current_puzzle.hint:
            self.hint_label.config(text=f"提示: {self.current_puzzle.hint}")
    
    def show_solution(self):
        """显示答案"""
        if self.current_puzzle:
            solution_text = "答案: " + " → ".join(
                f"({x},{y})" for x, y in self.current_puzzle.solution
            )
            messagebox.showinfo("答案", solution_text + "\n\n" + self.current_puzzle.explanation)
    
    def check_move(self, x: int, y: int) -> Tuple[bool, str]:
        """检查着法"""
        if not self.current_puzzle:
            return False, "请先选择题目"
        
        correct, feedback = self.current_puzzle.check_move(x, y)
        
        # 更新统计
        # TODO: 实现统计更新
        
        return correct, feedback
    
    def on_puzzle_loaded(self, puzzle: Puzzle):
        """题目加载回调（供外部调用）"""
        pass


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or ":memory:"
        self.connection = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id TEXT,
                lesson_id TEXT,
                step_completed INTEGER,
                completion_date TIMESTAMP,
                score INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, lesson_id, step_completed)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS puzzle_attempts (
                user_id TEXT,
                puzzle_id TEXT,
                attempt_date TIMESTAMP,
                success BOOLEAN,
                time_spent INTEGER,
                hints_used INTEGER DEFAULT 0
            )
        """)
        
        self.connection.commit()
    
    def record_lesson_progress(self, user_id: str, lesson_id: str, 
                              step: int, score: int = 0):
        """记录课程进度"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_progress 
            (user_id, lesson_id, step_completed, completion_date, score)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (user_id, lesson_id, step, score))
        self.connection.commit()
    
    def record_puzzle_attempt(self, user_id: str, puzzle_id: str,
                             success: bool, time_spent: int, hints_used: int = 0):
        """记录棋题尝试"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO puzzle_attempts
            (user_id, puzzle_id, attempt_date, success, time_spent, hints_used)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
        """, (user_id, puzzle_id, success, time_spent, hints_used))
        self.connection.commit()
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计"""
        cursor = self.connection.cursor()
        
        # 课程完成情况
        cursor.execute("""
            SELECT COUNT(DISTINCT lesson_id), SUM(score)
            FROM user_progress
            WHERE user_id = ?
        """, (user_id,))
        lessons_completed, total_score = cursor.fetchone()
        
        # 棋题统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total_attempts,
                SUM(success) as successes,
                AVG(time_spent) as avg_time,
                SUM(hints_used) as total_hints
            FROM puzzle_attempts
            WHERE user_id = ?
        """, (user_id,))
        
        puzzle_stats = cursor.fetchone()
        
        return {
            'lessons_completed': lessons_completed or 0,
            'total_score': total_score or 0,
            'puzzle_attempts': puzzle_stats[0] or 0,
            'puzzle_successes': puzzle_stats[1] or 0,
            'puzzle_success_rate': (puzzle_stats[1] / puzzle_stats[0] * 100) if puzzle_stats[0] else 0,
            'avg_puzzle_time': puzzle_stats[2] or 0,
            'hints_used': puzzle_stats[3] or 0
        }
    
    def get_lesson_progress(self, user_id: str, lesson_id: str) -> List[int]:
        """获取课程进度"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT step_completed
            FROM user_progress
            WHERE user_id = ? AND lesson_id = ?
            ORDER BY step_completed
        """, (user_id, lesson_id))
        
        return [row[0] for row in cursor.fetchall()]


class RulesTutorial:
    """规则教程"""
    
    def __init__(self):
        self.rules_content = {
            'chinese': self._get_chinese_rules(),
            'japanese': self._get_japanese_rules(),
            'aga': self._get_aga_rules()
        }
    
    def _get_chinese_rules(self) -> str:
        """中国规则说明"""
        return """中国规则（数子法）

基本原则：
1. 黑方先行，轮流落子
2. 提取对方无气之子
3. 禁止全局同形再现
4. 虚手表示放弃一手

计分方法：
- 数子法：计算己方活子数 + 围住的空点
- 黑方贴还3.75子（相当于7.5目）
- 子空皆地，总和多者胜

特点：
- 简单直观
- 不需要保留死子
- 收官阶段可以随意填子"""
    
    def _get_japanese_rules(self) -> str:
        """日本规则说明"""
        return """日本规则（数目法）

基本原则：
1. 黑方先行，轮流落子
2. 提取对方无气之子
3. 禁止立即回提（劫）
4. 连续两次虚手结束对局

计分方法：
- 数目法：计算围住的空点 + 提子 + 死子
- 白方贴6.5目
- 只数空，不数子

特点：
- 需要判定死活
- 收官需要技巧
- 有特殊规则（如双活无目）"""
    
    def _get_aga_rules(self) -> str:
        """AGA规则说明"""
        return """AGA规则（美国围棋协会规则）

基本原则：
- 综合中日规则特点
- 黑方先行，白方贴7.5目
- 使用区域计分法

计分方法：
- 类似中国规则的数子法
- 但白方每虚手要交还一个子给黑方
- 结果与日本规则基本一致

特点：
- 规则清晰明确
- 适合比赛使用
- 减少争议"""
    
    def get_rules_text(self, rule_type: str) -> str:
        """获取规则文本"""
        return self.rules_content.get(rule_type, "未知规则类型")


class BasicTutorial:
    """基础教程"""
    
    def __init__(self):
        self.tutorials = {
            'opening': "布局要点...",
            'middle_game': "中盘战斗...",
            'endgame': "收官技巧...",
            'life_death': "死活要点...",
            'ko': "劫的处理..."
        }
    
    def get_tutorial(self, topic: str) -> str:
        """获取教程内容"""
        return self.tutorials.get(topic, "教程内容暂未完成")
