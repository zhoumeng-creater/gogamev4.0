"""
分析引擎模块
提供局面分析、错着检测、建议等功能
"""

import time
import threading
from typing import List, Dict, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 导入核心模块
from core import Board, Rules, MoveResult, Territory
from ai import AIFactory, AIPlayer


class AnalysisMode(Enum):
    """分析模式"""
    QUICK = 'quick'  # 快速分析
    DEEP = 'deep'  # 深度分析
    CONTINUOUS = 'continuous'  # 持续分析
    COMPARATIVE = 'comparative'  # 对比分析


@dataclass
class MoveAnalysis:
    """单个着法的分析结果"""
    x: int
    y: int
    winrate: float
    score_change: float
    visits: int = 0
    pv: List[Tuple[int, int]] = field(default_factory=list)  # 主要变化
    comment: str = ""
    
    def get_coordinate_string(self) -> str:
        """获取坐标字符串"""
        if self.x < 0 or self.y < 0:
            return "Pass"
        col = chr(ord('A') + self.x)
        if col >= 'I':  # 跳过I
            col = chr(ord(col) + 1)
        row = 19 - self.y
        return f"{col}{row}"


@dataclass
class PositionAnalysis:
    """局面分析结果"""
    winrate: float
    score: float
    best_moves: List[MoveAnalysis]
    territory_estimate: Dict[str, int]
    dead_stones: List[Tuple[int, int]]
    influence_map: np.ndarray
    timestamp: float = field(default_factory=time.time)
    engine_name: str = ""
    analysis_depth: int = 0
    
    def get_best_move(self) -> Optional[MoveAnalysis]:
        """获取最佳着法"""
        return self.best_moves[0] if self.best_moves else None
    
    def get_winrate_text(self) -> str:
        """获取胜率文本"""
        if self.winrate > 0.5:
            return f"黑棋 {self.winrate:.1%}"
        else:
            return f"白棋 {(1-self.winrate):.1%}"


class MistakeType(Enum):
    """错误类型"""
    BLUNDER = 'blunder'  # 大错（胜率损失>20%）
    MISTAKE = 'mistake'  # 错误（胜率损失>10%）
    INACCURACY = 'inaccuracy'  # 不精确（胜率损失>5%）
    GOOD = 'good'  # 好手
    EXCELLENT = 'excellent'  # 妙手


@dataclass
class MistakeInfo:
    """错着信息"""
    move_number: int
    actual_move: Tuple[int, int]
    best_move: Tuple[int, int]
    winrate_loss: float
    mistake_type: MistakeType
    explanation: str = ""
    
    def get_severity_color(self) -> str:
        """获取严重程度对应的颜色"""
        colors = {
            MistakeType.BLUNDER: '#ff0000',
            MistakeType.MISTAKE: '#ff8800',
            MistakeType.INACCURACY: '#ffff00',
            MistakeType.GOOD: '#00ff00',
            MistakeType.EXCELLENT: '#00ffff'
        }
        return colors.get(self.mistake_type, '#ffffff')


