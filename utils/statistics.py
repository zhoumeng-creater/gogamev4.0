"""
统计系统模块
记录和分析游戏统计数据
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import statistics as stats


@dataclass
class GameStats:
    """单局游戏统计"""
    game_id: str
    date: str
    duration: int  # 秒
    board_size: int
    player_black: str
    player_white: str
    black_rating: Optional[int]
    white_rating: Optional[int]
    result: str
    move_count: int
    resignation: bool
    timeout: bool
    
    # 详细统计
    captures_black: int = 0
    captures_white: int = 0
    territory_black: int = 0
    territory_white: int = 0
    
    # 时间统计
    time_black: float = 0.0
    time_white: float = 0.0
    longest_think_black: float = 0.0
    longest_think_white: float = 0.0
    
    # 开局和定式
    opening_pattern: str = ""
    joseki_used: List[str] = field(default_factory=list)
    
    # 特殊事件
    ko_fights: int = 0
    passes: int = 0
    mistakes: int = 0
    brilliant_moves: int = 0
    
    def get_winner(self) -> Optional[str]:
        """获取胜者"""
        if 'B+' in self.result:
            return 'black'
        elif 'W+' in self.result:
            return 'white'
        return None
    
    def get_score_difference(self) -> Optional[float]:
        """获取分差"""
        try:
            if '+' in self.result:
                parts = self.result.split('+')
                if len(parts) == 2:
                    return float(parts[1].replace('R', ''))
        except:
            pass
        return None


@dataclass
class PlayerStats:
    """玩家统计"""
    player_name: str
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    
    # 分别统计黑白
    games_as_black: int = 0
    wins_as_black: int = 0
    games_as_white: int = 0
    wins_as_white: int = 0
    
    # 时间统计
    total_time_played: int = 0  # 秒
    average_move_time: float = 0.0
    fastest_game: Optional[int] = None
    longest_game: Optional[int] = None
    
    # 等级分
    rating: int = 1500
    highest_rating: int = 1500
    lowest_rating: int = 1500
    rating_history: List[Tuple[str, int]] = field(default_factory=list)
    
    # 成就
    achievements: List[str] = field(default_factory=list)
    winning_streak: int = 0
    longest_winning_streak: int = 0
    losing_streak: int = 0
    
    # 对手统计
    opponents: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # 开局偏好
    favorite_openings: Dict[str, int] = field(default_factory=dict)
    
    # 其他统计
    total_moves: int = 0
    total_captures: int = 0
    resignation_wins: int = 0
    resignation_losses: int = 0
    timeout_wins: int = 0
    timeout_losses: int = 0
    
    def get_win_rate(self) -> float:
        """计算胜率"""
        if self.total_games == 0:
            return 0.0
        return self.wins / self.total_games
    
    def get_black_win_rate(self) -> float:
        """黑棋胜率"""
        if self.games_as_black == 0:
            return 0.0
        return self.wins_as_black / self.games_as_black
    
    def get_white_win_rate(self) -> float:
        """白棋胜率"""
        if self.games_as_white == 0:
            return 0.0
        return self.wins_as_white / self.games_as_white
    
    def update_rating(self, new_rating: int, date: str):
        """更新等级分"""
        self.rating = new_rating
        self.highest_rating = max(self.highest_rating, new_rating)
        self.lowest_rating = min(self.lowest_rating, new_rating)
        self.rating_history.append((date, new_rating))
    
    def add_achievement(self, achievement: str):
        """添加成就"""
        if achievement not in self.achievements:
            self.achievements.append(achievement)


class Statistics:
    """统计管理器"""
    
    ACHIEVEMENTS = {
        'first_win': '首胜',
        'first_10_wins': '十连胜',
        'first_100_wins': '百胜',
        'winning_streak_5': '五连胜',
        'winning_streak_10': '十连胜',
        'perfect_game': '完美对局',
        'comeback_king': '逆转大师',
        'speed_demon': '快枪手',
        'marathon_player': '马拉松选手',
        'joseki_master': '定式大师',
        'fighting_spirit': '战斗精神',
        'peaceful_player': '和平主义者',
        'territory_king': '领地之王',
        'capture_master': '吃子大师',
        'early_bird': '早起鸟',
        'night_owl': '夜猫子',
        'dedication': '勤奋玩家',
    }
    
    def __init__(self, data_file: str = "statistics.json"):
        """
        初始化统计管理器
        
        Args:
            data_file: 数据文件路径
        """
        from . import resource_path
        self.data_file = resource_path(os.path.join("assets", "data", data_file))
        
        # 统计数据
        self.game_history: List[GameStats] = []
        self.player_stats: Dict[str, PlayerStats] = {}
        self.global_stats = {
            'total_games': 0,
            'total_time': 0,
            'most_popular_board': 19,
            'most_popular_rules': 'chinese',
            'daily_games': defaultdict(int),
            'hourly_distribution': defaultdict(int),
        }
        
        # 加载历史数据
        self.load_statistics()

    def _normalize_global_stats(self) -> None:
        """
        规范化全局统计结构。

        注意：JSON 反序列化会把 defaultdict 还原为普通 dict，导致后续 `+= 1` 时 KeyError。
        """
        daily_games = self.global_stats.get('daily_games') or {}
        if not isinstance(daily_games, defaultdict):
            try:
                self.global_stats['daily_games'] = defaultdict(int, daily_games)
            except Exception:
                self.global_stats['daily_games'] = defaultdict(int)

        hourly_distribution = self.global_stats.get('hourly_distribution') or {}
        if not isinstance(hourly_distribution, defaultdict):
            try:
                self.global_stats['hourly_distribution'] = defaultdict(int, hourly_distribution)
            except Exception:
                self.global_stats['hourly_distribution'] = defaultdict(int)

        # 兜底关键字段
        self.global_stats.setdefault('total_games', 0)
        self.global_stats.setdefault('total_time', 0)
        self.global_stats.setdefault('most_popular_board', 19)
        self.global_stats.setdefault('most_popular_rules', 'chinese')
    
    def load_statistics(self) -> bool:
        """加载统计数据"""
        if not os.path.exists(self.data_file):
            return False
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 加载游戏历史
                for game_data in data.get('game_history', []):
                    self.game_history.append(GameStats(**game_data))
                
                # 加载玩家统计
                for name, player_data in data.get('player_stats', {}).items():
                    self.player_stats[name] = PlayerStats(**player_data)
                
                # 加载全局统计
                self.global_stats.update(data.get('global_stats', {}))

                # 修复 defaultdict 丢失问题（避免 record_game 出现 KeyError）
                self._normalize_global_stats()
                
            return True
            
        except Exception as e:
            print(f"加载统计数据失败: {e}")
            return False
    
    def save_statistics(self) -> bool:
        """保存统计数据"""
        try:
            # 准备数据
            data = {
                'game_history': [asdict(game) for game in self.game_history[-1000:]],  # 只保留最近1000局
                'player_stats': {name: asdict(stats) for name, stats in self.player_stats.items()},
                'global_stats': self.global_stats
            }
            
            # 创建目录
            os.makedirs(os.path.dirname(self.data_file) or '.', exist_ok=True)
            
            # 保存文件
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"保存统计数据失败: {e}")
            return False
    
    def record_game(self, game_stats: GameStats) -> None:
        """
        记录一局游戏
        
        Args:
            game_stats: 游戏统计数据
        """
        # 添加到历史
        self.game_history.append(game_stats)

        # 确保结构类型正确（防止外部修改或旧数据导致 KeyError）
        self._normalize_global_stats()
        
        # 更新全局统计
        self.global_stats['total_games'] += 1
        self.global_stats['total_time'] += game_stats.duration
        
        # 更新日期统计
        date = game_stats.date[:10]  # YYYY-MM-DD
        self.global_stats['daily_games'][date] += 1
        
        # 更新小时分布
        hour = datetime.fromisoformat(game_stats.date).hour
        self.global_stats['hourly_distribution'][str(hour)] += 1
        
        # 更新玩家统计
        self._update_player_stats(game_stats.player_black, game_stats, 'black')
        self._update_player_stats(game_stats.player_white, game_stats, 'white')
        
        # 检查成就
        self._check_achievements(game_stats)
        
        # 保存数据
        self.save_statistics()

    def record_game_start(self, settings: Dict[str, Any]) -> None:
        """
        兼容旧接口：记录对局开始事件。

        旧版 UI 会在开局时调用该方法；当前统计系统主要在对局结束时通过
        `record_game()` 记录完整数据，因此这里保持轻量实现以避免崩溃。
        """
        return
    
    def _update_player_stats(self, player_name: str, game: GameStats, color: str) -> None:
        """更新玩家统计"""
        if player_name not in self.player_stats:
            self.player_stats[player_name] = PlayerStats(player_name=player_name)
        
        player = self.player_stats[player_name]
        player.total_games += 1
        player.total_time_played += game.duration // 2  # 假设双方时间各占一半
        player.total_moves += game.move_count // 2
        
        # 更新黑白统计
        if color == 'black':
            player.games_as_black += 1
            player.total_captures += game.captures_black
            time_used = game.time_black
        else:
            player.games_as_white += 1
            player.total_captures += game.captures_white
            time_used = game.time_white
        
        # 更新胜负
        winner = game.get_winner()
        if winner == color:
            player.wins += 1
            player.winning_streak += 1
            player.losing_streak = 0
            player.longest_winning_streak = max(player.longest_winning_streak, player.winning_streak)
            
            if color == 'black':
                player.wins_as_black += 1
            else:
                player.wins_as_white += 1
            
            if game.resignation:
                player.resignation_wins += 1
            elif game.timeout:
                player.timeout_wins += 1
                
        elif winner and winner != color:
            player.losses += 1
            player.winning_streak = 0
            player.losing_streak += 1
            
            if game.resignation:
                player.resignation_losses += 1
            elif game.timeout:
                player.timeout_losses += 1
        else:
            player.draws += 1
            player.winning_streak = 0
            player.losing_streak = 0
        
        # 更新对手统计
        opponent = game.player_white if color == 'black' else game.player_black
        if opponent not in player.opponents:
            player.opponents[opponent] = {'wins': 0, 'losses': 0, 'draws': 0}
        
        if winner == color:
            player.opponents[opponent]['wins'] += 1
        elif winner and winner != color:
            player.opponents[opponent]['losses'] += 1
        else:
            player.opponents[opponent]['draws'] += 1
        
        # 更新开局偏好
        if game.opening_pattern:
            if game.opening_pattern not in player.favorite_openings:
                player.favorite_openings[game.opening_pattern] = 0
            player.favorite_openings[game.opening_pattern] += 1
        
        # 更新时间统计
        if player.total_moves > 0:
            player.average_move_time = player.total_time_played / player.total_moves
        
        if player.fastest_game is None or game.duration < player.fastest_game:
            player.fastest_game = game.duration
        
        if player.longest_game is None or game.duration > player.longest_game:
            player.longest_game = game.duration
    
    def _check_achievements(self, game: GameStats) -> None:
        """检查并授予成就"""
        for player_name in [game.player_black, game.player_white]:
            if player_name not in self.player_stats:
                continue
            
            player = self.player_stats[player_name]
            
            # 首胜
            if player.wins == 1:
                player.add_achievement('first_win')
            
            # 十胜
            if player.wins == 10:
                player.add_achievement('first_10_wins')
            
            # 百胜
            if player.wins == 100:
                player.add_achievement('first_100_wins')
            
            # 连胜成就
            if player.winning_streak == 5:
                player.add_achievement('winning_streak_5')
            elif player.winning_streak == 10:
                player.add_achievement('winning_streak_10')
            
            # 完美对局（无子被吃）
            color = 'black' if player_name == game.player_black else 'white'
            if game.get_winner() == color:
                if (color == 'black' and game.captures_white == 0) or \
                   (color == 'white' and game.captures_black == 0):
                    player.add_achievement('perfect_game')
            
            # 快棋手（5分钟内完成对局）
            if game.duration < 300 and game.move_count > 50:
                player.add_achievement('speed_demon')
            
            # 马拉松（对局超过2小时）
            if game.duration > 7200:
                player.add_achievement('marathon_player')
            
            # 定式大师（使用5种以上定式）
            if len(game.joseki_used) >= 5:
                player.add_achievement('joseki_master')
            
            # 吃子大师（吃子超过20个）
            captures = game.captures_black if color == 'black' else game.captures_white
            if captures > 20:
                player.add_achievement('capture_master')
    
    def get_player_stats(self, player_name: str) -> Optional[PlayerStats]:
        """获取玩家统计"""
        return self.player_stats.get(player_name)
    
    def get_recent_games(self, player_name: Optional[str] = None, limit: int = 10) -> List[GameStats]:
        """
        获取最近的对局
        
        Args:
            player_name: 玩家名（None表示所有）
            limit: 数量限制
        
        Returns:
            游戏列表
        """
        if player_name:
            games = [g for g in self.game_history 
                    if g.player_black == player_name or g.player_white == player_name]
        else:
            games = self.game_history
        
        return games[-limit:]
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        if not self.game_history:
            return {
                'total_games': 0,
                'total_players': 0,
                'average_game_duration': 0,
                'average_moves': 0,
                'most_active_player': None,
                'highest_rated_player': None,
            }
        
        # 计算平均值
        durations = [g.duration for g in self.game_history]
        moves = [g.move_count for g in self.game_history]
        
        # 找出最活跃和最高分的玩家
        most_active = max(self.player_stats.values(), 
                         key=lambda p: p.total_games) if self.player_stats else None
        highest_rated = max(self.player_stats.values(), 
                           key=lambda p: p.rating) if self.player_stats else None
        
        return {
            'total_games': len(self.game_history),
            'total_players': len(self.player_stats),
            'average_game_duration': stats.mean(durations) if durations else 0,
            'average_moves': stats.mean(moves) if moves else 0,
            'most_active_player': most_active.player_name if most_active else None,
            'highest_rated_player': highest_rated.player_name if highest_rated else None,
            'total_time_played': self.global_stats['total_time'],
            'daily_average': self._calculate_daily_average(),
        }
    
    def _calculate_daily_average(self) -> float:
        """计算日均对局数"""
        if not self.global_stats['daily_games']:
            return 0.0
        
        days = len(self.global_stats['daily_games'])
        total = sum(self.global_stats['daily_games'].values())
        
        return total / days if days > 0 else 0.0
    
    def get_player_vs_player(self, player1: str, player2: str) -> Dict[str, Any]:
        """
        获取两名玩家的对战记录
        
        Args:
            player1: 玩家1
            player2: 玩家2
        
        Returns:
            对战统计
        """
        games = [g for g in self.game_history
                if (g.player_black == player1 and g.player_white == player2) or
                   (g.player_black == player2 and g.player_white == player1)]
        
        p1_wins = 0
        p2_wins = 0
        draws = 0
        
        for game in games:
            winner = game.get_winner()
            if winner:
                if (winner == 'black' and game.player_black == player1) or \
                   (winner == 'white' and game.player_white == player1):
                    p1_wins += 1
                else:
                    p2_wins += 1
            else:
                draws += 1
        
        return {
            'total_games': len(games),
            f'{player1}_wins': p1_wins,
            f'{player2}_wins': p2_wins,
            'draws': draws,
            'games': games
        }
    
    def calculate_elo_change(self, winner_rating: int, loser_rating: int, k: int = 32) -> Tuple[int, int]:
        """
        计算ELO等级分变化
        
        Args:
            winner_rating: 胜者当前分数
            loser_rating: 败者当前分数
            k: K因子
        
        Returns:
            (胜者新分数, 败者新分数)
        """
        # 计算期望胜率
        winner_expected = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
        loser_expected = 1 - winner_expected
        
        # 计算新分数
        winner_new = winner_rating + k * (1 - winner_expected)
        loser_new = loser_rating + k * (0 - loser_expected)
        
        return int(winner_new), int(loser_new)
    
    def export_statistics(self, file_path: str, format: str = 'json') -> bool:
        """
        导出统计数据
        
        Args:
            file_path: 文件路径
            format: 格式 (json/csv)
        
        Returns:
            是否成功
        """
        try:
            if format == 'json':
                data = {
                    'summary': self.get_statistics_summary(),
                    'player_stats': {name: asdict(stats) 
                                   for name, stats in self.player_stats.items()},
                    'recent_games': [asdict(g) for g in self.get_recent_games(limit=100)]
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            elif format == 'csv':
                import csv
                
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # 写入标题
                    writer.writerow(['Player', 'Games', 'Wins', 'Losses', 'Win Rate', 
                                   'Rating', 'Total Time', 'Average Move Time'])
                    
                    # 写入数据
                    for name, stats in self.player_stats.items():
                        writer.writerow([
                            name,
                            stats.total_games,
                            stats.wins,
                            stats.losses,
                            f"{stats.get_win_rate():.2%}",
                            stats.rating,
                            stats.total_time_played,
                            f"{stats.average_move_time:.1f}"
                        ])
            
            return True
            
        except Exception as e:
            print(f"导出统计失败: {e}")
            return False
