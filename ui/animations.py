"""
动画效果模块
提供落子、吃子、标记等动画效果
"""

import time
import math
from typing import Callable, Optional, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import tkinter as tk


class AnimationType(Enum):
    """动画类型枚举"""
    PLACE_STONE = 'place_stone'  # 落子动画
    CAPTURE_STONE = 'capture_stone'  # 吃子动画
    FADE_IN = 'fade_in'  # 淡入
    FADE_OUT = 'fade_out'  # 淡出
    SCALE = 'scale'  # 缩放
    MOVE = 'move'  # 移动
    ROTATE = 'rotate'  # 旋转
    PULSE = 'pulse'  # 脉冲


class EasingFunction(Enum):
    """缓动函数枚举"""
    LINEAR = 'linear'
    EASE_IN = 'ease_in'
    EASE_OUT = 'ease_out'
    EASE_IN_OUT = 'ease_in_out'
    BOUNCE = 'bounce'
    ELASTIC = 'elastic'
    BACK = 'back'


@dataclass
class Animation:
    """动画基类"""
    type: AnimationType
    target: Any  # 动画目标（canvas item id或其他）
    duration: float  # 持续时间（秒）
    start_time: float = field(default_factory=time.time)
    start_value: Any = None
    end_value: Any = None
    current_value: Any = None
    easing: EasingFunction = EasingFunction.EASE_IN_OUT
    on_complete: Optional[Callable] = None
    on_update: Optional[Callable] = None
    is_completed: bool = False
    is_cancelled: bool = False
    
    def update(self, current_time: float) -> bool:
        """
        更新动画状态
        
        Args:
            current_time: 当前时间
            
        Returns:
            动画是否完成
        """
        if self.is_completed or self.is_cancelled:
            return True
        
        elapsed = current_time - self.start_time
        progress = min(elapsed / self.duration, 1.0)
        
        # 应用缓动函数
        eased_progress = self._apply_easing(progress)
        
        # 计算当前值
        self.current_value = self._interpolate(eased_progress)
        
        # 调用更新回调
        if self.on_update:
            self.on_update(self.current_value)
        
        # 检查是否完成
        if progress >= 1.0:
            self.is_completed = True
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def _apply_easing(self, t: float) -> float:
        """应用缓动函数"""
        if self.easing == EasingFunction.LINEAR:
            return t
        elif self.easing == EasingFunction.EASE_IN:
            return t * t
        elif self.easing == EasingFunction.EASE_OUT:
            return 1 - (1 - t) * (1 - t)
        elif self.easing == EasingFunction.EASE_IN_OUT:
            if t < 0.5:
                return 2 * t * t
            else:
                return 1 - 2 * (1 - t) * (1 - t)
        elif self.easing == EasingFunction.BOUNCE:
            if t < 0.5:
                return 8 * t * t
            else:
                t = t - 0.75
                return 1 - 8 * t * t
        elif self.easing == EasingFunction.ELASTIC:
            if t == 0 or t == 1:
                return t
            p = 0.3
            s = p / 4
            return math.pow(2, -10 * t) * math.sin((t - s) * 2 * math.pi / p) + 1
        elif self.easing == EasingFunction.BACK:
            s = 1.70158
            t = t - 1
            return t * t * ((s + 1) * t + s) + 1
        else:
            return t
    
    def _interpolate(self, progress: float):
        """插值计算"""
        if isinstance(self.start_value, (int, float)):
            return self.start_value + (self.end_value - self.start_value) * progress
        elif isinstance(self.start_value, tuple) and len(self.start_value) == 2:
            # 位置插值
            x1, y1 = self.start_value
            x2, y2 = self.end_value
            return (
                x1 + (x2 - x1) * progress,
                y1 + (y2 - y1) * progress
            )
        else:
            return self.end_value if progress >= 1.0 else self.start_value
    
    def cancel(self):
        """取消动画"""
        self.is_cancelled = True


