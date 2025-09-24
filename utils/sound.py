"""
音效管理模块
处理游戏音效的加载和播放
"""

import os
import pygame
import threading
from typing import Dict, Optional, List
from pathlib import Path
from queue import Queue
import time


class SoundManager:
    """音效管理器"""
    
    # 音效文件映射
    SOUND_FILES = {
        'place_stone': 'place_stone.wav',
        'capture': 'capture.wav',
        'illegal': 'illegal.wav',
        'game_start': 'game_start.wav',
        'game_end': 'game_end.wav',
        'clock_tick': 'clock_tick.wav',
        'time_warning': 'time_warning.wav',
        'button_click': 'button_click.wav',
        'pass': 'pass.wav',
        'resign': 'resign.wav',
        'hint': 'hint.wav',
        'achievement': 'achievement.wav'
    }
    
    def __init__(self, config_manager=None):
        """
        初始化音效管理器
        
        Args:
            config_manager: 配置管理器
        """
        self.config = config_manager
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.enabled = True
        self.volume = 0.7
        self.initialized = False
        
        # 音效队列（避免同时播放过多音效）
        self.sound_queue = Queue()
        self.playing_thread = None
        self.stop_thread = False
        
        # 初始化pygame音频系统
        self._init_audio_system()
        
        # 加载配置
        if config_manager:
            self.enabled = config_manager.get('sound.enabled', True)
            self.volume = config_manager.get('sound.volume', 0.7)
        
        # 加载音效文件
        self.load_sounds()
        
        # 启动播放线程
        self._start_playing_thread()
    
    def _init_audio_system(self) -> bool:
        """初始化音频系统"""
        try:
            pygame.mixer.init(
                frequency=22050,
                size=-16,
                channels=2,
                buffer=512
            )
            self.initialized = True
            return True
        except Exception as e:
            print(f"初始化音频系统失败: {e}")
            self.initialized = False
            return False
    
    def load_sounds(self) -> None:
        """加载所有音效文件"""
        if not self.initialized:
            return
        
        # 确定音效目录
        from . import resource_path
        sound_dir = resource_path(os.path.join("assets", "sounds"))
        
        for name, filename in self.SOUND_FILES.items():
            file_path = os.path.join(sound_dir, filename)
            
            if os.path.exists(file_path):
                try:
                    sound = pygame.mixer.Sound(file_path)
                    sound.set_volume(self.volume)
                    self.sounds[name] = sound
                    print(f"已加载音效: {name}")
                except Exception as e:
                    print(f"加载音效 {name} 失败: {e}")
            else:
                # 尝试生成默认音效
                self._generate_default_sound(name)
    
    def _generate_default_sound(self, name: str) -> None:
        """生成默认音效（当文件不存在时）"""
        if not self.initialized:
            return
        
        try:
            # 创建简单的音效
            import numpy as np
            
            sample_rate = 22050
            duration = 0.1  # 100ms
            
            # 根据音效类型生成不同频率
            freq_map = {
                'place_stone': 440,  # A4
                'capture': 880,      # A5
                'illegal': 220,      # A3
                'button_click': 600,
                'pass': 330,         # E4
                'time_warning': 1000,
                'game_start': 523,   # C5
                'game_end': 262,     # C4
            }
            
            frequency = freq_map.get(name, 440)
            
            # 生成正弦波
            t = np.linspace(0, duration, int(sample_rate * duration))
            wave = np.sin(frequency * 2 * np.pi * t) * 0.3
            
            # 添加衰减
            envelope = np.exp(-t * 10)
            wave = wave * envelope
            
            # 转换为pygame格式
            wave = (wave * 32767).astype(np.int16)
            wave = np.repeat(wave.reshape(-1, 1), 2, axis=1)  # 立体声
            
            sound = pygame.sndarray.make_sound(wave)
            sound.set_volume(self.volume)
            self.sounds[name] = sound
            
        except Exception as e:
            print(f"生成默认音效 {name} 失败: {e}")
    
    def play(self, sound_name: str, force: bool = False) -> None:
        """
        播放音效
        
        Args:
            sound_name: 音效名称
            force: 是否强制播放（忽略设置）
        """
        if not self.initialized or (not self.enabled and not force):
            return
        
        if sound_name in self.sounds:
            self.sound_queue.put(sound_name)
    
    def play_immediate(self, sound_name: str) -> None:
        """立即播放音效（不排队）"""
        if not self.initialized or not self.enabled:
            return
        
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"播放音效失败: {e}")
    
    def _start_playing_thread(self) -> None:
        """启动音效播放线程"""
        if self.playing_thread and self.playing_thread.is_alive():
            return
        
        self.stop_thread = False
        self.playing_thread = threading.Thread(target=self._playing_worker, daemon=True)
        self.playing_thread.start()
    
    def _playing_worker(self) -> None:
        """音效播放工作线程"""
        while not self.stop_thread:
            try:
                # 获取待播放的音效（超时0.1秒）
                sound_name = self.sound_queue.get(timeout=0.1)
                
                if sound_name in self.sounds:
                    self.sounds[sound_name].play()
                    # 短暂延迟，避免音效重叠
                    time.sleep(0.05)
                    
            except:
                continue
    
    def set_enabled(self, enabled: bool) -> None:
        """设置音效开关"""
        self.enabled = enabled
        if self.config:
            self.config.set('sound.enabled', enabled)
    
    def set_volume(self, volume: float) -> None:
        """
        设置音量
        
        Args:
            volume: 音量（0.0 - 1.0）
        """
        self.volume = max(0.0, min(1.0, volume))
        
        # 更新所有音效的音量
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
        
        # 保存到配置
        if self.config:
            self.config.set('sound.volume', self.volume)
    
    def stop_all(self) -> None:
        """停止所有音效"""
        if self.initialized:
            pygame.mixer.stop()
    
    def pause_all(self) -> None:
        """暂停所有音效"""
        if self.initialized:
            pygame.mixer.pause()
    
    def resume_all(self) -> None:
        """恢复所有音效"""
        if self.initialized:
            pygame.mixer.unpause()
    
    def cleanup(self) -> None:
        """清理资源"""
        self.stop_thread = True
        if self.playing_thread:
            self.playing_thread.join(timeout=1.0)
        
        self.stop_all()
        self.sounds.clear()
        
        if self.initialized:
            pygame.mixer.quit()
            self.initialized = False
    
    def play_sequence(self, sound_names: List[str], interval: float = 0.2) -> None:
        """
        播放音效序列
        
        Args:
            sound_names: 音效名称列表
            interval: 音效间隔（秒）
        """
        def play_worker():
            for name in sound_names:
                self.play_immediate(name)
                time.sleep(interval)
        
        thread = threading.Thread(target=play_worker, daemon=True)
        thread.start()
    
    def create_custom_sound(self, name: str, file_path: str) -> bool:
        """
        添加自定义音效
        
        Args:
            name: 音效名称
            file_path: 音效文件路径
        
        Returns:
            是否成功
        """
        if not self.initialized or not os.path.exists(file_path):
            return False
        
        try:
            sound = pygame.mixer.Sound(file_path)
            sound.set_volume(self.volume)
            self.sounds[name] = sound
            return True
        except Exception as e:
            print(f"加载自定义音效失败: {e}")
            return False
    
    def get_channel_count(self) -> int:
        """获取可用音频通道数"""
        if self.initialized:
            return pygame.mixer.get_num_channels()
        return 0
    
    def set_channel_count(self, count: int) -> None:
        """设置音频通道数"""
        if self.initialized:
            pygame.mixer.set_num_channels(count)
    
    def __del__(self):
        """析构函数"""
        self.cleanup()