class AnalysisEngine:
    """分析引擎"""
    
    def __init__(self, board_size: int = 19):
        self.board_size = board_size
        
        # AI引擎池（用于多线程分析）
        self.ai_engines = {
            'quick': AIFactory.create_ai('expert', 'black', board_size),
            'deep': AIFactory.create_ai('mcts', 'black', board_size, simulations=2000),
            'neural': None  # 预留神经网络
        }
        
        # 分析缓存
        self.analysis_cache: Dict[str, PositionAnalysis] = {}
        
        # 分析线程
        self.analysis_thread: Optional[threading.Thread] = None
        self.stop_analysis = False
        
        # 回调函数
        self.on_analysis_complete: Optional[Callable] = None
        self.on_progress_update: Optional[Callable] = None
    
    def analyze_position(self, board: Board, color: str, 
                        mode: AnalysisMode = AnalysisMode.QUICK,
                        callback: Optional[Callable] = None) -> PositionAnalysis:
        """
        分析局面
        
        Args:
            board: 棋盘状态
            color: 当前玩家颜色
            mode: 分析模式
            callback: 完成回调
        
        Returns:
            分析结果
        """
        # 检查缓存
        board_hash = board.get_hash()
        cache_key = f"{board_hash}_{color}_{mode.value}"
        
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        # 选择合适的引擎
        if mode == AnalysisMode.QUICK:
            engine = self.ai_engines['quick']
            engine.thinking_time = 1.0
        elif mode == AnalysisMode.DEEP:
            engine = self.ai_engines['deep']
            engine.thinking_time = 5.0
        else:
            engine = self.ai_engines['deep']
            engine.thinking_time = 10.0
        
        # 设置引擎颜色
        engine.color = color
        engine.opponent_color = 'white' if color == 'black' else 'black'
        
        # 执行分析
        start_time = time.time()
        
        # 获取局面评估
        eval_result = engine.evaluate_position(board)
        
        # 获取最佳着法
        legal_moves = engine.get_legal_moves(board)
        best_moves = []
        
        # 分析前N个候选着法
        num_candidates = min(10 if mode == AnalysisMode.DEEP else 5, len(legal_moves))
        
        for i, (x, y) in enumerate(legal_moves[:num_candidates]):
            if self.stop_analysis:
                break
            
            # 模拟落子
            test_board = board.copy()
            test_board.place_stone(x, y, color)
            
            # 评估
            move_eval = engine.evaluate_position(test_board)
            
            move_analysis = MoveAnalysis(
                x=x,
                y=y,
                winrate=move_eval.winning_probability,
                score_change=move_eval.score - eval_result.score,
                visits=100 * (num_candidates - i),  # 模拟访问次数
                comment=self._generate_move_comment(x, y, move_eval.winning_probability)
            )
            
            best_moves.append(move_analysis)
            
            # 进度更新
            if self.on_progress_update:
                progress = (i + 1) / num_candidates
                self.on_progress_update(progress)
        
        # 排序
        best_moves.sort(key=lambda m: m.winrate, reverse=True)
        
        # 计算领地估算
        territory = Territory(board)
        territory_map = territory.calculate_territory()
        
        # 计算势力图
        influence_map = self._calculate_influence_map(board, color)
        
        # 创建分析结果
        analysis = PositionAnalysis(
            winrate=eval_result.winning_probability,
            score=eval_result.score,
            best_moves=best_moves[:5],
            territory_estimate={
                'black': territory_map['black'],
                'white': territory_map['white'],
                'neutral': territory_map.get('neutral', 0)
            },
            dead_stones=[],
            influence_map=influence_map,
            engine_name=engine.__class__.__name__,
            analysis_depth=num_candidates
        )
        
        # 缓存结果
        self.analysis_cache[cache_key] = analysis
        
        # 回调
        if callback:
            callback(analysis)
        if self.on_analysis_complete:
            self.on_analysis_complete(analysis)
        
        return analysis
    
    def analyze_game(self, moves: List[Tuple[int, int, str]], 
                    progress_callback: Optional[Callable] = None) -> List[PositionAnalysis]:
        """
        分析整个对局
        
        Args:
            moves: 棋谱着法列表
            progress_callback: 进度回调
        
        Returns:
            每一手的分析结果
        """
        analyses = []
        board = Board(self.board_size)
        
        for i, (x, y, color) in enumerate(moves):
            if self.stop_analysis:
                break
            
            # 分析当前局面
            analysis = self.analyze_position(board, color, AnalysisMode.QUICK)
            analyses.append(analysis)
            
            # 落子
            if x >= 0 and y >= 0:
                board.place_stone(x, y, color)
            
            # 更新进度
            if progress_callback:
                progress_callback((i + 1) / len(moves))
        
        return analyses
    
    def start_continuous_analysis(self, board: Board, color: str):
        """开始持续分析"""
        self.stop_analysis = False
        
        def analyze_loop():
            mode = AnalysisMode.QUICK
            while not self.stop_analysis:
                self.analyze_position(board, color, mode)
                # 逐步加深
                if mode == AnalysisMode.QUICK:
                    mode = AnalysisMode.DEEP
                time.sleep(0.1)
        
        self.analysis_thread = threading.Thread(target=analyze_loop)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
    
    def stop_continuous_analysis(self):
        """停止持续分析"""
        self.stop_analysis = True
        if self.analysis_thread:
            self.analysis_thread.join(timeout=1.0)
    
    def _calculate_influence_map(self, board: Board, color: str) -> np.ndarray:
        """计算势力图"""
        influence = np.zeros((self.board_size, self.board_size))
        
        for y in range(self.board_size):
            for x in range(self.board_size):
                stone = board.get_stone(x, y)
                if stone:
                    # 确定势力值
                    value = 10.0 if stone == color else -10.0
                    
                    # 传播势力
                    for dy in range(self.board_size):
                        for dx in range(self.board_size):
                            distance = max(abs(x - dx), abs(y - dy))
                            if distance > 0:
                                influence[dy, dx] += value * np.exp(-distance * 0.3)
        
        return influence
    
    def _generate_move_comment(self, x: int, y: int, winrate: float) -> str:
        """生成着法评注"""
        if winrate > 0.8:
            return "明显优势"
        elif winrate > 0.6:
            return "略优"
        elif winrate > 0.4:
            return "均势"
        elif winrate > 0.2:
            return "略差"
        else:
            return "明显劣势"
    
    def clear_cache(self):
        """清除分析缓存"""
        self.analysis_cache.clear()