class StoneAnimation(Animation):
    """棋子动画"""
    
    def __init__(self, canvas: tk.Canvas, x: int, y: int, color: str,
                 cell_size: int, margin: int, **kwargs):
        """
        初始化棋子动画
        
        Args:
            canvas: 画布
            x, y: 棋盘坐标
            color: 棋子颜色
            cell_size: 格子大小
            margin: 边距
        """
        # 提取或设置默认值
        duration = kwargs.pop('duration', 0.3)  # 默认0.3秒
        on_complete = kwargs.pop('on_complete', None)
        
        # 计算中心位置
        cx = margin + x * cell_size
        cy = margin + y * cell_size
        
        # 创建临时棋子作为 target
        temp_stone = canvas.create_oval(
            cx - 1, cy - 1, cx + 1, cy + 1,
            fill=color, state='hidden'
        )
        
        # 调用父类构造函数，传递所有必需参数
        super().__init__(
            type=AnimationType.PLACE_STONE,
            target=temp_stone,
            duration=duration
        )
        
        # 保存其他属性
        self.canvas = canvas
        self.x = x
        self.y = y
        self.color = color
        self.cell_size = cell_size
        self.margin = margin
        self.cx = cx
        self.cy = cy
        self.temp_stone = temp_stone
        
        # 设置动画参数
        self.start_value = 0
        self.end_value = cell_size * 0.45
        self.easing = EasingFunction.BOUNCE
        self.on_complete = on_complete
        self.on_update = self._update_stone
        
        # 开始动画
        self.canvas.itemconfig(self.temp_stone, state='normal')
    
    def _create_temp_stone(self):
        """创建临时棋子用于动画"""
        radius = self.cell_size * 0.45
        
        # 创建阴影
        shadow_offset = 2
        self.shadow = self.canvas.create_oval(
            self.cx - radius + shadow_offset,
            self.cy - radius + shadow_offset,
            self.cx + radius + shadow_offset,
            self.cy + radius + shadow_offset,
            fill='gray',
            outline='',
            state='hidden'
        )
        
        # 创建棋子
        fill_color = 'black' if self.color == 'black' else 'white'
        outline_color = '#333' if self.color == 'black' else '#ccc'
        
        self.temp_stone = self.canvas.create_oval(
            self.cx - radius,
            self.cy - radius,
            self.cx + radius,
            self.cy + radius,
            fill=fill_color,
            outline=outline_color,
            width=1,
            state='hidden'
        )
        
        # 设置更新回调
        self.on_update = self._update_stone
    
    def _update_stone(self, scale: float):
        """更新棋子大小"""
        radius = self.cell_size * 0.45 * scale
        
        # 更新阴影
        if scale > 0.1:
            shadow_offset = 2 * scale
            self.canvas.coords(
                self.shadow,
                self.cx - radius + shadow_offset,
                self.cy - radius + shadow_offset,
                self.cx + radius + shadow_offset,
                self.cy + radius + shadow_offset
            )
            self.canvas.itemconfig(self.shadow, state='normal')
        
        # 更新棋子
        self.canvas.coords(
            self.temp_stone,
            self.cx - radius,
            self.cy - radius,
            self.cx + radius,
            self.cy + radius
        )
        self.canvas.itemconfig(self.temp_stone, state='normal')
    
    def cancel(self):
        """取消动画并清理"""
        super().cancel()
        if self.temp_stone:
            self.canvas.delete(self.temp_stone)
        if hasattr(self, 'shadow'):
            self.canvas.delete(self.shadow)


class CaptureAnimation(Animation):
    """吃子动画"""
    
    def __init__(self, canvas: tk.Canvas, stone_id: int, **kwargs):
        """
        初始化吃子动画
        
        Args:
            canvas: 画布
            stone_id: 棋子ID
        """
        # 提取或设置默认值
        duration = kwargs.pop('duration', 0.4)
        on_complete = kwargs.pop('on_complete', None)
        
        # 调用父类构造函数
        super().__init__(
            type=AnimationType.CAPTURE_STONE,
            target=stone_id,
            duration=duration
        )
        
        self.canvas = canvas
        self.stone_id = stone_id
        
        # 设置动画参数
        self.start_value = 1.0
        self.end_value = 0.0
        self.easing = EasingFunction.EASE_OUT
        
        # 保存原始位置
        self.original_coords = canvas.coords(stone_id)
        
        # 设置回调
        self.on_update = self._update_capture
        self.on_complete = self._complete_capture or on_complete
    
    def _update_capture(self, value: float):
        """更新吃子效果"""
        if value <= 0:
            self.canvas.itemconfig(self.stone_id, state='hidden')
            return
        
        # 缩小并淡出效果
        if self.original_coords and len(self.original_coords) == 4:
            x1, y1, x2, y2 = self.original_coords
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            radius = (x2 - x1) / 2 * value
            
            self.canvas.coords(
                self.stone_id,
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius
            )
        
        # 淡出效果（通过改变填充色实现）
        # 注意：Tkinter不支持直接的透明度，这里通过颜色渐变模拟
        gray_value = int(255 * (1 - value))
        color = f'#{gray_value:02x}{gray_value:02x}{gray_value:02x}'
        self.canvas.itemconfig(self.stone_id, fill=color)
    
    def _complete_capture(self):
        """完成吃子动画"""
        self.canvas.delete(self.stone_id)


