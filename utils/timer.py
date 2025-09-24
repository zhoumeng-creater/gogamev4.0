"""
计时器模块
实现各种计时系统：包干时间、读秒、加拿大计时、费舍尔计时等
"""

import time
import threading
from enum import Enum
from typing import Optional, Tuple, Callable, Any, Dict
from dataclasses import dataclass


class TimeControl(Enum):
    """时间控制类型"""
    NONE = "none"              # 无限时
    ABSOLUTE = "absolute"      # 包干时间
    BYOYOMI = "byoyomi"       # 日本读秒
    CANADIAN = "canadian"      # 加拿大计时
    FISCHER = "fischer"        # 费舍尔计时（每步加时）
    BRONSTEIN = "bronstein"    # 布朗斯坦延时


@dataclass
class TimeSettings:
    """时间设置"""
    control_type: TimeControl = TimeControl.NONE
    main_time: int = 1800           # 基本时间（秒）
    
    # 读秒设置
    byoyomi_time: int = 30           # 每次读秒时间
    byoyomi_periods: int = 3         # 读秒次数
    
    # 加拿大计时设置
    canadian_time: int = 300         # 加拿大时间
    canadian_stones: int = 25        # 需要下的棋子数
    
    # 费舍尔/布朗斯坦设置
    increment: int = 10              # 每步增加的时间
    delay: int = 5                   # 延迟时间


class TimeSystem:
    """计时系统基类"""
    
    def __init__(self, settings: TimeSettings):
        self.settings = settings
        self.main_time = settings.main_time
        self.is_in_overtime = False
        
    def start_turn(self) -> None:
        """开始回合"""
        pass
    
    def end_turn(self) -> None:
        """结束回合"""
        pass
    
    def update(self, elapsed: float) -> Tuple[bool, str]:
        """
        更新时间
        
        Args:
            elapsed: 经过的时间（秒）
        
        Returns:
            (是否超时, 显示文本)
        """
        raise NotImplementedError
    
    def get_display(self) -> str:
        """获取显示文本"""
        raise NotImplementedError
    
    def reset(self) -> None:
        """重置计时器"""
        self.main_time = self.settings.main_time
        self.is_in_overtime = False


class AbsoluteTimeSystem(TimeSystem):
    """包干时间系统"""
    
    def update(self, elapsed: float) -> Tuple[bool, str]:
        self.main_time -= elapsed
        
        if self.main_time <= 0:
            return True, "超时"
        
        return False, self.get_display()
    
    def get_display(self) -> str:
        return self._format_time(max(0, self.main_time))
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间显示"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