class PositionAnalyzer:
    """局面分析器"""
    
    def __init__(self, engine: AnalysisEngine):
        self.engine = engine
    
    def analyze_territory(self, board: Board) -> Dict[str, Any]:
        """分析领地"""
        territory = Territory(board)
        territory_map = territory.calculate_territory()
        
        # 计算确定的领地和势力范围
        solid_territory = {'black': 0, 'white': 0}
        influence_territory = {'black': 0, 'white': 0}
        
        # TODO: 实现更精确的领地判定
        
        return {
            'territory_map': territory_map,
            'solid': solid_territory,
            'influence': influence_territory,
            'estimated_score': territory_map['black'] - territory_map['white']
        }
    
    def find_weak_groups(self, board: Board) -> List[Dict[str, Any]]:
        """查找弱棋"""
        weak_groups = []
        
        for group in board.get_all_groups():
            liberties = len(group.liberties)
            stones = len(group.stones)
            
            # 评估棋块强弱
            if liberties == 1:
                status = 'critical'  # 危急
            elif liberties == 2:
                status = 'weak'  # 虚弱
            elif liberties == 3 and stones > 5:
                status = 'unsettled'  # 不安定
            else:
                continue
            
            weak_groups.append({
                'group': group,
                'status': status,
                'liberties': liberties,
                'size': stones,
                'can_escape': self._can_escape(board, group),
                'can_make_eyes': self._can_make_eyes(board, group)
            })
        
        return weak_groups
    
    def _can_escape(self, board: Board, group) -> bool:
        """判断棋块是否能逃脱"""
        # 简化判断：如果有3气以上认为可以逃脱
        return len(group.liberties) >= 3
    
    def _can_make_eyes(self, board: Board, group) -> bool:
        """判断棋块是否能做眼"""
        # 简化判断：检查是否有足够的空间做两眼
        potential_eyes = 0
        
        for x, y in group.liberties:
            # 检查周围是否都是己方棋子或边界
            is_eye = True
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < board.size and 0 <= ny < board.size:
                    stone = board.get_stone(nx, ny)
                    if stone and stone != group.color:
                        is_eye = False
                        break
            
            if is_eye:
                potential_eyes += 1
        
        return potential_eyes >= 2