class AnimationManager:
    """动画管理器"""
    
    def __init__(self, canvas: tk.Canvas, fps: int = 60):
        """
        初始化动画管理器
        
        Args:
            canvas: 画布
            fps: 帧率
        """
        self.canvas = canvas
        self.fps = fps
        self.frame_time = 1000 // fps  # 毫秒
        
        self.animations: List[Animation] = []
        self.is_running = False
        self.animation_loop_id = None
        
        # 动画设置
        self.enable_animations = True
        self.animation_speed = 1.0  # 速度倍数
    
    def add_animation(self, animation: Animation):
        """添加动画"""
        if not self.enable_animations:
            # 如果禁用动画，直接执行结果
            if animation.on_complete:
                animation.on_complete()
            return
        
        # 调整动画速度
        animation.duration /= self.animation_speed
        
        self.animations.append(animation)
        
        # 启动动画循环
        if not self.is_running:
            self.start()
    
    def start(self):
        """启动动画循环"""
        if not self.is_running:
            self.is_running = True
            self._animation_loop()
    
    def stop(self):
        """停止动画循环"""
        self.is_running = False
        if self.animation_loop_id:
            self.canvas.after_cancel(self.animation_loop_id)
            self.animation_loop_id = None
    
    def _animation_loop(self):
        """动画循环"""
        if not self.is_running:
            return
        
        current_time = time.time()
        completed_animations = []
        
        # 更新所有动画
        for animation in self.animations:
            if animation.update(current_time):
                completed_animations.append(animation)
        
        # 移除完成的动画
        for animation in completed_animations:
            self.animations.remove(animation)
        
        # 继续循环或停止
        if self.animations:
            self.animation_loop_id = self.canvas.after(
                self.frame_time, self._animation_loop
            )
        else:
            self.stop()
    
    def clear_animations(self):
        """清除所有动画"""
        for animation in self.animations:
            animation.cancel()
        self.animations.clear()
        self.stop()
    
    def create_stone_animation(self, x: int, y: int, color: str,
                              cell_size: int, margin: int,
                              on_complete: Optional[Callable] = None) -> StoneAnimation:
        """
        创建落子动画
        
        Args:
            x, y: 棋盘坐标
            color: 棋子颜色
            cell_size: 格子大小
            margin: 边距
            on_complete: 完成回调
            
        Returns:
            棋子动画对象
        """
        animation = StoneAnimation(
            canvas=self.canvas,
            x=x, y=y,
            color=color,
            cell_size=cell_size,
            margin=margin,
            on_complete=on_complete
        )
        
        self.add_animation(animation)
        return animation
    
    def create_capture_animation(self, stone_id: int,
                                on_complete: Optional[Callable] = None) -> CaptureAnimation:
        """
        创建吃子动画
        
        Args:
            stone_id: 棋子ID
            on_complete: 完成回调
            
        Returns:
            吃子动画对象
        """
        animation = CaptureAnimation(
            canvas=self.canvas,
            stone_id=stone_id,
            on_complete=on_complete
        )
        
        self.add_animation(animation)
        return animation
    
    def set_animation_speed(self, speed: float):
        """
        设置动画速度
        
        Args:
            speed: 速度倍数（1.0为正常速度）
        """
        self.animation_speed = max(0.1, min(10.0, speed))
    
    def toggle_animations(self, enable: bool):
        """
        切换动画开关
        
        Args:
            enable: 是否启用
        """
        self.enable_animations = enable
        if not enable:
            self.clear_animations()