class ByoyomiTimeSystem(TimeSystem):
    """日本读秒系统"""
    
    def __init__(self, settings: TimeSettings):
        super().__init__(settings)
        self.byoyomi_time_left = settings.byoyomi_time
        self.byoyomi_periods_left = settings.byoyomi_periods
    
    def update(self, elapsed: float) -> Tuple[bool, str]:
        if not self.is_in_overtime:
            # 基本时间阶段
            self.main_time -= elapsed
            
            if self.main_time <= 0:
                # 进入读秒
                self.is_in_overtime = True
                self.byoyomi_time_left = self.settings.byoyomi_time
        else:
            # 读秒阶段
            self.byoyomi_time_left -= elapsed
            
            if self.byoyomi_time_left <= 0:
                self.byoyomi_periods_left -= 1
                
                if self.byoyomi_periods_left <= 0:
                    return True, "超时"
                
                # 重置读秒时间
                self.byoyomi_time_left = self.settings.byoyomi_time
        
        return False, self.get_display()
    
    def end_turn(self) -> None:
        """结束回合时重置读秒"""
        if self.is_in_overtime:
            self.byoyomi_time_left = self.settings.byoyomi_time
    
    def get_display(self) -> str:
        if not self.is_in_overtime:
            return self._format_time(max(0, self.main_time))
        else:
            return f"读秒 {int(self.byoyomi_time_left)}秒 ({self.byoyomi_periods_left}次)"
    
    def _format_time(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def reset(self) -> None:
        super().reset()
        self.byoyomi_time_left = self.settings.byoyomi_time
        self.byoyomi_periods_left = self.settings.byoyomi_periods


class CanadianTimeSystem(TimeSystem):
    """加拿大计时系统"""
    
    def __init__(self, settings: TimeSettings):
        super().__init__(settings)
        self.canadian_time_left = settings.canadian_time
        self.stones_to_play = settings.canadian_stones
        self.stones_played = 0
    
    def update(self, elapsed: float) -> Tuple[bool, str]:
        if not self.is_in_overtime:
            # 基本时间阶段
            self.main_time -= elapsed
            
            if self.main_time <= 0:
                # 进入加拿大计时
                self.is_in_overtime = True
                self.canadian_time_left = self.settings.canadian_time
                self.stones_played = 0
        else:
            # 加拿大计时阶段
            self.canadian_time_left -= elapsed
            
            if self.canadian_time_left <= 0:
                return True, "超时"
        
        return False, self.get_display()
    
    def end_turn(self) -> None:
        """结束回合"""
        if self.is_in_overtime:
            self.stones_played += 1
            
            # 检查是否完成了规定的着手数
            if self.stones_played >= self.settings.canadian_stones:
                # 重置加拿大计时
                self.canadian_time_left = self.settings.canadian_time
                self.stones_played = 0
    
    def get_display(self) -> str:
        if not self.is_in_overtime:
            return self._format_time(max(0, self.main_time))
        else:
            stones_remaining = self.settings.canadian_stones - self.stones_played
            time_str = self._format_time(max(0, self.canadian_time_left))
            return f"{time_str} / {stones_remaining}手"
    
    def _format_time(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def reset(self) -> None:
        super().reset()
        self.canadian_time_left = self.settings.canadian_time
        self.stones_to_play = self.settings.canadian_stones
        self.stones_played = 0


class FischerTimeSystem(TimeSystem):
    """费舍尔计时系统（每步加时）"""
    
    def __init__(self, settings: TimeSettings):
        super().__init__(settings)
        self.increment = settings.increment
    
    def update(self, elapsed: float) -> Tuple[bool, str]:
        self.main_time -= elapsed
        
        if self.main_time <= 0:
            return True, "超时"
        
        return False, self.get_display()
    
    def end_turn(self) -> None:
        """结束回合时增加时间"""
        self.main_time += self.increment
    
    def get_display(self) -> str:
        return self._format_time(max(0, self.main_time))
    
    def _format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


class Timer:
    """游戏计时器"""
    
    def __init__(self, settings: TimeSettings, callback: Optional[Callable] = None):
        """
        初始化计时器
        
        Args:
            settings: 时间设置
            callback: 超时回调函数
        """
        self.settings = settings
        self.callback = callback
        
        # 创建计时系统
        self.time_system = self._create_time_system(settings)
        
        # 计时状态
        self.is_running = False
        self.start_time = 0.0
        self.accumulated_time = 0.0
        
        # 线程控制
        self.timer_thread = None
        self.stop_event = threading.Event()
        
        # 统计信息
        self.move_count = 0
        self.total_time_used = 0.0
        self.longest_think = 0.0
        self.current_think_time = 0.0
    
    def _create_time_system(self, settings: TimeSettings) -> TimeSystem:
        """创建计时系统"""
        if settings.control_type == TimeControl.NONE:
            return None
        elif settings.control_type == TimeControl.ABSOLUTE:
            return AbsoluteTimeSystem(settings)
        elif settings.control_type == TimeControl.BYOYOMI:
            return ByoyomiTimeSystem(settings)
        elif settings.control_type == TimeControl.CANADIAN:
            return CanadianTimeSystem(settings)
        elif settings.control_type == TimeControl.FISCHER:
            return FischerTimeSystem(settings)
        else:
            return AbsoluteTimeSystem(settings)
    
    def start(self) -> None:
        """开始计时"""
        if self.time_system is None:
            return
        
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time()
            self.current_think_time = 0.0
            
            # 启动计时线程
            self.stop_event.clear()
            self.timer_thread = threading.Thread(target=self._timer_worker, daemon=True)
            self.timer_thread.start()
            
            # 通知计时系统
            self.time_system.start_turn()
    
    def stop(self) -> float:
        """
        停止计时
        
        Returns:
            本次思考时间
        """
        if self.time_system is None:
            return 0.0
        
        if self.is_running:
            self.is_running = False
            
            # 计算本次思考时间
            think_time = time.time() - self.start_time + self.accumulated_time
            self.accumulated_time = 0.0
            
            # 更新统计
            self.move_count += 1
            self.total_time_used += think_time
            self.longest_think = max(self.longest_think, think_time)
            
            # 停止计时线程
            self.stop_event.set()
            if self.timer_thread:
                self.timer_thread.join(timeout=1.0)
            
            # 通知计时系统
            self.time_system.end_turn()
            
            return think_time
        
        return 0.0
    
    def pause(self) -> None:
        """暂停计时"""
        if self.is_running:
            self.accumulated_time += time.time() - self.start_time
            self.is_running = False
            self.stop_event.set()
    
    def resume(self) -> None:
        """恢复计时"""
        if not self.is_running and self.time_system:
            self.is_running = True
            self.start_time = time.time()
            
            self.stop_event.clear()
            self.timer_thread = threading.Thread(target=self._timer_worker, daemon=True)
            self.timer_thread.start()
    
    def _timer_worker(self) -> None:
        """计时工作线程"""
        last_update = time.time()
        
        while not self.stop_event.wait(0.1):
            if self.is_running and self.time_system:
                current_time = time.time()
                elapsed = current_time - last_update
                last_update = current_time
                
                # 更新思考时间
                self.current_think_time += elapsed
                
                # 更新计时系统
                timeout, _ = self.time_system.update(elapsed)
                
                if timeout and self.callback:
                    self.callback('timeout')
    
    def get_time_left(self) -> float:
        """获取剩余时间（秒）"""
        if self.time_system is None:
            return float('inf')
        
        if hasattr(self.time_system, 'main_time'):
            return max(0, self.time_system.main_time)
        
        return 0.0
    
    def get_display_time(self) -> str:
        """获取显示时间"""
        if self.time_system is None:
            return "∞"
        
        return self.time_system.get_display()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_time = self.total_time_used / max(1, self.move_count)
        
        return {
            'move_count': self.move_count,
            'total_time': self.total_time_used,
            'average_time': avg_time,
            'longest_think': self.longest_think,
            'current_think': self.current_think_time
        }
    
    def reset(self) -> None:
        """重置计时器"""
        # 停止计时
        if self.is_running:
            self.stop_event.set()
            self.is_running = False
        
        # 重置计时系统
        if self.time_system:
            self.time_system.reset()
        
        # 重置状态
        self.accumulated_time = 0.0
        self.move_count = 0
        self.total_time_used = 0.0
        self.longest_think = 0.0
        self.current_think_time = 0.0
    
    def set_time_control(self, settings: TimeSettings) -> None:
        """更改时间控制设置"""
        self.settings = settings
        self.time_system = self._create_time_system(settings)
        self.reset()