class MistakeDetector:
    """错着检测器"""
    
    def __init__(self, engine: AnalysisEngine):
        self.engine = engine
        
        # 错误阈值
        self.thresholds = {
            MistakeType.BLUNDER: 0.20,
            MistakeType.MISTAKE: 0.10,
            MistakeType.INACCURACY: 0.05
        }
    
    def detect_mistakes(self, game_analyses: List[PositionAnalysis], 
                        moves: List[Tuple[int, int, str]]) -> List[MistakeInfo]:
        """
        检测错着
        
        Args:
            game_analyses: 每一手的分析结果
            moves: 实际下的棋
        
        Returns:
            错误列表
        """
        mistakes = []
        
        for i in range(len(moves) - 1):
            if i >= len(game_analyses) - 1:
                break
            
            current_analysis = game_analyses[i]
            next_analysis = game_analyses[i + 1]
            
            # 计算胜率损失
            color = moves[i][2]
            if color == 'black':
                winrate_before = current_analysis.winrate
                winrate_after = next_analysis.winrate
            else:
                winrate_before = 1 - current_analysis.winrate
                winrate_after = 1 - next_analysis.winrate
            
            winrate_loss = winrate_before - winrate_after
            
            # 判断错误类型
            mistake_type = self._classify_mistake(winrate_loss)
            
            if mistake_type:
                # 获取最佳着法
                best_move = current_analysis.get_best_move()
                best_coords = (best_move.x, best_move.y) if best_move else (-1, -1)
                
                mistake = MistakeInfo(
                    move_number=i + 1,
                    actual_move=(moves[i][0], moves[i][1]),
                    best_move=best_coords,
                    winrate_loss=winrate_loss,
                    mistake_type=mistake_type,
                    explanation=self._generate_explanation(
                        mistake_type, winrate_loss, moves[i], best_coords
                    )
                )
                
                mistakes.append(mistake)
        
        return mistakes
    
    def _classify_mistake(self, winrate_loss: float) -> Optional[MistakeType]:
        """分类错误"""
        if winrate_loss > self.thresholds[MistakeType.BLUNDER]:
            return MistakeType.BLUNDER
        elif winrate_loss > self.thresholds[MistakeType.MISTAKE]:
            return MistakeType.MISTAKE
        elif winrate_loss > self.thresholds[MistakeType.INACCURACY]:
            return MistakeType.INACCURACY
        elif winrate_loss < -0.05:  # 提升了胜率
            return MistakeType.GOOD
        elif winrate_loss < -0.15:
            return MistakeType.EXCELLENT
        
        return None
    
    def _generate_explanation(self, mistake_type: MistakeType, 
                             winrate_loss: float,
                             actual_move: Tuple[int, int, str],
                             best_move: Tuple[int, int]) -> str:
        """生成错误说明"""
        explanations = {
            MistakeType.BLUNDER: f"大错！胜率损失{winrate_loss:.1%}。",
            MistakeType.MISTAKE: f"错误。胜率损失{winrate_loss:.1%}。",
            MistakeType.INACCURACY: f"不够精确。胜率损失{winrate_loss:.1%}。",
            MistakeType.GOOD: f"好手！胜率提升{-winrate_loss:.1%}。",
            MistakeType.EXCELLENT: f"妙手！胜率提升{-winrate_loss:.1%}。"
        }
        
        base = explanations.get(mistake_type, "")
        
        if best_move[0] >= 0:
            col = chr(ord('A') + best_move[0])
            row = 19 - best_move[1]
            base += f" 推荐下在{col}{row}。"
        
        return base


