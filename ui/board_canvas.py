"""
棋盘绘制组件
负责棋盘的可视化展示、交互处理和动画效果
"""

import tkinter as tk
from tkinter import Canvas
import math
from typing import List, Tuple, Optional, Callable, Dict, Set
from PIL import Image, ImageDraw, ImageTk

from .themes import Theme
from .animations import AnimationManager


class BoardRenderer:
    """棋盘渲染器 - 负责绘制棋盘元素"""
    
    def __init__(self, canvas: Canvas, board_size: int, theme: Theme):
        """
        初始化渲染器
        
        Args:
            canvas: 画布
            board_size: 棋盘大小
            theme: 主题
        """
        self.canvas = canvas
        self.board_size = board_size
        self.theme = theme
        
        # 计算尺寸
        self.margin = 40
        self.update_dimensions()

        self.coord_offset_x = 0
        self.coord_offset_y = 0
        self.coord_board_size = board_size
        
        # 缓存的图形元素
        self.grid_lines = []
        self.star_points = []
        self.coordinates = []
        self.stones = {}  # (x, y) -> canvas_id
        self.markers = {}  # (x, y) -> canvas_id
        self.shadows = {}  # stone_id -> shadow_id
        
        # 预渲染的图片
        self.stone_images = {}
        self._prerender_stones()
    
    def update_dimensions(self):
        """更新尺寸计算"""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # 使用默认尺寸
            canvas_width = 600
            canvas_height = 600
        
        # 计算格子大小
        available_width = canvas_width - 2 * self.margin
        available_height = canvas_height - 2 * self.margin
        self.cell_size = min(
            available_width // (self.board_size - 1),
            available_height // (self.board_size - 1)
        )
        if self.cell_size < 1:
            self.cell_size = 1
        
        # 调整边距使棋盘居中
        board_width = (self.board_size - 1) * self.cell_size
        board_height = (self.board_size - 1) * self.cell_size
        self.margin_x = (canvas_width - board_width) // 2
        self.margin_y = (canvas_height - board_height) // 2
    
    def _prerender_stones(self):
        """预渲染棋子图片"""
        stone_radius = int(self.cell_size * 0.45)
        
        for color in ['black', 'white']:
            # 创建高质量的棋子图片
            size = stone_radius * 2 + 4
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # 绘制阴影
            if self.theme.enable_shadows:
                shadow_offset = 2
                shadow_color = (0, 0, 0, 80)
                draw.ellipse(
                    [shadow_offset, shadow_offset, 
                     size - 2 + shadow_offset, size - 2 + shadow_offset],
                    fill=shadow_color
                )
            
            # 绘制棋子主体
            if color == 'black':
                fill = (20, 20, 20, 255)
                border = self.theme.stone_black_border
            else:
                fill = (240, 240, 240, 255)
                border = self.theme.stone_white_border
            
            draw.ellipse([2, 2, size - 2, size - 2], fill=fill)
            
            # 添加高光效果
            if color == 'white':
                highlight_size = stone_radius // 2
                highlight_pos = (stone_radius // 3, stone_radius // 3)
                max_steps = min(3, highlight_size // 2 + 1)
                for i in range(max_steps):
                    alpha = 40 - i * 10
                    draw.ellipse(
                        [highlight_pos[0] + i, highlight_pos[1] + i,
                         highlight_pos[0] + highlight_size - i,
                         highlight_pos[1] + highlight_size - i],
                        fill=(255, 255, 255, alpha)
                    )
            else:
                # 黑子的微弱高光
                highlight_size = stone_radius // 3
                highlight_pos = (stone_radius // 4, stone_radius // 4)
                if highlight_size > 0:
                    draw.ellipse(
                        [highlight_pos[0], highlight_pos[1],
                         highlight_pos[0] + highlight_size,
                         highlight_pos[1] + highlight_size],
                        fill=(100, 100, 100, 30)
                    )
            
            # 转换为PhotoImage
            self.stone_images[color] = ImageTk.PhotoImage(img)
            
            # 创建半透明版本（用于预览）
            preview_img = img.copy()
            # 调整透明度，仅降低已有非透明区域的不透明度
            alpha_channel = preview_img.getchannel('A').point(lambda value: value // 2)
            preview_img.putalpha(alpha_channel)
            self.stone_images[f'{color}_preview'] = ImageTk.PhotoImage(preview_img)
    
    def draw_board(self):
        """绘制完整的棋盘"""
        self.clear()
        
        # 绘制背景
        self.draw_background()
        
        # 绘制网格
        self.draw_grid()
        
        # 绘制星位
        self.draw_star_points()
        
        # 绘制坐标（由 BoardCanvas.show_coordinates 控制）
        if getattr(self.canvas, 'show_coordinates', True):
            self.draw_coordinates()
    
    def clear(self):
        """清除所有绘制元素"""
        self.canvas.delete("all")
        self.grid_lines.clear()
        self.star_points.clear()
        self.coordinates.clear()
        self.stones.clear()
        self.markers.clear()
        self.shadows.clear()
    
    def draw_background(self):
        """绘制背景"""
        self.canvas.configure(bg=self.theme.board_background)
        
        # 可选：添加木纹纹理等效果
        if self.theme.name == 'classic':
            # 绘制木纹效果
            for i in range(0, self.canvas.winfo_width(), 5):
                color_var = 240 + (i % 20) - 10
                color = f'#{color_var:02x}{color_var-20:02x}{color_var-40:02x}'
                self.canvas.create_line(
                    i, 0, i, self.canvas.winfo_height(),
                    fill=color, width=5
                )
    
    def draw_grid(self):
        """绘制网格线"""
        for i in range(self.board_size):
            # 横线
            y = self.margin_y + i * self.cell_size
            line = self.canvas.create_line(
                self.margin_x, y,
                self.margin_x + (self.board_size - 1) * self.cell_size, y,
                fill=self.theme.board_grid_color,
                width=1
            )
            self.grid_lines.append(line)
            
            # 竖线
            x = self.margin_x + i * self.cell_size
            line = self.canvas.create_line(
                x, self.margin_y,
                x, self.margin_y + (self.board_size - 1) * self.cell_size,
                fill=self.theme.board_grid_color,
                width=1
            )
            self.grid_lines.append(line)
    
    def draw_star_points(self):
        """绘制星位"""
        coord_board_size = getattr(self, 'coord_board_size', self.board_size)
        offset_x = getattr(self, 'coord_offset_x', 0)
        offset_y = getattr(self, 'coord_offset_y', 0)
        star_positions = self._get_star_positions(coord_board_size)
        
        for x, y in star_positions:
            local_x = x - offset_x
            local_y = y - offset_y
            if not (0 <= local_x < self.board_size and 0 <= local_y < self.board_size):
                continue
            cx = self.margin_x + local_x * self.cell_size
            cy = self.margin_y + local_y * self.cell_size
            radius = max(3, self.cell_size // 10)
            
            star = self.canvas.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                fill=self.theme.board_star_color,
                outline=""
            )
            self.star_points.append(star)
    
    def _get_star_positions(self, board_size: Optional[int] = None) -> List[Tuple[int, int]]:
        """获取星位坐标"""
        size = board_size or self.board_size
        if size == 19:
            return [(3, 3), (3, 9), (3, 15), (9, 3), (9, 9),
                   (9, 15), (15, 3), (15, 9), (15, 15)]
        elif size == 13:
            return [(3, 3), (3, 9), (9, 3), (9, 9), (6, 6)]
        elif size == 9:
            return [(2, 2), (2, 6), (6, 2), (6, 6), (4, 4)]
        else:
            return []
    
    def draw_coordinates(self):
        """绘制坐标"""
        coord_board_size = getattr(self, 'coord_board_size', self.board_size)
        offset_x = getattr(self, 'coord_offset_x', 0)
        offset_y = getattr(self, 'coord_offset_y', 0)
        letters_full = 'ABCDEFGHJKLMNOPQRST'[:coord_board_size]
        
        for i in range(self.board_size):
            letter_index = offset_x + i
            letter = letters_full[letter_index] if 0 <= letter_index < len(letters_full) else '?'
            # 横坐标（字母）
            x = self.margin_x + i * self.cell_size
            
            # 上方坐标
            text = self.canvas.create_text(
                x, self.margin_y - 20,
                text=letter,
                fill=self.theme.board_coordinate_color,
                font=('Arial', 10)
            )
            self.coordinates.append(text)
            
            # 下方坐标
            text = self.canvas.create_text(
                x, self.margin_y + self.board_size * self.cell_size + 5,
                text=letter,
                fill=self.theme.board_coordinate_color,
                font=('Arial', 10)
            )
            self.coordinates.append(text)
            
            # 纵坐标（数字）
            y = self.margin_y + i * self.cell_size
            row_index = offset_y + i
            number = str(coord_board_size - row_index)
            
            # 左侧坐标
            text = self.canvas.create_text(
                self.margin_x - 20, y,
                text=number,
                fill=self.theme.board_coordinate_color,
                font=('Arial', 10)
            )
            self.coordinates.append(text)
            
            # 右侧坐标
            text = self.canvas.create_text(
                self.margin_x + self.board_size * self.cell_size + 5, y,
                text=number,
                fill=self.theme.board_coordinate_color,
                font=('Arial', 10)
            )
            self.coordinates.append(text)
    
    def place_stone(self, x: int, y: int, color: str) -> int:
        """
        放置棋子
        
        Args:
            x, y: 棋盘坐标
            color: 颜色
            
        Returns:
            棋子的canvas ID
        """
        cx = self.margin_x + x * self.cell_size
        cy = self.margin_y + y * self.cell_size
        
        # 移除旧棋子
        if (x, y) in self.stones:
            old_id = self.stones[(x, y)]
            self.canvas.delete(old_id)
            if old_id in self.shadows:
                self.canvas.delete(self.shadows[old_id])
        
        # 创建新棋子
        if color in self.stone_images:
            stone_id = self.canvas.create_image(
                cx, cy,
                image=self.stone_images[color],
                tags=('stone', f'{color}_stone', f'pos_{x}_{y}')
            )
        else:
            # 备用方案：使用简单圆形
            radius = self.cell_size * 0.45
            fill_color = 'black' if color == 'black' else 'white'
            outline_color = self.theme.stone_black_border if color == 'black' else self.theme.stone_white_border
            
            stone_id = self.canvas.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                fill=fill_color,
                outline=outline_color,
                width=1,
                tags=('stone', f'{color}_stone', f'pos_{x}_{y}')
            )
        
        self.stones[(x, y)] = stone_id
        return stone_id
    
    def remove_stone(self, x: int, y: int) -> Optional[int]:
        """
        移除棋子
        
        Args:
            x, y: 棋盘坐标
            
        Returns:
            被移除的棋子ID
        """
        if (x, y) in self.stones:
            stone_id = self.stones[(x, y)]
            del self.stones[(x, y)]
            return stone_id
        return None
    
    def show_preview(self, x: int, y: int, color: str):
        """
        显示落子预览
        
        Args:
            x, y: 棋盘坐标
            color: 颜色
        """
        if (x, y) in self.stones:
            return  # 已有棋子
        
        cx = self.margin_x + x * self.cell_size
        cy = self.margin_y + y * self.cell_size
        
        preview_key = f'{color}_preview'
        if preview_key in self.stone_images:
            self.canvas.create_image(
                cx, cy,
                image=self.stone_images[preview_key],
                tags=('preview',)
            )
        else:
            # 备用方案：半透明圆形
            radius = self.cell_size * 0.45
            fill_color = '#808080' if color == 'black' else '#C0C0C0'
            
            self.canvas.create_oval(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                fill=fill_color,
                outline='',
                stipple='gray50',
                tags=('preview',)
            )
    
    def clear_preview(self):
        """清除预览"""
        self.canvas.delete('preview')
    
    def mark_last_move(self, x: int, y: int):
        """
        标记最后一手
        
        Args:
            x, y: 棋盘坐标
        """
        # 清除旧标记
        self.canvas.delete('last_move_marker')
        
        cx = self.margin_x + x * self.cell_size
        cy = self.margin_y + y * self.cell_size
        radius = self.cell_size * 0.25
        
        self.canvas.create_oval(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            outline=self.theme.last_move_marker_color,
            width=2,
            tags=('last_move_marker',)
        )

    def _rgba_to_tk(self, color: str) -> Tuple[str, Optional[str]]:
        """
        将 `rgba(r, g, b, a)` 转为 Tk 可用颜色，并用 stipple 近似透明度。

        Tkinter 不支持 alpha 通道，因此这里用灰度网格模拟透明效果。
        """
        value = (color or "").strip()
        if not value.lower().startswith('rgba'):
            return value, None

        try:
            inside = value[value.find('(') + 1 : value.rfind(')')]
            parts = [p.strip() for p in inside.split(',')]
            r = int(float(parts[0]))
            g = int(float(parts[1]))
            b = int(float(parts[2]))
            a = float(parts[3]) if len(parts) >= 4 else 1.0
        except Exception:
            return '#808080', 'gray75'

        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        if a >= 0.9:
            return hex_color, None
        if a >= 0.5:
            return hex_color, 'gray50'
        return hex_color, 'gray75'
    
    def show_territory(self, territory_map: List[List[str]]):
        """
        显示地盘
        
        Args:
            territory_map: 地盘图
        """
        # 清除旧的地盘标记
        self.canvas.delete('territory')
        
        for y in range(self.board_size):
            for x in range(self.board_size):
                if territory_map[y][x] and (x, y) not in self.stones:
                    cx = self.margin_x + x * self.cell_size
                    cy = self.margin_y + y * self.cell_size
                    size = self.cell_size * 0.3
                    
                    if territory_map[y][x] == 'black':
                        color = self.theme.territory_black_color
                    elif territory_map[y][x] == 'white':
                        color = self.theme.territory_white_color
                    else:
                        color = self.theme.territory_neutral_color
                    
                    fill_color, stipple = self._rgba_to_tk(color)
                    kwargs = {
                        'fill': fill_color,
                        'outline': '',
                        'tags': ('territory',),
                    }
                    if stipple:
                        kwargs['stipple'] = stipple

                    self.canvas.create_rectangle(
                        cx - size, cy - size,
                        cx + size, cy + size,
                        **kwargs
                    )

    def show_influence(self, influence_map):
        """显示势力图（颜色 + stipple 近似强弱）。"""
        self.canvas.delete('influence')

        if influence_map is None:
            return

        # 计算最大势力用于归一化
        max_abs = 0.0
        try:
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if (x, y) in self.stones:
                        continue
                    v = float(influence_map[y, x])
                    if abs(v) > max_abs:
                        max_abs = abs(v)
        except Exception:
            return

        if max_abs <= 0.0:
            return

        size = self.cell_size * 0.38
        for y in range(self.board_size):
            for x in range(self.board_size):
                if (x, y) in self.stones:
                    continue

                v = float(influence_map[y, x])
                intensity = abs(v) / max_abs
                if intensity < 0.2:
                    continue

                # 黑方为正，白方为负
                base_color = '#2563eb' if v > 0 else '#ef4444'

                if intensity >= 0.66:
                    stipple = 'gray25'
                elif intensity >= 0.4:
                    stipple = 'gray50'
                else:
                    stipple = 'gray75'

                cx = self.margin_x + x * self.cell_size
                cy = self.margin_y + y * self.cell_size
                self.canvas.create_rectangle(
                    cx - size,
                    cy - size,
                    cx + size,
                    cy + size,
                    fill=base_color,
                    outline='',
                    stipple=stipple,
                    tags=('influence',),
                )

    def draw_move_numbers(self, move_numbers: Dict[Tuple[int, int], int]):
        """绘制手数（由 BoardCanvas.show_move_numbers 控制）。"""
        self.canvas.delete('move_number')

        if not move_numbers:
            return

        font_size = max(8, int(self.cell_size * 0.28))
        for (x, y), n in move_numbers.items():
            if not (0 <= x < self.board_size and 0 <= y < self.board_size):
                continue
            if (x, y) not in self.stones:
                continue

            try:
                stone_color = getattr(self.canvas, 'board_state', [['']])[y][x]
            except Exception:
                stone_color = ''

            text_color = 'white' if stone_color == 'black' else 'black'
            cx = self.margin_x + x * self.cell_size
            cy = self.margin_y + y * self.cell_size
            self.canvas.create_text(
                cx,
                cy,
                text=str(n),
                fill=text_color,
                font=('Arial', font_size, 'bold'),
                tags=('move_number',),
            )
    
    def mark_dead_stones(self, stones: Set[Tuple[int, int]]):
        """
        标记死子
        
        Args:
            stones: 死子坐标集合
        """
        # 清除旧标记
        self.canvas.delete('dead_stone_marker')
        
        for x, y in stones:
            if (x, y) in self.stones:
                cx = self.margin_x + x * self.cell_size
                cy = self.margin_y + y * self.cell_size
                size = self.cell_size * 0.3
                
                # 画X标记
                self.canvas.create_line(
                    cx - size, cy - size,
                    cx + size, cy + size,
                    fill=self.theme.dead_stone_marker_color,
                    width=2,
                    tags=('dead_stone_marker',)
                )
                self.canvas.create_line(
                    cx - size, cy + size,
                    cx + size, cy - size,
                    fill=self.theme.dead_stone_marker_color,
                    width=2,
                    tags=('dead_stone_marker',)
                )


class BoardCanvas(Canvas):
    """棋盘画布组件"""
    
    def __init__(self, parent, board_size: int = 19, theme: Optional[Theme] = None,
                 show_coordinates: bool = True, **kwargs):
        """
        初始化棋盘画布
        
        Args:
            parent: 父控件
            board_size: 棋盘大小
            theme: 主题
            show_coordinates: 是否显示坐标
        """
        super().__init__(parent, **kwargs)
        
        self.board_size = board_size
        self.theme = theme or Theme(name='default')
        self.show_coordinates = show_coordinates
        
        # 渲染器
        self.renderer = BoardRenderer(self, board_size, self.theme)
        
        # 动画管理器
        self.animation_manager = AnimationManager(self)
        
        # 棋盘状态
        self.board_state = [['' for _ in range(board_size)] for _ in range(board_size)]
        self.current_player = 'black'
        self.last_move: Optional[Tuple[int, int]] = None
        self.hover_pos: Optional[Tuple[int, int]] = None
        
        # 显示选项
        self.show_move_numbers = False
        self.move_numbers: Dict[Tuple[int, int], int] = {}
        self.show_territory = False
        self.territory_map = [['' for _ in range(board_size)] for _ in range(board_size)]
        self.show_influence = False
        self.influence_map = None

        # 数子/点目模式
        self.scoring_mode = False
        self._scoring_on_stone_click = None
        self._scoring_on_done = None
        self._dead_stones_marked: Set[Tuple[int, int]] = set()

        # 提示点（用于刷新后重绘）
        self._hint_pos: Optional[Tuple[int, int]] = None
        
        # 回调函数
        self.on_click: Optional[Callable[[int, int], None]] = None
        self.on_hover: Optional[Callable[[int, int], None]] = None
        self.on_right_click: Optional[Callable[[int, int], None]] = None
        
        # 绑定事件
        self._bind_events()
        
        # 配置画布
        self.configure(highlightthickness=0)
        
        # 延迟绘制（等待窗口尺寸确定）
        self.after(100, self.refresh)
    
    def _bind_events(self):
        """绑定事件处理器"""
        self.bind('<Button-1>', self._on_left_click)
        self.bind('<Button-3>', self._on_right_click)
        self.bind('<Motion>', self._on_mouse_move)
        self.bind('<Leave>', self._on_mouse_leave)
        self.bind('<Configure>', self._on_resize)
    
    def _on_left_click(self, event):
        """处理左键点击"""
        x, y = self._event_to_board_coords(event.x, event.y)
        
        if x is not None and y is not None:
            # 数子模式：点击棋子标记死活
            if self.scoring_mode and self._scoring_on_stone_click:
                try:
                    if self.board_state[y][x] != '':
                        self._scoring_on_stone_click(x, y)
                except Exception:
                    return
                return

            # 普通模式：调用回调
            if self.on_click:
                self.on_click(x, y)
    
    def _on_right_click(self, event):
        """处理右键点击"""
        x, y = self._event_to_board_coords(event.x, event.y)
        
        if x is not None and y is not None:
            # 数子模式：右键完成
            if self.scoring_mode and self._scoring_on_done:
                self._scoring_on_done()
                return
            if self.on_right_click:
                self.on_right_click(x, y)
    
    def _on_mouse_move(self, event):
        """处理鼠标移动"""
        x, y = self._event_to_board_coords(event.x, event.y)
        
        if x is not None and y is not None:
            if (x, y) != self.hover_pos:
                # 清除旧预览
                self.renderer.clear_preview()
                
                self.hover_pos = (x, y)
                
                # 调用回调
                if self.on_hover:
                    self.on_hover(x, y)
                else:
                    # 显示新预览（当没有外部 hover 回调时，使用内置预览逻辑）
                    if self.board_state[y][x] == '':
                        self.renderer.show_preview(x, y, self.current_player)
        else:
            self._on_mouse_leave(event)
    
    def _on_mouse_leave(self, event):
        """处理鼠标离开"""
        self.hover_pos = None
        self.renderer.clear_preview()
    
    def _on_resize(self, event):
        """处理窗口大小改变"""
        # 更新尺寸并重绘
        self.renderer.update_dimensions()
        self.renderer._prerender_stones()
        self.refresh()
    
    def _event_to_board_coords(self, event_x: int, event_y: int) -> Tuple[Optional[int], Optional[int]]:
        """
        将事件坐标转换为棋盘坐标
        
        Args:
            event_x, event_y: 事件坐标
            
        Returns:
            (x, y) 棋盘坐标，无效时返回 (None, None)
        """
        # 计算最近的交叉点
        x = round((event_x - self.renderer.margin_x) / self.renderer.cell_size)
        y = round((event_y - self.renderer.margin_y) / self.renderer.cell_size)
        
        # 检查是否在有效范围内
        if 0 <= x < self.board_size and 0 <= y < self.board_size:
            # 检查点击位置是否足够接近交叉点
            cx = self.renderer.margin_x + x * self.renderer.cell_size
            cy = self.renderer.margin_y + y * self.renderer.cell_size
            
            distance = math.sqrt((event_x - cx) ** 2 + (event_y - cy) ** 2)
            
            if distance <= self.renderer.cell_size * 0.4:
                return x, y
        
        return None, None
    
    def place_stone(self, x: int, y: int, color: str, animate: bool = True):
        """
        放置棋子
        
        Args:
            x, y: 棋盘坐标
            color: 颜色
            animate: 是否使用动画
        """
        if not (0 <= x < self.board_size and 0 <= y < self.board_size):
            return
        
        self.board_state[y][x] = color
        
        if animate and self.theme.enable_animations:
            # 使用动画放置
            self.animation_manager.create_stone_animation(
                x, y, color,
                self.renderer.cell_size,
                self.renderer.margin_x,
                on_complete=lambda: self.renderer.place_stone(x, y, color)
            )
        else:
            # 直接放置
            self.renderer.place_stone(x, y, color)
        
        # 清除预览
        self.renderer.clear_preview()
    
    def remove_stone(self, x: int, y: int, animate: bool = True):
        """
        移除棋子
        
        Args:
            x, y: 棋盘坐标
            animate: 是否使用动画
        """
        if not (0 <= x < self.board_size and 0 <= y < self.board_size):
            return
        
        self.board_state[y][x] = ''
        
        stone_id = self.renderer.remove_stone(x, y)
        
        if stone_id and animate and self.theme.enable_animations:
            # 使用动画移除
            self.animation_manager.create_capture_animation(stone_id)
        elif stone_id:
            # 直接删除
            self.delete(stone_id)
    
    def set_last_move(self, x: int, y: int):
        """设置最后一手"""
        self.last_move = (x, y)
        self.renderer.mark_last_move(x, y)
    
    def set_board_size(self, size: int, reset_coord: bool = True):
        """改变棋盘大小"""
        self.board_size = size
        self.renderer.board_size = size
        if reset_coord:
            self.renderer.coord_offset_x = 0
            self.renderer.coord_offset_y = 0
            self.renderer.coord_board_size = size
        self.board_state = [['' for _ in range(size)] for _ in range(size)]
        self.move_numbers.clear()
        self.territory_map = [['' for _ in range(size)] for _ in range(size)]
        self.influence_map = None
        self._dead_stones_marked = set()
        self._hint_pos = None
        self.renderer.update_dimensions()
        self.renderer._prerender_stones()
        self.refresh()
    
    def set_theme(self, theme: Theme):
        """设置主题"""
        self.theme = theme
        self.renderer.theme = theme
        self.renderer._prerender_stones()
        self.refresh()
    
    def set_current_player(self, color: str):
        """设置当前玩家"""
        self.current_player = color
    
    def clear_board(self):
        """清空棋盘"""
        self.board_state = [['' for _ in range(self.board_size)] 
                           for _ in range(self.board_size)]
        self.last_move = None
        self.move_numbers.clear()
        self._hint_pos = None
        self.delete('hint')
        self.refresh()
    
    def refresh(self):
        """刷新棋盘显示"""
        self.renderer.draw_board()
        
        # 重新绘制所有棋子
        for y in range(self.board_size):
            for x in range(self.board_size):
                if self.board_state[y][x]:
                    self.renderer.place_stone(x, y, self.board_state[y][x])
        
        # 显示手数（需在标记最后一手之前，避免遮挡最后一手标记）
        if self.show_move_numbers:
            self.renderer.draw_move_numbers(self.move_numbers)
        
        # 恢复最后一手标记
        if self.last_move:
            self.renderer.mark_last_move(*self.last_move)
        
        # 显示地盘
        if self.show_territory:
            self.renderer.show_territory(self.territory_map)

        # 显示势力
        if self.show_influence:
            self.renderer.show_influence(self.influence_map)

        # 数子模式下重绘死子标记
        if self.scoring_mode and self._dead_stones_marked:
            self.renderer.mark_dead_stones(self._dead_stones_marked)

        # 重绘提示点
        if self._hint_pos:
            self._draw_hint_marker(*self._hint_pos)
    
    def show_territory_map(self, territory_map: List[List[str]]):
        """显示地盘图"""
        self.territory_map = territory_map
        self.show_territory = True
        self.renderer.show_territory(territory_map)
    
    def hide_territory_map(self):
        """隐藏地盘图"""
        self.show_territory = False
        self.delete('territory')

    def show_influence_map(self, influence_map):
        """显示势力图"""
        self.influence_map = influence_map
        self.show_influence = True
        self.renderer.show_influence(influence_map)

    def hide_influence_map(self):
        """隐藏势力图"""
        self.show_influence = False
        self.influence_map = None
        self.delete('influence')
    
    def mark_dead_stones(self, stones: Set[Tuple[int, int]]):
        """标记死子"""
        self.renderer.mark_dead_stones(stones)
    
    def toggle_coordinates(self):
        """切换坐标显示"""
        self.show_coordinates = not self.show_coordinates
        self.refresh()
    
    def toggle_animations(self):
        """切换动画开关"""
        self.theme.enable_animations = not self.theme.enable_animations
        self.animation_manager.toggle_animations(self.theme.enable_animations)

    # --- 兼容 main.py 的方法（旧版 UI 调用） ---

    def update_board(self, board):
        """
        从 core.Board 同步棋盘显示。

        Args:
            board: core.board.Board 实例
        """
        try:
            size = board.size
        except Exception:
            return

        if size != self.board_size:
            self.set_board_size(size)

        self.board_state = [row[:] for row in board.grid]

        # 更新手数映射（用于显示手数）
        self.move_numbers.clear()
        try:
            history = getattr(board, 'stone_history', None) or []
            for stone in history:
                try:
                    x, y = int(stone.x), int(stone.y)
                    if not (0 <= x < size and 0 <= y < size):
                        continue
                    if board.grid[y][x] != stone.color:
                        continue
                    n = int(getattr(stone, 'move_number', 0) or 0)
                    if n > 0:
                        self.move_numbers[(x, y)] = n
                except Exception:
                    continue
        except Exception:
            pass

        # fallback：某些场景（例如悔棋/重做后）stone_history 可能不完整，可从 move_history 推导手数
        if not self.move_numbers:
            try:
                moves = getattr(board, 'move_history', None) or []
                for mv in moves:
                    try:
                        x, y = int(mv.x), int(mv.y)
                        if x < 0 or y < 0:
                            continue
                        if not (0 <= x < size and 0 <= y < size):
                            continue
                        if board.grid[y][x] != getattr(mv, 'color', ''):
                            continue
                        n = int(getattr(mv, 'move_number', 0) or 0)
                        if n > 0:
                            self.move_numbers[(x, y)] = n
                    except Exception:
                        continue
            except Exception:
                pass

        # 尝试根据棋子历史标记最后一手（如果有）
        last = None
        try:
            if getattr(board, 'stone_history', None):
                last_stone = board.stone_history[-1]
                last = (last_stone.x, last_stone.y)
        except Exception:
            last = None

        # fallback：从 move_history 推导最后一手（忽略虚手）
        if last is None:
            try:
                moves = getattr(board, 'move_history', None) or []
                for mv in reversed(moves):
                    try:
                        x, y = int(mv.x), int(mv.y)
                        if x < 0 or y < 0:
                            continue
                        if not (0 <= x < size and 0 <= y < size):
                            continue
                        if board.grid[y][x] != getattr(mv, 'color', ''):
                            continue
                        last = (x, y)
                        break
                    except Exception:
                        continue
            except Exception:
                pass

        self.last_move = last

        # 新局面刷新时清除提示点（避免过期提示）
        self._hint_pos = None
        self.delete('hint')
        self.refresh()

    def show_preview(self, x: int, y: int, color: str):
        """显示预览（供外部 hover 回调使用）。"""
        self.renderer.clear_preview()
        if 0 <= x < self.board_size and 0 <= y < self.board_size:
            if self.board_state[y][x] == '':
                self.renderer.show_preview(x, y, color)

    def show_hint(self, x: int, y: int):
        """显示提示标记（简单高亮）。"""
        self.delete('hint')
        self._hint_pos = None
        if not (0 <= x < self.board_size and 0 <= y < self.board_size):
            return
        self._hint_pos = (x, y)
        self._draw_hint_marker(x, y)

    def _draw_hint_marker(self, x: int, y: int):
        """内部：按当前尺寸重绘提示标记。"""
        self.delete('hint')
        cx = self.renderer.margin_x + x * self.renderer.cell_size
        cy = self.renderer.margin_y + y * self.renderer.cell_size
        radius = self.renderer.cell_size * 0.25
        self.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            outline='#ff8800',
            width=3,
            tags=('hint',),
        )

    def enter_scoring_mode(self, on_stone_click=None, on_done=None):
        """进入数子模式：点击棋子标记死活，右键完成。"""
        self.scoring_mode = True
        self._scoring_on_stone_click = on_stone_click
        self._scoring_on_done = on_done
        try:
            self.focus_set()
        except Exception:
            pass

    def update_dead_stones(self, dead_stones):
        """更新死子标记（使用现有的 X 标记）。"""
        try:
            self._dead_stones_marked = set(dead_stones)
            self.mark_dead_stones(set(dead_stones))
        except Exception:
            return

    def exit_scoring_mode(self):
        """退出数子模式（占位）。"""
        self.scoring_mode = False
        self._scoring_on_stone_click = None
        self._scoring_on_done = None
        self._dead_stones_marked = set()
        self.delete('dead_stone_marker')

    def set_show_coordinates(self, show: bool):
        self.show_coordinates = bool(show)
        self.refresh()

    def set_show_move_numbers(self, show: bool):
        self.show_move_numbers = bool(show)
        self.refresh()

    def set_highlight_last_move(self, show: bool):
        # 当前实现始终显示最后一手标记；保留接口避免崩溃
        if not show:
            self.delete('last_move_marker')
        else:
            if self.last_move:
                self.renderer.mark_last_move(*self.last_move)

    def set_coordinate_mapping(
        self,
        offset_x: int = 0,
        offset_y: int = 0,
        board_size: Optional[int] = None,
        refresh: bool = True,
    ):
        """设置坐标显示映射，用于预览裁切视图。"""
        self.renderer.coord_offset_x = max(0, int(offset_x))
        self.renderer.coord_offset_y = max(0, int(offset_y))
        self.renderer.coord_board_size = int(board_size) if board_size else self.board_size
        if refresh:
            self.refresh()

    def zoom(self, factor: float):
        # Tkinter Canvas 缩放会影响坐标换算，先保留接口避免崩溃
        return

    def reset_zoom(self):
        return

    def update_theme(self):
        """从当前 theme 重新渲染。"""
        self.set_theme(self.theme)