class SuggestionEngine:
    """建议引擎"""
    
    def __init__(self, analyzer: PositionAnalyzer):
        self.analyzer = analyzer
    
    def get_move_suggestions(self, board: Board, color: str, 
                            analysis: PositionAnalysis) -> List[Dict[str, Any]]:
        """
        获取着法建议
        
        Returns:
            建议列表，每个建议包含着法、理由、优先级
        """
        suggestions = []
        
        # 基于分析结果生成建议
        if analysis.best_moves:
            for i, move in enumerate(analysis.best_moves[:3]):
                priority = 'high' if i == 0 else 'medium' if i == 1 else 'low'
                
                suggestion = {
                    'move': (move.x, move.y),
                    'coordinate': move.get_coordinate_string(),
                    'reason': self._get_move_reason(board, move, analysis),
                    'priority': priority,
                    'winrate': move.winrate,
                    'score_change': move.score_change
                }
                
                suggestions.append(suggestion)
        
        # 检查紧急情况
        weak_groups = self.analyzer.find_weak_groups(board)
        for group_info in weak_groups:
            if group_info['status'] == 'critical':
                # 需要立即处理
                if group_info['group'].color == color:
                    # 救援己方
                    for liberty in group_info['group'].liberties:
                        suggestions.insert(0, {
                            'move': liberty,
                            'coordinate': self._coords_to_string(*liberty),
                            'reason': '紧急！救援危险棋块',
                            'priority': 'urgent',
                            'winrate': 0,
                            'score_change': 0
                        })
                else:
                    # 吃掉对方
                    for liberty in group_info['group'].liberties:
                        suggestions.insert(0, {
                            'move': liberty,
                            'coordinate': self._coords_to_string(*liberty),
                            'reason': '紧急！可以吃子',
                            'priority': 'urgent',
                            'winrate': 0,
                            'score_change': 0
                        })
        
        return suggestions
    
    def _get_move_reason(self, board: Board, move: MoveAnalysis, 
                        analysis: PositionAnalysis) -> str:
        """获取着法理由"""
        reasons = []
        
        # 基于胜率
        if move.winrate > 0.6:
            reasons.append("保持优势")
        elif move.winrate > 0.4:
            reasons.append("维持均势")
        else:
            reasons.append("力争翻盘")
        
        # 基于位置特征
        x, y = move.x, move.y
        
        # 角部
        if (x < 5 or x > 13) and (y < 5 or y > 13):
            reasons.append("占据角部")
        # 边
        elif x < 3 or x > 15 or y < 3 or y > 15:
            reasons.append("扩展边空")
        # 中腹
        else:
            reasons.append("控制中腹")
        
        return "，".join(reasons)
    
    def _coords_to_string(self, x: int, y: int) -> str:
        """坐标转字符串"""
        col = chr(ord('A') + x)
        if col >= 'I':
            col = chr(ord(col) + 1)
        row = 19 - y
        return f"{col}{row}"


class WinrateGraph(tk.Frame):
    """胜率图表组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # 创建图表
        self.figure = plt.Figure(figsize=(6, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        # 创建画布
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # 数据
        self.winrates = []
        self.move_numbers = []
        
        self._setup_plot()
    
    def _setup_plot(self):
        """设置图表"""
        self.ax.set_xlabel('手数')
        self.ax.set_ylabel('黑棋胜率')
        self.ax.set_ylim(0, 1)
        self.ax.grid(True, alpha=0.3)
        self.ax.axhline(y=0.5, color='gray', linestyle='-', alpha=0.5)
    
    def add_point(self, move_number: int, winrate: float):
        """添加数据点"""
        self.move_numbers.append(move_number)
        self.winrates.append(winrate)
        self.update_plot()
    
    def update_plot(self):
        """更新图表"""
        self.ax.clear()
        self._setup_plot()
        
        if self.winrates:
            # 绘制胜率曲线
            self.ax.plot(self.move_numbers, self.winrates, 'b-', linewidth=2)
            
            # 填充区域
            self.ax.fill_between(self.move_numbers, 0.5, self.winrates, 
                                where=[w >= 0.5 for w in self.winrates],
                                color='black', alpha=0.2)
            self.ax.fill_between(self.move_numbers, self.winrates, 0.5,
                                where=[w < 0.5 for w in self.winrates],
                                color='white', alpha=0.2)
            
            # 标记关键点
            if len(self.winrates) > 1:
                # 最大变化
                changes = [abs(self.winrates[i] - self.winrates[i-1]) 
                          for i in range(1, len(self.winrates))]
                if changes:
                    max_change_idx = changes.index(max(changes)) + 1
                    self.ax.plot(self.move_numbers[max_change_idx], 
                               self.winrates[max_change_idx],
                               'ro', markersize=8)
        
        self.canvas.draw()
    
    def clear(self):
        """清除数据"""
        self.winrates.clear()
        self.move_numbers.clear()
        self.update_plot()
    
    def set_data(self, move_numbers: List[int], winrates: List[float]):
        """设置数据"""
        self.move_numbers = move_numbers.copy()
        self.winrates = winrates.copy()
        self.update_plot()